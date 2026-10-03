from unittest.mock import MagicMock, patch
import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END

from app.core.config import settings
from app.graph.state import AgentState
from app.graph.workflow import route_next, workflow


def test_route_next_max_iterations():
    assert route_next({"iteration_count": settings.MAX_ITERATIONS, "next_node": "PLANNER"}) == END


def test_route_next_valid_nodes():
    for node in ["planner", "PLANNER", " researcher ", "EXECUTOR", "Reflector"]:
        assert route_next({"next_node": node}) == node.strip().lower()


def test_route_next_finish_or_unknown():
    for node in ["FINISH", "finish", "UNKNOWN", ""]:
        assert route_next({"next_node": node}) == END


@pytest.mark.asyncio
async def test_workflow_end_to_end_execution():
    graph = workflow.compile(checkpointer=MemorySaver())

    supervisor_sequence = [
        MagicMock(content="PLANNER"),
        MagicMock(content="RESEARCHER"),
        MagicMock(content="EXECUTOR"),
        MagicMock(content="FINISH"),
    ]

    planner_mock = MagicMock(content="1. Step one\n```python\nprint('Workflow ok')\n```")
    research_mock = [
        {"title": "Search result", "content": "Useful info", "url": "https://example.com"}
    ]

    initial_state: AgentState = {
        "user_goal": "Test complete workflow",
        "messages": [],
        "plan": "",
        "research_data": "",
        "execution_result": "",
        "reflection_critique": "",
        "iteration_count": 0,
        "next_node": "",
        "error": "",
    }

    config = {"configurable": {"thread_id": "test-thread-1"}}

    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_invoke, \
         patch("app.agents.researcher.search_web", return_value=research_mock):
        
        def side_effect(arg):
            if isinstance(arg, dict) and "plan" not in arg:
                return planner_mock
            if supervisor_sequence:
                return supervisor_sequence.pop(0)
            return MagicMock(content="FINISH")

        mock_invoke.side_effect = side_effect

        updates = []
        async for update in graph.astream(initial_state, config, stream_mode="updates"):
            updates.append(update)

    assert len(updates) > 0
    final_state = await graph.aget_state(config)
    assert final_state is not None
    assert "Workflow ok" in final_state.values.get("execution_result", "")


@pytest.mark.asyncio
async def test_parallel_simultaneous_execution():
    graph = workflow.compile(checkpointer=MemorySaver())

    planner_mock = MagicMock(content="1. Step one\n```python\nprint('Parallel ok')\n```")
    research_mock = [
        {"title": "Search result", "content": "Live intelligence", "url": "https://example.com"}
    ]

    initial_state: AgentState = {
        "user_goal": "Perform parallel task",
        "plan": "",
        "research_data": "",
        "execution_result": "",
        "reflection_critique": "",
        "iteration_count": 0,
        "next_node": "",
        "error": "",
        "execution_mode": "parallel",
    }

    config = {"configurable": {"thread_id": "test-parallel-thread"}}

    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=planner_mock), \
         patch("app.agents.researcher.search_web", return_value=research_mock):

        updates = []
        async for update in graph.astream(initial_state, config, stream_mode="updates"):
            updates.append(update)

    final_state = await graph.aget_state(config)
    assert final_state is not None
    assert "Parallel ok" in final_state.values.get("execution_result", "")
    assert "Live intelligence" in final_state.values.get("research_data", "")
    assert any("planner" in u for u in updates)
    assert any("researcher" in u for u in updates)

