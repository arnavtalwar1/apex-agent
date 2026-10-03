from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.graph.state import AgentState


prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are a planner. Break the user's goal into a clear, step-by-step actionable plan.
Output a numbered list with a clear action, required tools, and expected outcome for each step.
Be specific and practical. If code execution, computation, or verification is needed, include a self-contained, executable Python code snippet inside a ```python ``` code block.
Code snippets must run autonomously in an isolated sandbox:
- Use public unauthenticated API endpoints or graceful fallbacks if private tokens (like GITHUB_TOKEN) are unset (e.g. omit Authorization header if token is missing or None).
- Include try/except error handling so the script completes cleanly and outputs verified results.
- Do not import restricted system modules like sys, os, subprocess, shutil, or socket. Write clean Python code using standard libraries such as math, json, datetime, re, random, collections, itertools, or urllib.request.""",
		),
		("human", "Goal: {user_goal}\nAdditional context: {research_data}"),
	]
)


def planner_node(state: AgentState) -> AgentState:
	model = get_llm(temperature=0.2, max_tokens=1024)
	response = (prompt | model).invoke(
		{
			"user_goal": state.get("user_goal", ""),
			"research_data": state.get("research_data", ""),
		}
	)
	state["plan"] = response.content
	return state
