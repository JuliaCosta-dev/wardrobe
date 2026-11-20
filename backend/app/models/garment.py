from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Garment(Base):
    __tablename__ = "garments"

    id: Mapped[uuid4] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    profile_id: Mapped[uuid4] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    subcategory: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
    )

    primary_color: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    colors: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    pattern: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
    )

    fabric: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    season_tags: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    occasion_tags: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    formality: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    warmth_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    size_label: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    fit_preference: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="available",
        server_default="available",
    )

    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    __table_args__ = (
        CheckConstraint(
            "formality IS NULL OR formality BETWEEN 1 AND 4",
            name="ck_garments_formality",
        ),
        CheckConstraint(
            "warmth_level IS NULL OR warmth_level BETWEEN 1 AND 5",
            name="ck_garments_warmth",
        ),
        CheckConstraint(
            "status IN ('available', 'laundry', 'borrowed', 'out_of_season', 'archived')",
            name="ck_garments_status",
        ),
        CheckConstraint(
            "fit_preference IS NULL OR fit_preference IN ('tight', 'regular', 'loose')",
            name="ck_garments_fit_preference",
        ),
        Index("ix_garments_profile_category", "profile_id", "category"),
        Index("ix_garments_profile_status", "profile_id", "status"),
        Index("ix_garments_profile_created", "profile_id", "created_at"),
    )


class GarmentImage(Base):
    __tablename__ = "garment_images"

    id: Mapped[uuid4] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    garment_id: Mapped[uuid4] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("garments.id", ondelete="CASCADE"),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
