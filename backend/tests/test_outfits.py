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
            "display_name": "Outfit User",
        },
    )

    assert response.status_code == 201

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_garment(
    client,
    headers: dict[str, str],
    name: str,
    category: str,
    **extra,
) -> dict:
    """Cadastra uma peça pela API já existente."""

    payload = {
        "name": name,
        "category": category,
        "colors": [],
        "season_tags": [],
        "occasion_tags": [],
        "status": "available",
        **extra,
    }

    response = client.post(
        "/api/v1/garments",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_complete_closet(
    client,
    headers: dict[str, str],
) -> list[dict]:
    """Cria a estrutura mínima para gerar um look."""

    return [
        create_garment(
            client,
            headers,
            "Camiseta azul",
            "tops",
            primary_color="blue",
            season_tags=["summer", "spring"],
            occasion_tags=["casual"],
            formality=1,
        ),
        create_garment(
            client,
            headers,
            "Calça preta",
            "bottoms",
            primary_color="black",
            season_tags=["summer", "winter"],
            occasion_tags=["casual"],
            formality=1,
        ),
        create_garment(
            client,
            headers,
            "Tênis branco",
            "shoes",
            primary_color="white",
            season_tags=["summer", "spring", "autumn", "winter"],
            occasion_tags=["casual"],
            formality=1,
        ),
    ]


def test_generate_outfit(client):
    headers = create_user(client, "outfit@example.com")
    garments = create_complete_closet(client, headers)

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={"occasion": "casual", "season": "summer"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["occasion"] == "casual"
    assert data["season"] == "summer"
    assert len(data["items"]) == 3

    returned_garment_ids = {item["garment_id"] for item in data["items"]}

    expected_garment_ids = {garment["id"] for garment in garments}

    assert returned_garment_ids == expected_garment_ids

    assert data["expires_at"] > data["generated_at"]


def test_generated_outfit_has_valid_roles(client):
    headers = create_user(client, "roles@example.com")
    create_complete_closet(client, headers)

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert response.status_code == 201

    roles = {item["role"] for item in response.json()["items"]}

    assert roles == {"top", "bottom", "shoes"}


def test_outfit_requires_authentication(client):
    response = client.post(
        "/api/v1/outfits/generate",
        json={},
    )

    assert response.status_code == 401


def test_outfit_list_requires_authentication(client):
    response = client.get("/api/v1/outfits")

    assert response.status_code == 401


def test_outfit_detail_requires_authentication(client):
    response = client.get("/api/v1/outfits/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 401


def test_generation_requires_available_base_garments(client):
    headers = create_user(client, "incomplete@example.com")

    create_garment(
        client,
        headers,
        "Camiseta",
        "tops",
    )

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert response.status_code == 409


def test_generation_ignores_unavailable_garments(client):
    headers = create_user(client, "unavailable@example.com")

    create_garment(
        client,
        headers,
        "Camiseta",
        "tops",
        status="laundry",
    )

    create_garment(
        client,
        headers,
        "Calça",
        "bottoms",
    )

    create_garment(
        client,
        headers,
        "Tênis",
        "shoes",
    )

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert response.status_code == 409


def test_same_combination_is_not_repeated_within_retention(
    client,
):
    headers = create_user(client, "no-repeat@example.com")
    create_complete_closet(client, headers)

    first_response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    second_response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_list_generated_outfits(client):
    headers = create_user(client, "list-outfits@example.com")
    create_complete_closet(client, headers)

    client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    response = client.get(
        "/api/v1/outfits",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1


def test_get_generated_outfit(client):
    headers = create_user(client, "detail-outfit@example.com")
    create_complete_closet(client, headers)

    generated = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    outfit_id = generated.json()["id"]

    response = client.get(
        f"/api/v1/outfits/{outfit_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == outfit_id


def test_user_cannot_access_another_users_outfit(client):
    first_headers = create_user(client, "first-outfit@example.com")
    second_headers = create_user(client, "second-outfit@example.com")

    create_complete_closet(client, first_headers)

    generated = client.post(
        "/api/v1/outfits/generate",
        headers=first_headers,
        json={},
    )

    outfit_id = generated.json()["id"]

    response = client.get(
        f"/api/v1/outfits/{outfit_id}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_expired_outfit_is_removed_and_combination_can_be_reused(
    client,
    db_session,
):
    headers = create_user(client, "expired-outfit@example.com")
    create_complete_closet(client, headers)

    generated = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert generated.status_code == 201

    outfit_id = generated.json()["id"]

    # Recupera o perfil criado para alterar a validade diretamente
    # no banco de testes.
    profile = db_session.scalar(select(Profile).where(Profile.display_name == "Outfit User"))

    assert profile is not None

    outfit = db_session.get(Outfit, outfit_id)

    assert outfit is not None

    outfit.expires_at = datetime.now(UTC) - timedelta(days=1)
    db_session.commit()

    # A próxima geração remove o registro vencido antes de consultar
    # as combinações utilizadas.
    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    assert response.status_code == 201
    assert response.json()["id"] != outfit_id

    assert db_session.get(Outfit, outfit_id) is None


def test_generation_rejects_invalid_formality(client):
    headers = create_user(client, "invalid-formality@example.com")

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={"formality": 5},
    )

    assert response.status_code == 422


def test_generation_rejects_unknown_fields(client):
    headers = create_user(client, "unknown-fields@example.com")

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={"garment_ids": ["00000000-0000-0000-0000-000000000001"]},
    )

    assert response.status_code == 422


def test_generation_filters_by_occasion(client):
    headers = create_user(client, "occasion-filter@example.com")

    create_garment(
        client,
        headers,
        "Camiseta de festa",
        "tops",
        occasion_tags=["party"],
    )

    create_garment(
        client,
        headers,
        "Calça de festa",
        "bottoms",
        occasion_tags=["party"],
    )

    create_garment(
        client,
        headers,
        "Tênis de festa",
        "shoes",
        occasion_tags=["party"],
    )

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={"occasion": "work"},
    )

    assert response.status_code == 409


def test_generation_filters_by_season(client):
    headers = create_user(client, "season-filter@example.com")

    create_garment(
        client,
        headers,
        "Camiseta de verão",
        "tops",
        season_tags=["summer"],
    )

    create_garment(
        client,
        headers,
        "Calça de verão",
        "bottoms",
        season_tags=["summer"],
    )

    create_garment(
        client,
        headers,
        "Tênis de verão",
        "shoes",
        season_tags=["summer"],
    )

    response = client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={"season": "winter"},
    )

    assert response.status_code == 409


def test_outfit_list_pagination(client):
    headers = create_user(client, "pagination-outfit@example.com")
    create_complete_closet(client, headers)

    client.post(
        "/api/v1/outfits/generate",
        headers=headers,
        json={},
    )

    response = client.get(
        "/api/v1/outfits?skip=0&limit=1",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["skip"] == 0
    assert response.json()["limit"] == 1


def test_outfit_list_rejects_invalid_limit(client):
    headers = create_user(client, "invalid-limit@example.com")

    response = client.get(
        "/api/v1/outfits?limit=101",
        headers=headers,
    )

    assert response.status_code == 422
