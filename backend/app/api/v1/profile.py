from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import (
    ProfilePreferences,
    ProfileRead,
    ProfileUpdate,
)
from app.services import profile_service

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]


def get_existing_profile(
    db: Session,
    user_id,
) -> Profile:
    """Busca o perfil ou retorna 404."""

    profile = profile_service.get_profile(db, user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    return profile


@router.get(
    "/me",
    response_model=ProfileRead,
)
def read_profile(
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> Profile:
    """Retorna o perfil do usuário autenticado."""

    return get_existing_profile(db, current_user.id)


@router.patch(
    "/me",
    response_model=ProfileRead,
)
def update_profile(
    data: ProfileUpdate,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> Profile:
    """Atualiza os dados básicos do perfil."""

    changes = data.model_dump(exclude_unset=True)

    profile = profile_service.update_profile(
        db=db,
        user_id=current_user.id,
        changes=changes,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    return profile


@router.get(
    "/preferences",
    response_model=ProfilePreferences,
)
def read_preferences(
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> ProfilePreferences:
    """Retorna as preferências do usuário."""

    preferences = profile_service.get_preferences(
        db=db,
        user_id=current_user.id,
    )

    if preferences is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    return preferences


@router.patch(
    "/preferences",
    response_model=ProfilePreferences,
)
def update_preferences(
    data: ProfilePreferences,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> ProfilePreferences:
    """Atualiza as preferências do usuário."""

    changes = data.model_dump(exclude_unset=True)

    preferences = profile_service.update_preferences(
        db=db,
        user_id=current_user.id,
        changes=changes,
    )

    if preferences is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    return preferences
