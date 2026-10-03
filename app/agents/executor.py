import os
import re
import subprocess
import sys
import tempfile
from typing import Any

from langchain_core.prompts import ChatPromptTemplate


from app.core.config import settings
from app.core.llm import get_llm
from app.core.sandbox import SecureSandbox
from app.graph.state import AgentState


def extract_code(text: str) -> str:
	py_match = re.search(r"```(?:python|py)\b[^\r\n]*[\r\n]+(.*?)```", text, re.DOTALL | re.IGNORECASE)
	if py_match:
		raw = py_match.group(1).strip()
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
			raw = content.strip()
			break
		if not raw and "```" in text and not blocks:
			parts = text.split("```")
			if len(parts) >= 3:
				raw = parts[1].strip()

	if not raw:
		return ""

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
	return "\n".join(clean_lines).strip()


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


def executor_node(state: AgentState) -> dict[str, Any]:
	plan_text = state.get("plan", "")
	code = extract_code(plan_text)
	research_data = state.get("research_data", "")
	user_goal = state.get("user_goal", "")

	if not code:
		return synthesize_answer(state, "No code execution required.")

	sandbox = SecureSandbox(
		timeout_seconds=min(settings.MAX_CODE_TIMEOUT_SECONDS, 8),
		max_output_chars=settings.MAX_CODE_OUTPUT_CHARS,
		enable_ast_check=settings.SECURE_SANDBOX_ENABLED,
	)
	res = sandbox.execute(code)

	if not res.success:
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
