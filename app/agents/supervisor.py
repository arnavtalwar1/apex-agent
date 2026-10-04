from typing import Any
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


def supervisor_node(state: AgentState) -> dict[str, Any]:
	exec_res = state.get("execution_result", "")
	error = state.get("error", "")
	iteration_count = state.get("iteration_count", 0)
	plan_text = state.get("plan", "").strip()
	research_text = state.get("research_data", "").strip()
	execution_mode = state.get("execution_mode", "").lower()


	is_exec_failed = bool(exec_res and (exec_res.startswith("FAILED") or exec_res.startswith("EXCEPTION") or exec_res.startswith("Answer generation failed")))

	# 1. Deterministic guard: If execution already succeeded without errors, immediately terminate without looping (0 tokens)
	if exec_res and not error and not is_exec_failed:
		state["next_node"] = "FINISH"
		return {"next_node": "FINISH"}

	# 2. Deterministic guard: If execution failed with an unaddressed error, route to REFLECTOR (0 tokens)
	if (error or is_exec_failed) and iteration_count < settings.MAX_ITERATIONS:
		state["next_node"] = "REFLECTOR"
		return {"next_node": "REFLECTOR"}

	# 3. Deterministic guard: If iteration count reached max iterations, terminate (0 tokens)
	if iteration_count >= settings.MAX_ITERATIONS:
		state["next_node"] = "FINISH"
		return {"next_node": "FINISH"}

	# 4. Zero-token deterministic sequential progression (Classic APEX Architecture)
	if execution_mode == "sequential":
		if not plan_text:
			state["next_node"] = "PLANNER"
			return {"next_node": "PLANNER"}
		if not research_text:
			state["next_node"] = "RESEARCHER"
			return {"next_node": "RESEARCHER"}
		if not exec_res and not error:
			state["next_node"] = "EXECUTOR"
			return {"next_node": "EXECUTOR"}
		state["next_node"] = "FINISH"
		return {"next_node": "FINISH"}

	# 5. Parallel mode fast-path (if explicitly requested)
	if not plan_text and not research_text and execution_mode == "parallel":
		state["next_node"] = "PARALLEL"
		return {"next_node": "PARALLEL"}

	if (plan_text or research_text) and not exec_res and not error and execution_mode == "parallel":
		state["next_node"] = "EXECUTOR"
		return {"next_node": "EXECUTOR"}

	# 6. Fallback LLM supervisor decision for sequential mode or edge cases (token-efficient fast tier)
	model = get_llm(tier="fast", temperature=0, max_tokens=128)
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

	return {"next_node": state["next_node"]}

