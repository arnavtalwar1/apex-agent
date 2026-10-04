"""
Tests for RAG-ready episodic memory, observability tracing, and background execution.
"""

import pytest
from httpx import AsyncClient

from app.core.memory import InMemoryVectorStore
from app.core.observability import finish_trace, start_trace


def test_in_memory_vector_store_retrieval():
    store = InMemoryVectorStore()

    store.add(
        content="When executing SQL queries, always parameterize inputs to prevent injection.",
        metadata={"type": "reflection", "topic": "security"},
    )
    store.add(
        content="For electric vehicle range calculations, verify battery kilowatt hours.",
        metadata={"type": "reflection", "topic": "ev"},
    )

    results = store.search("parameterized SQL database injection", limit=1)
    assert len(results) == 1
    assert "SQL queries" in results[0].content
    assert results[0].score > 0

    ev_insights = store.recall_reflection_insights("electric vehicle battery range")
    assert len(ev_insights) == 1
    assert "battery kilowatt" in ev_insights[0]


def test_observability_tracing_metrics():
    trace = start_trace(task_id=99)
    assert trace.trace_id != ""

    trace.record_node("planner", duration_seconds=0.25, success=True, steps=3)
    trace.record_node("executor", duration_seconds=0.45, success=True)

    summary = finish_trace(trace.trace_id)
    assert summary is not None
    assert summary.end_time is not None
    assert summary.total_duration_seconds >= 0

    trace_dict = trace.to_dict()
    assert trace_dict["task_id"] == 99
    assert trace_dict["node_count"] == 2
    assert trace_dict["nodes"][0]["node"] == "planner"


@pytest.mark.asyncio
async def test_run_task_background_endpoint(client: AsyncClient, auth_user, monkeypatch):
    from unittest.mock import AsyncMock
    worker = AsyncMock()
    monkeypatch.setattr("app.api.tasks.execute_task_lifecycle", worker)
    _, headers = auth_user

    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": "Asynchronous background task processing"},
        headers=headers,
    )
    assert create_res.status_code == 200
    task_id = create_res.json()["id"]

    bg_res = await client.post(f"/api/v1/tasks/{task_id}/run-background", headers=headers)
    assert bg_res.status_code == 200
    data = bg_res.json()
    assert data["status"] == "started"
    assert data["mode"] == "background"
    assert "thread_id" in data

    worker.assert_awaited_once()
