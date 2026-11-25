from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_profile
from app.models.profile import Profile
from app.schemas.recommendation_feedback import (
    RecommendationFeedbackCreate,
    RecommendationFeedbackRead,
)
from app.services import recommendation_feedback_service as service

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendation Feedback"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedProfile = Annotated[Profile, Depends(get_current_profile)]


@router.put(
    "/outfit/{outfit_id}/feedback",
    response_model=RecommendationFeedbackRead,
    status_code=status.HTTP_200_OK,
)
def create_or_update_feedback(
    outfit_id: UUID,
    data: RecommendationFeedbackCreate,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> RecommendationFeedbackRead:
    """
    Cria ou atualiza o feedback de uma recomendação.

    O perfil é obtido pelo token de autenticação.
    O cliente não pode escolher o proprietário da avaliação.
    """

    try:
        return service.create_or_update_feedback(
            db=db,
            profile=profile,
            outfit_id=outfit_id,
            data=data,
        )

    except service.RecommendationFeedbackError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from None


@router.get(
    "/outfit/{outfit_id}/feedback",
    response_model=RecommendationFeedbackRead,
)
def read_feedback(
    outfit_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> RecommendationFeedbackRead:
    """Consulta a avaliação do perfil autenticado."""

    try:
        feedback = service.get_feedback(
            db=db,
            profile_id=profile.id,
            outfit_id=outfit_id,
        )

        if feedback is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avaliação não encontrada.",
            )

        return feedback

    except service.RecommendationFeedbackError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from None


@router.delete(
    "/outfit/{outfit_id}/feedback",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_feedback(
    outfit_id: UUID,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> Response:
    """Remove a avaliação do perfil autenticado."""

    try:
        service.delete_feedback(
            db=db,
            profile_id=profile.id,
            outfit_id=outfit_id,
        )

    except service.RecommendationFeedbackError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)
