from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.outfit import Outfit
from app.models.profile import Profile


def create_user(client, email: str) -> dict[str, str]:
    """Cria um usuário e devolve o cabeçalho de autenticação."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "display_name": "Feedback User",
        },
    )

    assert response.status_code == 201

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_recommended_outfit(
    db_session,
    profile: Profile,
) -> Outfit:
    """
    Cria diretamente um look recomendado no banco de testes.

    Isso evita chamar o provedor meteorológico durante os testes
    de feedback. O objetivo aqui é testar o módulo de avaliação,
    não repetir os testes do motor de recomendações.
    """

    now = datetime.now(UTC)

    outfit = Outfit(
        profile_id=profile.id,
        occasion="casual",
        season="summer",
        formality=1,
        signature="a" * 64,
        generated_at=now,
        expires_at=now + timedelta(days=30),
        recommendation_score=85.0,
        recommendation_reasons=[
            "Combinação adequada ao clima.",
        ],
        weather_snapshot={
            "temperature": 25.0,
            "source": "MET Norway",
        },
    )

    db_session.add(outfit)
    db_session.commit()
    db_session.refresh(outfit)

    return outfit


def get_profile(db_session) -> Profile:
    """Recupera o perfil criado pelo endpoint de cadastro."""

    profile = db_session.scalar(
        select(Profile).where(
            Profile.display_name == "Feedback User",
        )
    )

    assert profile is not None

    return profile


def test_feedback_requires_authentication(client):
    response = client.put(
        "/api/v1/recommendations/outfit/00000000-0000-0000-0000-000000000001/feedback",
        json={"rating": "positive"},
    )

    assert response.status_code == 401


def test_feedback_creates_positive_evaluation(
    client,
    db_session,
):
    headers = create_user(client, "feedback-create@example.com")
    profile = get_profile(db_session)
    outfit = create_recommended_outfit(db_session, profile)

    response = client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
        json={
            "rating": "positive",
            "reason": "liked_style",
            "comment": "Gostei bastante da combinação.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["outfit_id"] == str(outfit.id)
    assert data["rating"] == "positive"
    assert data["reason"] == "liked_style"
    assert data["comment"] == "Gostei bastante da combinação."


def test_feedback_updates_existing_evaluation(
    client,
    db_session,
):
    headers = create_user(client, "feedback-update@example.com")
    profile = get_profile(db_session)
    outfit = create_recommended_outfit(db_session, profile)

    first_response = client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
        json={
            "rating": "positive",
            "reason": "liked_style",
        },
    )

    second_response = client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
        json={
            "rating": "negative",
            "reason": "not_my_style",
            "comment": "Mudei de ideia.",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json()["id"] == second_response.json()["id"]
    assert second_response.json()["rating"] == "negative"
    assert second_response.json()["reason"] == "not_my_style"
    assert second_response.json()["comment"] == "Mudei de ideia."


def test_feedback_can_be_read(
    client,
    db_session,
):
    headers = create_user(client, "feedback-read@example.com")
    profile = get_profile(db_session)
    outfit = create_recommended_outfit(db_session, profile)

    client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
        json={"rating": "positive"},
    )

    response = client.get(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["rating"] == "positive"


def test_feedback_can_be_deleted(
    client,
    db_session,
):
    headers = create_user(client, "feedback-delete@example.com")
    profile = get_profile(db_session)
    outfit = create_recommended_outfit(db_session, profile)

    client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
        json={"rating": "positive"},
    )

    response = client.delete(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
    )

    assert response.status_code == 204

    read_response = client.get(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
    )

    assert read_response.status_code == 404


def test_user_cannot_evaluate_another_users_outfit(
    client,
    db_session,
):
    # Cria o proprietário do look.
    # O retorno não é necessário porque ele não fará a requisição.
    create_user(client, "feedback-owner@example.com")

    first_profile = get_profile(db_session)
    outfit = create_recommended_outfit(db_session, first_profile)

    # Cria um segundo usuário, que tentará avaliar o look alheio.
    second_headers = create_user(client, "feedback-attacker@example.com")

    second_profile = db_session.scalar(
        select(Profile).where(
            Profile.display_name == "Feedback User",
            Profile.id != first_profile.id,
        )
    )

    assert second_profile is not None

    response = client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=second_headers,
        json={"rating": "positive"},
    )

    # O sistema deve impedir que um usuário avalie o look de outro.
    assert response.status_code == 404


def test_feedback_rejects_invalid_rating(client):
    headers = create_user(client, "feedback-invalid-rating@example.com")

    response = client.put(
        "/api/v1/recommendations/outfit/00000000-0000-0000-0000-000000000001/feedback",
        headers=headers,
        json={"rating": "neutral"},
    )

    assert response.status_code == 422


def test_feedback_rejects_invalid_reason(client):
    headers = create_user(client, "feedback-invalid-reason@example.com")

    response = client.put(
        "/api/v1/recommendations/outfit/00000000-0000-0000-0000-000000000001/feedback",
        headers=headers,
        json={
            "rating": "positive",
            "reason": "invented_reason",
        },
    )

    assert response.status_code == 422


def test_feedback_rejects_comment_over_500_characters(client):
    headers = create_user(client, "feedback-long-comment@example.com")

    response = client.put(
        "/api/v1/recommendations/outfit/00000000-0000-0000-0000-000000000001/feedback",
        headers=headers,
        json={
            "rating": "positive",
            "comment": "a" * 501,
        },
    )

    assert response.status_code == 422


def test_feedback_rejects_unknown_fields(client):
    headers = create_user(client, "feedback-extra-fields@example.com")

    response = client.put(
        "/api/v1/recommendations/outfit/00000000-0000-0000-0000-000000000001/feedback",
        headers=headers,
        json={
            "rating": "positive",
            "profile_id": "00000000-0000-0000-0000-000000000001",
        },
    )

    assert response.status_code == 422


def test_feedback_rejects_outfit_without_recommendation(
    client,
    db_session,
):
    headers = create_user(client, "feedback-old-outfit@example.com")
    profile = get_profile(db_session)

    now = datetime.now(UTC)

    # Esse look representa o endpoint antigo de geração.
    # Ele não possui recommendation_score.
    outfit = Outfit(
        profile_id=profile.id,
        occasion="casual",
        season="summer",
        formality=1,
        signature="b" * 64,
        generated_at=now,
        expires_at=now + timedelta(days=30),
    )

    db_session.add(outfit)
    db_session.commit()

    response = client.put(
        f"/api/v1/recommendations/outfit/{outfit.id}/feedback",
        headers=headers,
        json={"rating": "positive"},
    )

    assert response.status_code == 404
