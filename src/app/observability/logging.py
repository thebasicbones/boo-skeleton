"""
Structured logging with trace correlation for CRUD operations.

This module provides the StructuredLogger class that handles structured
logging with JSON formatting and automatic trace context injection. All logs
include trace IDs and span IDs for correlation with distributed traces.

The logger uses python-json-logger for JSON formatting and integrates with
OpenTelemetry to automatically inject trace context into log records.
"""

import logging
from typing import Any

from opentelemetry import trace
from pythonjsonlogger import jsonlogger


class TraceContextFilter(logging.Filter):
    """
    Logging filter that injects OpenTelemetry trace context into log records.

    This filter adds trace_id and span_id fields to every log record,
    enabling correlation between logs and distributed traces in Grafana.

    Attributes:
        None

    Example:
        >>> logger = logging.getLogger(__name__)
        >>> logger.addFilter(TraceContextFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add trace context to log record.

        Args:
            record: Log record to enhance with trace context

        Returns:
            True (always allow the record to be logged)
        """
        # Get current span context
        span = trace.get_current_span()
        span_context = span.get_span_context()

        # Add trace context if available
        if span_context.is_valid:
            record.trace_id = format(span_context.trace_id, '032x')
            record.span_id = format(span_context.span_id, '016x')
        else:
            record.trace_id = None
            record.span_id = None

        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.

    This formatter extends python-json-logger to include additional fields
    and ensure consistent log structure across all log entries.

    Attributes:
        None

    Example:
        >>> formatter = CustomJsonFormatter()
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
    """

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """
        Add custom fields to the log record.

        This method is called by JsonFormatter to add additional fields
        to the JSON log output. It ensures consistent field names and
        includes trace context.

        Args:
            log_record: Dictionary that will be serialized to JSON
            record: Original logging.LogRecord
            message_dict: Dictionary from the log message
        """
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = self.formatTime(record, self.datefmt)

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add trace context if available
        if hasattr(record, 'trace_id') and record.trace_id:
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'span_id') and record.span_id:
            log_record['span_id'] = record.span_id

        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


class StructuredLogger:
    """
    Provides structured logging with trace correlation.

    This class wraps a standard Python logger and provides convenience methods
    for logging CRUD operations with consistent structured fields. All logs
    are formatted as JSON and include trace context for correlation.

    Attributes:
        logger: Underlying Python logger instance
        service_name: Service name to include in logs

    Example:
        >>> logger = StructuredLogger.create(__name__)
        >>> logger.log_operation_start("create", resource_id="res_001")
        >>> # ... perform operation ...
        >>> logger.log_operation_complete("create", duration=0.045, resource_id="res_001")
    """

    def __init__(self, logger: logging.Logger, service_name: str = "fastapi-crud-backend"):
        """
        Initialize structured logger.

        Args:
            logger: Python logger instance to wrap
            service_name: Service name to include in all logs
        """
        self.logger = logger
        self.service_name = service_name

    @classmethod
    def create(
        cls,
        name: str,
        service_name: str = "fastapi-crud-backend",
        level: int = logging.INFO
    ) -> "StructuredLogger":
        """
        Create a new StructuredLogger with JSON formatting and trace context.

        This factory method creates a logger with:
        - JSON formatting via CustomJsonFormatter
        - Trace context injection via TraceContextFilter
        - Appropriate log level

        Args:
            name: Logger name (typically __name__)
            service_name: Service name for log context
            level: Logging level (default: INFO)

        Returns:
            StructuredLogger instance

        Example:
            >>> logger = StructuredLogger.create(__name__)
        """
        # Get or create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Check if handler already exists to avoid duplicates
        if not logger.handlers:
            # Create handler with JSON formatter
            handler = logging.StreamHandler()
            formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # Add trace context filter if not already present
        if not any(isinstance(f, TraceContextFilter) for f in logger.filters):
            logger.addFilter(TraceContextFilter())

        return cls(logger, service_name)

    def _build_context(self, **kwargs: Any) -> dict[str, Any]:
        """
        Build context dictionary with service name and additional fields.

        Args:
            **kwargs: Additional context fields

        Returns:
            Context dictionary with service name and provided fields
        """
        context = {"service.name": self.service_name}
        context.update(kwargs)
        return context

    def log_operation_start(
        self,
        operation: str,
        resource_id: str | None = None,
        **context: Any
    ) -> None:
        """
        Log operation start with trace context.

        This method logs the beginning of a CRUD operation with structured
        fields including operation type, resource ID, and any additional context.

        Args:
            operation: Type of CRUD operation (create, read, update, delete, search)
            resource_id: Optional resource identifier
            **context: Additional context fields (e.g., resource_name, db_type)

        Example:
            >>> logger.log_operation_start(
            ...     "create",
            ...     resource_name="Frontend App",
            ...     db_type="mongodb"
            ... )
        """
        log_context = self._build_context(
            operation_type=operation,
            resource_id=resource_id,
            **context
        )

        message = f"Starting {operation} operation"
        if resource_id:
            message += f" for resource {resource_id}"

        self.logger.info(message, extra=log_context)

    def log_operation_complete(
        self,
        operation: str,
        duration: float,
        resource_id: str | None = None,
        **context: Any
    ) -> None:
        """
        Log operation completion with duration and outcome.

        This method logs the successful completion of a CRUD operation,
        including the operation duration in milliseconds.

        Args:
            operation: Type of CRUD operation (create, read, update, delete, search)
            duration: Operation duration in seconds
            resource_id: Optional resource identifier
            **context: Additional context fields (e.g., status, db_type)

        Example:
            >>> start_time = time.time()
            >>> # ... perform operation ...
            >>> logger.log_operation_complete(
            ...     "create",
            ...     duration=time.time() - start_time,
            ...     resource_id="res_001",
            ...     status="success"
            ... )
        """
        duration_ms = duration * 1000

        log_context = self._build_context(
            operation_type=operation,
            resource_id=resource_id,
            duration_ms=round(duration_ms, 2),
            status=context.get("status", "success"),
            **context
        )

        message = f"Completed {operation} operation in {duration_ms:.2f}ms"
        if resource_id:
            message += f" for resource {resource_id}"

        self.logger.info(message, extra=log_context)

    def log_error(
        self,
        operation: str,
        error: Exception,
        resource_id: str | None = None,
        **context: Any
    ) -> None:
        """
        Log error with full context and exception details.

        This method logs operation failures with complete exception information
        including stack traces for debugging. The error type is automatically
        extracted from the exception.

        Args:
            operation: Type of CRUD operation (create, read, update, delete, search)
            error: Exception that occurred
            resource_id: Optional resource identifier
            **context: Additional context fields (e.g., db_type)

        Example:
            >>> try:
            ...     # ... perform operation ...
            ... except Exception as e:
            ...     logger.log_error("create", e, resource_id="res_001", db_type="mongodb")
            ...     raise
        """
        error_type = type(error).__name__

        log_context = self._build_context(
            operation_type=operation,
            resource_id=resource_id,
            error_type=error_type,
            error_message=str(error),
            status="error",
            **context
        )

        message = f"Error in {operation} operation: {error_type}"
        if resource_id:
            message += f" for resource {resource_id}"

        self.logger.error(message, extra=log_context, exc_info=True)

    def log_validation_error(
        self,
        operation: str,
        field: str,
        error_message: str,
        **context: Any
    ) -> None:
        """
        Log validation error with field details.

        This method logs validation failures with information about which
        field failed validation and why.

        Args:
            operation: Type of CRUD operation
            field: Field that failed validation
            error_message: Validation error message
            **context: Additional context fields

        Example:
            >>> logger.log_validation_error(
            ...     "create",
            ...     field="name",
            ...     error_message="Name cannot be empty",
            ...     resource_id="temp_id"
            ... )
        """
        log_context = self._build_context(
            operation_type=operation,
            error_type="validation",
            validation_field=field,
            error_message=error_message,
            status="error",
            **context
        )

        message = f"Validation error in {operation} operation: {field} - {error_message}"

        self.logger.warning(message, extra=log_context)

    def log_circular_dependency(
        self,
        operation: str,
        resource_id: str,
        cycle: list[str],
        **context: Any
    ) -> None:
        """
        Log circular dependency detection.

        This method logs when a circular dependency is detected, including
        the full cycle path for debugging.

        Args:
            operation: Type of CRUD operation
            resource_id: Resource that would create the cycle
            cycle: List of resource IDs forming the cycle
            **context: Additional context fields

        Example:
            >>> logger.log_circular_dependency(
            ...     "create",
            ...     resource_id="res_003",
            ...     cycle=["res_001", "res_002", "res_003", "res_001"]
            ... )
        """
        log_context = self._build_context(
            operation_type=operation,
            resource_id=resource_id,
            error_type="circular_dependency",
            cycle_path=" -> ".join(cycle),
            cycle_length=len(cycle),
            status="error",
            **context
        )

        message = f"Circular dependency detected in {operation} operation: {' -> '.join(cycle)}"

        self.logger.error(message, extra=log_context)

    def log_cascade_delete(
        self,
        resource_id: str,
        deleted_count: int,
        deleted_ids: list[str] | None = None,
        **context: Any
    ) -> None:
        """
        Log cascade delete operation.

        This method logs when a cascade delete removes multiple resources,
        including the count and optionally the IDs of deleted resources.

        Args:
            resource_id: Primary resource being deleted
            deleted_count: Number of resources deleted in cascade
            deleted_ids: Optional list of deleted resource IDs
            **context: Additional context fields

        Example:
            >>> logger.log_cascade_delete(
            ...     resource_id="res_001",
            ...     deleted_count=5,
            ...     deleted_ids=["res_002", "res_003", "res_004", "res_005", "res_006"]
            ... )
        """
        log_context = self._build_context(
            operation_type="delete",
            resource_id=resource_id,
            cascade_delete_count=deleted_count,
            **context
        )

        if deleted_ids:
            log_context["deleted_resource_ids"] = deleted_ids

        message = f"Cascade delete removed {deleted_count} resources for resource {resource_id}"

        self.logger.info(message, extra=log_context)

    def log_search(
        self,
        query: str | None,
        result_count: int,
        duration: float,
        **context: Any
    ) -> None:
        """
        Log search operation with query and results.

        This method logs search operations including the query string,
        number of results, and search duration.

        Args:
            query: Search query string (None for list all)
            result_count: Number of results returned
            duration: Search duration in seconds
            **context: Additional context fields

        Example:
            >>> start_time = time.time()
            >>> # ... perform search ...
            >>> logger.log_search(
            ...     query="frontend",
            ...     result_count=3,
            ...     duration=time.time() - start_time
            ... )
        """
        duration_ms = duration * 1000

        log_context = self._build_context(
            operation_type="search",
            search_query=query,
            result_count=result_count,
            duration_ms=round(duration_ms, 2),
            has_query=query is not None,
            **context
        )

        if query:
            message = f"Search for '{query}' returned {result_count} results in {duration_ms:.2f}ms"
        else:
            message = f"List all returned {result_count} resources in {duration_ms:.2f}ms"

        self.logger.info(message, extra=log_context)

    def debug(self, message: str, **context: Any) -> None:
        """
        Log debug message with context.

        Args:
            message: Debug message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self.logger.debug(message, extra=log_context)

    def info(self, message: str, **context: Any) -> None:
        """
        Log info message with context.

        Args:
            message: Info message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self.logger.info(message, extra=log_context)

    def warning(self, message: str, **context: Any) -> None:
        """
        Log warning message with context.

        Args:
            message: Warning message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self.logger.warning(message, extra=log_context)

    def error(self, message: str, exc_info: bool = False, **context: Any) -> None:
        """
        Log error message with context.

        Args:
            message: Error message
            exc_info: Include exception info if True
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self.logger.error(message, extra=log_context, exc_info=exc_info)


def get_logger(name: str, service_name: str = "fastapi-crud-backend") -> StructuredLogger:
    """
    Get a structured logger instance.

    This is a convenience function for creating StructuredLogger instances
    with consistent configuration.

    Args:
        name: Logger name (typically __name__)
        service_name: Service name for log context

    Returns:
        StructuredLogger instance

    Example:
        >>> from app.observability.logging import get_logger
        >>> logger = get_logger(__name__)
    """
    return StructuredLogger.create(name, service_name)


__all__ = [
    "StructuredLogger",
    "TraceContextFilter",
    "CustomJsonFormatter",
    "get_logger",
]
