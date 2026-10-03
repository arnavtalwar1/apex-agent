"""
Model routing, token cost estimation, and task budget enforcement.
Prevents runaway model spend through granular token tracking.
"""

import enum
from typing import Optional
from app.core.config import settings
from app.core.errors import BudgetExceededError


class ModelTier(str, enum.Enum):
    FAST_CHEAP = "fast_cheap"     # Lightweight, high-throughput (supervisor, search query)
    BALANCED = "balanced"         # General-purpose (planner, executor synthesizer)
    REASONING = "reasoning"       # Deep reasoning (reflector, complex debugging)


# Estimated USD cost per 1,000 tokens (input, output)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.00015, 0.00060),
    "gpt-4o": (0.00250, 0.01000),
    "openai/gpt-oss-120b": (0.00020, 0.00080),
    "openai/gpt-oss-20b": (0.00008, 0.00030),
    "llama-3.3-70b-versatile": (0.00059, 0.00079),
    "qwen/qwen3.8-27b": (0.00010, 0.00040),
}
DEFAULT_PRICING = (0.00020, 0.00080)


def estimate_token_cost(prompt_tokens: int, completion_tokens: int, model_name: str) -> float:
    """Calculates USD cost estimate for prompt and completion token counts."""
    pricing = MODEL_PRICING.get(model_name.lower(), DEFAULT_PRICING)
    input_cost = (prompt_tokens / 1000.0) * pricing[0]
    output_cost = (completion_tokens / 1000.0) * pricing[1]
    return round(input_cost + output_cost, 6)


def route_model(tier: ModelTier = ModelTier.BALANCED) -> str:
    """
    Selects optimal model tier based on task criticality and latency budget.
    """
    if tier == ModelTier.FAST_CHEAP:
        return "gpt-4o-mini"
    elif tier == ModelTier.REASONING:
        # Use primary model or high-capability fallback
        return settings.MODEL_NAME or "gpt-4o-mini"
    return settings.MODEL_NAME or "gpt-4o-mini"


class TaskCostTracker:
    """
    Monitors and caps token consumption and dollar spend for a given task execution.
    """

    def __init__(self, task_id: Optional[int] = None, max_budget_usd: Optional[float] = None):
        self.task_id = task_id
        self.max_budget_usd = max_budget_usd or settings.MAX_COST_PER_TASK_USD
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.cumulative_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    def record_step(self, prompt_tokens: int, completion_tokens: int, model_name: str) -> float:
        """Records token usage and increments dollar cost."""
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        step_cost = estimate_token_cost(prompt_tokens, completion_tokens, model_name)
        self.cumulative_cost_usd = round(self.cumulative_cost_usd + step_cost, 6)
        self.verify_budget()
        return step_cost

    def verify_budget(self) -> None:
        """Raises BudgetExceededError if cumulative spend exceeds policy limit."""
        if self.max_budget_usd and self.cumulative_cost_usd > self.max_budget_usd:
            raise BudgetExceededError(
                message=f"Task spend (${self.cumulative_cost_usd:.4f}) exceeded configured budget limit (${self.max_budget_usd:.4f}).",
                current_cost=self.cumulative_cost_usd,
                max_budget=self.max_budget_usd,
            )
