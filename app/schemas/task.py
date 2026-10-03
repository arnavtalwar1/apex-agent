from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
	goal: str
	title: str | None = None
	max_iterations: int = 5
	requires_approval: bool = False


class TaskResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	title: str | None
	goal: str
	status: str
	plan: str | None
	current_node: str | None
	reflection_count: int
	final_output: str | None
	requires_approval: bool = False
	approval_status: str = "none"
	token_cost: float = 0.0
	trace_id: str | None = None
	created_at: datetime
