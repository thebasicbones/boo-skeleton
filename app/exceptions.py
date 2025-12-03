"""Custom exception classes for the application"""


class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found"""

    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource not found: {resource_id}")


class ValidationError(Exception):
    """Exception raised when validation fails"""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CircularDependencyError(Exception):
    """Exception raised when a circular dependency is detected"""

    def __init__(self, cycle_path: list[str]):
        self.cycle_path = cycle_path
        cycle_str = " → ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class DatabaseError(Exception):
    """Base exception for database errors"""

    pass


class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class DatabaseTimeoutError(DatabaseError):
    """Database operation timed out"""

    def __init__(self, message: str, operation: str | None = None):
        self.message = message
        self.operation = operation
        super().__init__(message)


class DuplicateResourceError(DatabaseError):
    """Resource with same identifier already exists"""

    def __init__(self, resource_id: str, details: str | None = None):
        self.resource_id = resource_id
        self.details = details
        super().__init__(f"Resource with id {resource_id} already exists")
