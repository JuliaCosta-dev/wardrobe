from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.garments import GarmentRead

# Valores permitidos para os filtros de geração.
OutfitSeason = Literal[
    "spring",
    "summer",
    "autumn",
    "winter",
]


class OutfitGenerateRequest(BaseModel):
    """
    Parâmetros opcionais para orientar a geração de um look.

    O cliente informa o contexto, mas não escolhe as peças.
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

    season: OutfitSeason | None = None

    formality: int | None = Field(
        default=None,
        ge=1,
        le=4,
    )


class OutfitItemRead(BaseModel):
    """Representa uma peça dentro de um look."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_id: UUID
    role: str

    # Expõe os dados públicos da peça, sem storage_key
    # ou caminhos internos do armazenamento.
    garment: GarmentRead


class OutfitRead(BaseModel):
    """Resposta completa de um look gerado."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    occasion: str | None
    season: str | None
    formality: int | None
    generated_at: datetime
    expires_at: datetime

    # Indica ao frontend se o usuário favoritou o look.
    is_favorite: bool

    items: list[OutfitItemRead]

    recommendation_score: float | None = None
    recommendation_reasons: list[str] | None = None
    weather_snapshot: dict | None = None


class OutfitList(BaseModel):
    """Resposta paginada do histórico de looks."""

    items: list[OutfitRead]
    total: int
    skip: int
    limit: int
