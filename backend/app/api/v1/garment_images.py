from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_profile
from app.models.garment import GarmentImage
from app.models.profile import Profile
from app.schemas.garment_images import GarmentImageRead
from app.services import garment_image_service, image_storage

router = APIRouter(
    prefix="/garments",
    tags=["Garment Images"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedProfile = Annotated[Profile, Depends(get_current_profile)]


def handle_not_found(error: Exception) -> HTTPException:
    """Converte erros de domínio em respostas HTTP."""

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error) or "Peça ou imagem não encontrada.",
    )


@router.post(
    "/{garment_id}/images",
    response_model=GarmentImageRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_garment_image(
    garment_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
    file: Annotated[UploadFile, File()],
    is_primary: Annotated[bool, Form()] = False,
) -> GarmentImage:
    """Envia uma imagem para uma peça do perfil autenticado."""

    try:
        original_bytes = file.file.read(image_storage.MAX_UPLOAD_SIZE + 1)

        image = garment_image_service.upload_image(
            db=db,
            garment_id=garment_id,
            profile_id=profile.id,
            original_bytes=original_bytes,
            is_primary=is_primary,
        )

        return image

    except image_storage.ImageValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None

    except garment_image_service.GarmentNotFoundError as error:
        raise handle_not_found(error) from None


@router.get(
    "/{garment_id}/images",
    response_model=list[GarmentImageRead],
)
def list_garment_images(
    garment_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> list[GarmentImage]:
    """Lista as imagens de uma peça."""

    try:
        return garment_image_service.list_images(
            db=db,
            garment_id=garment_id,
            profile_id=profile.id,
        )

    except garment_image_service.GarmentNotFoundError as error:
        raise handle_not_found(error) from None


@router.get(
    "/{garment_id}/images/{image_id}",
)
def read_garment_image(
    garment_id: UUID,
    image_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> Response:
    """Entrega os bytes de uma imagem após validar sua propriedade."""

    try:
        image, content = garment_image_service.get_image(
            db=db,
            garment_id=garment_id,
            image_id=image_id,
            profile_id=profile.id,
        )

    except (
        garment_image_service.GarmentNotFoundError,
        garment_image_service.GarmentImageNotFoundError,
    ) as error:
        raise handle_not_found(error) from None

    return Response(
        content=content,
        media_type=image.mime_type,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": 'inline; filename="garment.webp"',
        },
    )


@router.patch(
    "/{garment_id}/images/{image_id}/primary",
    response_model=GarmentImageRead,
)
def make_primary_image(
    garment_id: UUID,
    image_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> GarmentImage:
    """Define uma imagem como principal."""

    try:
        return garment_image_service.set_primary_image(
            db=db,
            garment_id=garment_id,
            image_id=image_id,
            profile_id=profile.id,
        )

    except (
        garment_image_service.GarmentNotFoundError,
        garment_image_service.GarmentImageNotFoundError,
    ) as error:
        raise handle_not_found(error) from None


@router.delete(
    "/{garment_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_garment_image(
    garment_id: UUID,
    image_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> Response:
    """Exclui uma imagem pertencente a uma peça do perfil."""

    try:
        garment_image_service.delete_image(
            db=db,
            garment_id=garment_id,
            image_id=image_id,
            profile_id=profile.id,
        )

    except (
        garment_image_service.GarmentNotFoundError,
        garment_image_service.GarmentImageNotFoundError,
    ) as error:
        raise handle_not_found(error) from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)
