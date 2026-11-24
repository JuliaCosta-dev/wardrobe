from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_profile
from app.models.outfit import Outfit
from app.models.profile import Profile
from app.schemas.outfits import (
    OutfitGenerateRequest,
    OutfitList,
    OutfitRead,
)
from app.services import outfit_service

router = APIRouter(
    prefix="/outfits",
    tags=["Outfits"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedProfile = Annotated[Profile, Depends(get_current_profile)]


@router.post(
    "/generate",
    response_model=OutfitRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_outfit(
    data: OutfitGenerateRequest,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> Outfit:
    """
    Gera automaticamente uma combinação de roupas.

    O cliente informa somente o contexto.
    A seleção das peças é feita pelo serviço de geração.
    """

    try:
        return outfit_service.generate_outfit(
            db=db,
            profile_id=profile.id,
            request=data,
        )

    except outfit_service.OutfitGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from None


@router.get(
    "",
    response_model=OutfitList,
)
def list_outfits(
    db: DatabaseSession,
    profile: AuthenticatedProfile,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OutfitList:
    """Lista os looks ainda válidos do perfil autenticado."""

    items, total = outfit_service.list_outfits(
        db=db,
        profile_id=profile.id,
        skip=skip,
        limit=limit,
    )

    return OutfitList(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{outfit_id}",
    response_model=OutfitRead,
)
def read_outfit(
    outfit_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> Outfit:
    """Consulta um look específico do perfil autenticado."""

    outfit = outfit_service.get_outfit(
        db=db,
        profile_id=profile.id,
        outfit_id=outfit_id,
    )

    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Look não encontrado.",
        )

    return outfit
