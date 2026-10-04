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


def test_virtualize_file_io_transforms_open_and_runs_safely():
    from app.agents.executor import virtualize_file_io
    from app.core.sandbox import SecureSandbox, analyze_code_security

    code = """
with open("data.txt", "w") as f:
    f.write("APEX Autonomous Intelligence")
with open("data.txt", "r") as f:
    val = f.read()
print("RESULT:", val)
"""
    transformed = virtualize_file_io(code)
    assert "_apex_safe_open" in transformed

    # Verify transformed code passes AST static security checks
    is_safe, violations = analyze_code_security(transformed)
    assert is_safe is True
    assert len(violations) == 0

    # Verify it executes cleanly in sandbox
    sandbox = SecureSandbox(timeout_seconds=5)
    res = sandbox.execute(transformed)
    assert res.success is True
    assert res.exit_code == 0
    assert "RESULT: APEX Autonomous Intelligence" in res.stdout


def test_virtualize_file_io_preserves_code_without_open():
    from app.agents.executor import virtualize_file_io

    code = "import math\nprint(math.sqrt(16))"
    assert virtualize_file_io(code) == code


def test_extract_code_handles_nested_markdown_indentation():
    # Markdown list with indented code block
    text = """
1. Step one
   ```python
       import json
       data = {'item': 100}
       print(data)
   ```
"""
    code = extract_code(text)
    import ast
    # Ensure parsed without unexpected indent syntax error
    ast.parse(code)
    assert "import json" in code
    assert "print(data)" in code


def test_extract_github_repo_strips_sentence_words_after_dot():
    goal = "This is a github repository . https://github.com/akashgahlot-1a/PowerBI-Starbucks-Beverage-Analytics.Analyse this repo and generate its report"
    assert extract_github_repo(goal) == "akashgahlot-1a/PowerBI-Starbucks-Beverage-Analytics"


def test_executor_synthesizes_on_final_iteration_after_failed_code():
    from unittest.mock import patch, MagicMock
    from app.agents.executor import executor_node

    state: AgentState = {
        "user_goal": "Analyse repo",
        "plan": "```python\nraise RuntimeError('Mock execution issue')\n```",
        "iteration_count": 2, # final reflection iteration
    }
    mock_resp = MagicMock(content="Comprehensive Repository Analysis Report", response_metadata={})
    with patch("langchain_core.runnables.base.RunnableSequence.invoke", return_value=mock_resp):
        res = executor_node(state)
    assert "Comprehensive Repository Analysis Report" in res["execution_result"]
    assert res["error"] == ""


def test_virtualize_file_io_sanitizes_os_and_sys_imports():
    from app.agents.executor import virtualize_file_io
    from app.core.sandbox import SecureSandbox, analyze_code_security

    code = """import os
import sys
from os.path import join, exists

path = join("folder", "sub", "file.json")
with open("test.txt", "w") as f:
    f.write("APEX")

print("PATH:", path)
print("EXISTS:", exists("test.txt"))
print("SYS_ARGV:", len(sys.argv) > 0)
"""
    transformed = virtualize_file_io(code)
    is_safe, violations = analyze_code_security(transformed)
    assert is_safe is True
    assert len(violations) == 0

    sandbox = SecureSandbox(timeout_seconds=5)
    res = sandbox.execute(transformed)
    assert res.success is True
    assert res.exit_code == 0
    assert "PATH: folder/sub/file.json" in res.stdout
    assert "EXISTS: True" in res.stdout
    assert "SYS_ARGV: True" in res.stdout

