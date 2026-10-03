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
			"""You are an executive deliverable synthesizer.
Using the research findings, plan, and user goal, produce a direct, concise, high-value final answer that directly satisfies the user's objective (e.g. structured bulleted list, exact specifications, or executive summary).
Be direct, structured, and concise. Do not include conversational preamble, conversational filler, or introductory remarks.""",
		),
		(
			"human",
			"""Objective: {user_goal}

Research Findings:
{research_data}

Plan:
{plan}""",
		),
	]
)


def executor_node(state: AgentState) -> dict[str, Any]:
	plan_text = state.get("plan", "")
	code = extract_code(plan_text)

	if not code:
		if state.get("research_data"):
			try:
				model = get_llm(tier="fast", temperature=0.2, max_tokens=384)
				synthesis = (synth_prompt | model).invoke(
					{
						"user_goal": state.get("user_goal", ""),
						"research_data": state.get("research_data", ""),
						"plan": plan_text,
					}
				).content
				res_text = synthesis
			except Exception:
				res_text = f"RESEARCH DATA:\n{state.get('research_data')}"
		else:
			res_text = "Plan verified: No executable Python code required."
		state["execution_result"] = res_text
		state["error"] = ""
		return {"execution_result": res_text, "error": ""}

	sandbox = SecureSandbox(
		timeout_seconds=min(settings.MAX_CODE_TIMEOUT_SECONDS, 8),
		max_output_chars=settings.MAX_CODE_OUTPUT_CHARS,
		enable_ast_check=settings.SECURE_SANDBOX_ENABLED,
	)
	res = sandbox.execute(code)

	if res.success:
		exec_res = f"SUCCESS:\n{res.stdout or 'No output'}"
		error_res = ""
	else:
		exec_res = f"FAILED (code {res.exit_code}):\n{res.stderr}"
		error_res = res.stderr

	state["execution_result"] = exec_res
	state["error"] = error_res
	return {"execution_result": exec_res, "error": error_res}

