from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.memory import agent_memory
from app.core.structured_llm import parse_reflection_output
from app.graph.state import AgentState


prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are a reflection agent. Analyze the execution result and any errors.
If execution failed:
1. Identify the exact root cause of the error (e.g. missing API token, 401 unauthorized, invalid headers, network exception, or syntax bug).
2. Fix the Python code snippet in the plan: make it robust, self-contained, and runnable in an automated sandbox (e.g. omit Authorization headers if token is missing/None, add exception handling, use public fallback endpoints or sample data).
3. Provide a clear CRITIQUE and the complete CORRECTED_PLAN.
If execution succeeded, suggest improvements and identify uncovered edge cases.

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


def reflector_node(state: AgentState) -> AgentState:
	model = get_llm(temperature=0.3, max_tokens=1024)
	response = (prompt | model).invoke(
		{
			"user_goal": state.get("user_goal", ""),
			"plan": state.get("plan", ""),
			"execution_result": state.get("execution_result", ""),
			"error": state.get("error", ""),
		}
	)
	parsed = parse_reflection_output(response)
	state["reflection_critique"] = response.content
	state["iteration_count"] = state.get("iteration_count", 0) + 1

	if parsed.corrected_plan:
		state["plan"] = parsed.corrected_plan
		state["execution_result"] = ""
		state["error"] = ""

	# Store critique into episodic memory for future RAG recall
	try:
		agent_memory.add(
			content=parsed.critique,
			metadata={
				"type": "reflection",
				"goal": state.get("user_goal", ""),
				"iteration": state["iteration_count"],
			},
		)
	except Exception:
		pass

	return state
