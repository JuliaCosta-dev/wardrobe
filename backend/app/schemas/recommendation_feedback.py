from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# O usuário só pode escolher uma dessas duas avaliações.
FeedbackRating = Literal["positive", "negative"]

# Motivos controlados para manter os dados consistentes.
FeedbackReason = Literal[
    "liked_style",
    "comfortable",
    "matched_weather",
    "not_my_style",
    "weather_mismatch",
    "disliked_items",
    "other",
]


class RecommendationFeedbackCreate(BaseModel):
    """
    Dados enviados pelo cliente ao avaliar um look.

    profile_id e outfit_id não são aceitos aqui:
    ambos serão definidos pelo backend.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    rating: FeedbackRating

    reason: FeedbackReason | None = None

    comment: str | None = Field(
        default=None,
        max_length=500,
    )


class RecommendationFeedbackRead(BaseModel):
    """Representação pública de uma avaliação."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    outfit_id: UUID
    rating: FeedbackRating
    reason: FeedbackReason | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
