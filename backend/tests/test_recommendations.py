def create_user(client, email: str) -> dict[str, str]:
    """Cria um usuário e devolve o cabeçalho de autenticação."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "display_name": "Recommendation User",
        },
    )

    assert response.status_code == 201

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_recommendation_requires_authentication(client):
    """Impede a geração de recomendações sem autenticação."""

    response = client.post(
        "/api/v1/recommendations/outfit",
        json={},
    )

    assert response.status_code == 401


def test_recommendation_rejects_garment_ids(client):
    """Rejeita campos não permitidos na solicitação de recomendação."""

    headers = create_user(
        client,
        "recommendation-validation@example.com",
    )

    response = client.post(
        "/api/v1/recommendations/outfit",
        headers=headers,
        json={
            "garment_ids": [
                "00000000-0000-0000-0000-000000000001",
            ],
        },
    )

    assert response.status_code == 422
