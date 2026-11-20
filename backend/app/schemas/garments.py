from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

GarmentCategory = Literal[
    "tops",
    "bottoms",
    "one_piece",
    "shoes",
    "bags",
    "accessories",
    "jewelry",
    "makeup",
    "hair_accessories",
]

GarmentStatus = Literal[
    "available",
    "laundry",
    "borrowed",
    "out_of_season",
    "archived",
]

FitPreference = Literal["tight", "regular", "loose"]


class GarmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: GarmentCategory

    subcategory: str | None = Field(default=None, max_length=60)
    primary_color: str | None = Field(default=None, max_length=40)

    colors: list[str] = Field(default_factory=list, max_length=10)
    pattern: str | None = Field(default=None, max_length=60)
    fabric: str | None = Field(default=None, max_length=100)

    season_tags: list[str] = Field(default_factory=list)
    occasion_tags: list[str] = Field(default_factory=list)

    formality: int | None = Field(default=None, ge=1, le=4)
    warmth_level: int | None = Field(default=None, ge=1, le=5)

    size_label: str | None = Field(default=None, max_length=30)
    fit_preference: FitPreference | None = None

    status: GarmentStatus = "available"
    is_favorite: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class GarmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: GarmentCategory | None = None

    subcategory: str | None = Field(default=None, max_length=60)
    primary_color: str | None = Field(default=None, max_length=40)

    colors: list[str] | None = Field(default=None, max_length=10)
    pattern: str | None = Field(default=None, max_length=60)
    fabric: str | None = Field(default=None, max_length=100)

    season_tags: list[str] | None = None
    occasion_tags: list[str] | None = None

    formality: int | None = Field(default=None, ge=1, le=4)
    warmth_level: int | None = Field(default=None, ge=1, le=5)

    size_label: str | None = Field(default=None, max_length=30)
    fit_preference: FitPreference | None = None

    status: GarmentStatus | None = None
    is_favorite: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_non_nullable_fields(self):
        non_nullable = {
            "name",
            "category",
            "colors",
            "season_tags",
            "occasion_tags",
            "status",
            "is_favorite",
        }

        for field in non_nullable:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} não pode ser nulo.")

        return self


class GarmentRead(BaseModel):
    id: UUID
    name: str
    category: str
    subcategory: str | None
    primary_color: str | None
    colors: list[str]
    pattern: str | None
    fabric: str | None
    season_tags: list[str]
    occasion_tags: list[str]
    formality: int | None
    warmth_level: int | None
    size_label: str | None
    fit_preference: str | None
    status: str
    is_favorite: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GarmentList(BaseModel):
    items: list[GarmentRead]
    total: int
    skip: int
    limit: int


# permite enviar somente os campos que a pessoa deseja altera. 
# Por exemplo, mudar a cor nõo exige reenviar o nome, a categoria e todos os demais atributos.
