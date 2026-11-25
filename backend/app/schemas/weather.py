from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WeatherRead(BaseModel):
    """Dados meteorológicos normalizados para uso na aplicação."""

    model_config = ConfigDict(extra="forbid")

    temperature: float
    wind_speed: float | None = None
    precipitation_probability: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    precipitation_amount: float | None = Field(
        default=None,
        ge=0,
    )
    symbol_code: str | None = None

    forecast_time: datetime
    updated_at: datetime | None = None

    is_stale: bool = False

    source: str = "MET Norway"
    attribution: str = "Data from MET Norway"
    license_url: str = "https://creativecommons.org/licenses/by/4.0/"
