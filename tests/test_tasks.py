import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reflection import Reflection
from app.models.task import Task, TaskStatus


@pytest.mark.asyncio
async def test_create_and_list_tasks(client: AsyncClient, auth_user):
    user, headers = auth_user

    # Create first task
    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": "Build a fast API endpoint", "title": "FastAPI Task"},
        headers=headers,
    )
    assert create_res.status_code == 200
    task_data = create_res.json()
    assert task_data["id"] is not None
    assert task_data["goal"] == "Build a fast API endpoint"
    assert task_data["title"] == "FastAPI Task"
    assert task_data["status"] == "pending"

    # List tasks
    list_res = await client.get("/api/v1/tasks/", headers=headers)
    assert list_res.status_code == 200
    tasks = list_res.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_data["id"]


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient, auth_user):
    user, headers = auth_user

    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": "Deep learning analysis"},
        headers=headers,
    )
    task_id = create_res.json()["id"]

    get_res = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_nonexistent_task(client: AsyncClient, auth_user):
    _, headers = auth_user
    response = await client.get("/api/v1/tasks/99999", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest.mark.asyncio
async def test_get_reflections_for_task(client: AsyncClient, auth_user, db_session: AsyncSession):
    user, headers = auth_user

    task = Task(user_id=user.id, goal="Test reflections", status=TaskStatus.REFLECTING)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Check empty reflections
    res_empty = await client.get(f"/api/v1/reflections/task/{task.id}", headers=headers)
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # Insert a reflection
    reflection = Reflection(
        task_id=task.id,
        iteration=1,
        failed_node="executor",
        error_trace="IndexError: list index out of range",
        verbal_critique="Need to check array length before indexing",
        corrected_strategy="Check bounds and provide default value",
    )
    db_session.add(reflection)
    await db_session.commit()

    # Check populated reflections
    res_populated = await client.get(f"/api/v1/reflections/task/{task.id}", headers=headers)
    assert res_populated.status_code == 200
    reflections = res_populated.json()
    assert len(reflections) == 1
    assert reflections[0]["iteration"] == 1
    assert reflections[0]["verbal_critique"] == "Need to check array length before indexing"


@pytest.mark.asyncio
async def test_tasks_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_task_success_and_cascade(client: AsyncClient, auth_user, db_session: AsyncSession):
    user, headers = auth_user
    task = Task(user_id=user.id, goal="Task to be deleted", status=TaskStatus.COMPLETED)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    reflection = Reflection(
        task_id=task.id,
        iteration=1,
        failed_node="executor",
        error_trace="Test error",
        verbal_critique="Test critique",
        corrected_strategy="Test correction",
    )
    db_session.add(reflection)
    await db_session.commit()

    del_res = await client.delete(f"/api/v1/tasks/{task.id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["detail"] == "Task deleted successfully"

    get_res = await client.get(f"/api/v1/tasks/{task.id}", headers=headers)
    assert get_res.status_code == 404

    ref_res = await client.get(f"/api/v1/reflections/task/{task.id}", headers=headers)
    assert ref_res.status_code in [200, 404]
    if ref_res.status_code == 200:
        assert ref_res.json() == []


@pytest.mark.asyncio
async def test_delete_nonexistent_task(client: AsyncClient, auth_user):
    _, headers = auth_user
    del_res = await client.delete("/api/v1/tasks/99999", headers=headers)
    assert del_res.status_code == 404

