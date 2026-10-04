"""
Comprehensive security test suite for Python sandbox execution and AST verification.
"""

from app.core.sandbox import ASTSecurityAnalyzer, SecureSandbox, analyze_code_security


def test_ast_allows_safe_standard_libraries():
    safe_code = """
import math
import json
import re
import datetime

val = math.sqrt(144)
data = json.dumps({"result": val})
print(data)
"""
    is_safe, violations = analyze_code_security(safe_code)
    assert is_safe is True
    assert len(violations) == 0


def test_ast_rejects_forbidden_modules():
    forbidden_snippets = [
        "import os\nos.system('dir')",
        "import subprocess\nsubprocess.run(['dir'])",
        "import sys\nsys.exit(0)",
        "import shutil\nshutil.rmtree('/')",
        "import socket\ns = socket.socket()",
        "from os import path",
        "from subprocess import Popen",
    ]

    for snippet in forbidden_snippets:
        is_safe, violations = analyze_code_security(snippet)
        assert is_safe is False, f"Expected unsafe for: {snippet}"
        assert len(violations) > 0


def test_ast_rejects_eval_exec_and_open():
    dangerous_calls = [
        "eval('1 + 1')",
        "exec('x = 10')",
        "open('/etc/passwd', 'r')",
        "compile('x = 1', '<string>', 'exec')",
    ]

    for snippet in dangerous_calls:
        is_safe, violations = analyze_code_security(snippet)
        assert is_safe is False, f"Expected unsafe for: {snippet}"
        assert any("prohibited built-in function" in v for v in violations)


def test_ast_rejects_dunder_sandbox_escapes():
    escape_snippets = [
        "().__class__.__bases__[0].__subclasses__()",
        "f = lambda: None; f.__code__",
        "x = ().__class__.__mro__",
    ]

    for snippet in escape_snippets:
        is_safe, violations = analyze_code_security(snippet)
        assert is_safe is False, f"Expected unsafe for: {snippet}"
        assert any("restricted attribute" in v for v in violations)


def test_sandbox_strips_sensitive_environment_variables():
    sandbox = SecureSandbox(timeout_seconds=5)
    env = sandbox.sanitize_environment()

    # Confirm secrets are completely eliminated from child process
    assert "OPENAI_API_KEY" not in env
    assert "GROQ_API_KEY" not in env
    assert "TAVILY_API_KEY" not in env
    assert "JWT_SECRET_KEY" not in env
    assert "DATABASE_URL" not in env


def test_sandbox_executes_benign_code_successfully():
    sandbox = SecureSandbox(timeout_seconds=10)
    code = "import math\nprint('Computed:', math.factorial(6))"
    result = sandbox.execute(code)

    assert result.success is True
    assert "Computed: 720" in result.stdout
    assert result.exit_code == 0
    assert result.stderr == ""


def test_sandbox_blocks_unsafe_code_without_running_process():
    sandbox = SecureSandbox(timeout_seconds=5, enable_ast_check=True)
    code = "import os\nos.system('whoami')"
    result = sandbox.execute(code)

    assert result.success is False
    assert result.exit_code == -1
    assert "Security Policy Violation" in result.stderr
    assert len(result.violations) > 0


def test_sandbox_enforces_timeout():
    sandbox = SecureSandbox(timeout_seconds=1, enable_ast_check=False)
    # Infinite loop
    code = "import time\nwhile True:\n    pass"
    result = sandbox.execute(code)

    assert result.success is False
    assert "TIMEOUT" in result.stderr
    assert result.exit_code == 124


def test_sandbox_blocks_indirect_io_network_and_dynamic_lookup():
    snippets = [
        'import pathlib', 'import urllib.request', 'import requests', 'import app.core.config',
        'import io\nio.open("/etc/passwd")', 'from io import FileIO\nFileIO("/etc/passwd")',
        'f = eval\nf("1+1")', 'getattr(object, "__subclasses__")',
    ]
    for code in snippets:
        safe, violations = analyze_code_security(code)
        assert not safe, code
        assert violations
