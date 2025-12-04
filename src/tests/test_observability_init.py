"""
Unit tests for observability module initialization and configuration.

Tests the basic functionality of the observability module including
initialization, shutdown, and configuration loading.
"""

from unittest.mock import patch

from app.observability import (
    get_meter,
    get_tracer,
    init_observability,
    observability_error_handler,
    shutdown_observability,
)
from app.observability.config import ObservabilitySettings
from config.settings import Settings


class TestObservabilitySettings:
    """Test ObservabilitySettings configuration model."""

    def test_default_settings(self):
        """Test that default settings are created correctly."""
        settings = ObservabilitySettings()

        assert settings.otel_enabled is True
        assert settings.service_name == "fastapi-crud-backend"
        assert settings.service_version == "1.0.0"
        assert settings.deployment_environment == "development"
        assert settings.otlp_endpoint == "http://localhost:4317"
        assert settings.metrics_export_interval_ms == 60000
        assert settings.traces_sample_rate == 1.0
        assert settings.otlp_insecure is True

    def test_from_settings(self):
        """Test creating ObservabilitySettings from application Settings."""
        app_settings = Settings()
        obs_settings = ObservabilitySettings.from_settings(app_settings)

        assert obs_settings.otel_enabled == app_settings.otel_enabled
        assert obs_settings.service_name == app_settings.otel_service_name
        assert obs_settings.service_version == app_settings.otel_service_version
        assert obs_settings.deployment_environment == app_settings.environment
        assert obs_settings.otlp_endpoint == app_settings.otel_otlp_endpoint

    def test_endpoint_fallback(self):
        """Test that endpoint getters fall back to default OTLP endpoint."""
        settings = ObservabilitySettings(
            otlp_endpoint="http://default:4317"
        )

        # When specific endpoints are not set, should fall back to default
        assert settings.get_metrics_endpoint() == "http://default:4317"
        assert settings.get_traces_endpoint() == "http://default:4317"
        assert settings.get_logs_endpoint() == "http://default:4317"

    def test_specific_endpoints(self):
        """Test that specific endpoints are used when provided."""
        settings = ObservabilitySettings(
            otlp_endpoint="http://default:4317",
            otlp_metrics_endpoint="http://metrics:4317",
            otlp_traces_endpoint="http://traces:4317",
            otlp_logs_endpoint="http://logs:4317",
        )

        assert settings.get_metrics_endpoint() == "http://metrics:4317"
        assert settings.get_traces_endpoint() == "http://traces:4317"
        assert settings.get_logs_endpoint() == "http://logs:4317"


class TestObservabilityInitialization:
    """Test observability initialization and shutdown."""

    @patch('app.observability.OTLPMetricExporter')
    @patch('app.observability.OTLPSpanExporter')
    def test_init_observability_enabled(self, mock_span_exporter, mock_metric_exporter):
        """Test that observability initializes when enabled."""
        settings = ObservabilitySettings(otel_enabled=True)

        # Initialize
        init_observability(settings)

        # Verify exporters were created
        assert mock_metric_exporter.called
        assert mock_span_exporter.called

        # Cleanup
        shutdown_observability()

    def test_init_observability_disabled(self):
        """Test that observability does not initialize when disabled."""
        settings = ObservabilitySettings(otel_enabled=False)

        # Should not raise any errors
        init_observability(settings)
        shutdown_observability()

    @patch('app.observability.OTLPMetricExporter')
    @patch('app.observability.OTLPSpanExporter')
    def test_get_meter(self, mock_span_exporter, mock_metric_exporter):
        """Test getting a meter instance."""
        settings = ObservabilitySettings(otel_enabled=True)
        init_observability(settings)

        meter = get_meter("test.module")
        assert meter is not None

        shutdown_observability()

    @patch('app.observability.OTLPMetricExporter')
    @patch('app.observability.OTLPSpanExporter')
    def test_get_tracer(self, mock_span_exporter, mock_metric_exporter):
        """Test getting a tracer instance."""
        settings = ObservabilitySettings(otel_enabled=True)
        init_observability(settings)

        tracer = get_tracer("test.module")
        assert tracer is not None

        shutdown_observability()

    def test_shutdown_when_not_initialized(self):
        """Test that shutdown works even when not initialized."""
        # Should not raise any errors
        shutdown_observability()


class TestObservabilityErrorHandler:
    """Test observability error handling utilities."""

    def test_error_handler_catches_exceptions(self):
        """Test that error handler catches and logs exceptions."""
        with observability_error_handler("test_operation", test_context="value"):
            # This should not raise
            raise ValueError("Test error")

    def test_error_handler_allows_normal_execution(self):
        """Test that error handler allows normal execution."""
        result = None
        with observability_error_handler("test_operation"):
            result = "success"

        assert result == "success"
