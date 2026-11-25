from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from app.core.config import settings

# Endpoint oficial do produto Locationforecast 2.0.
BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"


@dataclass(frozen=True)
class WeatherProviderResult:
    """
    Resultado bruto da comunicação com o provedor.

    Separar o resultado HTTP do processamento meteorológico permite
    testar a integração sem depender da API externa.
    """

    status_code: int
    payload: dict[str, Any] | None
    last_modified: str | None
    expires_at: datetime | None


def _parse_http_date(value: str | None) -> datetime | None:
    """Converte uma data HTTP para datetime com fuso horário UTC."""

    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)

        return parsed.astimezone(UTC)

    except (TypeError, ValueError, OverflowError):
        return None


def fetch_forecast(
    latitude: float,
    longitude: float,
    last_modified: str | None = None,
) -> WeatherProviderResult:
    """
    Consulta a previsão meteorológica do MET Norway.

    As coordenadas são limitadas a quatro casas decimais, conforme
    a política de uso do provedor.

    last_modified permite solicitar uma resposta condicional:
    se os dados não mudaram, o servidor pode responder HTTP 304.
    """

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude inválida.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude inválida.")

    headers = {
        "User-Agent": settings.met_no_user_agent,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }

    if last_modified:
        headers["If-Modified-Since"] = last_modified

    params = {
        "lat": f"{latitude:.4f}",
        "lon": f"{longitude:.4f}",
    }

    timeout = httpx.Timeout(settings.weather_timeout_seconds)

    # O cliente é criado por chamada e fechado automaticamente.
    # Não deixamos conexões externas abertas indefinidamente.
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        response = client.get(
            BASE_URL,
            params=params,
            headers=headers,
        )

    # 304 significa que a previsão armazenada continua válida.
    if response.status_code == 304:
        return WeatherProviderResult(
            status_code=304,
            payload=None,
            last_modified=response.headers.get("Last-Modified") or last_modified,
            expires_at=_parse_http_date(response.headers.get("Expires")),
        )

    # Converte respostas HTTP de erro em exceções controladas pelo HTTPX.
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("O provedor retornou um formato JSON inesperado.")

    return WeatherProviderResult(
        status_code=response.status_code,
        payload=payload,
        last_modified=response.headers.get("Last-Modified"),
        expires_at=_parse_http_date(response.headers.get("Expires")),
    )
