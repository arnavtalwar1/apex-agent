from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.graph.state import AgentState


prompt = ChatPromptTemplate.from_messages(
	[
		(
			"system",
			"""You are a task supervisor. Analyze the current state and decide which agent should act next.

Available agents: PLANNER, RESEARCHER, EXECUTOR, REFLECTOR, FINISH.

Rules:
- If no plan exists, choose PLANNER.
- If a plan exists but no research exists, choose RESEARCHER.
- If plan and research exist and execution hasn't run yet, choose EXECUTOR.
- If reflection provided a corrected plan and execution has not run on it yet, choose EXECUTOR.
- If execution failed with an unaddressed error, choose REFLECTOR.
- If execution succeeded or verified, choose FINISH.
- If iteration count is at least the configured limit, choose FINISH.

Reply with exactly one word: PLANNER, RESEARCHER, EXECUTOR, REFLECTOR, or FINISH.""",
		),
		(
			"human",
			"""User goal: {user_goal}
Current plan: {plan}
Research data: {research_data}
Execution result: {execution_result}
Reflection: {reflection_critique}
Iteration: {iteration_count}
Error: {error}""",
		),
	]
)


def supervisor_node(state: AgentState) -> AgentState:
	model = get_llm(temperature=0, max_tokens=16)
	response = (prompt | model).invoke(
		{
			"user_goal": state.get("user_goal", ""),
			"plan": state.get("plan", ""),
			"research_data": state.get("research_data", ""),
			"execution_result": state.get("execution_result", ""),
			"reflection_critique": state.get("reflection_critique", ""),
			"iteration_count": state.get("iteration_count", 0),
			"error": state.get("error", ""),
		}
	)
	cleaned = response.content.strip().upper().replace("*", "").replace(".", "")
	valid = {"PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"}
	words = [w for w in cleaned.split() if w in valid]
	if words:
		state["next_node"] = words[0]
	elif not state.get("plan"):
		state["next_node"] = "PLANNER"
	elif not state.get("research_data"):
		state["next_node"] = "RESEARCHER"
	elif not state.get("execution_result"):
		state["next_node"] = "EXECUTOR"
	else:
		state["next_node"] = "FINISH"
	return state
