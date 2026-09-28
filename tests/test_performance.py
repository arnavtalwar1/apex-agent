import time
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_latency_under_200ms(client: AsyncClient, auth_user):
    """Verify that non-LLM CRUD endpoints respond in well under 200 ms (NFR target)."""
    _, headers = auth_user

    endpoints = [
        ("GET", "/api/v1/auth/me", None),
        ("GET", "/api/v1/tasks/", None),
        ("POST", "/api/v1/tasks/", {"goal": "Fast benchmark task", "title": "Benchmark"}),
    ]

    latencies: list[float] = []

    for method, path, body in endpoints:
        start_time = time.perf_counter()
        if method == "GET":
            response = await client.get(path, headers=headers)
        else:
            response = await client.post(path, json=body, headers=headers)
        duration_ms = (time.perf_counter() - start_time) * 1000

        assert response.status_code in (200, 201)
        latencies.append(duration_ms)
        # Verify latency target (< 200ms)
        assert duration_ms < 200.0, f"{method} {path} took {duration_ms:.2f}ms (target: < 200ms)"

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 100.0, f"Average latency was {avg_latency:.2f}ms"
