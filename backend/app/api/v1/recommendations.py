from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_profile
from app.models.profile import Profile
from app.schemas.recommendations import (
    OutfitRecommendationRead,
    OutfitRecommendationRequest,
)
from app.services import (
    contextual_outfit_generator,
    recommendation_service,
    weather_service,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedProfile = Annotated[Profile, Depends(get_current_profile)]


@router.post(
    "/outfit",
    response_model=OutfitRecommendationRead,
    status_code=status.HTTP_201_CREATED,
)
def recommend_outfit(
    data: OutfitRecommendationRequest,
    db: DatabaseSession,
    profile: AuthenticatedProfile,
) -> OutfitRecommendationRead:
    """
    Gera uma recomendação baseada no closet, nas preferências
    do perfil e na previsão meteorológica.

    A localização vem exclusivamente do perfil autenticado.
    """

    try:
        outfit, weather = recommendation_service.recommend_outfit(
            db=db,
            profile=profile,
            request=data,
        )
    except weather_service.WeatherLocationRequiredError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from None

    except weather_service.WeatherUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from None

    except (
        recommendation_service.RecommendationError,
        contextual_outfit_generator.ContextualOutfitError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from None

    return OutfitRecommendationRead(
        outfit=outfit,
        weather=weather,
        score=outfit.recommendation_score or 0,
        reasons=outfit.recommendation_reasons or [],
    )
