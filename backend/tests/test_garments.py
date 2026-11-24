from uuid import uuid4


def create_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid4().hex}@example.com",
            "password": "Correct-Horse-42!",
            "display_name": "Closet User",
        },
    )

    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def garment_payload():
    return {
        "name": "Camiseta preta",
        "category": "tops",
        "subcategory": "t-shirt",
        "primary_color": "black",
        "colors": ["black"],
        "season_tags": ["autumn", "winter"],
        "occasion_tags": ["casual", "daily"],
        "formality": 1,
        "warmth_level": 1,
        "status": "available",
        "is_favorite": False,
    }


def test_create_garment(client):
    token = create_user(client)

    response = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Camiseta preta"
    assert response.json()["category"] == "tops"


def test_list_garments(client):
    token = create_user(client)
    headers = auth_headers(token)

    client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=headers,
    )

    response = client.get(
        "/api/v1/garments?category=tops&skip=0&limit=10",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1


def test_garment_without_image_returns_null_primary_image(client):
    token = create_user(client)
    headers = auth_headers(token)

    created = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["primary_image"] is None


def test_list_garments_returns_primary_image_metadata(client):
    from io import BytesIO

    from PIL import Image

    token = create_user(client)
    headers = auth_headers(token)

    created = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=headers,
    )

    garment_id = created.json()["id"]

    image = Image.new("RGB", (100, 150), color=(30, 80, 160))
    output = BytesIO()
    image.save(output, format="PNG")

    uploaded = client.post(
        f"/api/v1/garments/{garment_id}/images",
        headers=headers,
        files={
            "file": (
                "shirt.png",
                output.getvalue(),
                "image/png",
            )
        },
        data={"is_primary": "true"},
    )

    assert uploaded.status_code == 201

    response = client.get(
        "/api/v1/garments",
        headers=headers,
    )

    assert response.status_code == 200

    garment = response.json()["items"][0]
    primary_image = garment["primary_image"]

    assert primary_image is not None
    assert primary_image["id"] == uploaded.json()["id"]
    assert primary_image["garment_id"] == garment_id
    assert primary_image["mime_type"] == "image/webp"
    assert primary_image["width"] == 100
    assert primary_image["height"] == 150

    assert primary_image["url"] == (f"/api/v1/garments/{garment_id}/images/{uploaded.json()['id']}")

    assert "storage_key" not in primary_image


def test_get_garment_returns_primary_image_metadata(client):
    from io import BytesIO

    from PIL import Image

    token = create_user(client)
    headers = auth_headers(token)

    created = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=headers,
    )

    garment_id = created.json()["id"]

    image = Image.new("RGB", (100, 150), color=(30, 80, 160))
    output = BytesIO()
    image.save(output, format="PNG")

    uploaded = client.post(
        f"/api/v1/garments/{garment_id}/images",
        headers=headers,
        files={
            "file": (
                "shirt.png",
                output.getvalue(),
                "image/png",
            )
        },
        data={"is_primary": "true"},
    )

    assert uploaded.status_code == 201

    response = client.get(
        f"/api/v1/garments/{garment_id}",
        headers=headers,
    )

    assert response.status_code == 200

    primary_image = response.json()["primary_image"]

    assert primary_image is not None
    assert primary_image["id"] == uploaded.json()["id"]


def test_update_garment(client):
    token = create_user(client)
    headers = auth_headers(token)

    created = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=headers,
    )

    garment_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/garments/{garment_id}",
        json={"name": "Camiseta preta favorita", "is_favorite": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Camiseta preta favorita"
    assert response.json()["is_favorite"] is True


def test_delete_garment(client):
    token = create_user(client)
    headers = auth_headers(token)

    created = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=headers,
    )

    garment_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/garments/{garment_id}",
        headers=headers,
    )

    assert response.status_code == 204


def test_user_cannot_access_another_users_garment(client):
    first_token = create_user(client)
    second_token = create_user(client)

    created = client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=auth_headers(first_token),
    )

    garment_id = created.json()["id"]

    response = client.get(
        f"/api/v1/garments/{garment_id}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404


def test_user_cannot_list_another_users_garments(client):
    first_token = create_user(client)
    second_token = create_user(client)

    client.post(
        "/api/v1/garments",
        json=garment_payload(),
        headers=auth_headers(first_token),
    )

    response = client.get(
        "/api/v1/garments",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []
