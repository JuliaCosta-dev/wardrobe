from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile


def get_by_user_id(
    db: Session,
    user_id: UUID,
) -> Profile | None:
    """Busca o perfil associado ao usuário autenticado."""

    statement = select(Profile).where(Profile.user_id == user_id)

    return db.scalar(statement)


def save(
    db: Session,
    profile: Profile,
) -> Profile:
    """Persiste as alterações do perfil."""

    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)

        return profile

    except Exception:
        db.rollback()
        raise
