"""
Observability, contextual tracing, latency tracking, and structured diagnostics.
"""

import contextvars
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


logger = logging.getLogger("apex.observability")
logger.setLevel(logging.INFO)

# ContextVar to propagate trace ID across async execution chains
current_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_trace_id", default="")


@dataclass
class NodeMetrics:
    node_name: str
    duration_seconds: float
    success: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowTrace:
    trace_id: str
    task_id: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    node_metrics: list[NodeMetrics] = field(default_factory=list)
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def total_duration_seconds(self) -> float:
        end = self.end_time or time.time()
        return round(end - self.start_time, 4)

    def record_node(
        self,
        name: str,
        duration: float = 0.0,
        duration_seconds: Optional[float] = None,
        success: bool = True,
        **details,
    ):
        dur = duration_seconds if duration_seconds is not None else duration
        self.node_metrics.append(
            NodeMetrics(
                node_name=name,
                duration_seconds=round(dur, 4),
                success=success,
                details=details,
            )
        )
        logger.info(
            "Node execution completed: trace_id=%s task_id=%s node=%s duration=%.3fs success=%s",
            self.trace_id,
            self.task_id,
            name,
            duration,
            success,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "total_duration_seconds": self.total_duration_seconds,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "node_count": len(self.node_metrics),
            "nodes": [
                {
                    "node": m.node_name,
                    "duration_seconds": m.duration_seconds,
                    "success": m.success,
                    "details": m.details,
                }
                for m in self.node_metrics
            ],
        }


# Global in-memory trace registry (retained for active session inspection)
ACTIVE_TRACES: dict[str, WorkflowTrace] = {}


def start_trace(task_id: Optional[int] = None, custom_trace_id: Optional[str] = None) -> WorkflowTrace:
    """Initializes and registers a new execution trace."""
    trace_id = custom_trace_id or str(uuid.uuid4())
    trace = WorkflowTrace(trace_id=trace_id, task_id=task_id)
    ACTIVE_TRACES[trace_id] = trace
    current_trace_id.set(trace_id)
    return trace


def get_current_trace() -> Optional[WorkflowTrace]:
    """Retrieves the active trace for the current async execution context."""
    trace_id = current_trace_id.get()
    return ACTIVE_TRACES.get(trace_id)


def finish_trace(trace_id: str) -> Optional[WorkflowTrace]:
    """Marks a trace as complete and returns its summary metrics."""
    trace = ACTIVE_TRACES.get(trace_id)
    if trace:
        trace.end_time = time.time()
    return trace
