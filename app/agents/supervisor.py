from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.core.llm import get_llm
from app.core.structured_llm import parse_supervisor_decision
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
	exec_res = state.get("execution_result", "")
	error = state.get("error", "")
	iteration_count = state.get("iteration_count", 0)

	# 1. Deterministic guard: If execution already succeeded without errors, immediately terminate without looping
	if exec_res and not error:
		state["next_node"] = "FINISH"
		return state

	# 2. Deterministic guard: If execution failed with an unaddressed error, route to REFLECTOR
	if error and iteration_count < settings.MAX_ITERATIONS:
		state["next_node"] = "REFLECTOR"
		return state

	# 3. Deterministic guard: If iteration count reached max iterations, terminate
	if iteration_count >= settings.MAX_ITERATIONS:
		state["next_node"] = "FINISH"
		return state

	# 4. LLM supervisor decision with adequate token window for reasoning models
	model = get_llm(temperature=0, max_tokens=256)
	plan_text = state.get("plan", "").strip()
	response = (prompt | model).invoke(
		{
			"user_goal": state.get("user_goal", ""),
			"plan": plan_text,
			"research_data": state.get("research_data", ""),
			"execution_result": state.get("execution_result", ""),
			"reflection_critique": state.get("reflection_critique", ""),
			"iteration_count": state.get("iteration_count", 0),
			"error": state.get("error", ""),
		}
	)
	decision = parse_supervisor_decision(
		response,
		default_fallback="PLANNER" if not plan_text else "EXECUTOR",
	)
	if decision.next_agent in {"PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"}:
		state["next_node"] = decision.next_agent
	elif not plan_text:
		state["next_node"] = "PLANNER"
	elif not state.get("research_data"):
		state["next_node"] = "RESEARCHER"
	elif not state.get("execution_result"):
		state["next_node"] = "EXECUTOR"
	else:
		state["next_node"] = "FINISH"

	# Safety Guard: Never terminate prematurely if no plan exists or no execution/research was performed
	if state["next_node"] == "FINISH" and not exec_res and not state.get("research_data"):
		state["next_node"] = "PLANNER" if not plan_text else "EXECUTOR"

	# Guard: Never re-run planner if plan already formulated unless in reflection
	if state["next_node"] == "PLANNER" and plan_text and not state.get("reflection_critique"):
		state["next_node"] = "RESEARCHER" if not state.get("research_data") else "EXECUTOR"

	# Guard: Never re-run executor if execution already completed without error
	if state["next_node"] == "EXECUTOR" and state.get("execution_result") and not state.get("error"):
		state["next_node"] = "FINISH"

	return state
