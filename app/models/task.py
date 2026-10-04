import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaskStatus(str, enum.Enum):
	PENDING = "pending"
	AWAITING_APPROVAL = "awaiting_approval"
	PLANNING = "planning"
	RESEARCHING = "researching"
	EXECUTING = "executing"
	REFLECTING = "reflecting"
	COMPLETED = "completed"
	FAILED = "failed"
	REJECTED = "rejected"


class Task(Base):
	__tablename__ = "tasks"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	title = Column(String(255))
	goal = Column(Text, nullable=False)
	status = Column(
		Enum(
			TaskStatus,
			name="taskstatus",
			values_callable=lambda x: [e.value for e in x],
		),
		default=TaskStatus.PENDING,
	)
	plan = Column(Text)
	current_node = Column(String(50))
	reflection_count = Column(Integer, default=0)
	final_output = Column(Text)
	requires_approval = Column(Boolean, default=False)
	approval_status = Column(String(50), default="none")
	token_cost = Column(Float, default=0.0)
	trace_id = Column(String(64), nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), onupdate=func.now())

	user = relationship("User", backref="tasks")
	reflections = relationship("Reflection", backref="task", cascade="all, delete-orphan")
