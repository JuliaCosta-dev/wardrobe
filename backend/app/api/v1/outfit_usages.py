from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_profile
from app.models.profile import Profile
from app.schemas.outfit_usages import (
    OutfitUsageCreate,
    OutfitUsageList,
    OutfitUsageRead,
    OutfitUsageUpdate,
)
from app.services import outfit_usage_service as service

router = APIRouter(tags=["Outfit Usages"])

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedProfile = Annotated[Profile, Depends(get_current_profile)]


@router.post(
    "/outfits/{outfit_id}/usages",
    response_model=OutfitUsageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_usage(
    outfit_id: UUID,
    data: OutfitUsageCreate,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> OutfitUsageRead:
    """Registra uma utilização real de um look."""

    try:
        return service.create_usage(
            db=db,
            profile_id=profile.id,
            outfit_id=outfit_id,
            data=data,
        )

    except service.OutfitUsageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Look não encontrado.",
        ) from None


@router.get(
    "/outfits/{outfit_id}/usages",
    response_model=OutfitUsageList,
)
def list_outfit_usages(
    outfit_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OutfitUsageList:
    """Lista as utilizações de um look."""

    try:
        items, total = service.list_outfit_usages(
            db=db,
            profile_id=profile.id,
            outfit_id=outfit_id,
            skip=skip,
            limit=limit,
        )

    except service.OutfitUsageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Look não encontrado.",
        ) from None

    # A listagem vazia não distingue um look inexistente de um
    # look sem utilizações. Verificamos a propriedade do look.
    from sqlalchemy import select

    from app.models.outfit import Outfit

    outfit = db.scalar(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.profile_id == profile.id,
        )
    )

    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Look não encontrado.",
        )

    return OutfitUsageList(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/outfit-usages",
    response_model=OutfitUsageList,
)
def list_profile_usages(
    db: DatabaseSession,
    profile: AuthenticatedProfile,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    outfit_id: UUID | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OutfitUsageList:
    """Lista o histórico geral de utilizações do perfil."""

    try:
        items, total = service.list_profile_usages(
            db=db,
            profile_id=profile.id,
            start_date=start_date,
            end_date=end_date,
            outfit_id=outfit_id,
            skip=skip,
            limit=limit,
        )

    except service.InvalidOutfitUsageError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None

    return OutfitUsageList(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/outfit-usages/{usage_id}",
    response_model=OutfitUsageRead,
)
def get_usage(
    usage_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> OutfitUsageRead:
    """Consulta uma utilização."""

    try:
        return service.get_usage(
            db=db,
            profile_id=profile.id,
            usage_id=usage_id,
        )

    except service.OutfitUsageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de utilização não encontrado.",
        ) from None


@router.patch(
    "/outfit-usages/{usage_id}",
    response_model=OutfitUsageRead,
)
def update_usage(
    usage_id: UUID,
    data: OutfitUsageUpdate,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> OutfitUsageRead:
    """Atualiza uma utilização."""

    try:
        return service.update_usage(
            db=db,
            profile_id=profile.id,
            usage_id=usage_id,
            data=data,
        )

    except service.OutfitUsageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de utilização não encontrado.",
        ) from None

    except service.InvalidOutfitUsageError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None


@router.delete(
    "/outfit-usages/{usage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_usage(
    usage_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> Response:
    """Remove um registro de utilização sem excluir o look."""

    try:
        service.delete_usage(
            db=db,
            profile_id=profile.id,
            usage_id=usage_id,
        )

    except service.OutfitUsageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de utilização não encontrado.",
        ) from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)
