from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.weather import met_no_client
from app.models.profile import Profile
from app.repositories import weather_cache_repository
from app.schemas.weather import WeatherRead


class WeatherUnavailableError(Exception):
    """Não foi possível obter dados meteorológicos utilizáveis."""


class WeatherLocationRequiredError(WeatherUnavailableError):
    """O perfil ainda não possui coordenadas cadastradas."""


def normalize_coordinates(value: float) -> float:
    """Normaliza coordenadas conforme a política do MET Norway."""

    return round(value, 4)


def _parse_datetime(value: str) -> datetime:
    """Converte timestamps ISO 8601 em datetime com fuso."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        raise ValueError("O provedor retornou um horário sem fuso.")

    return parsed


def _extract_weather(
    payload: dict[str, Any],
    is_stale: bool,
) -> WeatherRead:
    """
    Extrai a previsão mais próxima do momento atual.

    O formato do MET Norway separa variáveis instantâneas
    e agregações de períodos de previsão.
    """

    properties = payload.get("properties", {})
    meta = properties.get("meta", {})
    timeseries = properties.get("timeseries", [])

    if not isinstance(timeseries, list) or not timeseries:
        raise ValueError("A previsão meteorológica não contém horários.")

    now = datetime.now(UTC)

    parsed_items = []

    for item in timeseries:
        if not isinstance(item, dict):
            continue

        try:
            forecast_time = _parse_datetime(item["time"])
        except (KeyError, TypeError, ValueError):
            continue

        data = item.get("data", {})
        instant = data.get("instant", {}).get("details", {})

        if not isinstance(instant, dict):
            continue

        parsed_items.append((forecast_time, data, instant))

    if not parsed_items:
        raise ValueError("Não foi possível interpretar a previsão.")

    # Prioriza a primeira previsão igual ou posterior ao momento atual.
    future_items = [item for item in parsed_items if item[0] >= now]

    forecast_time, data, instant = future_items[0] if future_items else parsed_items[-1]

    # Os dados de precipitação podem estar em diferentes períodos.
    # next_1_hours tem prioridade quando está disponível.
    period_data = (
        data.get("next_1_hours") or data.get("next_6_hours") or data.get("next_12_hours") or {}
    )

    period_details = period_data.get("details", {})
    period_summary = period_data.get("summary", {})

    temperature = instant.get("air_temperature")

    if not isinstance(temperature, (int, float)):
        raise ValueError("A previsão não contém uma temperatura válida.")

    wind_speed = instant.get("wind_speed")
    precipitation_probability = period_details.get("probability_of_precipitation")
    precipitation_amount = period_details.get("precipitation_amount")

    return WeatherRead(
        temperature=float(temperature),
        wind_speed=(float(wind_speed) if isinstance(wind_speed, (int, float)) else None),
        precipitation_probability=(
            float(precipitation_probability)
            if isinstance(precipitation_probability, (int, float))
            else None
        ),
        precipitation_amount=(
            float(precipitation_amount) if isinstance(precipitation_amount, (int, float)) else None
        ),
        symbol_code=period_summary.get("symbol_code"),
        forecast_time=forecast_time,
        updated_at=(_parse_datetime(meta["updated_at"]) if meta.get("updated_at") else None),
        is_stale=is_stale,
    )


def get_weather(
    db: Session,
    profile: Profile,
) -> WeatherRead:
    """
    Obtém a previsão da localização do perfil autenticado.

    A aplicação não aceita coordenadas enviadas pelo cliente.
    Isso impede que uma requisição altere arbitrariamente
    a localização utilizada pela recomendação.
    """

    if profile.latitude is None or profile.longitude is None:
        raise WeatherLocationRequiredError(
            "Cadastre a localização do seu perfil para receber recomendações baseadas no clima."
        )

    latitude = normalize_coordinates(profile.latitude)
    longitude = normalize_coordinates(profile.longitude)

    now = datetime.now(UTC)

    cache = weather_cache_repository.get_by_coordinates(
        db,
        latitude,
        longitude,
    )

    # Enquanto o cache estiver válido, nenhuma chamada externa é feita.
    if cache is not None and cache.expires_at > now:
        return _extract_weather(
            cache.payload,
            is_stale=False,
        )

    try:
        result = met_no_client.fetch_forecast(
            latitude=latitude,
            longitude=longitude,
            last_modified=cache.last_modified if cache else None,
        )

        if result.status_code == 304:
            if cache is None:
                raise WeatherUnavailableError(
                    "O provedor informou que os dados não foram modificados, "
                    "mas não existe uma previsão armazenada."
                )

            expires_at = result.expires_at or (
                now + timedelta(minutes=settings.weather_fallback_ttl_minutes)
            )

            cache.expires_at = expires_at
            cache.fetched_at = now

            if result.last_modified:
                cache.last_modified = result.last_modified

            db.commit()
            db.refresh(cache)

            return _extract_weather(
                cache.payload,
                is_stale=False,
            )

        if result.payload is None:
            raise WeatherUnavailableError("O provedor retornou uma previsão vazia.")

        # O cabeçalho Expires do provedor tem prioridade.
        # O intervalo de fallback só é usado quando ele não existe.
        expires_at = result.expires_at or (
            now + timedelta(minutes=settings.weather_fallback_ttl_minutes)
        )

        # Proteção adicional: nunca armazenar uma previsão com validade
        # inferior ao intervalo mínimo estabelecido para este projeto.
        minimum_expiration = now + timedelta(minutes=settings.weather_fallback_ttl_minutes)

        if expires_at < minimum_expiration:
            expires_at = minimum_expiration

        weather_cache_repository.save(
            db=db,
            latitude=latitude,
            longitude=longitude,
            payload=result.payload,
            last_modified=result.last_modified,
            expires_at=expires_at,
        )

        return _extract_weather(
            result.payload,
            is_stale=False,
        )

    except (
        httpx.HTTPError,
        ValueError,
        KeyError,
        TypeError,
        WeatherUnavailableError,
    ) as error:
        db.rollback()

        # Se o provedor falhar, usamos a última previsão armazenada.
        # Ela será marcada como desatualizada para que a API não esconda
        # essa condição do consumidor.
        if cache is not None:
            try:
                return _extract_weather(
                    cache.payload,
                    is_stale=True,
                )
            except (ValueError, KeyError, TypeError):
                pass

        raise WeatherUnavailableError(
            "Não foi possível obter informações meteorológicas no momento."
        ) from error
