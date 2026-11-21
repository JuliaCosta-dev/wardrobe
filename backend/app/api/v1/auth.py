from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.database import get_db
from app.deps import get_current_user
from app.models.profile import Profile
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.schemas.auth import (
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def create_token_pair(
    db: Session,
    user: User,
) -> TokenResponse:
    """
    Cria um par de tokens para o usuário.

    O access token é utilizado para autenticar as requisições.
    O refresh token é armazenado no banco somente em formato hash.
    """
    refresh_token = create_refresh_token()

    session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=(datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)),
    )

    db.add(session)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )


def authentication_error() -> HTTPException:
    """Retorna uma resposta padronizada para falhas de autenticação."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou sessão expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Registra um usuário, cria seu perfil e gera os tokens."""
    existing_user = db.scalar(select(User).where(User.email == data.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )

    profile = Profile(
        display_name=data.display_name,
    )

    # O relacionamento ORM associa automaticamente o perfil ao usuário.
    user.profile = profile

    db.add(user)

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível criar a conta com este e-mail.",
        ) from None

    return create_token_pair(db, user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Autentica um usuário com e-mail e senha."""
    user = db.scalar(select(User).where(User.email == data.email))

    if user is None or not verify_password(data.password, user.password_hash) or not user.is_active:
        raise authentication_error()

    return create_token_pair(db, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Renova os tokens e revoga a sessão anterior.

    Se um refresh token já revogado for reutilizado,
    todas as sessões ativas do usuário serão revogadas.
    """
    token_hash = hash_refresh_token(data.refresh_token)

    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == token_hash))

    if session is None:
        raise authentication_error()

    now = datetime.now(UTC)

    # A reutilização de um token revogado pode indicar comprometimento.
    if session.revoked_at is not None:
        db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.user_id == session.user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        db.commit()

        raise authentication_error()

    if session.expires_at <= now:
        session.revoked_at = now
        db.commit()

        raise authentication_error()

    user = db.get(User, session.user_id)

    if user is None or not user.is_active:
        session.revoked_at = now
        db.commit()

        raise authentication_error()

    new_refresh_token = create_refresh_token()

    new_session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_token(new_refresh_token),
        expires_at=(now + timedelta(days=settings.refresh_token_expire_days)),
    )

    db.add(new_session)
    db.flush()

    session.revoked_at = now
    session.replaced_by_session_id = new_session.id

    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    data: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Revoga uma sessão utilizando seu refresh token."""
    token_hash = hash_refresh_token(data.refresh_token)

    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == token_hash))

    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserRead,
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Retorna os dados do usuário autenticado."""
    return current_user
