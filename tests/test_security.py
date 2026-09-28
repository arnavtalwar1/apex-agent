from datetime import timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.task import Task, TaskStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_passwords_never_exposed_in_api(client: AsyncClient, auth_user):
    """Verify passwords or hashed passwords are never exposed in user responses."""
    user, headers = auth_user

    # Test /auth/me
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert "password" not in data
    assert "hashed_password" not in data
    assert data["email"] == user.email


@pytest.mark.asyncio
async def test_idor_protection_tasks(client: AsyncClient, db_session: AsyncSession, auth_user):
    """Verify that User B cannot access or view User A's tasks."""
    user_a, headers_a = auth_user

    # Create User B
    user_b = User(
        email="user_b@example.com",
        hashed_password=get_password_hash("secret456"),
        full_name="User B",
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    token_b = create_access_token({"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a task
    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": "User A private goal", "title": "A's Task"},
        headers=headers_a,
    )
    assert create_res.status_code == 200
    task_a_id = create_res.json()["id"]

    # User B attempts to access User A's task
    get_res = await client.get(f"/api/v1/tasks/{task_a_id}", headers=headers_b)
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Task not found"

    # User B lists tasks - must NOT see User A's task
    list_res = await client.get("/api/v1/tasks/", headers=headers_b)
    assert list_res.status_code == 200
    user_b_tasks = list_res.json()
    assert len(user_b_tasks) == 0


@pytest.mark.asyncio
async def test_idor_protection_reflections(client: AsyncClient, db_session: AsyncSession, auth_user):
    """Verify that User B cannot access reflections for User A's task."""
    user_a, headers_a = auth_user

    # Create User B
    user_b = User(
        email="user_b2@example.com",
        hashed_password=get_password_hash("secret456"),
        full_name="User B2",
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    token_b = create_access_token({"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Task belongs to User A
    task_a = Task(user_id=user_a.id, goal="Confidential task", status=TaskStatus.COMPLETED)
    db_session.add(task_a)
    await db_session.commit()
    await db_session.refresh(task_a)

    # User B queries reflections for Task A
    ref_res = await client.get(f"/api/v1/reflections/task/{task_a.id}", headers=headers_b)
    assert ref_res.status_code == 404


@pytest.mark.asyncio
async def test_sql_injection_resilience(client: AsyncClient, auth_user, db_session: AsyncSession):
    """Verify parameterized queries safely neutralize SQL injection vectors in goals."""
    user, headers = auth_user

    sql_injection_payload = "'; DROP TABLE tasks; SELECT * FROM users WHERE '1'='1"
    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": sql_injection_payload, "title": "SQL Injection Test"},
        headers=headers,
    )
    assert create_res.status_code == 200
    task_id = create_res.json()["id"]

    # Confirm table was not dropped and data is safely stored verbatim
    fetch_res = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert fetch_res.status_code == 200
    assert fetch_res.json()["goal"] == sql_injection_payload

    # Database query still works
    res = await db_session.execute(text("SELECT count(*) FROM tasks"))
    count = res.scalar()
    assert count >= 1


@pytest.mark.asyncio
async def test_xss_payload_safety(client: AsyncClient, auth_user):
    """Verify XSS payloads are stored safely without evaluation or corruption."""
    _, headers = auth_user
    xss_payload = "<script>alert('xss-exploit')</script><img src=x onerror=alert(1)>"

    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": xss_payload, "title": "XSS Test"},
        headers=headers,
    )
    assert create_res.status_code == 200
    assert create_res.json()["goal"] == xss_payload


@pytest.mark.asyncio
async def test_expired_jwt_rejection(client: AsyncClient):
    """Verify expired tokens are rejected with 401 Unauthorized."""
    expired_token = create_access_token(
        data={"sub": "1"},
        expires_delta=timedelta(seconds=-10),  # Already expired in the past
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"] or "Not authenticated" in response.json()["detail"]
