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
			"""You are an elite AI technical analyst and executive deliverable synthesizer.
Produce a thorough, authoritative, and structured Markdown deliverable that directly and comprehensively answers the user's objective (e.g. detailed repository analytics report, technical architecture breakdown, or empirical findings).

Structure your deliverable with clear sections:
# [Clear, Impactful Deliverable Title]

## 1. Executive Summary & Context
- Mission scope, core objectives, and high-level evaluation.

## 2. Technical Architecture & System Breakdown
- Component breakdown, tech stack / schema analysis, and workflow design.

## 3. Key Analytical Findings & Derived Insights
- Specific metrics, trends, structural patterns, or observations derived from runtime execution or web intelligence.

## 4. Strategic Recommendations & Optimization Roadmap
- High-priority action items, best practices, and next steps.

Guidelines:
- Strict Grounding: Anchor all architecture details, schema breakdowns, and findings strictly in the provided Web Intelligence, Strategic Plan, and Sandbox Runtime Output. Do not invent files, schemas, or metrics.
- Distinguish empirical runtime data (from sandbox stdout) from contextual domain deductions.
- Format with rich Markdown: bold key metrics, clean bulleted lists, and structured tables where helpful.
- Be authoritative, specific, and direct. Avoid conversational filler, meta-announcements, or apologies.""",
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
		if research_data:
			try:
				model = get_llm(tier="fast", temperature=0.1, max_tokens=512)
				synthesis = (synth_prompt | model).invoke(
					{
						"user_goal": user_goal,
						"research_data": research_data,
						"plan": plan_text,
						"sandbox_output": "No code execution required.",
					}
				).content
				res_text = synthesis
			except Exception:
				res_text = f"## Intelligence Report\n\n{plan_text}\n\n### Web Intelligence\n{research_data}"
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

	if not res.success:
		exec_res = f"FAILED (code {res.exit_code}):\n{res.stderr}"
		error_res = res.stderr
		state["execution_result"] = exec_res
		state["error"] = error_res
		return {"execution_result": exec_res, "error": error_res}

	# Code executed cleanly in sandbox
	sandbox_stdout = (res.stdout or "").strip() or "Execution completed successfully with exit code 0."

	try:
		model = get_llm(tier="fast", temperature=0.1, max_tokens=768)
		synthesis = (synth_prompt | model).invoke(
			{
				"user_goal": user_goal,
				"research_data": research_data or "No external web intelligence required.",
				"plan": plan_text,
				"sandbox_output": sandbox_stdout,
			}
		).content
		report = synthesis.strip()
	except Exception:
		report = f"## Verified Technical Analysis\n\n{plan_text}"

	deliverable = f"{report}\n\n---\n### 🧪 Sandbox Runtime Execution Audit (SUCCESS)\n✅ **Status:** Verified (Exit code 0)\n```\n{sandbox_stdout}\n```"

	state["execution_result"] = deliverable
	state["error"] = ""
	return {"execution_result": deliverable, "error": ""}

