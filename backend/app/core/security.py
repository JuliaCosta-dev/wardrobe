import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()


# transforma uma senha em um hash argon2id
def hash_password(password: str) -> str:
    return password_hasher.hash(password)


# verifica se uma senha correponde ao hash armazenado
def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


# gera um jwt com identificação da conta e validade
def create_access_token(user_id: UUID) -> str:
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


# valida assinatura, expiração e tipo do token
def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


# gera um token aleatório
def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


# gera o hash que será armazenado no banco de dados
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
