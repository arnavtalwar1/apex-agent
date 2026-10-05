import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_root_and_health(client: AsyncClient):
    res_root = await client.get("/")
    assert res_root.status_code == 200
    assert "message" in res_root.json()

    res_health = await client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword", "full_name": "New User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "duplicate@example.com", "password": "password123", "full_name": "User 1"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 200

    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "Email already registered" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@example.com", "password": "mypassword", "full_name": "Login User"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, auth_user):
    user, headers = auth_user
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == user.email


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_invalid_email_formats(client: AsyncClient):
    """Verify invalid email formats are rejected with HTTP 422."""
    for invalid_email in ["invalidemail", "user@", "@example.com", "user name@example.com"]:
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": invalid_email, "password": "password123", "full_name": "Test"},
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_fields(client: AsyncClient):
    """Verify missing required fields return HTTP 422."""
    res_no_name = await client.post(
        "/api/v1/auth/register",
        json={"email": "noname@example.com", "password": "password123"},
    )
    assert res_no_name.status_code == 422

    res_no_email = await client.post(
        "/api/v1/auth/register",
        json={"password": "password123", "full_name": "No Email"},
    )
    assert res_no_email.status_code == 422


@pytest.mark.asyncio
async def test_register_and_login_long_password(client: AsyncClient):
    """Verify passwords exceeding 72 bytes are safely truncated and verified without error."""
    long_pass = "A" * 100
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "longpass_unit@example.com", "password": long_pass, "full_name": "Long Pass User"},
    )
    assert reg_res.status_code == 200

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "longpass_unit@example.com", "password": long_pass},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    """Verify missing credentials or invalid emails on login return HTTP 422."""
    res_empty = await client.post("/api/v1/auth/login", json={})
    assert res_empty.status_code == 422

    res_no_pass = await client.post("/api/v1/auth/login", json={"email": "test@example.com"})
    assert res_no_pass.status_code == 422

    res_bad_email = await client.post("/api/v1/auth/login", json={"email": "bademail", "password": "pass"})
    assert res_bad_email.status_code == 422


@pytest.mark.asyncio
async def test_get_me_with_query_param_token(client: AsyncClient, auth_user):
    """Verify GET /api/v1/auth/me accepts token via query parameter (used by SSE EventSource)."""
    user, headers = auth_user
    token = headers["Authorization"].split(" ")[1]

    response = await client.get(f"/api/v1/auth/me?token={token}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == user.email


@pytest.mark.asyncio
async def test_get_me_malformed_token(client: AsyncClient):
    """Verify malformed tokens return HTTP 401."""
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_get_me_nonexistent_user(client: AsyncClient):
    """Verify valid JWT with non-existent user ID returns HTTP 401."""
    fake_token = create_access_token({"sub": "999999", "email": "ghost@example.com"})
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_forgot_password_and_reset_flow(client: AsyncClient):
    # 1. Register a test user
    email = "reset_test@example.com"
    old_password = "initialPassword123"
    new_password = "newSecurePassword456"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password, "full_name": "Reset Test"},
    )

    # 2. Request forgot password
    forgot_res = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    data = forgot_res.json()
    assert "detail" in data
    reset_token = data.get("reset_token")
    assert reset_token is not None

    # 3. Non-existent email still returns 200 (enumeration safety) with no token
    ghost_res = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert ghost_res.status_code == 200
    assert ghost_res.json()["reset_token"] is None

    # 4. Reset password using valid reset token
    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": new_password},
    )
    assert reset_res.status_code == 200
    assert "successfully reset" in reset_res.json()["detail"]

    # 5. Token reuse is blocked (revocation)
    replay_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "yetAnotherPassword789"},
    )
    assert replay_res.status_code == 401

    # 6. Verify old password no longer works
    old_login = await client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    assert old_login.status_code == 401

    # 7. Verify new password logs in successfully
    new_login = await client.post("/api/v1/auth/login", json={"email": email, "password": new_password})
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

