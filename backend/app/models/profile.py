from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.garment import Garment
    from app.models.outfit import Outfit
    from app.models.user import User


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="America/Sao_Paulo",
        server_default="America/Sao_Paulo",
    )

    city: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="profile",
    )

    garments: Mapped[list[Garment]] = relationship(
        "Garment",
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    outfits: Mapped[list[Outfit]] = relationship(
        "Outfit",
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="ck_profiles_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="ck_profiles_longitude_range",
        ),
    )
