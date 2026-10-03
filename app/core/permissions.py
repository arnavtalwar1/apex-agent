"""
Tool permission scopes, sensitivity matrices, and Human-in-the-Loop (HITL) policies.
"""

import enum
from typing import NamedTuple, Optional


class PermissionScope(str, enum.Enum):
    READ = "read"
    SEARCH = "search"
    WRITE = "write"
    CODE_EXECUTION = "code_execution"
    DESTRUCTIVE = "destructive"
    ADMIN = "admin"


class ToolDefinition(NamedTuple):
    name: str
    required_scope: PermissionScope
    requires_human_approval: bool
    description: str


# Permissions registry for all agent tools and execution actions
TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "web_search": ToolDefinition(
        name="web_search",
        required_scope=PermissionScope.SEARCH,
        requires_human_approval=False,
        description="Search Tavily or DuckDuckGo for public web intelligence",
    ),
    "python_sandbox": ToolDefinition(
        name="python_sandbox",
        required_scope=PermissionScope.CODE_EXECUTION,
        requires_human_approval=False,  # Can be elevated dynamically by task policy
        description="Execute verified Python code in the isolated AST sandbox",
    ),
    "file_system_write": ToolDefinition(
        name="file_system_write",
        required_scope=PermissionScope.WRITE,
        requires_human_approval=True,
        description="Write persistent files to the host project directory",
    ),
    "destructive_operation": ToolDefinition(
        name="destructive_operation",
        required_scope=PermissionScope.DESTRUCTIVE,
        requires_human_approval=True,
        description="Delete or overwrite production resources or databases",
    ),
}


def evaluate_action_permission(
    action_name: str,
    task_requires_approval: bool = False,
    global_approval_required: bool = False,
) -> tuple[bool, Optional[str]]:
    """
    Evaluates whether an action requires human approval before proceeding.
    Returns (needs_approval, reason).
    """
    tool_def = TOOL_REGISTRY.get(action_name)
    if not tool_def:
        # Default policy for untracked actions: if task or global requires approval, prompt
        if task_requires_approval or global_approval_required:
            return True, f"Action '{action_name}' requires explicit human authorization."
        return False, None

    if tool_def.requires_human_approval:
        return True, f"Tool '{tool_def.name}' requires human approval ({tool_def.required_scope.value})."

    if (task_requires_approval or global_approval_required) and tool_def.required_scope == PermissionScope.CODE_EXECUTION:
        return True, "Code execution requires human sign-off under active policy."

    return False, None
