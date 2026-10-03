"""
Secure Python code execution sandbox with AST analysis, process isolation,
and strict environment variable sanitization.
"""

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Optional


# Modules prohibited from being imported in untrusted LLM-generated code
FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "pty",
    "ctypes",
    "multiprocessing",
    "threading",
    "signal",
    "inspect",
    "builtins",
    "importlib",
    "code",
    "codeop",
    "webbrowser",
    "posix",
    "nt",
    "posixpath",
    "ntpath",
    "pickle",
    "shelve",
    "marshal",
}

# Built-in functions forbidden from direct call
FORBIDDEN_CALLS = {
    "exec",
    "eval",
    "compile",
    "__import__",
    "open",
    "input",
    "globals",
    "locals",
}

# Forbidden dunder attribute accesses commonly used in sandbox escapes
FORBIDDEN_ATTRIBUTES = {
    "__subclasses__",
    "__bases__",
    "__mro__",
    "__globals__",
    "__code__",
    "__builtins__",
    "__import__",
}

# Safe environment variables allowed in the sandbox child process
SAFE_ENV_VARS = {
    "PATH",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "PYTHONIOENCODING",
    "PYTHONPATH",
    "LANG",
    "LC_ALL",
}


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    violations: list[str] = field(default_factory=list)


class ASTSecurityAnalyzer(ast.NodeVisitor):
    """
    Statically analyzes Python code AST for hazardous operations,
    prohibited imports, and sandbox escape vectors.
    """

    def __init__(self, allowed_modules: Optional[set[str]] = None):
        self.violations: list[str] = []
        self.allowed_modules = allowed_modules

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            root_module = alias.name.split(".")[0].lower()
            if root_module in FORBIDDEN_MODULES:
                self.violations.append(f"Import of forbidden module '{alias.name}' (line {node.lineno})")
            elif self.allowed_modules and root_module not in self.allowed_modules:
                self.violations.append(f"Module '{alias.name}' is not in allowed whitelist (line {node.lineno})")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            root_module = node.module.split(".")[0].lower()
            if root_module in FORBIDDEN_MODULES:
                self.violations.append(f"Import from forbidden module '{node.module}' (line {node.lineno})")
            elif self.allowed_modules and root_module not in self.allowed_modules:
                self.violations.append(f"Module '{node.module}' is not in allowed whitelist (line {node.lineno})")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Detect calls to forbidden functions like eval(), exec(), open()
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_CALLS:
                self.violations.append(f"Call to prohibited built-in function '{func_name}()' (line {node.lineno})")
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in FORBIDDEN_ATTRIBUTES:
                self.violations.append(f"Access to restricted attribute '{attr_name}' (line {node.lineno})")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in FORBIDDEN_ATTRIBUTES:
            self.violations.append(f"Access to restricted attribute '{node.attr}' (line {node.lineno})")
        self.generic_visit(node)


def analyze_code_security(code: str) -> tuple[bool, list[str]]:
    """
    Parses and inspects code AST. Returns (is_safe, violations).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as syntax_err:
        return False, [f"Syntax error: {syntax_err}"]

    analyzer = ASTSecurityAnalyzer()
    analyzer.visit(tree)
    is_safe = len(analyzer.violations) == 0
    return is_safe, analyzer.violations


class SecureSandbox:
    """
    Executes Python code with AST static analysis, environment variable stripping,
    strict timeout enforcement, and output truncation.
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_output_chars: int = 25000,
        enable_ast_check: bool = True,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars
        self.enable_ast_check = enable_ast_check

    def sanitize_environment(self) -> dict[str, str]:
        """
        Creates an isolated environment whitelist.
        Prevents leaking OpenAI, Groq, Tavily, Redis, Database, and JWT secrets.
        """
        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in SAFE_ENV_VARS
        }
        clean_env["PYTHONIOENCODING"] = "utf-8"
        return clean_env

    def execute(self, code: str) -> ExecutionResult:
        """
        Validates and runs Python code in an isolated subshell.
        """
        if not code.strip():
            return ExecutionResult(
                success=True,
                stdout="No code provided.",
                stderr="",
                exit_code=0,
            )

        # 1. AST Static Security Check
        if self.enable_ast_check:
            is_safe, violations = analyze_code_security(code)
            if not is_safe:
                violation_summary = "; ".join(violations)
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Security Policy Violation: Untrusted code rejected: {violation_summary}",
                    exit_code=-1,
                    violations=violations,
                )

        # 2. Write to isolated temporary file
        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name

            clean_env = self.sanitize_environment()

            # 3. Subprocess execution with resource & timeout caps
            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                env=clean_env,
                check=False,
            )

            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip()

            # Enforce output length limit to avoid buffer exhaustion
            if len(stdout) > self.max_output_chars:
                stdout = stdout[: self.max_output_chars] + "\n...[OUTPUT TRUNCATED: Exceeded char limit]"
            if len(stderr) > self.max_output_chars:
                stderr = stderr[: self.max_output_chars] + "\n...[STDERR TRUNCATED: Exceeded char limit]"

            return ExecutionResult(
                success=proc.returncode == 0,
                stdout=stdout or "No output",
                stderr=stderr,
                exit_code=proc.returncode,
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"TIMEOUT: Execution exceeded {self.timeout_seconds} seconds",
                exit_code=124,
            )
        except Exception as exc:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"EXECUTION EXCEPTION: {exc}",
                exit_code=-1,
            )
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
