from typing import TypedDict


class AgentState(TypedDict, total=False):
	user_goal: str
	plan: str
	research_data: str
	execution_result: str
	reflection_critique: str
	iteration_count: int
	next_node: str
	error: str
	execution_mode: str

