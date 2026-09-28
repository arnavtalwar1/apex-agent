from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Reflection(Base):
	__tablename__ = "reflections"

	id = Column(Integer, primary_key=True, index=True)
	task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
	iteration = Column(Integer, nullable=False)
	failed_node = Column(String(50))
	error_trace = Column(Text)
	verbal_critique = Column(Text)
	corrected_strategy = Column(Text)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
