from uuid import uuid4


def register_user(client):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid4().hex}@example.com",
            "password": "Correct-Horse-42!",
            "display_name": "Test User",
        },
    )


def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 201

    data = response.json()

    assert data["user"]["email"].endswith("@example.com")
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_authenticated_user_can_access_me(client):
    register_response = register_user(client)
    token = register_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_login_with_invalid_password(client):
    register_response = register_user(client)
    email = register_response.json()["user"]["email"]

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Wrong-Password-42!",
        },
    )

    assert response.status_code == 401


def test_unauthenticated_user_cannot_access_garments(client):
    response = client.get("/api/v1/garments")

    assert response.status_code == 401


def test_refresh_token_rotation(client):
    register_response = register_user(client)
    old_refresh_token = register_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert response.status_code == 200

    new_refresh_token = response.json()["refresh_token"]

    assert new_refresh_token != old_refresh_token

    old_token_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert old_token_response.status_code == 401


def test_logout_revokes_refresh_token(client):
    register_response = register_user(client)
    refresh_token = register_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 204

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401
