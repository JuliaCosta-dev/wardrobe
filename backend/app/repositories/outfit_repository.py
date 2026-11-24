from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.garment import Garment
from app.models.outfit import Outfit, OutfitItem
from app.models.profile import Profile


def lock_profile(
    db: Session,
    profile_id: UUID,
) -> Profile | None:
    """
    Bloqueia a linha do perfil durante a geração.

    SELECT FOR UPDATE impede que duas requisições simultâneas
    do mesmo perfil gerem e registrem a mesma combinação.
    """

    statement = select(Profile).where(Profile.id == profile_id).with_for_update()

    return db.scalar(statement)


def delete_expired(
    db: Session,
    profile_id: UUID,
    now: datetime,
) -> int:
    """
    Remove looks vencidos do perfil.

    A exclusão dos OutfitItems acontece pelo CASCADE
    configurado no banco de dados.
    """

    statement = (
        delete(Outfit)
        .where(
            Outfit.profile_id == profile_id,
            Outfit.expires_at <= now,
        )
        .returning(Outfit.id)
    )

    return len(db.scalars(statement).all())


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
    """Retorna as assinaturas de looks ainda dentro da validade."""

    statement = select(Outfit.signature).where(
        Outfit.profile_id == profile_id,
        Outfit.expires_at > now,
    )

    return set(db.scalars(statement).all())


def save_outfit(
    db: Session,
    outfit: Outfit,
    garment_roles: list[tuple[Garment, str]],
) -> Outfit:
    """
    Persiste o look e suas peças em uma única transação.

    Se alguma associação falhar, a transação poderá ser revertida
    sem deixar um look parcialmente cadastrado.
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
) -> Outfit | None:
    """
    Busca um look com suas peças e respectivas imagens.

    Os relacionamentos são carregados antecipadamente
    para evitar consultas adicionais durante a serialização.
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

    return db.scalar(statement)


def list_by_profile(
    db: Session,
    profile_id: UUID,
    now: datetime,
    skip: int,
    limit: int,
) -> tuple[list[Outfit], int]:
    """
    Lista looks válidos com paginação.

    Carrega as peças e suas imagens em consultas agrupadas,
    evitando o problema N+1.
    """

    base_statement = select(Outfit).where(
        Outfit.profile_id == profile_id,
        Outfit.expires_at > now,
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
