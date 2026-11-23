from uuid import UUID

from sqlalchemy.orm import Session

from app.models.garment import GarmentImage
from app.repositories import garment_image_repository as repository
from app.services import image_storage


class GarmentNotFoundError(Exception):
    """A peça não existe ou não pertence ao perfil autenticado."""


class GarmentImageNotFoundError(Exception):
    """A imagem não existe ou não pertence à peça."""


def list_images(
    db: Session,
    garment_id: UUID,
    profile_id: UUID,
) -> list[GarmentImage]:
    """Lista imagens de uma peça pertencente ao perfil."""

    garment = repository.get_garment(
        db,
        garment_id,
        profile_id,
    )

    if garment is None:
        raise GarmentNotFoundError

    return repository.list_by_garment(db, garment.id)


def upload_image(
    db: Session,
    garment_id: UUID,
    profile_id: UUID,
    original_bytes: bytes,
    is_primary: bool,
) -> GarmentImage:
    """Valida, processa, armazena e associa uma imagem à peça."""

    garment = repository.get_garment_for_update(
        db,
        garment_id,
        profile_id,
    )

    if garment is None:
        raise GarmentNotFoundError

    processed_bytes, width, height = image_storage.process_image(original_bytes)

    existing_images = repository.list_by_garment(db, garment.id)

    should_be_primary = is_primary or not existing_images

    storage_key = image_storage.save_image(processed_bytes)

    try:
        if should_be_primary:
            repository.unset_primary_images(db, garment.id)

        image = GarmentImage(
            garment_id=garment.id,
            storage_key=storage_key,
            mime_type="image/webp",
            width=width,
            height=height,
            is_primary=should_be_primary,
        )

        repository.save(db, image)
        db.commit()
        db.refresh(image)

        return image

    except Exception:
        db.rollback()

        try:
            image_storage.delete_image(storage_key)
        except OSError:
            pass

        raise


def get_image(
    db: Session,
    garment_id: UUID,
    image_id: UUID,
    profile_id: UUID,
) -> tuple[GarmentImage, bytes]:
    """Localiza e lê uma imagem após validar a propriedade da peça."""

    garment = repository.get_garment(
        db,
        garment_id,
        profile_id,
    )

    if garment is None:
        raise GarmentNotFoundError

    image = repository.get_by_id(db, image_id, garment.id)

    if image is None:
        raise GarmentImageNotFoundError

    try:
        content = image_storage.read_image(image.storage_key)
    except FileNotFoundError:
        raise GarmentImageNotFoundError("Arquivo da imagem não encontrado.") from None

    return image, content


def set_primary_image(
    db: Session,
    garment_id: UUID,
    image_id: UUID,
    profile_id: UUID,
) -> GarmentImage:
    """Define uma imagem como principal da peça."""

    garment = repository.get_garment_for_update(
        db,
        garment_id,
        profile_id,
    )

    if garment is None:
        raise GarmentNotFoundError

    image = repository.get_by_id(db, image_id, garment.id)

    if image is None:
        raise GarmentImageNotFoundError

    try:
        repository.unset_primary_images(db, garment.id)
        image.is_primary = True

        db.commit()
        db.refresh(image)

        return image

    except Exception:
        db.rollback()
        raise


def delete_image(
    db: Session,
    garment_id: UUID,
    image_id: UUID,
    profile_id: UUID,
) -> None:
    """Exclui uma imagem e atualiza a imagem principal, se necessário."""

    garment = repository.get_garment_for_update(
        db,
        garment_id,
        profile_id,
    )

    if garment is None:
        raise GarmentNotFoundError

    image = repository.get_by_id(db, image_id, garment.id)

    if image is None:
        raise GarmentImageNotFoundError

    storage_key = image.storage_key
    was_primary = image.is_primary

    try:
        repository.delete(db, image)

        remaining_images = repository.list_by_garment(
            db,
            garment.id,
        )

        if was_primary and remaining_images:
            remaining_images[0].is_primary = True

        db.commit()

    except Exception:
        db.rollback()
        raise

    try:
        image_storage.delete_image(storage_key)
    except OSError:
        # A linha do banco já foi removida. Uma falha física de limpeza
        # não deve transformar a exclusão confirmada em erro para o cliente.
        pass
