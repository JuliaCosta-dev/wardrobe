from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outfit import Outfit
from app.repositories import outfit_repository as repository
from app.schemas.outfits import OutfitGenerateRequest
from app.services import outfit_generator

# Tempo durante o qual uma combinação participa do histórico.
OUTFIT_RETENTION_DAYS = 30


class OutfitGenerationError(Exception):
    """Erro de negócio durante a geração de um look."""


def generate_outfit(
    db: Session,
    profile_id: UUID,
    request: OutfitGenerateRequest,
) -> Outfit:
    """
    Gera e registra um look para o perfil autenticado.

    Toda a operação é executada em uma transação:
    - bloqueio do perfil;
    - remoção de looks vencidos;
    - consulta das peças;
    - geração de combinação;
    - gravação do look e seus itens.
    """

    now = datetime.now(UTC)

    try:
        # Serializa as gerações do mesmo perfil.
        # Isso reduz o risco de duas requisições simultâneas
        # registrarem a mesma combinação.
        profile = repository.lock_profile(db, profile_id)

        if profile is None:
            raise OutfitGenerationError("Perfil não encontrado.")

        # Remove registros vencidos antes de consultar o histórico.
        repository.delete_expired(
            db=db,
            profile_id=profile_id,
            now=now,
        )

        garments = repository.list_available_garments(
            db=db,
            profile_id=profile_id,
        )

        used_signatures = repository.list_recent_signatures(
            db=db,
            profile_id=profile_id,
            now=now,
        )

        try:
            candidate, signature = outfit_generator.generate_unique_combination(
                garments=garments,
                used_signatures=used_signatures,
                occasion=request.occasion,
                season=request.season,
                formality=request.formality,
            )
        except outfit_generator.OutfitCombinationError as error:
            # Confirma a limpeza dos registros vencidos mesmo quando
            # não foi possível gerar um novo look.
            db.commit()
            raise OutfitGenerationError(str(error)) from None

        outfit = Outfit(
            profile_id=profile_id,
            occasion=request.occasion,
            season=request.season,
            formality=request.formality,
            signature=signature,
            generated_at=now,
            expires_at=now + timedelta(days=OUTFIT_RETENTION_DAYS),
        )

        repository.save_outfit(
            db=db,
            outfit=outfit,
            garment_roles=candidate,
        )

        db.commit()

        # Reconsulta o registro para carregar os relacionamentos
        # que serão utilizados na resposta da API.
        saved_outfit = repository.get_by_id(
            db=db,
            outfit_id=outfit.id,
            profile_id=profile_id,
        )

        if saved_outfit is None:
            raise OutfitGenerationError("O look foi salvo, mas não foi possível recuperá-lo.")

        return saved_outfit

    except OutfitGenerationError:
        raise

    except Exception:
        db.rollback()
        raise


def get_outfit(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
) -> Outfit | None:
    """Busca um look válido pertencente ao perfil."""

    now = datetime.now(UTC)

    try:
        repository.delete_expired(db, profile_id, now)
        db.commit()

        outfit = repository.get_by_id(
            db=db,
            outfit_id=outfit_id,
            profile_id=profile_id,
        )

        if outfit is not None and outfit.expires_at <= now:
            return None

        return outfit

    except Exception:
        db.rollback()
        raise


def list_outfits(
    db: Session,
    profile_id: UUID,
    skip: int,
    limit: int,
):
    """Lista o histórico ainda válido do perfil."""

    now = datetime.now(UTC)

    try:
        repository.delete_expired(db, profile_id, now)
        db.commit()

        return repository.list_by_profile(
            db=db,
            profile_id=profile_id,
            now=now,
            skip=skip,
            limit=limit,
        )

    except Exception:
        db.rollback()
        raise
