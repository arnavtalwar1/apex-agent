import ast
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from typing import Any

from langchain_core.prompts import ChatPromptTemplate


from app.core.config import settings
from app.core.llm import get_llm
from app.core.sandbox import SecureSandbox
from app.graph.state import AgentState


def extract_code(text: str) -> str:
	py_match = re.search(r"```(?:python|py)\b[^\r\n]*[\r\n]+(.*?)```", text, re.DOTALL | re.IGNORECASE)
	if py_match:
		raw = py_match.group(1)
	else:
		blocks = re.findall(r"```([a-zA-Z0-9_-]*)[^\r\n]*[\r\n]+(.*?)```", text, re.DOTALL)
		raw = ""
		ignored_langs = {
			"bash", "sh", "shell", "zsh", "cmd", "powershell", "ps1",
			"json", "yaml", "yml", "toml", "dockerfile", "markdown", "md",
			"sql", "html", "css", "text", "txt"
		}
		for lang, content in blocks:
			if lang.strip().lower() in ignored_langs:
				continue
			raw = content
			break
		if not raw and "```" in text and not blocks:
			parts = text.split("```")
			if len(parts) >= 3:
				raw = parts[1]

	if not raw or not raw.strip():
		return ""

	# 1. Dedent raw block so any uniform indentation from markdown lists/quotes is stripped evenly
	raw = textwrap.dedent(raw)

	non_code_prefixes = ("pip ", "pip3 ", "!pip ", "%pip ", "npm ", "yarn ", "pnpm ", "curl ", "apt-get ", "bash ", "sh ")
	lines = raw.splitlines()
	clean_lines = []
	for line in lines:
		stripped = line.strip()
		if stripped.lower() in {"bash", "sh", "shell", "cmd", "python", "py"}:
			continue
		if any(stripped.startswith(prefix) for prefix in non_code_prefixes):
			continue
		clean_lines.append(line)

	full_code = textwrap.dedent("\n".join(clean_lines)).strip()

	# 2. Self-heal unexpected indentation on line 2+
	try:
		ast.parse(full_code)
	except SyntaxError:
		split_lines = full_code.splitlines()
		if len(split_lines) > 1 and (split_lines[1].startswith("    ") or split_lines[1].startswith("\t")):
			rest_dedented = textwrap.dedent("\n".join(split_lines[1:]))
			healed = split_lines[0] + "\n" + rest_dedented
			try:
				ast.parse(healed)
				full_code = healed
			except SyntaxError:
				pass

	return full_code


synth_prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You produce the final answer to the user's objective, not a plan or execution acknowledgement.
Follow the user's requested format and scope. Use an appropriate structure for the task; do not force simple answers into a technical report.
For code requests, include the requested implementation and relevant usage instructions.
Ground factual claims in the supplied evidence. Cite source URLs when present.
A plan is proposed work, not verified evidence. A README does not prove repository metrics or implementation details.
Never invent data, files, metrics, citations, or claim live verification without supporting evidence.
If external evidence is unavailable, state the limitation and answer only what can be supported by the user's input or general knowledge.
Sandbox execution verifies only that the supplied code ran, not the truth of embedded data.
Distinguish assumptions, illustrative examples, and actual observed results.
Return a complete answer; avoid filler.""",
		),
		(
			"human",
			"""Objective: {user_goal}

Web Intelligence:
{research_data}

Strategic Plan:
{plan}

