"""
OpenTelemetry observability module for FastAPI CRUD backend.

This module provides comprehensive observability through:
- Metrics: Track operation performance, error rates, and resource counts
- Traces: Distributed tracing for request flow analysis
- Logs: Structured logging with trace correlation

The module initializes OpenTelemetry providers and exporters during
application startup and provides instrumentation utilities for the
service layer.
"""

import logging
from contextlib import contextmanager
from typing import Any

from opentelemetry import metrics as otel_metrics, trace as otel_trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import ObservabilitySettings
from .metrics import MetricsInstrumentor, create_metrics_instrumentor

logger = logging.getLogger(__name__)

# Global state for observability components
_meter_provider: MeterProvider | None = None
_tracer_provider: TracerProvider | None = None
_initialized: bool = False


def init_observability(settings: ObservabilitySettings) -> None:
    """
    Initialize OpenTelemetry providers and exporters.
    
    This function sets up:
    1. Resource attributes (service name, version, environment)
    2. Metrics provider with OTLP exporter
    3. Trace provider with OTLP exporter
    4. Automatic instrumentation for FastAPI
    
    Args:
        settings: Observability configuration settings
        
    Raises:
        Exception: If initialization fails (logged but not raised to allow graceful degradation)
    """
    global _meter_provider, _tracer_provider, _initialized
    
    if not settings.otel_enabled:
        logger.info("OpenTelemetry observability is disabled")
        return
    
    if _initialized:
        logger.warning("OpenTelemetry already initialized, skipping")
        return
    
    try:
        logger.info("Initializing OpenTelemetry observability...")
        
        # Create resource with service information
        resource = Resource.create({
            "service.name": settings.service_name,
            "service.version": settings.service_version,
            "deployment.environment": settings.deployment_environment,
        })
        
        # Initialize metrics provider
        _initialize_metrics(settings, resource)
        
        # Initialize trace provider
        _initialize_tracing(settings, resource)
        
        _initialized = True
        logger.info(
            f"OpenTelemetry initialized successfully for service '{settings.service_name}' "
            f"(version {settings.service_version}, environment {settings.deployment_environment})"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        # Don't raise - allow application to continue with degraded observability


def _initialize_metrics(settings: ObservabilitySettings, resource: Resource) -> None:
    """
    Initialize metrics provider with OTLP exporter.
    
    Args:
        settings: Observability configuration settings
        resource: OpenTelemetry resource with service attributes
    """
    global _meter_provider
    
    try:
        # Determine metrics endpoint
        metrics_endpoint = settings.otlp_metrics_endpoint or settings.otlp_endpoint
        
        logger.info(f"Configuring metrics exporter to {metrics_endpoint}")
        
        # Create OTLP metrics exporter
        exporter = OTLPMetricExporter(
            endpoint=metrics_endpoint,
            insecure=settings.otlp_insecure,
        )
        
        # Create periodic metric reader
        reader = PeriodicExportingMetricReader(
            exporter=exporter,
            export_interval_millis=settings.metrics_export_interval_ms,
        )
        
        # Create and set meter provider
        _meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[reader],
        )
        
        otel_metrics.set_meter_provider(_meter_provider)
        logger.info("Metrics provider initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize metrics provider: {e}", exc_info=True)
        raise


def _initialize_tracing(settings: ObservabilitySettings, resource: Resource) -> None:
    """
    Initialize trace provider with OTLP exporter.
    
    Args:
        settings: Observability configuration settings
        resource: OpenTelemetry resource with service attributes
    """
    global _tracer_provider
    
    try:
        # Determine traces endpoint
        traces_endpoint = settings.otlp_traces_endpoint or settings.otlp_endpoint
        
        logger.info(f"Configuring trace exporter to {traces_endpoint}")
        
        # Create OTLP trace exporter
        exporter = OTLPSpanExporter(
            endpoint=traces_endpoint,
            insecure=settings.otlp_insecure,
        )
        
        # Create trace provider with batch span processor
        _tracer_provider = TracerProvider(resource=resource)
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(
                exporter,
                max_export_batch_size=settings.traces_export_batch_size,
            )
        )
        
        otel_trace.set_tracer_provider(_tracer_provider)
        logger.info("Trace provider initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize trace provider: {e}", exc_info=True)
        raise


def shutdown_observability() -> None:
    """
    Shutdown OpenTelemetry providers and flush pending telemetry.
    
    This function should be called during application shutdown to ensure
    all pending metrics and traces are exported before the application exits.
    """
    global _meter_provider, _tracer_provider, _initialized
    
    if not _initialized:
        logger.debug("OpenTelemetry not initialized, skipping shutdown")
        return
    
    try:
        logger.info("Shutting down OpenTelemetry...")
        
        # Shutdown meter provider
        if _meter_provider:
            try:
                _meter_provider.shutdown()
                logger.info("Metrics provider shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down metrics provider: {e}", exc_info=True)
        
        # Shutdown tracer provider
        if _tracer_provider:
            try:
                _tracer_provider.shutdown()
                logger.info("Trace provider shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down trace provider: {e}", exc_info=True)
        
        _initialized = False
        logger.info("OpenTelemetry shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during OpenTelemetry shutdown: {e}", exc_info=True)


def get_meter(name: str) -> otel_metrics.Meter:
    """
    Get a meter for creating metrics instruments.
    
    Args:
        name: Name of the meter (typically module name)
        
    Returns:
        Meter instance for creating metrics
    """
    return otel_metrics.get_meter(name)


def get_tracer(name: str) -> otel_trace.Tracer:
    """
    Get a tracer for creating spans.
    
    Args:
        name: Name of the tracer (typically module name)
        
    Returns:
        Tracer instance for creating spans
    """
    return otel_trace.get_tracer(name)


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
        
    Example:
        with observability_error_handler("record_metric", metric_name="operation.duration"):
            meter.record(duration)
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


__all__ = [
    "init_observability",
    "shutdown_observability",
    "get_meter",
    "get_tracer",
    "observability_error_handler",
    "ObservabilitySettings",
    "MetricsInstrumentor",
    "create_metrics_instrumentor",
]
