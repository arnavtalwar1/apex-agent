from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.api import tasks
from app.models.task import Task, TaskStatus
from app.models.reflection import Reflection
from app.core.security import create_refresh_token


@pytest.mark.asyncio
@pytest.mark.parametrize("goal", ["", "   ", "x" * 10001])
async def test_invalid_goals_rejected(client, auth_user, goal):
    _, headers = auth_user
    response = await client.post('/api/v1/tasks/', headers=headers, json={'goal': goal})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, -1, 201])
async def test_list_limit_bounded(client, auth_user, limit):
    _, headers = auth_user
    assert (await client.get(f'/api/v1/tasks/?limit={limit}', headers=headers)).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ['run', 'run-background', 'approve', 'reject', 'delete'])
async def test_active_tasks_cannot_be_modified(client, auth_user, db_session, action):
    user, headers = auth_user
    task = Task(user_id=user.id, goal='Already running', status=TaskStatus.EXECUTING)
    db_session.add(task)
    await db_session.commit()
    url = f'/api/v1/tasks/{task.id}'
    response = await (client.delete(url, headers=headers) if action == 'delete' else client.post(f'{url}/{action}', headers=headers))
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize('endpoint', ['run', 'run-background'])
async def test_rejected_tasks_cannot_bypass_gate(client, auth_user, endpoint):
    _, headers = auth_user
    task = (await client.post('/api/v1/tasks/', headers=headers, json={'goal': 'Review me', 'requires_approval': True})).json()
    await client.post(f'/api/v1/tasks/{task["id"]}/reject', headers=headers)
    response = await client.post(f'/api/v1/tasks/{task["id"]}/{endpoint}', headers=headers)
    assert response.status_code == 409
    assert (await client.get(f'/api/v1/tasks/{task["id"]}', headers=headers)).json()['status'] == 'rejected'


@pytest.mark.asyncio
async def test_inactive_user_cannot_access_or_login(client, auth_user, db_session):
    user, headers = auth_user
    user.is_active = False
    await db_session.commit()
    assert (await client.get('/api/v1/auth/me', headers=headers)).status_code == 401
    assert (await client.post('/api/v1/auth/login', json={'email': user.email, 'password': 'testpass123'})).status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client, auth_user):
    user, headers = auth_user
    refresh = create_refresh_token({'sub': str(user.id)})
    assert (await client.post('/api/v1/auth/logout', headers=headers, json={'refresh_token': refresh})).status_code == 200
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': refresh})).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize('background', [False, True])
async def test_shared_lifecycle_persists_recovery(client, auth_user, db_session, monkeypatch, background):
    _, headers = auth_user
    created = (await client.post('/api/v1/tasks/', headers=headers, json={'goal': 'Recover task'})).json()

    async def stream(*args, **kwargs):
        yield {'executor': {'error': 'ZeroDivisionError', 'execution_result': 'FAILED'}}
        yield {'reflector': {'error': '', 'iteration_count': 1, 'reflection_critique': 'Fix divisor', 'plan': 'Use 2'}}
        yield {'executor': {'execution_result': 'Recovered answer', 'error': ''}}

    monkeypatch.setattr(tasks.app_graph, 'astream', stream)
    monkeypatch.setattr(tasks.app_graph, 'aget_state', AsyncMock(return_value=MagicMock(values={'execution_result': 'Recovered answer', 'error': '', 'iteration_count': 1, 'plan': 'Use 2'})))
    endpoint = 'run-background' if background else 'run'
    result = await client.post(f'/api/v1/tasks/{created["id"]}/{endpoint}', headers=headers)
    assert result.status_code == 200
    persisted = (await client.get(f'/api/v1/tasks/{created["id"]}', headers=headers)).json()
    assert persisted['status'] == 'completed'
    assert persisted['final_output'] == 'Recovered answer'
    assert persisted['reflection_count'] == 1
    reflection = (await db_session.execute(select(Reflection).where(Reflection.task_id == created['id']))).scalar_one()
    assert reflection.error_trace == 'ZeroDivisionError'
