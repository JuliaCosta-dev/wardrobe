from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.outfit import Outfit
from app.models.outfit_usage import OutfitUsage


def create(
    db: Session,
    usage: OutfitUsage,
) -> OutfitUsage:
    """Adiciona uma utilização à sessão do banco."""

    db.add(usage)
    db.flush()

    return usage


def get_by_id(
    db: Session,
    usage_id: UUID,
    profile_id: UUID,
) -> OutfitUsage | None:
    """
    Busca uma utilização pertencente ao perfil autenticado.

    A consulta utiliza JOIN com Outfit para verificar o proprietário.
    Isso impede que um usuário consulte registros de outro perfil,
    mesmo que conheça o UUID da utilização.
    """

    statement = (
        select(OutfitUsage)
        .join(Outfit, Outfit.id == OutfitUsage.outfit_id)
        .where(
            OutfitUsage.id == usage_id,
            Outfit.profile_id == profile_id,
        )
    )

    return db.scalar(statement)


def list_by_outfit(
    db: Session,
    outfit_id: UUID,
    profile_id: UUID,
    skip: int,
    limit: int,
) -> tuple[list[OutfitUsage], int]:
    """Lista as utilizações de um look pertencente ao perfil."""

    base_statement = (
        select(OutfitUsage)
        .join(Outfit, Outfit.id == OutfitUsage.outfit_id)
        .where(
            OutfitUsage.outfit_id == outfit_id,
            Outfit.profile_id == profile_id,
        )
    )

    total_statement = select(func.count()).select_from(base_statement.subquery())

    total = db.scalar(total_statement) or 0

    statement = (
        base_statement.order_by(
            OutfitUsage.used_at.desc(),
            OutfitUsage.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(statement).all())

    return items, total


def list_by_profile(
    db: Session,
    profile_id: UUID,
    start_date: datetime | None,
    end_date: datetime | None,
    outfit_id: UUID | None,
    skip: int,
    limit: int,
) -> tuple[list[OutfitUsage], int]:
    """
    Lista todas as utilizações de looks do perfil.

    Os filtros são aplicados diretamente no banco, antes da
    paginação. Isso evita carregar todos os registros em memória.
    """

    base_statement = (
        select(OutfitUsage)
        .join(Outfit, Outfit.id == OutfitUsage.outfit_id)
        .where(Outfit.profile_id == profile_id)
    )

    if start_date is not None:
        base_statement = base_statement.where(OutfitUsage.used_at >= start_date)

    if end_date is not None:
        base_statement = base_statement.where(OutfitUsage.used_at <= end_date)

    if outfit_id is not None:
        base_statement = base_statement.where(OutfitUsage.outfit_id == outfit_id)

    total_statement = select(func.count()).select_from(base_statement.subquery())

    total = db.scalar(total_statement) or 0

    statement = (
        base_statement.order_by(
            OutfitUsage.used_at.desc(),
            OutfitUsage.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(statement).all())

    return items, total


def update(
    db: Session,
    usage: OutfitUsage,
    data: dict,
) -> OutfitUsage:
    """Atualiza somente os campos previamente validados pelo schema."""

    for field, value in data.items():
        setattr(usage, field, value)

    db.flush()

    return usage


def delete(
    db: Session,
    usage: OutfitUsage,
) -> None:
    """Remove um registro de utilização."""

    db.delete(usage)
    db.flush()
