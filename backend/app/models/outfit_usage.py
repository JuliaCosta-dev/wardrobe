from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OutfitUsage(Base):
    """
    Representa uma utilização real de um look.

    Um mesmo Outfit pode possuir vários OutfitUsage.
    Cada registro representa uma ocasião diferente em que
    o usuário utilizou aquela combinação.

    A tabela reaproveita a estrutura já existente no PostgreSQL.
    """

    __tablename__ = "outfit_usages"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Look utilizado.
    # ON DELETE CASCADE remove os registros de utilização caso
    # o look seja excluído explicitamente.
    outfit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("outfits.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Data e horário em que o usuário realmente utilizou o look.
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Observações opcionais, limitadas a 500 caracteres.
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Data em que o registro foi criado no sistema.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relacionamento com o look.
    outfit = relationship(
        "Outfit",
        back_populates="usages",
    )

    __table_args__ = (
        # Índice utilizado para consultar as utilizações de um look
        # em ordem cronológica.
        Index(
            "ix_outfit_usages_outfit_used_at",
            "outfit_id",
            "used_at",
        ),
    )
