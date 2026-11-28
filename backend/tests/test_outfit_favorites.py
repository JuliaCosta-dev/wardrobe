
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.models.outfit import Outfit
from app.models.profile import Profile
from app.models.user import User


def create_user(client, email: str) -> dict[str, str]:
    """Cria um usuário pela API e retorna seu cabeçalho de autenticação."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "display_name": "Favorite User",
        },
    )

    assert response.status_code == 201

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def get_profile_id(db_session, email: str):
    """Localiza o perfil pelo e-mail do usuário criado no teste."""

    statement = (
        select(Profile)
        .join(User, User.id == Profile.user_id)
        .where(User.email == email)
    )

    profile = db_session.scalar(statement)

    assert profile is not None

    return profile.id


def create_outfit(
    db_session,
    profile_id,
    *,
    is_favorite: bool = False,
    expires_at: datetime | None = None,
) -> Outfit:
    """Cria um look diretamente no banco para isolar os testes."""

    now = datetime.now(UTC)

    outfit = Outfit(
        profile_id=profile_id,
        occasion="casual",
        season="summer",
        formality=1,
        signature=uuid4().hex + uuid4().hex,
        generated_at=now,
        expires_at=expires_at or now + timedelta(days=30),
        is_favorite=is_favorite,
    )

    db_session.add(outfit)
    db_session.commit()
    db_session.refresh(outfit)

    return outfit


def test_favorite_outfit(client, db_session):
    """O usuário consegue favoritar um look próprio."""

    email = "favorite-outfit@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    outfit = create_outfit(db_session, profile_id)

    response = client.put(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(outfit.id)
    assert response.json()["is_favorite"] is True


def test_favorite_outfit_is_idempotent(client, db_session):
    """Favoritar duas vezes mantém o mesmo estado."""

    email = "favorite-idempotent@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    outfit = create_outfit(db_session, profile_id)

    first_response = client.put(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=headers,
    )

    second_response = client.put(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["is_favorite"] is True
    assert second_response.json()["id"] == first_response.json()["id"]


def test_unfavorite_outfit(client, db_session):
    """O usuário consegue remover um look dos favoritos."""

    email = "unfavorite-outfit@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    outfit = create_outfit(
        db_session,
        profile_id,
        is_favorite=True,
    )

    response = client.delete(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=headers,
    )

    assert response.status_code == 204

    db_session.refresh(outfit)

    assert outfit.is_favorite is False


def test_unfavorite_outfit_is_idempotent(client, db_session):
    """Desfavoritar um look já desfavoritado continua válido."""

    email = "unfavorite-idempotent@example.com"
    headers = create_user(client, email)

    profile_id = get_profile_id(db_session, email)

    outfit = create_outfit(db_session, profile_id)

    first_response = client.delete(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=headers,
    )

    second_response = client.delete(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=headers,
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 204


def test_list_favorite_outfits(client, db_session):
    """A listagem retorna somente os looks favoritados do perfil."""

    email = "favorite-list@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    favorite = create_outfit(
        db_session,
        profile_id,
        is_favorite=True,
    )

    create_outfit(
        db_session,
        profile_id,
        is_favorite=False,
    )

    response = client.get(
        "/api/v1/outfits/favorites",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(favorite.id)
    assert data["items"][0]["is_favorite"] is True


def test_favorite_outfits_pagination(client, db_session):
    """A listagem de favoritos respeita skip e limit."""

    email = "favorite-pagination@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    create_outfit(db_session, profile_id, is_favorite=True)
    create_outfit(db_session, profile_id, is_favorite=True)

    response = client.get(
        "/api/v1/outfits/favorites?skip=0&limit=1",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1
    assert response.json()["skip"] == 0
    assert response.json()["limit"] == 1


def test_favorite_list_rejects_invalid_limit(client, db_session):
    """O limite máximo da paginação continua sendo aplicado."""

    headers = create_user(client, "favorite-invalid-limit@example.com")

    response = client.get(
        "/api/v1/outfits/favorites?limit=101",
        headers=headers,
    )

    assert response.status_code == 422


def test_favorite_requires_authentication(client, db_session):
    """Não é possível favoritar sem autenticação."""

    response = client.put(
        f"/api/v1/outfits/{uuid4()}/favorite",
    )

    assert response.status_code == 401


def test_favorite_list_requires_authentication(client):
    """A listagem de favoritos exige autenticação."""

    response = client.get("/api/v1/outfits/favorites")

    assert response.status_code == 401


def test_user_cannot_favorite_another_users_outfit(client, db_session):
    """Um usuário não consegue alterar o look de outro perfil."""

    first_email = "first-owner@example.com"
    second_email = "second-owner@example.com"

    first_headers = create_user(client, first_email)
    second_headers = create_user(client, second_email)

    first_profile_id = get_profile_id(db_session, first_email)

    outfit = create_outfit(db_session, first_profile_id)

    response = client.put(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=second_headers,
    )

    assert response.status_code == 404

    db_session.refresh(outfit)

    assert outfit.is_favorite is False

    # O proprietário original ainda pode favoritar.
    owner_response = client.put(
        f"/api/v1/outfits/{outfit.id}/favorite",
        headers=first_headers,
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["is_favorite"] is True


def test_favorite_nonexistent_outfit_returns_404(client):
    """IDs inexistentes não devem gerar erro interno."""

    headers = create_user(client, "favorite-missing@example.com")

    response = client.put(
        f"/api/v1/outfits/{uuid4()}/favorite",
        headers=headers,
    )

    assert response.status_code == 404


def test_favorite_preserves_expired_outfit(client, db_session):
    """
    Um look favoritado e expirado permanece no histórico permanente,
    no banco de dados e na listagem de favoritos.
    """

    email = "favorite-expiration@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    outfit = create_outfit(db_session, profile_id)
    outfit_id = outfit.id

    # O usuário favorita o look enquanto ele ainda está dentro do prazo.
    favorite_response = client.put(
        f"/api/v1/outfits/{outfit_id}/favorite",
        headers=headers,
    )

    assert favorite_response.status_code == 200
    assert favorite_response.json()["is_favorite"] is True

    # Simula um look cuja data de expiração já passou.
    outfit.expires_at = datetime.now(UTC) - timedelta(days=31)
    db_session.commit()

    # O histórico geral deve continuar incluindo o look.
    history_response = client.get(
        "/api/v1/outfits",
        headers=headers,
    )

    assert history_response.status_code == 200

    history_ids = {
        item["id"]
        for item in history_response.json()["items"]
    }

    assert str(outfit_id) in history_ids

    # O look continua salvo no banco.
    db_session.expire_all()

    saved_outfit = db_session.get(Outfit, outfit_id)

    assert saved_outfit is not None
    assert saved_outfit.is_favorite is True

    # O look expirado também continua aparecendo nos favoritos.
    favorites_response = client.get(
        "/api/v1/outfits/favorites",
        headers=headers,
    )

    assert favorites_response.status_code == 200

    favorite_ids = {
        item["id"]
        for item in favorites_response.json()["items"]
    }

    assert str(outfit_id) in favorite_ids


def test_expired_non_favorite_outfit_remains_in_permanent_history(
    client,
    db_session,
):
    """
    Um look expirado e não favoritado permanece no banco
    e continua aparecendo no histórico permanente.
    """

    email = "expired-non-favorite@example.com"
    headers = create_user(client, email)
    profile_id = get_profile_id(db_session, email)

    outfit = create_outfit(
        db_session,
        profile_id,
        is_favorite=False,
        expires_at=datetime.now(UTC) - timedelta(days=31),
    )

    outfit_id = outfit.id

    # Consulta o histórico mesmo depois da expiração.
    response = client.get(
        "/api/v1/outfits",
        headers=headers,
    )

    assert response.status_code == 200

    history_ids = {
        item["id"]
        for item in response.json()["items"]
    }

    # A expiração não remove o look do histórico.
    assert str(outfit_id) in history_ids

    # A expiração também não remove o registro do banco.
    db_session.expire_all()

    saved_outfit = db_session.get(Outfit, outfit_id)

    assert saved_outfit is not None
    assert saved_outfit.is_favorite is False
