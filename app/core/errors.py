"""
Typed domain exceptions and error handling for the APEX Agent platform.
Provides structured, secure, and RFC 7807-compatible error abstractions.
"""

from typing import Any, Optional


class ApexException(Exception):
    """Base exception for all APEX domain errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "APEX_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class SecurityViolationError(ApexException):
    """Raised when code execution violates security sandbox policies."""

    def __init__(self, message: str, violations: Optional[list[str]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="SECURITY_VIOLATION",
            details={"violations": violations or []},
        )


class ApprovalRequiredError(ApexException):
    """Raised when an action requires human approval before proceeding."""

    def __init__(self, message: str, action: str, task_id: int):
        super().__init__(
            message=message,
            status_code=428,  # Precondition Required
            error_code="APPROVAL_REQUIRED",
            details={"action": action, "task_id": task_id},
        )


class TokenRevokedError(ApexException):
    """Raised when a revoked or blacklisted JWT token is presented."""

    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="TOKEN_REVOKED",
        )


class InvalidTokenError(ApexException):
    """Raised when a token has invalid claims, type or signature."""

    def __init__(self, message: str = "Invalid authentication token"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="INVALID_TOKEN",
        )


class BudgetExceededError(ApexException):
    """Raised when LLM token or dollar cost exceeds the configured task budget."""

    def __init__(self, message: str, current_cost: float, max_budget: float):
        super().__init__(
            message=message,
            status_code=429,  # Too Many Requests / Resource Exhausted
            error_code="BUDGET_EXCEEDED",
            details={"current_cost_usd": current_cost, "max_budget_usd": max_budget},
        )


class ResourceNotFoundError(ApexException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
        )
