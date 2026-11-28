from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outfit import Outfit
from app.repositories import outfit_repository as repository
from app.schemas.outfits import OutfitGenerateRequest
from app.services import outfit_generator

# A validade controla somente a regra de não repetição.
# Ela não representa o tempo de armazenamento do histórico.
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
    """Gera e registra um look sem apagar o histórico anterior."""

    now = datetime.now(UTC)

    try:
        profile = repository.lock_profile(db, profile_id)

        if profile is None:
            raise OutfitGenerationError("Perfil não encontrado.")

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

        saved_outfit = repository.get_by_id(
            db=db,
            outfit_id=outfit.id,
            profile_id=profile_id,
        )

        if saved_outfit is None:
            raise OutfitGenerationError("O look foi salvo, mas não foi possível recuperá-lo.")

        return saved_outfit

    except OutfitGenerationError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


def get_outfit(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
) -> Outfit | None:
    """Consulta um look independentemente de sua data de expiração."""

    return repository.get_by_id(
        db=db,
        outfit_id=outfit_id,
        profile_id=profile_id,
    )


def list_outfits(
    db: Session,
    profile_id: UUID,
    skip: int,
    limit: int,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    occasion: str | None = None,
    season: str | None = None,
    formality: int | None = None,
    is_favorite: bool | None = None,
    order: str = "desc",
) -> tuple[list[Outfit], int]:
    """Lista o histórico permanente com filtros."""

    if start_date and end_date and start_date > end_date:
        raise ValueError("A data inicial não pode ser posterior à data final.")

    return repository.list_by_profile(
        db=db,
        profile_id=profile_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        occasion=occasion,
        season=season,
        formality=formality,
        is_favorite=is_favorite,
        order=order,
    )


def set_outfit_favorite(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
    *,
    is_favorite: bool,
) -> Outfit:
    """Favorita ou desfavorita um look do perfil autenticado."""

    try:
        outfit = repository.get_by_id(
            db=db,
            outfit_id=outfit_id,
            profile_id=profile_id,
            for_update=True,
        )

        if outfit is None:
            raise OutfitNotFoundError("Look não encontrado.")

        outfit.is_favorite = is_favorite

        db.commit()
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
    """Lista os favoritos do perfil, independentemente da expiração."""

    return repository.list_favorites(
        db=db,
        profile_id=profile_id,
        skip=skip,
        limit=limit,
    )
