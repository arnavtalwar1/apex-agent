"""
Structured LLM outputs and schema-driven response parsing.
Guarantees validated Pydantic representations across agent decision cycles.
"""

import json
import re
from typing import Any, Literal, Optional, Type, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T", bound=BaseModel)


class SupervisorDecision(BaseModel):
    """Structured decision output from the supervisor node."""

    next_agent: Literal["PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"]
    reasoning: str = Field(default="", description="Reason for selecting the next agent")


class PlanOutput(BaseModel):
    """Structured plan decomposition from the planner node."""

    steps: list[str] = Field(default_factory=list, description="Ordered actionable execution steps")
    code_snippet: Optional[str] = Field(default=None, description="Executable Python code block if required")
    tools_needed: list[str] = Field(default_factory=list, description="Tools needed for this plan")


class ReflectionOutput(BaseModel):
    """Structured critique and self-correction from the reflector node."""

    critique: str = Field(..., description="Root cause diagnosis of prior failure or edge cases")
    root_cause: str = Field(default="", description="Category of error: e.g. syntax, network, logic")
    corrected_plan: str = Field(default="", description="Self-healed executable plan")
    should_retry: bool = Field(default=True, description="Whether to retry execution")


def parse_supervisor_decision(
    content: Any,
    default_fallback: Literal["PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"] = "PLANNER",
) -> SupervisorDecision:
    """
    Parses supervisor LLM content into a validated SupervisorDecision.
    Handles JSON blocks, Pydantic objects, and plain uppercase text fallbacks.
    """
    if isinstance(content, SupervisorDecision):
        return content

    if isinstance(content, dict):
        agent = content.get("next_agent", "").upper()
        if agent in {"PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"}:
            return SupervisorDecision(next_agent=agent, reasoning=content.get("reasoning", ""))

    text = str(content.content if hasattr(content, "content") else content).strip()

    # Try JSON extraction
    json_match = re.search(r"\{.*?\}", text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            agent = parsed.get("next_agent", "").upper()
            if agent in {"PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"}:
                return SupervisorDecision(next_agent=agent, reasoning=parsed.get("reasoning", ""))
        except Exception:
            pass

    # Fallback to word scan
    cleaned = text.upper().replace("*", "").replace(".", "")
    valid = {"PLANNER", "RESEARCHER", "EXECUTOR", "REFLECTOR", "FINISH"}
    words = [w for w in cleaned.split() if w in valid]
    if words:
        return SupervisorDecision(next_agent=words[0], reasoning=text)

    return SupervisorDecision(next_agent=default_fallback, reasoning="Default fallback")


def parse_reflection_output(content: Any) -> ReflectionOutput:
    """
    Parses reflection LLM output into a validated ReflectionOutput model.
    Supports both structured format and legacy CRITIQUE / CORRECTED_PLAN markers.
    """
    if isinstance(content, ReflectionOutput):
        return content

    text = str(content.content if hasattr(content, "content") else content).strip()

    critique = text
    corrected_plan = ""
    root_cause = ""

    if "CORRECTED_PLAN:" in text:
        parts = text.split("CORRECTED_PLAN:", 1)
        critique_part = parts[0]
        corrected_plan = parts[1].strip()
        if "CRITIQUE:" in critique_part:
            critique = critique_part.split("CRITIQUE:", 1)[1].strip()
        else:
            critique = critique_part.strip()
    elif "CRITIQUE:" in text:
        critique = text.split("CRITIQUE:", 1)[1].strip()

    return ReflectionOutput(
        critique=critique or "Analysis complete.",
        root_cause=root_cause,
        corrected_plan=corrected_plan,
        should_retry=bool(corrected_plan),
    )
