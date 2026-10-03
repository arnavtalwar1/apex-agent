from typing import Any
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.config import settings
from app.core.memory import agent_memory
from app.core.structured_llm import parse_reflection_output
from app.graph.state import AgentState


prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are a reflection agent. Analyze the execution result and any errors.
Be direct, structured, and concise. Do not include conversational filler, preamble, or apologies.
If execution failed:
1. Identify the exact root cause of the error.
2. Fix the Python code snippet in the plan: make it robust, self-contained, and runnable in an automated sandbox (no sys/os/subprocess imports, avoid prohibited built-in functions like open()/eval()/exec(), compute in-memory, omit unneeded auth headers, add exception handling).
3. Provide a clear CRITIQUE and the complete CORRECTED_PLAN.

Use this format:
- CRITIQUE: analysis of failure and resolution
- CORRECTED_PLAN: updated plan with working code""",
		),
		(
			"human",
			"User goal: {user_goal}\nOriginal plan: {plan}\nExecution result: {execution_result}\nError: {error}",
		),
	]
)


def reflector_node(state: AgentState) -> dict[str, Any]:
	model = get_llm(tier="fast", temperature=0.0, max_tokens=min(settings.MAX_TOKENS, 2048))
	response = (prompt | model).invoke(
		{
			"user_goal": state.get("user_goal", ""),
			"plan": state.get("plan", ""),
			"execution_result": state.get("execution_result", ""),
			"error": state.get("error", ""),
		}
	)
	parsed = parse_reflection_output(response)
	new_iteration = state.get("iteration_count", 0) + 1
	new_plan = parsed.corrected_plan or state.get("plan", "")

	state["reflection_critique"] = response.content
	state["iteration_count"] = new_iteration
	if parsed.corrected_plan:
		state["plan"] = new_plan
		state["execution_result"] = ""
		state["error"] = ""

	# Store critique into episodic memory for future RAG recall
	try:
		agent_memory.add(
			content=parsed.critique,
			metadata={
				"type": "reflection",
				"goal": state.get("user_goal", ""),
				"iteration": new_iteration,
			},
		)
	except Exception:
		pass

	return {
		"reflection_critique": response.content,
		"iteration_count": new_iteration,
		"plan": new_plan,
		"execution_result": "" if parsed.corrected_plan else state.get("execution_result", ""),
		"error": "" if parsed.corrected_plan else state.get("error", ""),
	}
