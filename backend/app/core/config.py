from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# encontra a pasta backend independente de onde o script for executado
BACKEND_DIR = Path(__file__).resolve().parents[2]


# BaseSettings lê as variáveis de ambiente
class Settings(BaseSettings):
    # recebem os valores do .env
    postgres_db: str
    postgres_user: str
    postgres_password: str
    # valores de teste recebidos do env
    postgres_test_db: str
    # tem valores padrão
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433

    # protege a exibição acidental de senhas e chaves em representações dos objetos de configuração
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
