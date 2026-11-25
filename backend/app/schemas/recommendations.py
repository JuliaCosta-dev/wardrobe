from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.outfits import OutfitRead
from app.schemas.weather import WeatherRead


class OutfitRecommendationRequest(BaseModel):
    """
    Contexto opcional para orientar uma recomendação.

    O usuário informa o tipo de ocasião e os filtros desejados,
    mas nunca envia IDs de peças para controlar a combinação.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    occasion: str | None = Field(
        default=None,
        min_length=1,
        max_length=40,
    )

    season: (
        Literal[
            "spring",
            "summer",
            "autumn",
            "winter",
        ]
        | None
    ) = None

    formality: int | None = Field(
        default=None,
        ge=1,
        le=4,
    )


class OutfitRecommendationRead(BaseModel):
    """Resposta completa da recomendação contextual."""

    outfit: OutfitRead
    weather: WeatherRead

    score: float = Field(
        ge=0,
        le=100,
    )

    reasons: list[str]