Sandbox Runtime Output:
{sandbox_output}""",
		),
	]
)


def sanitize_code_imports(code: str) -> str:
	"""
	Sanitizes import statements targeting forbidden modules (os, sys, shutil, posixpath, ntpath).
	Uses AST node transformation with regex fallback to guarantee zero forbidden import nodes survive.
	"""
	forbidden_roots = {"os", "sys", "shutil", "posixpath", "ntpath"}

	try:
		tree = ast.parse(code)

		class ImportSanitizer(ast.NodeTransformer):
			def visit_Import(self, node: ast.Import):
				new_names = [alias for alias in node.names if alias.name.split(".")[0].lower() not in forbidden_roots]
				if not new_names:
					return None
				node.names = new_names
				return node

			def visit_ImportFrom(self, node: ast.ImportFrom):
				if node.module and node.module.split(".")[0].lower() in forbidden_roots:
					return None
				return node

		tree = ImportSanitizer().visit(tree)
		ast.fix_missing_locations(tree)
		return ast.unparse(tree)
	except Exception:
		# Fallback to line-by-line regex if syntax parsing fails
		lines = code.splitlines()
		cleaned_lines = []
		for line in lines:
			stripped = line.strip()
			if stripped.startswith("#"):
				cleaned_lines.append(line)
				continue

			# Handle 'from <module> import ...'
			from_m = re.match(r"^([ \t]*)from[ \t]+([a-zA-Z0-9_\.]+)[ \t]+import[ \t]+(.*)$", line)
			if from_m:
				indent, mod, imports = from_m.group(1), from_m.group(2), from_m.group(3)
				root_mod = mod.split(".")[0].lower()
				if root_mod in forbidden_roots:
					cleaned_lines.append(f"{indent}# [APEX Virtualized] {stripped}")
					continue

			# Handle 'import ...'
			import_m = re.match(r"^([ \t]*)import[ \t]+(.*)$", line)
			if import_m:
				indent, modules_str = import_m.group(1), import_m.group(2)
				parts = [p.strip() for p in modules_str.split(",")]
				keep = []
				for p in parts:
					p_root = p.split()[0].split(".")[0].lower()
					if p_root in forbidden_roots:
						pass
					else:
						keep.append(p)
				if keep:
					cleaned_lines.append(f"{indent}import " + ", ".join(keep))
				else:
					cleaned_lines.append(f"{indent}# [APEX Virtualized] {stripped}")
				continue

			cleaned_lines.append(line)

		return "\n".join(cleaned_lines)


def virtualize_file_io(code: str, force: bool = False) -> str:
	"""
	Transforms code containing open() calls and system imports into safe in-memory virtual operations.
	Prevents sandbox security policy violation while safely supporting file simulations and calculations.
	"""
	has_open = bool(re.search(r"\bopen\s*\(", code))
	has_forbidden_mod = bool(
		re.search(
			r"\b(import\s+(?:[a-zA-Z0-9_,\s]*\b)?(os|sys|shutil|posixpath|ntpath)\b|from\s+(os|sys|shutil|posixpath|ntpath)\b)",
			code,
		)
	)

	if not force and not has_open and not has_forbidden_mod:
		return code

	cleaned = sanitize_code_imports(code)
	transformed = re.sub(r"\bopen\s*\(", "_apex_safe_open(", cleaned)

	virtual_shim = """import io as _apex_io

_apex_virtual_fs = {}

class _ApexVirtualFile:
    def __init__(self, filename, mode="r", *args, **kwargs):
        self.filename = str(filename)
        self.mode = mode
        clean_name = self.filename.replace("\\\\", "/").strip("/")
        self._key = clean_name
        if "b" in mode:
            raw = _apex_virtual_fs.get(self._key, _apex_virtual_fs.get(self.filename, b""))
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            initial = raw if ("a" in mode or "r" in mode) else b""
            self._stream = _apex_io.BytesIO(initial)
            if "a" in mode:
                self._stream.seek(0, _apex_io.SEEK_END)
        else:
            raw = _apex_virtual_fs.get(self._key, _apex_virtual_fs.get(self.filename, ""))
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            initial = raw if ("a" in mode or "r" in mode) else ""
            self._stream = _apex_io.StringIO(initial)
            if "a" in mode:
                self._stream.seek(0, _apex_io.SEEK_END)

    def write(self, s):
        res = self._stream.write(s)
        val = self._stream.getvalue()
        _apex_virtual_fs[self._key] = val
        _apex_virtual_fs[self.filename] = val
        return res

    def read(self, *args):
        return self._stream.read(*args)

    def readline(self, *args):
        return self._stream.readline(*args)

    def readlines(self, *args):
        return self._stream.readlines(*args)

    def seek(self, *args):
        return self._stream.seek(*args)

    def tell(self):
        return self._stream.tell()

    def flush(self):
        if hasattr(self, "_stream") and not self._stream.closed:
            if "w" in self.mode or "a" in self.mode:
                val = self._stream.getvalue()
                _apex_virtual_fs[self._key] = val
                _apex_virtual_fs[self.filename] = val

    def close(self):
        if hasattr(self, "_stream") and not self._stream.closed:
            if "w" in self.mode or "a" in self.mode:
                val = self._stream.getvalue()
                _apex_virtual_fs[self._key] = val
                _apex_virtual_fs[self.filename] = val
            self._stream.close()

    def __iter__(self):
        return iter(self._stream)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

def _apex_safe_open(filename, mode="r", *args, **kwargs):
    return _ApexVirtualFile(filename, mode, *args, **kwargs)

