from typing import Any
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.config import settings
from app.graph.state import AgentState



prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are an elite AI technical architect and planner. Break the user's goal into an actionable, comprehensive strategic plan.
Output a numbered list with clear objectives, required data components, and expected outcomes.
Be direct, structured, and authoritative. Do not include conversational filler, preamble, or apologies.

If computation, data modeling, or metric verification is needed, include an executable Python code block (```python ... ```).
Code snippets must run autonomously in the sandbox:
- Write 100% self-contained Python computation code using standard libraries (math, json, datetime, re, random, collections, itertools, statistics).
- For repository or dataset analytics: DO NOT make external HTTP or network requests in the script. Use only actual data provided by the user or research context. Never fabricate representative repository files, datasets, or metrics. If the evidence is missing, plan to explain that limitation instead of computing invented numbers.
- Do not import restricted system modules like sys, os, subprocess, shutil, or socket.""",
		),
		("human", "Goal: {user_goal}\nAdditional context / Ground Truth:\n{research_data}"),
	]
)


def planner_node(state: AgentState) -> dict[str, Any]:
	user_goal = state.get("user_goal", "")
	research_data = state.get("research_data", "").strip()

	# If research data is not yet set (e.g. concurrent parallel launch), retrieve ground truth directly
	if not research_data:
		from app.agents.researcher import extract_github_repo
		repo = extract_github_repo(user_goal)
		if repo:
			try:
				from app.agents.researcher import fetch_github_raw
				fetched = fetch_github_raw(repo)
				if fetched:
					research_data = f"### GitHub README evidence (code and metrics not inspected):\n{fetched}"
			except Exception:
				pass

	model = get_llm(tier="fast", temperature=0.0, max_tokens=min(settings.MAX_TOKENS, 2048))
	response = (prompt | model).invoke(
		{
			"user_goal": user_goal,
			"research_data": research_data or "General technical objective.",
		}
	)
	state["plan"] = response.content
	return {"plan": response.content}
