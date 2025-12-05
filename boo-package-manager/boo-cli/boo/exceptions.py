"""Custom exceptions for boo CLI."""

from typing import Optional, Any


class BooError(Exception):
    """Base exception for all boo errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize the error.

        Args:
            message: Error message
            details: Optional additional details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NetworkError(BooError):
    """Network-related errors (connection, timeout, etc.)."""

    pass


class BackendError(BooError):
    """Backend API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize backend error.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Optional additional details
        """
        super().__init__(message, details)
        self.status_code = status_code


class ValidationError(BooError):
    """Validation errors (circular dependencies, invalid input, etc.)."""

    pass


class CircularDependencyError(ValidationError):
    """Circular dependency detected."""

    def __init__(self, message: str, cycle_path: list[str]) -> None:
        """
        Initialize circular dependency error.

        Args:
            message: Error message
            cycle_path: List of resource IDs forming the cycle
        """
        super().__init__(message, {"cycle_path": cycle_path})
        self.cycle_path = cycle_path


class InstallationError(BooError):
    """Installation errors (pip failures, permission errors, etc.)."""

    pass


class UserError(BooError):
    """User input errors (invalid commands, missing arguments, etc.)."""

    pass


class NotFoundError(BooError):
    """Resource not found error."""

    pass
