from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.garment import Garment, GarmentImage


def get_garment(
    db: Session,
    garment_id: UUID,
    profile_id: UUID,
) -> Garment | None:
    """Busca uma peça pertencente ao perfil, sem bloqueá-la."""

    statement = select(Garment).where(
        Garment.id == garment_id,
        Garment.profile_id == profile_id,
    )

    return db.scalar(statement)


def get_garment_for_update(
    db: Session,
    garment_id: UUID,
    profile_id: UUID,
) -> Garment | None:
    """Busca e bloqueia a peça durante uma operação de escrita."""

    statement = (
        select(Garment)
        .where(
            Garment.id == garment_id,
            Garment.profile_id == profile_id,
        )
        .with_for_update()
    )

    return db.scalar(statement)


def get_by_id(
    db: Session,
    image_id: UUID,
    garment_id: UUID,
) -> GarmentImage | None:
    """Busca uma imagem pertencente a uma peça específica."""

    statement = select(GarmentImage).where(
        GarmentImage.id == image_id,
        GarmentImage.garment_id == garment_id,
    )

    return db.scalar(statement)


def list_by_garment(
    db: Session,
    garment_id: UUID,
) -> list[GarmentImage]:
    """Lista as imagens de uma peça."""

    statement = (
        select(GarmentImage)
        .where(GarmentImage.garment_id == garment_id)
        .order_by(
            GarmentImage.is_primary.desc(),
            GarmentImage.created_at.asc(),
        )
    )

    return list(db.scalars(statement).all())


def unset_primary_images(
    db: Session,
    garment_id: UUID,
) -> None:
    """Remove a indicação de imagem principal das imagens da peça."""

    statement = (
        update(GarmentImage).where(GarmentImage.garment_id == garment_id).values(is_primary=False)
    )

    db.execute(statement)


def save(
    db: Session,
    image: GarmentImage,
) -> GarmentImage:
    """Persiste uma imagem."""

    db.add(image)
    db.flush()
    db.refresh(image)

    return image


def delete(
    db: Session,
    image: GarmentImage,
) -> None:
    """Remove uma imagem do banco."""

    db.delete(image)
    db.flush()
