from unittest.mock import MagicMock, patch
import pytest

from app.agents.executor import executor_node, extract_code, synthesize_answer
from app.agents.planner import planner_node
from app.agents.reflector import reflector_node
from app.agents.researcher import extract_github_repo, researcher_node
from app.graph.state import AgentState


def test_extract_code_ignores_non_python_blocks():
    text = "```bash\ncurl -s https://example.com\n```\n```python\nprint(42)\n```"
    assert extract_code(text) == "print(42)"


def test_extract_code_strips_package_manager_prefixes():
    text = "```python\npip install requests\n!pip install pandas\nimport math\nprint(math.pi)\n```"
    code = extract_code(text)
    assert "pip install" not in code
    assert "import math" in code


def test_extract_github_repo_url_and_removes_git():
    assert extract_github_repo("Analyze https://github.com/torvalds/linux.git now") == "torvalds/linux"
    assert extract_github_repo("Investigate owner/repo for architecture") == "owner/repo"
    assert extract_github_repo("See https://example.com/not/github for info") is None
    assert extract_github_repo("Check https://github.com/arnavtalwar1/apex-agent repository") == "arnavtalwar1/apex-agent"
    assert extract_github_repo("Inspect github.com/arnavtalwar1/apex-agent.") == "arnavtalwar1/apex-agent"


def test_default_max_tokens_is_4096():
    from app.core.config import settings
    assert settings.MAX_TOKENS == 4096


def test_synthesize_answer_execution_success():
    state: AgentState = {
        "user_goal": "Calculate numbers",
        "research_data": "",
        "plan": "1. Run code",
    }
    mock_resp = MagicMock(content="Here is the calculated result.", response_metadata={})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = synthesize_answer(state, "42", executed=True)
    assert "Here is the calculated result." in res["execution_result"]
    assert "Sandbox execution (SUCCESS)" in res["execution_result"]
    assert "42" in res["execution_result"]
    assert res["error"] == ""


def test_synthesize_answer_length_exceeded():
    state: AgentState = {"user_goal": "Big prompt", "plan": "Plan"}
    mock_resp = MagicMock(content="Partial text", response_metadata={"finish_reason": "length"})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = synthesize_answer(state, "Output", executed=False)
    assert "Answer exceeded the configured token limit" in res["error"]


def test_synthesize_answer_empty_response():
    state: AgentState = {"user_goal": "Goal", "plan": "Plan"}
    mock_resp = MagicMock(content="", response_metadata={})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = synthesize_answer(state, "Output", executed=False)
    assert "empty answer" in res["error"]


def test_reflector_preserves_error_when_no_corrected_plan():
    state: AgentState = {
        "user_goal": "Task",
        "plan": "Original plan",
        "execution_result": "FAILED: SyntaxError",
        "error": "SyntaxError on line 1",
    }
    mock_resp = MagicMock(content="CRITIQUE: Unfixable problem with no code provided.", response_metadata={})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = reflector_node(state)
    assert res["error"] == "SyntaxError on line 1"
    assert res["execution_result"] == "FAILED: SyntaxError"


def test_researcher_includes_citations():
    results = [
        {"title": "Documentation", "content": "FastAPI overview", "url": "https://fastapi.tiangolo.com"}
    ]
    state: AgentState = {"user_goal": "Check FastAPI documentation"}
    with patch("app.agents.researcher.search_web", return_value=results):
        res = researcher_node(state)
    assert "Source: https://fastapi.tiangolo.com" in res["research_data"]


def test_text_only_task_generates_final_answer():
    state: AgentState = {
        "user_goal": "Explain architectural trade-offs of microservices",
        "plan": "1. Define microservices.\n2. List trade-offs.",
        "research_data": "Decoupled deployability vs distributed complexity.",
    }
    mock_resp = MagicMock(content="Microservices offer strong decoupling but increase operational complexity.", response_metadata={})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = executor_node(state)
    assert res["error"] == ""
    assert "Plan verified" not in res["execution_result"]
    assert "Microservices offer strong decoupling" in res["execution_result"]


def test_synthesize_answer_max_tokens_finish_reason():
    state: AgentState = {"user_goal": "Lengthy request", "plan": "Plan"}
    mock_resp = MagicMock(content="Cut-off output", response_metadata={"finish_reason": "max_tokens"})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = synthesize_answer(state, "Output", executed=False)
    assert "Answer exceeded the configured token limit" in res["error"]

