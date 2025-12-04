"""
Metrics instrumentation for CRUD operations.

This module provides the MetricsInstrumentor class that handles all metrics
collection for CRUD operations, including:
- Operation duration histograms
- Success/failure counters
- Resource count tracking
- Cascade delete metrics

All metrics follow OpenTelemetry conventions and include contextual attributes
for filtering and analysis in Grafana.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any

from opentelemetry.metrics import Histogram, Counter, UpDownCounter, Meter

logger = logging.getLogger(__name__)


@contextmanager
def observability_error_handler(operation: str, **context: Any):
    """
    Context manager for handling observability errors gracefully.
    
    This ensures that errors in observability instrumentation don't
    break the main application flow.
    
    Args:
        operation: Name of the operation being instrumented
        **context: Additional context for error logging
        
    Yields:
        None
    """
    try:
        yield
    except Exception as e:
        logger.error(
            f"Observability error in {operation}: {e}",
            extra=context,
            exc_info=True
        )
        # Don't re-raise - allow application to continue


class MetricsInstrumentor:
    """
    Handles metrics collection for CRUD operations.
    
    This class provides a centralized interface for recording all metrics
    related to CRUD operations. It creates and manages OpenTelemetry metric
    instruments and provides methods for recording operation metrics with
    appropriate attributes.
    
    Attributes:
        operation_duration: Histogram for operation duration in milliseconds
        operation_count: Counter for total CRUD operations
        operation_errors: Counter for failed operations
        resources_total: UpDownCounter for current resource count
        cascade_delete_count: Histogram for cascade delete counts
    
    Example:
        >>> meter = get_meter(__name__)
        >>> instrumentor = MetricsInstrumentor(meter)
        >>> start_time = instrumentor.record_operation_start("create", "mongodb")
        >>> # ... perform operation ...
        >>> instrumentor.record_operation_complete("create", "mongodb", time.time() - start_time, "success")
    """
    
    def __init__(self, meter: Meter):
        """
        Initialize metrics instrumentor with OpenTelemetry meter.
        
        Args:
            meter: OpenTelemetry meter for creating metric instruments
        """
        self.meter = meter
        
        # Initialize metric instruments
        with observability_error_handler("initialize_metrics"):
            self._initialize_instruments()
    
    def _initialize_instruments(self) -> None:
        """
        Create all metric instruments.
        
        This method creates the following instruments:
        - operation_duration: Histogram for operation timing
        - operation_count: Counter for operation counts
        - operation_errors: Counter for error tracking
        - resources_total: UpDownCounter for resource counts
        - cascade_delete_count: Histogram for cascade delete metrics
        """
        # Operation duration histogram (in milliseconds)
        self.operation_duration: Histogram = self.meter.create_histogram(
            name="crud.operation.duration",
            description="Time taken for CRUD operations",
            unit="ms"
        )
        
        # Operation count counter
        self.operation_count: Counter = self.meter.create_counter(
            name="crud.operation.count",
            description="Total number of CRUD operations",
            unit="1"
        )
        
        # Operation errors counter
        self.operation_errors: Counter = self.meter.create_counter(
            name="crud.operation.errors",
            description="Number of failed CRUD operations",
            unit="1"
        )
        
        # Resource total up-down counter
        self.resources_total: UpDownCounter = self.meter.create_up_down_counter(
            name="crud.resources.total",
            description="Current total number of resources",
            unit="1"
        )
        
        # Cascade delete count histogram
        self.cascade_delete_count: Histogram = self.meter.create_histogram(
            name="crud.cascade.delete.count",
            description="Number of resources deleted in cascade operations",
            unit="1"
        )
        
        logger.info("Metrics instruments initialized successfully")
    
    def record_operation_start(self, operation: str, db_type: str) -> float:
        """
        Record operation start time.
        
        This is a convenience method that returns the current timestamp
        for use in calculating operation duration.
        
        Args:
            operation: Type of CRUD operation (create, read, update, delete, search)
            db_type: Database backend type (sqlite, mongodb)
            
        Returns:
            Current timestamp in seconds (from time.time())
            
        Example:
            >>> start_time = instrumentor.record_operation_start("create", "mongodb")
        """
        return time.time()
    
    def record_operation_complete(
        self,
        operation: str,
        db_type: str,
        duration: float,
        status: str = "success",
        **additional_attributes: Any
    ) -> None:
        """
        Record successful operation completion.
        
        This method records both the operation duration histogram and
        increments the operation count counter with success status.
        
        Args:
            operation: Type of CRUD operation (create, read, update, delete, search)
            db_type: Database backend type (sqlite, mongodb)
            duration: Operation duration in seconds
            status: Operation status (success, error)
            **additional_attributes: Additional metric attributes (e.g., http_status_code)
            
        Example:
            >>> start_time = time.time()
            >>> # ... perform operation ...
            >>> instrumentor.record_operation_complete(
            ...     "create", "mongodb", time.time() - start_time, "success",
            ...     http_status_code=201
            ... )
        """
        with observability_error_handler("record_operation_complete", operation_type=operation):
            # Convert duration to milliseconds
            duration_ms = duration * 1000
            
            # Build attributes dictionary
            attributes = {
                "operation.type": operation,
                "db.type": db_type,
                "status": status,
            }
            attributes.update(additional_attributes)
            
            # Record duration histogram
            self.operation_duration.record(duration_ms, attributes)
            
            # Increment operation counter
            self.operation_count.add(1, attributes)
            
            logger.debug(
                f"Recorded {status} {operation} operation: {duration_ms:.2f}ms",
                extra={"operation": operation, "db_type": db_type, "duration_ms": duration_ms}
            )
    
    def record_operation_error(
        self,
        operation: str,
        db_type: str,
        error_type: str,
        duration: float | None = None,
        **additional_attributes: Any
    ) -> None:
        """
        Record operation failure.
        
        This method increments the error counter with error type information
        and optionally records the operation duration if provided.
        
        Args:
            operation: Type of CRUD operation (create, read, update, delete, search)
            db_type: Database backend type (sqlite, mongodb)
            error_type: Type of error (validation, not_found, circular_dependency, database)
            duration: Optional operation duration in seconds
            **additional_attributes: Additional metric attributes
            
        Example:
            >>> instrumentor.record_operation_error(
            ...     "create", "mongodb", "validation",
            ...     http_status_code=422
            ... )
        """
        with observability_error_handler("record_operation_error", operation_type=operation):
            # Build attributes dictionary
            attributes = {
                "operation.type": operation,
                "db.type": db_type,
                "error.type": error_type,
                "status": "error",
            }
            attributes.update(additional_attributes)
            
            # Increment error counter
            self.operation_errors.add(1, attributes)
            
            # Also increment operation counter with error status
            self.operation_count.add(1, attributes)
            
            # Record duration if provided
            if duration is not None:
                duration_ms = duration * 1000
                self.operation_duration.record(duration_ms, attributes)
            
            logger.debug(
                f"Recorded error for {operation} operation: {error_type}",
                extra={"operation": operation, "db_type": db_type, "error_type": error_type}
            )
    
    def increment_resource_count(self, db_type: str, delta: int = 1) -> None:
        """
        Update resource count.
        
        This method increments or decrements the total resource count.
        Use positive delta for resource creation, negative for deletion.
        
        Args:
            db_type: Database backend type (sqlite, mongodb)
            delta: Change in resource count (positive for create, negative for delete)
            
        Example:
            >>> # After creating a resource
            >>> instrumentor.increment_resource_count("mongodb", delta=1)
            >>> # After deleting a resource
            >>> instrumentor.increment_resource_count("mongodb", delta=-1)
        """
        with observability_error_handler("increment_resource_count", db_type=db_type):
            attributes = {"db.type": db_type}
            self.resources_total.add(delta, attributes)
            
            logger.debug(
                f"Resource count changed by {delta}",
                extra={"db_type": db_type, "delta": delta}
            )
    
    def record_cascade_delete(self, count: int, db_type: str) -> None:
        """
        Record cascade delete operation.
        
        This method records the number of resources deleted in a cascade
        delete operation using a histogram metric.
        
        Args:
            count: Number of resources deleted in cascade
            db_type: Database backend type (sqlite, mongodb)
            
        Example:
            >>> # After cascade delete that removed 5 resources
            >>> instrumentor.record_cascade_delete(5, "mongodb")
        """
        with observability_error_handler("record_cascade_delete", count=count):
            attributes = {"db.type": db_type}
            self.cascade_delete_count.record(count, attributes)
            
            logger.debug(
                f"Recorded cascade delete of {count} resources",
                extra={"db_type": db_type, "count": count}
            )


def create_metrics_instrumentor(meter: Meter) -> MetricsInstrumentor:
    """
    Factory function to create a MetricsInstrumentor instance.
    
    This function provides a convenient way to create a metrics instrumentor
    with proper error handling.
    
    Args:
        meter: OpenTelemetry meter for creating metric instruments
        
    Returns:
        MetricsInstrumentor instance
        
    Example:
        >>> from app.observability import get_meter
        >>> meter = get_meter(__name__)
        >>> instrumentor = create_metrics_instrumentor(meter)
    """
    try:
        return MetricsInstrumentor(meter)
    except Exception as e:
        logger.error(f"Failed to create metrics instrumentor: {e}", exc_info=True)
        raise


__all__ = [
    "MetricsInstrumentor",
    "create_metrics_instrumentor",
]
