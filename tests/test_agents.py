from unittest.mock import MagicMock, patch

from app.agents.executor import executor_node, extract_code
from app.agents.planner import planner_node
from app.agents.reflector import reflector_node
from app.agents.researcher import researcher_node
from app.agents.supervisor import supervisor_node
from app.graph.state import AgentState


def test_extract_code():
    assert extract_code("```python\nprint('hello')\n```") == "print('hello')"
    assert extract_code("```\nx = 10\n```") == "x = 10"
    assert extract_code("1. Step one\n2. Step two") == ""
    assert extract_code("```bash\npip install httpx\n```") == ""
    assert extract_code("```bash\npip install httpx\n```\n```python\nprint('live')\n```") == "print('live')"
    assert extract_code("```python\nbash pip install httpx\nprint('clean')\n```") == "print('clean')"


def test_executor_node_successful_code():
    state: AgentState = {
        "user_goal": "Compute factorial of 5",
        "plan": "```python\nimport math\nprint('Result:', math.factorial(5))\n```",
    }
    result = executor_node(state)
    assert "SUCCESS" in result["execution_result"]
    assert "Result: 120" in result["execution_result"]
    assert result["error"] == ""


def test_executor_node_failing_code():
    state: AgentState = {
        "user_goal": "Cause a ZeroDivisionError",
        "plan": "```python\nprint(1 / 0)\n```",
    }
    result = executor_node(state)
    assert "FAILED" in result["execution_result"]
    assert "ZeroDivisionError" in result["error"]


def test_executor_node_non_code_plan():
    state: AgentState = {
        "user_goal": "Summarize text",
        "plan": "1. Review notes.\n2. Summarize key points.",
    }
    result = executor_node(state)
    assert "No executable Python code required" in result["execution_result"]
    assert result["error"] == ""


def test_reflector_node_updates_plan_and_resets_error():
    mock_response = MagicMock(
        content="- CRITIQUE: Condition check needed.\n- CORRECTED_PLAN:\n```python\nprint(10)\n```"
    )
    state: AgentState = {
        "user_goal": "Divide safely",
        "plan": "print(1 / 0)",
        "execution_result": "FAILED",
        "error": "ZeroDivisionError",
    }

    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_response):
        result = reflector_node(state)

    assert result["iteration_count"] == 1
    assert "Condition check" in result["reflection_critique"]
    assert "```python" in result["plan"]
    assert result["error"] == ""
    assert result["execution_result"] == ""


def test_supervisor_node_sanitizes_next_node():
    mock_response = MagicMock(content="  **EXECUTOR**.  \n")
    state: AgentState = {"user_goal": "Do work"}

    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_response):
        result = supervisor_node(state)

    assert result["next_node"] == "EXECUTOR"


def test_planner_node():
    mock_response = MagicMock(content="1. Step\n```python\nprint('done')\n```")
    state: AgentState = {"user_goal": "Process data"}

    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_response):
        result = planner_node(state)

    assert "Step" in result["plan"]


def test_researcher_node():
    results = [{"title": "FastAPI", "content": "Async framework", "url": "https://fastapi.tiangolo.com"}]
    state: AgentState = {"user_goal": "Frameworks", "plan": "Search"}

    with patch("app.agents.researcher.search_web", return_value=results):
        result = researcher_node(state)

    assert "FastAPI" in result["research_data"]
