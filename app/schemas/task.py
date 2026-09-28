from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
	goal: str
	title: str | None = None
	max_iterations: int = 5


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
	created_at: datetime
