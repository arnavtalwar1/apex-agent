from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.executor import executor_node
from app.agents.planner import planner_node
from app.agents.reflector import reflector_node
from app.agents.supervisor import supervisor_node
from app.graph.state import AgentState
from app.graph.workflow import route_next


@pytest.mark.asyncio
async def test_agentic_happy_path_scenario():
    """Scenario 1: Happy path where goal is planned and executed cleanly on first pass."""
    state: AgentState = {
        "user_goal": "Calculate factorial of 5 and print it",
        "plan": "",
        "research_data": "",
        "execution_result": "",
        "reflection_critique": "",
        "iteration_count": 0,
        "next_node": "",
        "error": "",
    }

    # 1. Planner decomposes into valid python block
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_chain:
        mock_chain.return_value = MagicMock(
            content="1. Calculate factorial\n```python\nimport math\nprint(math.factorial(5))\n```"
        )
        state.update(planner_node(state))

    assert "math.factorial" in state["plan"]

    # 2. Supervisor routes to executor
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_chain:
        mock_chain.return_value = MagicMock(content="EXECUTOR")
        state.update(supervisor_node(state))

    assert state["next_node"].lower() == "executor"

    # 3. Executor runs python code safely
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=MagicMock(content="Computation verified", response_metadata={})):
        state.update(executor_node(state))
    assert state["error"] == ""
    assert "120" in state["execution_result"]

    # 4. Supervisor sees success and signals FINISH
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_chain:
        mock_chain.return_value = MagicMock(content="FINISH")
        state.update(supervisor_node(state))

    assert route_next(state) == END


@pytest.mark.asyncio
async def test_agentic_failure_and_self_healing_recovery():
    """Scenario 2: Failure recovery where a broken script is diagnosed and self-healed by the Reflector."""
    state: AgentState = {
        "user_goal": "Compute sum of numbers",
        "plan": "```python\n# Injected intentional division by zero error\nres = 10 / 0\nprint(res)\n```",
        "research_data": "",
        "execution_result": "",
        "reflection_critique": "",
        "iteration_count": 0,
        "next_node": "",
        "error": "",
    }

    # 1. Executor fails and logs ZeroDivisionError
    state.update(executor_node(state))
    assert state["error"] != ""
    assert "ZeroDivisionError" in state["error"]

    # 2. Supervisor routes to reflector upon failure
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_chain:
        mock_chain.return_value = MagicMock(content="REFLECTOR")
        state.update(supervisor_node(state))

    assert state["next_node"].lower() == "reflector"

    # 3. Reflector diagnoses root cause and produces corrected code
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_chain:
        mock_chain.return_value = MagicMock(
            content="CRITIQUE: Do not divide by zero.\nCORRECTED_PLAN:\n```python\nres = 10 / 2\nprint(int(res))\n```"
        )
        state.update(reflector_node(state))

    # Error state should be reset by reflector for execution retry
    assert state["error"] == ""
    assert state["iteration_count"] == 1
    assert "Do not divide by zero" in state["reflection_critique"]

    # 4. Supervisor routes corrected plan to executor
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_chain:
        mock_chain.return_value = MagicMock(content="EXECUTOR")
        state.update(supervisor_node(state))

    assert state["next_node"].lower() == "executor"

    # 5. Executor re-runs with corrected code and succeeds!
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=MagicMock(content="Computation verified", response_metadata={})):
        state.update(executor_node(state))
    assert state["error"] == ""
    assert "5" in state["execution_result"]


@pytest.mark.asyncio
async def test_sse_streaming_task_run_endpoint(client: AsyncClient, auth_user):
    """Scenario 3: Verify POST /api/v1/tasks/{id}/run returns valid SSE stream."""
    _, headers = auth_user

    # Create a task
    create_res = await client.post(
        "/api/v1/tasks/",
        json={"goal": "Say hello world"},
        headers=headers,
    )
    assert create_res.status_code == 200
    task_id = create_res.json()["id"]

    # Run the task via SSE stream
    with patch("app.graph.workflow.app_graph.astream") as mock_astream, \
         patch("app.graph.workflow.app_graph.aget_state") as mock_aget_state:

        async def mock_stream_generator(*args, **kwargs):
            yield {"planner": {"plan": "Step 1: Print hello"}}
            yield {"executor": {"execution_result": "hello world"}}

        mock_astream.side_effect = mock_stream_generator
        mock_aget_state.return_value = MagicMock(
            values={"plan": "Step 1: Print hello", "execution_result": "hello world", "iteration_count": 0, "error": ""}
        )

        response = await client.post(f"/api/v1/tasks/{task_id}/run", headers=headers)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Verify SSE content contains data events and terminal [DONE]
        content = response.text
        assert "data:" in content
        assert "[DONE]" in content
