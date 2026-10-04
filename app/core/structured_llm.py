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
    Supports structured JSON, flexible markdown headers (bold/headings/case-insensitive),
    and code block fallback extraction.
    """
    if isinstance(content, ReflectionOutput):
        return content

    if isinstance(content, dict):
        critique = content.get("critique") or content.get("root_cause") or "Analysis complete."
        plan = content.get("corrected_plan") or content.get("corrected_strategy") or content.get("plan") or ""
        return ReflectionOutput(
            critique=critique,
            root_cause=content.get("root_cause", ""),
            corrected_plan=plan,
            should_retry=bool(plan),
        )

    text = str(content.content if hasattr(content, "content") else content).strip()

    # 1. Try JSON extraction
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            if isinstance(data, dict) and ("critique" in data or "corrected_plan" in data or "corrected_strategy" in data):
                critique = data.get("critique") or data.get("root_cause") or "Analysis complete."
                plan = data.get("corrected_plan") or data.get("corrected_strategy") or data.get("plan") or ""
                return ReflectionOutput(
                    critique=critique,
                    root_cause=data.get("root_cause", ""),
                    corrected_plan=plan,
                    should_retry=bool(plan),
                )
        except Exception:
            pass

    # 2. Flexible header splitting with regex (case-insensitive, handles **, ##, spaces, underscores, colons)
    plan_header_pattern = r"(?i)(?:^|\n)[ \t]*(?:\*{0,2}#{0,4}[ \t]*)?(?:CORRECTED[_\s]+PLAN|CORRECTED[_\s]+STRATEGY|UPDATED[_\s]+PLAN|CORRECTED[_\s]+CODE)\s*[:#-]*[ \t]*(?:\*{0,2})"
    critique_header_pattern = r"(?i)(?:^|\n)[ \t]*(?:\*{0,2}#{0,4}[ \t]*)?CRITIQUE\s*[:#-]*[ \t]*(?:\*{0,2})"

    critique = text
    corrected_plan = ""
    root_cause = ""

    plan_match = re.search(plan_header_pattern, text)
    if plan_match:
        critique_part = text[:plan_match.start()].strip()
        corrected_plan = text[plan_match.end():].strip()
        critique_m = re.search(critique_header_pattern, critique_part)
        if critique_m:
            critique = critique_part[critique_m.end():].strip()
        else:
            critique = critique_part.strip()
    else:
        critique_m = re.search(critique_header_pattern, text)
        if critique_m:
            critique = text[critique_m.end():].strip()

    # 3. Fallback: if no separate plan header was found, but a Python code block exists, use it
    if not corrected_plan:
        py_match = re.search(r"```(?:python|py)\b[^\r\n]*[\r\n]+(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if py_match:
            corrected_plan = text

    return ReflectionOutput(
        critique=critique or "Analysis complete.",
        root_cause=root_cause,
        corrected_plan=corrected_plan,
        should_retry=bool(corrected_plan),
    )
