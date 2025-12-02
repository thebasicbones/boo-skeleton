"""Custom exception classes for the application"""
from typing import Dict, Optional, List


class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found"""
    
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource not found: {resource_id}")


class ValidationError(Exception):
    """Exception raised when validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CircularDependencyError(Exception):
    """Exception raised when a circular dependency is detected"""
    
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        cycle_str = " → ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")
