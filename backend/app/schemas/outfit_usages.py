from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OutfitUsageCreate(BaseModel):
    """
    Dados necessários para registrar uma utilização.

    used_at é opcional: caso não seja enviado, será utilizado
    o horário atual em UTC.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    used_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    notes: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("used_at")
    @classmethod
    def validate_used_at(cls, value: datetime) -> datetime:
        """Exige uma data com informação de fuso horário."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("A data de utilização deve possuir fuso horário.")

        return value.astimezone(UTC)


class OutfitUsageUpdate(BaseModel):
    """
    Campos permitidos na atualização de uma utilização.

    Todos são opcionais para permitir PATCH.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    used_at: datetime | None = None

    notes: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("used_at")
    @classmethod
    def validate_used_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("A data de utilização deve possuir fuso horário.")

        return value.astimezone(UTC)


class OutfitUsageRead(BaseModel):
    """Representação pública de uma utilização."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    outfit_id: UUID
    used_at: datetime
    notes: str | None
    created_at: datetime


class OutfitUsageList(BaseModel):
    """Resposta paginada do histórico de utilizações."""

    items: list[OutfitUsageRead]
    total: int
    skip: int
    limit: int
