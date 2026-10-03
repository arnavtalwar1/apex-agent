"""
Human-in-the-Loop (HITL) and tool permission test suite.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import evaluate_action_permission
from app.models.task import Task, TaskStatus


def test_permission_evaluator_policies():
    # Read/search does not require human approval
    needs_approval, _ = evaluate_action_permission("web_search")
    assert needs_approval is False

    # Python sandbox does not require approval by default
    needs_approval, _ = evaluate_action_permission("python_sandbox", task_requires_approval=False)
    assert needs_approval is False

    # Python sandbox with task approval required triggers human gate
    needs_approval, reason = evaluate_action_permission("python_sandbox", task_requires_approval=True)
    assert needs_approval is True
    assert "human sign-off" in reason.lower()

    # Destructive operations always require human sign-off
    needs_approval, _ = evaluate_action_permission("destructive_operation")
    assert needs_approval is True


@pytest.mark.asyncio
async def test_task_approval_gate_and_lifecycle(client: AsyncClient, auth_user, db_session: AsyncSession):
    user, headers = auth_user

    # Create task with requires_approval = True
    create_res = await client.post(
        "/api/v1/tasks/",
        json={
            "goal": "Drop production database and rebuild schemas",
            "title": "Sensitive Ops Task",
            "requires_approval": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    task_id = create_res.json()["id"]
    assert create_res.json()["requires_approval"] is True
    assert create_res.json()["approval_status"] == "pending"

    # Running task before approval enters awaiting_approval state
    run_res = await client.post(f"/api/v1/tasks/{task_id}/run", headers=headers)
    assert run_res.status_code == 200
    content = run_res.text
    assert "awaiting_approval" in content

    # Verify database status is AWAITING_APPROVAL
    get_res = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert get_res.json()["status"] == "awaiting_approval"

    # User approves task
    approve_res = await client.post(f"/api/v1/tasks/{task_id}/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["approval_status"] == "approved"
    assert approve_res.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_task_rejection(client: AsyncClient, auth_user):
    _, headers = auth_user

    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": "Exfiltrate logs", "requires_approval": True},
        headers=headers,
    )
    task_id = create_res.json()["id"]

    # Reject the task
    reject_res = await client.post(f"/api/v1/tasks/{task_id}/reject", headers=headers)
    assert reject_res.status_code == 200
    assert reject_res.json()["approval_status"] == "rejected"
    assert reject_res.json()["status"] == "rejected"
