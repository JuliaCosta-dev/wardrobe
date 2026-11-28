from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.garment import Garment
from app.models.outfit import Outfit, OutfitItem
from app.models.profile import Profile


def lock_profile(
    db: Session,
    profile_id: UUID,
) -> Profile | None:
    """
    Bloqueia a linha do perfil durante a geração de looks.

    SELECT FOR UPDATE evita que duas gerações simultâneas
    do mesmo perfil registrem a mesma combinação.
    """
    statement = select(Profile).where(Profile.id == profile_id).with_for_update()

    return db.scalar(statement)


def list_available_garments(
    db: Session,
    profile_id: UUID,
) -> list[Garment]:
    """
    Busca somente peças disponíveis pertencentes ao perfil.

    A filtragem por profile_id é uma regra de segurança:
    nunca buscamos peças de outros usuários.
    """
    statement = (
        select(Garment)
        .where(
            Garment.profile_id == profile_id,
            Garment.status == "available",
        )
        .order_by(Garment.created_at.asc())
    )

    return list(db.scalars(statement).all())


def list_recent_signatures(
    db: Session,
    profile_id: UUID,
    now: datetime,
) -> set[str]:
    """
    Retorna somente combinações ainda dentro do período de
    não repetição ou que estejam favoritando a combinação.

    A expiração deixa de excluir o registro do histórico.
    Ela apenas permite que a combinação volte a ser gerada.
    """
    statement = select(Outfit.signature).where(
        Outfit.profile_id == profile_id,
        ((Outfit.expires_at > now) | Outfit.is_favorite.is_(True)),
    )

    return set(db.scalars(statement).all())


def save_outfit(
    db: Session,
    outfit: Outfit,
    garment_roles: list[tuple[Garment, str]],
) -> Outfit:
    """
    Persiste o look e suas peças em uma única transação.

    Se alguma associação falhar, a transação poderá ser
    revertida sem deixar um look parcialmente cadastrado.
    """
    db.add(outfit)
    db.flush()

    for garment, role in garment_roles:
        db.add(
            OutfitItem(
                outfit_id=outfit.id,
                garment_id=garment.id,
                role=role,
            )
        )

    db.flush()

    return outfit


def get_by_id(
    db: Session,
    outfit_id: UUID,
    profile_id: UUID,
    *,
    for_update: bool = False,
) -> Outfit | None:
    """
    Busca um look pertencente ao perfil informado.

    Os relacionamentos são carregados antecipadamente para
    evitar consultas adicionais durante a serialização.

    for_update bloqueia a linha quando uma operação precisa
    alterar o estado do look.
    """
    statement = (
        select(Outfit)
        .where(
            Outfit.id == outfit_id,
            Outfit.profile_id == profile_id,
        )
        .options(
            selectinload(Outfit.items).selectinload(OutfitItem.garment).selectinload(Garment.images)
        )
    )

    if for_update:
        statement = statement.with_for_update()

    return db.scalar(statement)


def list_by_profile(
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
    """
    Lista todo o histórico permanente do perfil com filtros.
    """
    base_statement = select(Outfit).where(
        Outfit.profile_id == profile_id,
    )

    if start_date is not None:
        base_statement = base_statement.where(Outfit.generated_at >= start_date)

    if end_date is not None:
        base_statement = base_statement.where(Outfit.generated_at <= end_date)

    if occasion is not None:
        base_statement = base_statement.where(Outfit.occasion == occasion)

    if season is not None:
        base_statement = base_statement.where(Outfit.season == season)

    if formality is not None:
        base_statement = base_statement.where(Outfit.formality == formality)

    if is_favorite is not None:
        base_statement = base_statement.where(Outfit.is_favorite.is_(is_favorite))

    total_statement = select(func.count()).select_from(base_statement.subquery())

    total = db.scalar(total_statement) or 0

    sort_column = Outfit.generated_at.asc() if order == "asc" else Outfit.generated_at.desc()

    statement = (
        base_statement.options(
            selectinload(Outfit.items).selectinload(OutfitItem.garment).selectinload(Garment.images)
        )
        .order_by(sort_column)
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(statement).all())

    return items, total


def list_favorites(
    db: Session,
    profile_id: UUID,
    skip: int,
    limit: int,
) -> tuple[list[Outfit], int]:
    """
    Lista os looks favoritados do perfil.

    Não filtra expires_at: um look favoritado continua
    disponível mesmo depois do prazo normal de retenção.
    """
    base_statement = select(Outfit).where(
        Outfit.profile_id == profile_id,
        Outfit.is_favorite.is_(True),
    )

    total_statement = select(func.count()).select_from(base_statement.subquery())

    total = db.scalar(total_statement) or 0

    statement = (
        base_statement.options(
            selectinload(Outfit.items).selectinload(OutfitItem.garment).selectinload(Garment.images)
        )
        .order_by(Outfit.generated_at.desc())
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(statement).all())

    return items, total
