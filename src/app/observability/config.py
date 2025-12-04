"""
Configuration for OpenTelemetry observability.

This module provides the ObservabilitySettings model that encapsulates
all configuration needed for metrics, traces, and logs collection and export.
"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.app.config import Settings


class ObservabilitySettings(BaseModel):
    """
    OpenTelemetry configuration settings.

    This model defines all configuration parameters for observability,
    including service identification, OTLP endpoints, export intervals,
    and sampling rates.

    Attributes:
        otel_enabled: Enable/disable observability features
        service_name: Service name for telemetry identification
        service_version: Service version for telemetry
        deployment_environment: Deployment environment (dev, staging, prod)
        otlp_endpoint: Default OTLP gRPC endpoint for all telemetry
        otlp_metrics_endpoint: Separate endpoint for metrics (optional)
        otlp_traces_endpoint: Separate endpoint for traces (optional)
        otlp_logs_endpoint: Separate endpoint for logs (optional)
        metrics_export_interval_ms: Metrics export interval in milliseconds
        traces_export_batch_size: Batch size for trace export
        logs_export_batch_size: Batch size for log export
        traces_sample_rate: Trace sampling rate (0.0 to 1.0)
        otlp_insecure: Use insecure connection (no TLS)
    """

    # Enable/disable observability
    otel_enabled: bool = Field(
        default=True,
        description="Enable OpenTelemetry observability"
    )

    # Service identification
    service_name: str = Field(
        default="fastapi-crud-backend",
        description="Service name for telemetry"
    )
    service_version: str = Field(
        default="1.0.0",
        description="Service version"
    )
    deployment_environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)"
    )

    # OTLP Endpoints
    otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP gRPC endpoint for all telemetry"
    )
    otlp_metrics_endpoint: str | None = Field(
        default=None,
        description="Separate OTLP endpoint for metrics (optional)"
    )
    otlp_traces_endpoint: str | None = Field(
        default=None,
        description="Separate OTLP endpoint for traces (optional)"
    )
    otlp_logs_endpoint: str | None = Field(
        default=None,
        description="Separate OTLP endpoint for logs (optional)"
    )

    # Export configuration
    metrics_export_interval_ms: int = Field(
        default=60000,
        description="Metrics export interval in milliseconds",
        ge=1000
    )
    traces_export_batch_size: int = Field(
        default=512,
        description="Batch size for trace export",
        ge=1
    )
    logs_export_batch_size: int = Field(
        default=512,
        description="Batch size for log export",
        ge=1
    )

    # Sampling
    traces_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Trace sampling rate (0.0 to 1.0, 1.0 = 100%)"
    )

    # Connection settings
    otlp_insecure: bool = Field(
        default=True,
        description="Use insecure connection (no TLS) - set to False in production"
    )

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }

    @classmethod
    def from_settings(cls, settings: "Settings") -> "ObservabilitySettings":
        """
        Create ObservabilitySettings from application Settings.

        This factory method extracts observability-related configuration
        from the main application settings object.

        Args:
            settings: Application settings instance

        Returns:
            ObservabilitySettings instance
        """
        return cls(
            otel_enabled=settings.otel_enabled,
            service_name=settings.otel_service_name,
            service_version=settings.otel_service_version,
            deployment_environment=settings.environment,
            otlp_endpoint=settings.otel_otlp_endpoint,
            otlp_metrics_endpoint=settings.otel_otlp_metrics_endpoint,
            otlp_traces_endpoint=settings.otel_otlp_traces_endpoint,
            otlp_logs_endpoint=settings.otel_otlp_logs_endpoint,
            metrics_export_interval_ms=settings.otel_metrics_export_interval_ms,
            traces_sample_rate=settings.otel_traces_sample_rate,
            otlp_insecure=settings.otel_otlp_insecure,
        )

    def get_metrics_endpoint(self) -> str:
        """
        Get the metrics endpoint, falling back to default OTLP endpoint.

        Returns:
            Metrics endpoint URL
        """
        return self.otlp_metrics_endpoint or self.otlp_endpoint

    def get_traces_endpoint(self) -> str:
        """
        Get the traces endpoint, falling back to default OTLP endpoint.

        Returns:
            Traces endpoint URL
        """
        return self.otlp_traces_endpoint or self.otlp_endpoint

    def get_logs_endpoint(self) -> str:
        """
        Get the logs endpoint, falling back to default OTLP endpoint.

        Returns:
            Logs endpoint URL
        """
        return self.otlp_logs_endpoint or self.otlp_endpoint
