"""
Test suite for structured LLM outputs, model routing, and token budget limits.
"""

import pytest
from app.core.cost_manager import (
    ModelTier,
    TaskCostTracker,
    estimate_token_cost,
    route_model,
)
from app.core.errors import BudgetExceededError
from app.core.structured_llm import (
    SupervisorDecision,
    parse_reflection_output,
    parse_supervisor_decision,
)


def test_parse_supervisor_decision_json():
    json_str = '{"next_agent": "EXECUTOR", "reasoning": "Plan verified with safe code."}'
    decision = parse_supervisor_decision(json_str)
    assert decision.next_agent == "EXECUTOR"
    assert "Plan verified" in decision.reasoning


def test_parse_supervisor_decision_plain_text():
    raw_text = "  **RESEARCHER**.  "
    decision = parse_supervisor_decision(raw_text)
    assert decision.next_agent == "RESEARCHER"


def test_parse_reflection_output_critique_and_plan():
    text = (
        "CRITIQUE: Missing bounds check on input list.\n"
        "CORRECTED_PLAN:\n```python\nif len(items) > 0:\n    print(items[0])\n```"
    )
    result = parse_reflection_output(text)
    assert "Missing bounds check" in result.critique
    assert "len(items) > 0" in result.corrected_plan
    assert result.should_retry is True


def test_estimate_token_cost():
    cost = estimate_token_cost(prompt_tokens=1000, completion_tokens=500, model_name="gpt-4o-mini")
    assert cost > 0
    assert cost == pytest.approx(0.00015 + (0.5 * 0.00060), rel=1e-3)


def test_task_cost_tracker_enforces_budget():
    tracker = TaskCostTracker(task_id=1, max_budget_usd=0.01)

    # Step within budget
    tracker.record_step(prompt_tokens=1000, completion_tokens=500, model_name="gpt-4o-mini")
    assert tracker.cumulative_cost_usd > 0

    # Step exceeding budget
    with pytest.raises(BudgetExceededError) as exc_info:
        tracker.record_step(prompt_tokens=100000, completion_tokens=50000, model_name="gpt-4o")

    assert "exceeded configured budget" in str(exc_info.value)


def test_model_routing():
    assert route_model(ModelTier.FAST_CHEAP) == "gpt-4o-mini"
