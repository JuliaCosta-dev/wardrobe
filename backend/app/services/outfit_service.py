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


class OutfitNotFoundError(Exception):
    """Look não encontrado para o perfil autenticado."""


def generate_outfit(
    db: Session,
    profile_id: UUID,
    request: OutfitGenerateRequest,
) -> Outfit:
    """
    Gera e registra um look para o perfil autenticado.

    Toda a operação é executada em uma transação:
    - bloqueio do perfil;
    - remoção de looks vencidos não favoritados;
    - consulta das peças;
    - geração da combinação;
    - gravação do look e seus itens.
    """

    now = datetime.now(UTC)

    try:
        # Serializa as gerações do mesmo perfil.
        profile = repository.lock_profile(db, profile_id)

        if profile is None:
            raise OutfitGenerationError("Perfil não encontrado.")

        # Favoritos vencidos não são removidos por esta operação.
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
            # Confirma a limpeza dos looks vencidos mesmo quando
            # não foi possível gerar uma nova combinação.
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
            is_favorite=False,
        )

        repository.save_outfit(
            db=db,
            outfit=outfit,
            garment_roles=candidate,
        )

        db.commit()

        # Reconsulta o registro para carregar os relacionamentos.
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
    """
    Busca um look pertencente ao perfil.

    Looks vencidos não favoritados são removidos.
    Looks favoritados continuam acessíveis após a expiração.
    """

    now = datetime.now(UTC)

    try:
        repository.delete_expired(
            db,
            profile_id,
            now,
        )
        db.commit()

        outfit = repository.get_by_id(
            db=db,
            outfit_id=outfit_id,
            profile_id=profile_id,
        )

        if outfit is not None:
            # Proteção adicional para registros vencidos.
            if outfit.expires_at <= now and not outfit.is_favorite:
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
) -> tuple[list[Outfit], int]:
    """Lista o histórico ainda válido do perfil."""

    now = datetime.now(UTC)

    try:
        repository.delete_expired(
            db,
            profile_id,
            now,
        )
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


def set_outfit_favorite(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
    *,
    is_favorite: bool,
) -> Outfit:
    """
    Favorita ou desfavorita um look do perfil autenticado.

    A operação é idempotente:
    - favoritar um look já favoritado mantém True;
    - desfavoritar um look já desfavoritado mantém False.

    O bloqueio da linha evita alterações simultâneas conflitantes.
    """

    try:
        outfit = repository.get_by_id(
            db=db,
            outfit_id=outfit_id,
            profile_id=profile_id,
            for_update=True,
        )

        if outfit is None:
            raise OutfitNotFoundError("Look não encontrado.")

        # Um look vencido e não favoritado não deve ser
        # recuperado apenas porque alguém tentou favoritar.
        now = datetime.now(UTC)

        if outfit.expires_at <= now and not outfit.is_favorite:
            repository.delete_expired(
                db=db,
                profile_id=profile_id,
                now=now,
            )
            db.commit()
            raise OutfitNotFoundError("Look não encontrado.")

        outfit.is_favorite = is_favorite

        db.commit()

        # Atualiza os valores e relacionamentos após o commit.
        db.refresh(outfit)

        return (
            repository.get_by_id(
                db=db,
                outfit_id=outfit.id,
                profile_id=profile_id,
            )
            or outfit
        )

    except OutfitNotFoundError:
        raise

    except Exception:
        db.rollback()
        raise


def list_favorite_outfits(
    db: Session,
    profile_id: UUID,
    skip: int,
    limit: int,
) -> tuple[list[Outfit], int]:
    """Lista os favoritos do perfil, inclusive os já vencidos."""

    try:
        return repository.list_favorites(
            db=db,
            profile_id=profile_id,
            skip=skip,
            limit=limit,
        )

    except Exception:
        db.rollback()
        raise
