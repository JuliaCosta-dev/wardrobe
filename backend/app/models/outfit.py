from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Outfit(Base):
    """
    Representa uma combinação de roupas gerada pelo sistema.

    O look é criado pelo serviço de geração a partir das peças
    disponíveis no closet do perfil.

    expires_at controla por quanto tempo a combinação participa
    do histórico usado para evitar repetições.

    is_favorite indica se o usuário deseja preservar o look.
    Looks favoritados não são removidos pela limpeza de expiração.
    """

    __tablename__ = "outfits"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Perfil proprietário do look.
    profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Contexto informado na geração.
    occasion: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    season: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    formality: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Pontuação calculada pelo motor de recomendação.
    # Pode ser nula em looks gerados pelo endpoint tradicional.
    recommendation_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Motivos que explicam a recomendação.
    recommendation_reasons: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Retrato meteorológico utilizado na recomendação.
    weather_snapshot: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Indica se o usuário salvou o look como favorito.
    # O padrão também é definido no PostgreSQL.
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Hash dos IDs das peças que compõem o look.
    signature: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    profile = relationship(
        "Profile",
        back_populates="outfits",
    )

    # Ao excluir um look, seus itens associados também são removidos.
    items: Mapped[list[OutfitItem]] = relationship(
        "OutfitItem",
        back_populates="outfit",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="OutfitItem.created_at",
    )

    __table_args__ = (
        # Uma mesma combinação não pode ser registrada duas vezes
        # para o mesmo perfil enquanto o registro anterior existir.
        UniqueConstraint(
            "profile_id",
            "signature",
            name="uq_outfits_profile_signature",
        ),
        Index(
            "ix_outfits_profile_expiration",
            "profile_id",
            "expires_at",
        ),
        Index(
            "ix_outfits_profile_generated",
            "profile_id",
            "generated_at",
        ),
        # Otimiza a listagem de favoritos de cada perfil.
        Index(
            "ix_outfits_profile_favorite_generated",
            "profile_id",
            "is_favorite",
            "generated_at",
        ),
    )


class OutfitItem(Base):
    """
    Associação entre um look e uma peça do closet.

    Cada registro representa uma peça utilizada no look,
    identificada também pela função que exerce na combinação.
    """

    __tablename__ = "outfit_items"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    outfit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("outfits.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Se a peça for excluída do closet, sua associação ao look
    # também será removida.
    garment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("garments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Exemplos: top, bottom, shoes, one_piece, bag.
    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    outfit = relationship(
        "Outfit",
        back_populates="items",
    )

    garment = relationship(
        "Garment",
    )

    __table_args__ = (
        UniqueConstraint(
            "outfit_id",
            "garment_id",
            name="uq_outfit_items_outfit_garment",
        ),
        UniqueConstraint(
            "outfit_id",
            "role",
            name="uq_outfit_items_outfit_role",
        ),
        Index(
            "ix_outfit_items_garment",
            "garment_id",
        ),
    )
