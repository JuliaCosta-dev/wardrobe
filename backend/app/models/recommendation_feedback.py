from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RecommendationFeedback(Base):
    """
    Representa a avaliação de uma recomendação de look.

    Cada look pode receber somente uma avaliação por vez.
    Caso o usuário avalie novamente, o registro existente
    será atualizado pelo serviço.

    O feedback pertence ao perfil autenticado e ao look
    que recebeu a avaliação.
    """

    __tablename__ = "recommendation_feedback"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Perfil proprietário da avaliação.
    # A exclusão do perfil remove seus feedbacks.
    profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Look avaliado.
    # Um feedback não pode existir sem o look correspondente.
    outfit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("outfits.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Avaliação geral.
    # Valores permitidos: positive ou negative.
    rating: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    # Motivo estruturado da avaliação.
    # É opcional porque o usuário pode avaliar sem justificar.
    reason: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    # Comentário livre opcional, limitado a 500 caracteres
    # também pelo schema da API.
    comment: Mapped[str | None] = mapped_column(
        String(500),
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
        # Segunda camada de validação: mesmo que algum código
        # tente gravar diretamente no banco, rating precisa ser válido.
        CheckConstraint(
            "rating IN ('positive', 'negative')",
            name="ck_recommendation_feedback_rating",
        ),
        CheckConstraint(
            """
            reason IS NULL OR reason IN (
                'liked_style',
                'comfortable',
                'matched_weather',
                'not_my_style',
                'weather_mismatch',
                'disliked_items',
                'other'
            )
            """,
            name="ck_recommendation_feedback_reason",
        ),
        Index(
            "ix_recommendation_feedback_profile_created",
            "profile_id",
            "created_at",
        ),
    )
