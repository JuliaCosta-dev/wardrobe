from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Encontra a pasta backend independentemente de onde o script for executado.
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurações centralizadas da aplicação."""

    # Banco de dados principal.
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_test_db: str

    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433

    # Autenticação.
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Identificação obrigatória para acessar a API do MET Norway.
    # Use um contato real que possa receber comunicações sobre o uso da API.
    met_no_user_agent: str = Field(min_length=10, max_length=250)

    # Limite de espera pela API externa, em segundos.
    weather_timeout_seconds: float = Field(default=8.0, gt=0, le=30)

    # Intervalo mínimo de segurança utilizado quando o provedor
    # não informa um cabeçalho Expires.
    weather_fallback_ttl_minutes: int = Field(default=180, ge=180, le=1440)

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
