from uuid import UUID

from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.repositories import profile_repository
from app.schemas.profile import ProfilePreferences


def get_profile(
    db: Session,
    user_id: UUID,
) -> Profile | None:
    """Retorna o perfil do usuário."""

    return profile_repository.get_by_user_id(db, user_id)


def update_profile(
    db: Session,
    user_id: UUID,
    changes: dict[str, object],
) -> Profile | None:
    """Atualiza somente os campos enviados pelo usuário."""

    profile = get_profile(db, user_id)

    if profile is None:
        return None

    if not changes:
        return profile

    for field, value in changes.items():
        setattr(profile, field, value)

    return profile_repository.save(db, profile)


def get_preferences(
    db: Session,
    user_id: UUID,
) -> ProfilePreferences | None:
    """Retorna as preferências do usuário."""

    profile = get_profile(db, user_id)

    if profile is None:
        return None

    return ProfilePreferences.model_validate(profile.preferences or {})


def update_preferences(
    db: Session,
    user_id: UUID,
    changes: dict[str, object],
) -> ProfilePreferences | None:
    """Atualiza as preferências preservando os campos não enviados."""

    profile = get_profile(db, user_id)

    if profile is None:
        return None

    current_preferences = ProfilePreferences.model_validate(profile.preferences or {})

    merged_preferences = current_preferences.model_dump()
    merged_preferences.update(changes)

    updated_preferences = ProfilePreferences.model_validate(merged_preferences)

    if not changes:
        return current_preferences

    profile.preferences = updated_preferences.model_dump()

    profile_repository.save(db, profile)

    return updated_preferences
