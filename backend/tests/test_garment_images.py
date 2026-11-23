from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image

from app.services import image_storage


@pytest.fixture(autouse=True)
def isolated_image_storage(tmp_path, monkeypatch):
    """Mantém os arquivos de teste separados do armazenamento real."""

    monkeypatch.setattr(
        image_storage,
        "GARMENT_STORAGE",
        tmp_path / "garments",
    )


def create_image_bytes(
    image_format: str = "PNG",
    size: tuple[int, int] = (100, 100),
) -> bytes:
    """Gera uma imagem válida para os testes."""

    image = Image.new("RGB", size, color=(30, 80, 160))
    output = BytesIO()
    image.save(output, format=image_format)

    return output.getvalue()


def create_user(client) -> dict[str, str]:
    """Cria um usuário e retorna seus headers de autenticação."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid4().hex}@example.com",
            "password": "Correct-Horse-42!",
            "display_name": "Image User",
        },
    )

    assert response.status_code == 201

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_garment(client, headers: dict[str, str]) -> str:
    """Cria uma peça e retorna seu identificador."""

    response = client.post(
        "/api/v1/garments",
        headers=headers,
        json={
            "name": "Camiseta azul",
            "category": "tops",
            "primary_color": "blue",
            "colors": ["blue"],
            "season_tags": ["summer"],
            "occasion_tags": ["casual"],
            "formality": 1,
            "warmth_level": 1,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def upload_image(
    client,
    headers: dict[str, str],
    garment_id: str,
    content: bytes | None = None,
    filename: str = "shirt.png",
    is_primary: bool = False,
):
    """Executa o upload de uma imagem."""

    return client.post(
        f"/api/v1/garments/{garment_id}/images",
        headers=headers,
        files={
            "file": (
                filename,
                content if content is not None else create_image_bytes(),
                "image/png",
            )
        },
        data={"is_primary": str(is_primary).lower()},
    )


def test_upload_garment_image(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    response = upload_image(client, headers, garment_id)

    assert response.status_code == 201

    data = response.json()

    assert data["garment_id"] == garment_id
    assert data["mime_type"] == "image/webp"
    assert data["width"] == 100
    assert data["height"] == 100
    assert data["is_primary"] is True
    assert "storage_key" not in data


def test_first_image_becomes_primary(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    response = upload_image(
        client,
        headers,
        garment_id,
        is_primary=False,
    )

    assert response.status_code == 201
    assert response.json()["is_primary"] is True


def test_upload_second_image_does_not_replace_primary(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    first = upload_image(client, headers, garment_id)
    second = upload_image(client, headers, garment_id)

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["is_primary"] is True
    assert second.json()["is_primary"] is False


def test_list_garment_images(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    upload_image(client, headers, garment_id)

    response = client.get(
        f"/api/v1/garments/{garment_id}/images",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_read_garment_image(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    uploaded = upload_image(client, headers, garment_id)
    image_id = uploaded.json()["id"]

    response = client.get(
        f"/api/v1/garments/{garment_id}/images/{image_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content.startswith(b"RIFF")
    assert response.content[8:12] == b"WEBP"


def test_invalid_image_is_rejected(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    response = upload_image(
        client,
        headers,
        garment_id,
        content=b"This is not an image",
        filename="invalid.png",
    )

    assert response.status_code == 422


def test_image_larger_than_limit_is_rejected(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    oversized_content = b"x" * (image_storage.MAX_UPLOAD_SIZE + 1)

    response = upload_image(
        client,
        headers,
        garment_id,
        content=oversized_content,
    )

    assert response.status_code == 422


def test_set_primary_image(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    first = upload_image(client, headers, garment_id)
    second = upload_image(client, headers, garment_id)

    first_id = first.json()["id"]
    second_id = second.json()["id"]

    response = client.patch(
        f"/api/v1/garments/{garment_id}/images/{second_id}/primary",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_primary"] is True

    listing = client.get(
        f"/api/v1/garments/{garment_id}/images",
        headers=headers,
    )

    images = {item["id"]: item for item in listing.json()}

    assert images[first_id]["is_primary"] is False
    assert images[second_id]["is_primary"] is True


def test_delete_primary_image_promotes_another_image(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    first = upload_image(client, headers, garment_id)
    second = upload_image(client, headers, garment_id)

    first_id = first.json()["id"]
    second_id = second.json()["id"]

    response = client.delete(
        f"/api/v1/garments/{garment_id}/images/{first_id}",
        headers=headers,
    )

    assert response.status_code == 204

    listing = client.get(
        f"/api/v1/garments/{garment_id}/images",
        headers=headers,
    )

    images = listing.json()

    assert len(images) == 1
    assert images[0]["id"] == second_id
    assert images[0]["is_primary"] is True


def test_user_cannot_access_another_users_image(client):
    first_headers = create_user(client)
    second_headers = create_user(client)

    garment_id = create_garment(client, first_headers)

    uploaded = upload_image(client, first_headers, garment_id)
    image_id = uploaded.json()["id"]

    response = client.get(
        f"/api/v1/garments/{garment_id}/images/{image_id}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_user_cannot_list_another_users_images(client):
    first_headers = create_user(client)
    second_headers = create_user(client)

    garment_id = create_garment(client, first_headers)

    upload_image(client, first_headers, garment_id)

    response = client.get(
        f"/api/v1/garments/{garment_id}/images",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_image_endpoints_require_authentication(client):
    response = client.get(
        f"/api/v1/garments/{uuid4()}/images",
    )

    assert response.status_code == 401


def test_image_must_belong_to_requested_garment(client):
    headers = create_user(client)
    first_garment = create_garment(client, headers)
    second_garment = create_garment(client, headers)

    uploaded = upload_image(client, headers, first_garment)
    image_id = uploaded.json()["id"]

    response = client.get(
        f"/api/v1/garments/{second_garment}/images/{image_id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_delete_image_removes_stored_file(client):
    headers = create_user(client)
    garment_id = create_garment(client, headers)

    uploaded = upload_image(client, headers, garment_id)
    image_id = uploaded.json()["id"]

    files = list(image_storage.GARMENT_STORAGE.glob("*.webp"))

    assert len(files) == 1
    assert files[0].exists()

    response = client.delete(
        f"/api/v1/garments/{garment_id}/images/{image_id}",
        headers=headers,
    )

    assert response.status_code == 204
    assert not files[0].exists()