class _ApexSafePath:
    @staticmethod
    def join(*args):
        parts = []
        for a in args:
            if not a:
                continue
            s = str(a).replace("\\\\", "/")
            if s.startswith("/"):
                parts = [s.rstrip("/")]
            else:
                parts.append(s.strip("/"))
        joined = "/".join(p for p in parts if p)
        if args and str(args[0]).startswith("/") and not joined.startswith("/"):
            joined = "/" + joined
        return joined or "."

    @staticmethod
    def basename(p):
        return str(p).replace("\\\\", "/").rstrip("/").split("/")[-1]

    @staticmethod
    def dirname(p):
        parts = str(p).replace("\\\\", "/").rstrip("/").split("/")
        return "/".join(parts[:-1]) if len(parts) > 1 else ("/" if str(p).startswith("/") else "")

    @staticmethod
    def split(p):
        return _ApexSafePath.dirname(p), _ApexSafePath.basename(p)

    @staticmethod
    def splitext(p):
        p_str = str(p)
        base = p_str.replace("\\\\", "/").rstrip("/").split("/")[-1]
        dot = base.rfind(".")
        if dot > 0:
            ext_len = len(base) - dot
            return p_str[:-ext_len], p_str[-ext_len:]
        return p_str, ""

    @staticmethod
    def exists(p):
        p_str = str(p).replace("\\\\", "/").strip("/")
        return bool(p_str in _apex_virtual_fs or str(p) in _apex_virtual_fs or any(k.startswith(p_str + "/") for k in _apex_virtual_fs))

    @staticmethod
    def isfile(p):
        p_str = str(p).replace("\\\\", "/").strip("/")
        return bool(p_str in _apex_virtual_fs or str(p) in _apex_virtual_fs)

    @staticmethod
    def isdir(p):
        p_str = str(p).replace("\\\\", "/").strip("/")
        return any(k.startswith(p_str + "/") for k in _apex_virtual_fs)

    @staticmethod
    def getsize(p):
        p_str = str(p).replace("\\\\", "/").strip("/")
        val = _apex_virtual_fs.get(p_str, _apex_virtual_fs.get(str(p), ""))
        return len(val) if isinstance(val, (str, bytes)) else 0

    @staticmethod
    def abspath(p):
        return "/" + str(p).replace("\\\\", "/").lstrip("/")

    @staticmethod
    def relpath(p, start=None):
        return str(p).replace("\\\\", "/").lstrip("/")

    @staticmethod
    def isabs(p):
        s = str(p)
        return s.startswith("/") or s.startswith("\\\\") or (len(s) > 1 and s[1] == ":")

    @staticmethod
    def normpath(p):
        return str(p).replace("\\\\", "/")

class _ApexSafeOS:
    path = _ApexSafePath
    sep = "/"
    linesep = "\\n"
    name = "posix"
    curdir = "."
    pardir = ".."
    extsep = "."
    devnull = "/dev/null"
    environ = {}

    @staticmethod
    def getenv(key, default=None):
        return _ApexSafeOS.environ.get(key, default)

    @staticmethod
    def getcwd():
        return "/"

    @staticmethod
    def listdir(path="."):
        return list(_apex_virtual_fs.keys())

    @staticmethod
    def walk(top=".", *args, **kwargs):
        yield (".", [], list(_apex_virtual_fs.keys()))

    @staticmethod
    def makedirs(name, exist_ok=False):
        pass

    @staticmethod
    def mkdir(name):
        pass

    @staticmethod
    def remove(path):
        p_str = str(path).replace("\\\\", "/").strip("/")
        _apex_virtual_fs.pop(p_str, None)
        _apex_virtual_fs.pop(str(path), None)

    @staticmethod
    def unlink(path):
        _ApexSafeOS.remove(path)

class _ApexSafeSys:
    argv = ["sandbox.py"]
    version = "3.11.0 (APEX Sandbox)"
    platform = "linux"
    maxsize = 9223372036854775807
    byteorder = "little"
    exit = staticmethod(lambda code=0: None)

class _ApexSafeShutil:
    @staticmethod
    def copy(src, dst):
        if str(src) in _apex_virtual_fs:
            _apex_virtual_fs[str(dst)] = _apex_virtual_fs[str(src)]

    @staticmethod
    def move(src, dst):
        if str(src) in _apex_virtual_fs:
            _apex_virtual_fs[str(dst)] = _apex_virtual_fs.pop(str(src))

    @staticmethod
    def rmtree(path, ignore_errors=False):
        p_str = str(path)
        for k in list(_apex_virtual_fs.keys()):
            if k.startswith(p_str):
                _apex_virtual_fs.pop(k, None)

