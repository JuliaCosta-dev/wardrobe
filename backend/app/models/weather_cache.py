from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeatherCache(Base):
    """
    Armazena previsões meteorológicas consultadas externamente.

    A localização é arredondada para quatro casas decimais.
    A previsão é reutilizada enquanto expires_at estiver no futuro.
    """

    __tablename__ = "weather_cache"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Resposta original do provedor.
    # O serviço meteorológico transforma esses dados em um schema
    # interno antes de entregá-los à API.
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    last_modified: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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
        UniqueConstraint(
            "latitude",
            "longitude",
            name="uq_weather_cache_coordinates",
        ),
        Index(
            "ix_weather_cache_expiration",
            "expires_at",
        ),
    )
