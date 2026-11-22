def create_authenticated_user(
    client,
    email: str = "profile@example.com",
    display_name: str = "Profile User",
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "display_name": display_name,
        },
    )

    assert response.status_code == 201

    access_token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_get_profile(client):
    headers = create_authenticated_user(client)

    response = client.get(
        "/api/v1/profile/me",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["display_name"] == "Profile User"
    assert data["timezone"] == "America/Sao_Paulo"
    assert data["city"] is None


def test_update_profile(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/api/v1/profile/me",
        headers=headers,
        json={
            "display_name": "Updated Name",
            "city": "Belo Horizonte",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["display_name"] == "Updated Name"
    assert data["city"] == "Belo Horizonte"
    assert data["timezone"] == "America/Sao_Paulo"


def test_update_profile_can_clear_city(client):
    headers = create_authenticated_user(client)

    client.patch(
        "/api/v1/profile/me",
        headers=headers,
        json={"city": "Belo Horizonte"},
    )

    response = client.patch(
        "/api/v1/profile/me",
        headers=headers,
        json={"city": None},
    )

    assert response.status_code == 200
    assert response.json()["city"] is None


def test_update_profile_rejects_invalid_timezone(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/api/v1/profile/me",
        headers=headers,
        json={"timezone": "Invalid/Timezone"},
    )

    assert response.status_code == 422


def test_update_profile_rejects_invalid_coordinates(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/api/v1/profile/me",
        headers=headers,
        json={"latitude": 120},
    )

    assert response.status_code == 422


def test_get_preferences(client):
    headers = create_authenticated_user(client)

    response = client.get(
        "/api/v1/profile/preferences",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["preferred_colors"] == []
    assert data["avoided_colors"] == []
    assert data["preferred_styles"] == []
    assert data["fit_preferences"] == []
    assert data["formality_levels"] == []
    assert data["seasons"] == []
    assert data["occasions"] == []
    assert data["recommendations_enabled"] is True


def test_update_preferences(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/api/v1/profile/preferences",
        headers=headers,
        json={
            "preferred_colors": ["Black", "Blue"],
            "avoided_colors": ["Yellow"],
            "preferred_styles": ["Minimalist"],
            "fit_preferences": ["regular", "loose"],
            "formality_levels": ["casual", "smart_casual"],
            "seasons": ["summer", "winter"],
            "occasions": ["work", "casual"],
            "recommendations_enabled": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["preferred_colors"] == ["black", "blue"]
    assert data["avoided_colors"] == ["yellow"]
    assert data["preferred_styles"] == ["minimalist"]
    assert data["fit_preferences"] == ["regular", "loose"]
    assert data["recommendations_enabled"] is True


def test_partial_preferences_update_preserves_other_fields(client):
    headers = create_authenticated_user(client)

    client.patch(
        "/api/v1/profile/preferences",
        headers=headers,
        json={
            "preferred_colors": ["blue"],
            "preferred_styles": ["minimalist"],
        },
    )

    response = client.patch(
        "/api/v1/profile/preferences",
        headers=headers,
        json={
            "avoided_colors": ["red"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["preferred_colors"] == ["blue"]
    assert data["preferred_styles"] == ["minimalist"]
    assert data["avoided_colors"] == ["red"]


def test_preferences_reject_invalid_fit(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/api/v1/profile/preferences",
        headers=headers,
        json={
            "fit_preferences": ["oversized"],
        },
    )

    assert response.status_code == 422


def test_profile_requires_authentication(client):
    response = client.get("/api/v1/profile/me")

    assert response.status_code == 401


def test_preferences_require_authentication(client):
    response = client.get("/api/v1/profile/preferences")

    assert response.status_code == 401


def test_users_cannot_access_each_others_profiles(client):
    first_headers = create_authenticated_user(
        client,
        email="first@example.com",
        display_name="First User",
    )

    second_headers = create_authenticated_user(
        client,
        email="second@example.com",
        display_name="Second User",
    )

    client.patch(
        "/api/v1/profile/me",
        headers=first_headers,
        json={"display_name": "Modified First User"},
    )

    response = client.get(
        "/api/v1/profile/me",
        headers=second_headers,
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Second User"
