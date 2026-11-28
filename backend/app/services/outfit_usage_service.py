from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outfit import Outfit
from app.models.outfit_usage import OutfitUsage
from app.repositories import outfit_usage_repository as repository
from app.schemas.outfit_usages import OutfitUsageCreate, OutfitUsageUpdate


class OutfitUsageNotFoundError(Exception):
    """Look ou registro de utilização não encontrado."""


class InvalidOutfitUsageError(Exception):
    """Dados de utilização incompatíveis com as regras de negócio."""


def create_usage(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
    data: OutfitUsageCreate,
) -> OutfitUsage:
    """
    Registra a utilização real de um look.

    A consulta do look sempre considera o profile_id autenticado.
    O cliente não escolhe o proprietário do registro.
    """

    try:
        outfit = db.scalar(
            select(Outfit).where(
                Outfit.id == outfit_id,
                Outfit.profile_id == profile_id,
            )
        )
        if outfit is None:
            raise OutfitUsageNotFoundError("Look não encontrado.")

        usage = OutfitUsage(
            outfit_id=outfit.id,
            used_at=data.used_at,
            notes=data.notes,
        )

        repository.create(db, usage)
        db.commit()
        db.refresh(usage)

        return usage

    except OutfitUsageNotFoundError:
        raise

    except Exception:
        db.rollback()
        raise


def select_outfit_statement(
    outfit_id: UUID,
    profile_id: UUID,
):
    """Monta uma consulta limitada ao perfil proprietário."""

    from sqlalchemy import select

    return select(Outfit).where(
        Outfit.id == outfit_id,
        Outfit.profile_id == profile_id,
    )


def list_outfit_usages(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
    skip: int,
    limit: int,
) -> tuple[list[OutfitUsage], int]:
    """Lista as utilizações de um look específico."""

    try:
        return repository.list_by_outfit(
            db=db,
            outfit_id=outfit_id,
            profile_id=profile_id,
            skip=skip,
            limit=limit,
        )

    except Exception:
        db.rollback()
        raise


def list_profile_usages(
    db: Session,
    profile_id: UUID,
    start_date: datetime | None,
    end_date: datetime | None,
    outfit_id: UUID | None,
    skip: int,
    limit: int,
) -> tuple[list[OutfitUsage], int]:
    """Lista o histórico geral de utilizações do perfil."""

    if start_date and end_date and start_date > end_date:
        raise InvalidOutfitUsageError("A data inicial não pode ser posterior à data final.")

    try:
        return repository.list_by_profile(
            db=db,
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
            outfit_id=outfit_id,
            skip=skip,
            limit=limit,
        )

    except Exception:
        db.rollback()
        raise


def get_usage(
    db: Session,
    profile_id: UUID,
    usage_id: UUID,
) -> OutfitUsage:
    """Consulta uma utilização pertencente ao perfil."""

    usage = repository.get_by_id(
        db=db,
        usage_id=usage_id,
        profile_id=profile_id,
    )

    if usage is None:
        raise OutfitUsageNotFoundError("Registro de utilização não encontrado.")

    return usage


def update_usage(
    db: Session,
    profile_id: UUID,
    usage_id: UUID,
    data: OutfitUsageUpdate,
) -> OutfitUsage:
    """Atualiza a data ou as observações de uma utilização."""

    usage = get_usage(
        db=db,
        profile_id=profile_id,
        usage_id=usage_id,
    )

    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise InvalidOutfitUsageError("Informe pelo menos um campo para atualização.")

    try:
        repository.update(
            db=db,
            usage=usage,
            data=changes,
        )

        db.commit()
        db.refresh(usage)

        return usage

    except Exception:
        db.rollback()
        raise


def delete_usage(
    db: Session,
    profile_id: UUID,
    usage_id: UUID,
) -> None:
    """Exclui somente o registro de utilização, não o look."""

    usage = get_usage(
        db=db,
        profile_id=profile_id,
        usage_id=usage_id,
    )

    try:
        repository.delete(db, usage)
        db.commit()

    except Exception:
        db.rollback()
        raise


def ensure_outfit_exists(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
) -> None:
    """Garante que o look pertence ao perfil autenticado."""

    from sqlalchemy import select

    outfit = db.scalar(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.profile_id == profile_id,
        )
    )

    if outfit is None:
        raise OutfitUsageNotFoundError("Look não encontrado.")
