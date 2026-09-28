import enum

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaskStatus(str, enum.Enum):
	PENDING = "pending"
	PLANNING = "planning"
	RESEARCHING = "researching"
	EXECUTING = "executing"
	REFLECTING = "reflecting"
	COMPLETED = "completed"
	FAILED = "failed"


class Task(Base):
	__tablename__ = "tasks"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	title = Column(String(255))
	goal = Column(Text, nullable=False)
	status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
	plan = Column(Text)
	current_node = Column(String(50))
	reflection_count = Column(Integer, default=0)
	final_output = Column(Text)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), onupdate=func.now())

	user = relationship("User", backref="tasks")
	reflections = relationship("Reflection", backref="task", cascade="all, delete-orphan", passive_deletes=True)
