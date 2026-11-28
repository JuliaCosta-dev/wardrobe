from datetime import UTC, datetime, timedelta
from uuid import uuid4


def create_user(client, email: str) -> dict[str, str]:
    """Cria um usuário autenticado."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "display_name": "Usage User",
        },
    )

    assert response.status_code == 201

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_garment(
    client,
    headers: dict[str, str],
    name: str,
    category: str,
) -> dict:
    """Cadastra uma peça para os testes."""

    response = client.post(
        "/api/v1/garments",
        headers=headers,
        json={
            "name": name,
            "category": category,
            "colors": [],
            "season_tags": [],
            "occasion_tags": [],
            "status": "available",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_outfit(client, headers: dict[str, str]) -> dict:
    """Monta o closet mínimo e gera um look."""

    create_garment(client, headers, "Camiseta", "tops")
    create_garment(client, headers, "Calça", "bottoms")
    create_garment(client, headers, "Tênis", "shoes")

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert response.status_code == 201

    return response.json()


def test_usage_requires_authentication(client):
    response = client.post(
        f"/api/v1/outfits/{uuid4()}/usages",
        json={},
    )

    assert response.status_code == 401


def test_create_usage(client):
    headers = create_user(client, "usage-create@example.com")
    outfit = create_outfit(client, headers)

    response = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={
            "notes": "Utilizado no trabalho.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["outfit_id"] == outfit["id"]
    assert data["notes"] == "Utilizado no trabalho."
    assert data["used_at"] is not None


def test_same_outfit_can_have_multiple_usages(client):
    headers = create_user(client, "usage-multiple@example.com")
    outfit = create_outfit(client, headers)

    first_date = datetime.now(UTC) - timedelta(days=5)
    second_date = datetime.now(UTC) - timedelta(days=2)

    first = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={"used_at": first_date.isoformat()},
    )

    second = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={"used_at": second_date.isoformat()},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] != second.json()["id"]


def test_user_cannot_register_usage_for_another_users_outfit(client):
    first_headers = create_user(client, "usage-owner@example.com")
    second_headers = create_user(client, "usage-other@example.com")

    outfit = create_outfit(client, first_headers)

    response = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=second_headers,
        json={},
    )

    assert response.status_code == 404


def test_list_usages(client):
    headers = create_user(client, "usage-list@example.com")
    outfit = create_outfit(client, headers)

    for _ in range(2):
        response = client.post(
            f"/api/v1/outfits/{outfit['id']}/usages",
            headers=headers,
            json={},
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_profile_usages(client):
    headers = create_user(client, "usage-profile-list@example.com")
    outfit = create_outfit(client, headers)

    client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={},
    )

    response = client.get(
        "/api/v1/outfit-usages",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_usage(client):
    headers = create_user(client, "usage-update@example.com")
    outfit = create_outfit(client, headers)

    created = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={"notes": "Original"},
    )

    usage_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/outfit-usages/{usage_id}",
        headers=headers,
        json={"notes": "Atualizado"},
    )

    assert response.status_code == 200
    assert response.json()["notes"] == "Atualizado"


def test_delete_usage(client):
    headers = create_user(client, "usage-delete@example.com")
    outfit = create_outfit(client, headers)

    created = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={},
    )

    usage_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/outfit-usages/{usage_id}",
        headers=headers,
    )

    assert response.status_code == 204

    # Excluir a utilização não exclui o look.
    outfit_response = client.get(
        f"/api/v1/outfits/{outfit['id']}",
        headers=headers,
    )

    assert outfit_response.status_code == 200


def test_usage_rejects_unknown_fields(client):
    headers = create_user(client, "usage-extra@example.com")
    outfit = create_outfit(client, headers)

    response = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={
            "profile_id": str(uuid4()),
        },
    )

    assert response.status_code == 422


def test_usage_rejects_naive_datetime(client):
    headers = create_user(client, "usage-naive-date@example.com")
    outfit = create_outfit(client, headers)

    response = client.post(
        f"/api/v1/outfits/{outfit['id']}/usages",
        headers=headers,
        json={
            "used_at": "2026-11-27T10:00:00",
        },
    )

    assert response.status_code == 422
