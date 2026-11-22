from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileUpdate(BaseModel):
    """Campos permitidos para atualização parcial do perfil."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    display_name: str | None = Field(default=None, max_length=80)
    timezone: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str:
        if value is None or not value:
            raise ValueError("O nome de exibição não pode ser vazio.")

        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str:
        if value is None or not value:
            raise ValueError("O fuso horário não pode ser vazio.")

        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Informe um fuso horário IANA válido.") from None

        return value

    @field_validator("city")
    @classmethod
    def normalize_city(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class ProfileRead(BaseModel):
    """Dados públicos do perfil."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    display_name: str
    timezone: str
    city: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime


class ProfilePreferences(BaseModel):
    """Preferências utilizadas na personalização e recomendação de looks."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    preferred_colors: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    avoided_colors: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    preferred_styles: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    fit_preferences: list[Literal["tight", "regular", "loose"]] = Field(
        default_factory=list,
        max_length=3,
    )

    formality_levels: list[Literal["very_casual", "casual", "smart_casual", "formal"]] = Field(
        default_factory=list,
        max_length=4,
    )

    seasons: list[Literal["spring", "summer", "autumn", "winter"]] = Field(
        default_factory=list,
        max_length=4,
    )

    occasions: list[
        Literal[
            "work",
            "casual",
            "formal_event",
            "party",
            "date",
            "sport",
            "travel",
        ]
    ] = Field(
        default_factory=list,
        max_length=7,
    )

    recommendations_enabled: bool = True

    @field_validator(
        "preferred_colors",
        "avoided_colors",
        "preferred_styles",
    )
    @classmethod
    def normalize_text_lists(cls, values: list[str]) -> list[str]:
        normalized = []

        for value in values:
            item = value.strip().lower()

            if not item:
                raise ValueError("Os valores das listas não podem ser vazios.")

            if len(item) > 40:
                raise ValueError("Cada valor deve possuir no máximo 40 caracteres.")

            if item not in normalized:
                normalized.append(item)

        return normalized
