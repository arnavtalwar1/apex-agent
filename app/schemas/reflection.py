from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReflectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    iteration: int
    failed_node: str | None
    error_trace: str | None
    verbal_critique: str | None
    corrected_strategy: str | None
    created_at: datetime