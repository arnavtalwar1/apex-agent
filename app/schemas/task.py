from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
	goal: str = Field(min_length=1, max_length=10000)
	title: str | None = Field(default=None, max_length=200)
	max_iterations: int = 5
	requires_approval: bool = False

	@field_validator("goal")
	@classmethod
	def validate_goal(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("Task goal cannot be blank")
		return value


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
