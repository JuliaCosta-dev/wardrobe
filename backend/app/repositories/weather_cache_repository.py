from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.weather_cache import WeatherCache


def get_by_coordinates(
    db: Session,
    latitude: float,
    longitude: float,
) -> WeatherCache | None:
    """Busca uma previsão pelas coordenadas normalizadas."""

    statement = select(WeatherCache).where(
        WeatherCache.latitude == latitude,
        WeatherCache.longitude == longitude,
    )

    return db.scalar(statement)


def save(
    db: Session,
    latitude: float,
    longitude: float,
    payload: dict,
    last_modified: str | None,
    expires_at: datetime,
) -> WeatherCache:
    """
    Cria ou atualiza uma previsão de maneira atômica.

    O ON CONFLICT evita que requisições concorrentes criem
    dois registros para as mesmas coordenadas.
    """

    now = datetime.now(UTC)

    statement = (
        insert(WeatherCache)
        .values(
            latitude=latitude,
            longitude=longitude,
            payload=payload,
            last_modified=last_modified,
            fetched_at=now,
            expires_at=expires_at,
        )
        .on_conflict_do_update(
            index_elements=[
                WeatherCache.latitude,
                WeatherCache.longitude,
            ],
            set_={
                "payload": payload,
                "last_modified": last_modified,
                "fetched_at": now,
                "expires_at": expires_at,
                "updated_at": now,
            },
        )
    )

    try:
        db.execute(statement)
        db.commit()

        cache = get_by_coordinates(
            db,
            latitude,
            longitude,
        )

        if cache is None:
            raise RuntimeError("Não foi possível recuperar o cache meteorológico.")

        return cache

    except Exception:
        db.rollback()
        raise
