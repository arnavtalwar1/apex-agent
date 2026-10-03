"""
Advanced authentication and session management test suite.
Verifies refresh tokens, token rotation, blacklisting, and logout.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, token_blacklist
from app.models.user import User


@pytest.mark.asyncio
async def test_login_returns_access_and_refresh_tokens(client: AsyncClient, db_session: AsyncSession):
    from app.core.security import get_password_hash

    user = User(
        email="session_user@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Session User",
    )
    db_session.add(user)
    await db_session.commit()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "session_user@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, db_session: AsyncSession):
    from app.core.security import get_password_hash

    user = User(
        email="refresh_user@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Refresh User",
    )
    db_session.add(user)
    await db_session.commit()

    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token  # Must be rotated

    # Attempting to re-use old refresh token must fail
    replay_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replay_res.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient, auth_user):
    user, headers = auth_user

    # Verify initially valid
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Logout
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert "revoked" in logout_res.json()["detail"]

    # Subsequent access must be rejected
    rejected_res = await client.get("/api/v1/auth/me", headers=headers)
    assert rejected_res.status_code == 401
    assert "revoked" in rejected_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_token_type_enforcement(client: AsyncClient, auth_user):
    user, _ = auth_user
    # Issue a refresh token
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # Try to access protected endpoint /api/v1/auth/me using refresh token
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    # Protected endpoint must reject refresh tokens when an access token is expected
    assert res.status_code == 401
    assert "Invalid token type" in res.json()["detail"]
