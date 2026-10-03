from typing import Any
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.graph.state import AgentState



prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are a planner. Break the user's goal into a clear, step-by-step actionable plan.
Output a numbered list with a clear action, required tools, and expected outcome for each step.
Be direct, structured, and concise. Avoid conversational filler, conversational preambles, or conversational intros/outros.
If code execution, computation, or verification is needed, include a self-contained, executable Python code snippet inside a ```python ``` code block.
Code snippets must run autonomously in an isolated sandbox:
- For repository metrics, analytics, or external services: write self-contained Python computation using embedded samples, simulated structures, or regex. Do not block on external APIs that rate-limit or hang; if making an HTTP request, enforce timeout=2 with instant fallback sample data so execution finishes in under 2 seconds.
- Do not import restricted system modules like sys, os, subprocess, shutil, or socket. Write clean Python code using standard libraries such as math, json, datetime, re, random, collections, itertools, or statistics.""",
		),
		("human", "Goal: {user_goal}\nAdditional context: {research_data}"),
	]
)


def planner_node(state: AgentState) -> dict[str, Any]:
	model = get_llm(tier="fast", temperature=0.0, max_tokens=512)
	response = (prompt | model).invoke(
		{
			"user_goal": state.get("user_goal", ""),
			"research_data": state.get("research_data", ""),
		}
	)
	state["plan"] = response.content
	return {"plan": response.content}