os = _ApexSafeOS()
sys = _ApexSafeSys()
shutil = _ApexSafeShutil()
path = _ApexSafePath
join = _ApexSafePath.join
exists = _ApexSafePath.exists
basename = _ApexSafePath.basename
dirname = _ApexSafePath.dirname
splitext = _ApexSafePath.splitext
split = _ApexSafePath.split
abspath = _ApexSafePath.abspath
relpath = _ApexSafePath.relpath
isabs = _ApexSafePath.isabs
normpath = _ApexSafePath.normpath
isfile = _ApexSafePath.isfile
isdir = _ApexSafePath.isdir
getsize = _ApexSafePath.getsize
getenv = _ApexSafeOS.getenv
environ = _ApexSafeOS.environ
argv = _ApexSafeSys.argv
"""
	return virtual_shim + "\n" + transformed


def executor_node(state: AgentState) -> dict[str, Any]:
	plan_text = state.get("plan", "")
	code = extract_code(plan_text)
	research_data = state.get("research_data", "")
	user_goal = state.get("user_goal", "")

	if not code:
		return synthesize_answer(state, "No code execution required.")

	# Prepare code: virtualize open() calls to safe in-memory file I/O
	run_code = virtualize_file_io(code)

	sandbox = SecureSandbox(
		timeout_seconds=max(settings.MAX_CODE_TIMEOUT_SECONDS, 15),
		max_output_chars=settings.MAX_CODE_OUTPUT_CHARS,
		enable_ast_check=settings.SECURE_SANDBOX_ENABLED,
	)
	res = sandbox.execute(run_code)

	# If initial execution failed due to an open() or forbidden module violation, retry with forced virtualization
	if not res.success and run_code == code:
		run_code = virtualize_file_io(code, force=True)
		res = sandbox.execute(run_code)

	if not res.success:
		# If on the final reflection iteration, synthesize the final answer with an execution diagnosis
		# so the user receives their complete report and analysis instead of a raw pipeline error.
		iteration_count = state.get("iteration_count", 0)
		if iteration_count >= settings.MAX_ITERATIONS - 1:
			fail_note = f"Execution note: Sandbox execution encountered: {res.stderr.strip()}. Synthesizing comprehensive technical deliverable from research context and strategic plan."
			return synthesize_answer(state, sandbox_output=fail_note, executed=False)

		exec_res = f"FAILED (code {res.exit_code}):\n{res.stderr}"
		error_res = res.stderr
		state["execution_result"] = exec_res
		state["error"] = error_res
		return {"execution_result": exec_res, "error": error_res}

	# Code executed cleanly in sandbox
	sandbox_stdout = (res.stdout or "").strip() or "Execution completed successfully with exit code 0."

	return synthesize_answer(state, sandbox_stdout, executed=True)


def synthesize_answer(state: AgentState, sandbox_output: str, executed: bool = False) -> dict[str, Any]:
	try:
		model = get_llm(tier="reasoning", temperature=0.1, max_tokens=settings.MAX_TOKENS)
		response = (synth_prompt | model).invoke({
			"user_goal": state.get("user_goal", ""),
			"research_data": state.get("research_data", "") or "No external sources available.",
			"plan": state.get("plan", ""),
			"sandbox_output": sandbox_output,
		})
		finish_reason = (
			getattr(response, "response_metadata", {}).get("finish_reason")
			or getattr(response, "response_metadata", {}).get("stop_reason")
			or getattr(response, "additional_kwargs", {}).get("finish_reason")
			or getattr(response, "additional_kwargs", {}).get("stop_reason")
		)
		if finish_reason in ("length", "max_tokens"):
			raise ValueError("Answer exceeded the configured token limit; increase MAX_TOKENS.")
		report = response.content.strip()
		if not report:
			raise ValueError("The model returned an empty answer.")
		if executed:
			report += f"\n\n---\n### Sandbox execution (SUCCESS)\nCode ran with exit code 0. Embedded data was not independently verified.\n```\n{sandbox_output}\n```"
		result = {"execution_result": report, "error": ""}
	except Exception as exc:
		error = f"Answer generation failed: {exc}"
		result = {"execution_result": error, "error": error}
	state.update(result)
	return result
