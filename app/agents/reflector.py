from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.graph.state import AgentState


prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are a reflection agent. Analyze the execution result.
If execution failed, identify the root cause, provide a specific fix, and rewrite the corrected plan.
If execution succeeded, suggest improvements and identify uncovered edge cases.
Use this format:
- CRITIQUE: analysis
- CORRECTED_PLAN: updated plan or improvements""",
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
	state["reflection_critique"] = response.content
	state["iteration_count"] = state.get("iteration_count", 0) + 1
	if "CORRECTED_PLAN:" in response.content:
		state["plan"] = response.content.split("CORRECTED_PLAN:", 1)[1].strip()
		state["execution_result"] = ""
		state["error"] = ""
	return state
