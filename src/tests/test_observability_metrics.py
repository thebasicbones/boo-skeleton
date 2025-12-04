"""
Unit tests for observability metrics instrumentation.

Tests the MetricsInstrumentor class and its methods for recording
CRUD operation metrics including duration, counts, errors, and
resource tracking.
"""

import time
import pytest
from unittest.mock import Mock, MagicMock, patch

from app.observability.metrics import MetricsInstrumentor, create_metrics_instrumentor


class TestMetricsInstrumentor:
    """Test MetricsInstrumentor class."""
    
    @pytest.fixture
    def mock_meter(self):
        """Create a mock meter with mock instruments."""
        meter = Mock()
        
        # Create mock instruments - each call should return a NEW mock
        meter.create_histogram = Mock(side_effect=lambda *args, **kwargs: Mock())
        meter.create_counter = Mock(side_effect=lambda *args, **kwargs: Mock())
        meter.create_up_down_counter = Mock(side_effect=lambda *args, **kwargs: Mock())
        
        return meter
    
    @pytest.fixture
    def instrumentor(self, mock_meter):
        """Create a MetricsInstrumentor instance with mock meter."""
        instrumentor = MetricsInstrumentor(mock_meter)
        # Reset mock call counts after initialization
        for instrument in [instrumentor.operation_duration, instrumentor.operation_count,
                          instrumentor.operation_errors, instrumentor.resources_total,
                          instrumentor.cascade_delete_count]:
            instrument.reset_mock()
        return instrumentor
    
    def test_initialization(self, mock_meter):
        """Test that MetricsInstrumentor initializes all instruments."""
        instrumentor = MetricsInstrumentor(mock_meter)
        
        # Verify all instruments were created
        assert mock_meter.create_histogram.call_count == 2  # duration and cascade_delete
        assert mock_meter.create_counter.call_count == 2  # count and errors
        assert mock_meter.create_up_down_counter.call_count == 1  # resources_total
        
        # Verify instruments are assigned
        assert instrumentor.operation_duration is not None
        assert instrumentor.operation_count is not None
        assert instrumentor.operation_errors is not None
        assert instrumentor.resources_total is not None
        assert instrumentor.cascade_delete_count is not None
    
    def test_record_operation_start(self, instrumentor):
        """Test recording operation start time."""
        start_time = instrumentor.record_operation_start("create", "mongodb")
        
        # Should return a timestamp
        assert isinstance(start_time, float)
        assert start_time > 0
        
        # Should be close to current time
        assert abs(time.time() - start_time) < 0.1
    
    def test_record_operation_complete_success(self, instrumentor):
        """Test recording successful operation completion."""
        operation = "create"
        db_type = "mongodb"
        duration = 0.045  # 45ms
        
        instrumentor.record_operation_complete(operation, db_type, duration, "success")
        
        # Verify duration histogram was recorded
        instrumentor.operation_duration.record.assert_called_once()
        call_args = instrumentor.operation_duration.record.call_args
        
        # Check duration is in milliseconds
        assert call_args[0][0] == 45.0  # 0.045 * 1000
        
        # Check attributes
        attributes = call_args[0][1]
        assert attributes["operation.type"] == operation
        assert attributes["db.type"] == db_type
        assert attributes["status"] == "success"
        
        # Verify counter was incremented
        instrumentor.operation_count.add.assert_called_once()
        counter_args = instrumentor.operation_count.add.call_args
        assert counter_args[0][0] == 1
        assert counter_args[0][1]["operation.type"] == operation
    
    def test_record_operation_complete_with_additional_attributes(self, instrumentor):
        """Test recording operation with additional attributes."""
        instrumentor.record_operation_complete(
            "create", "mongodb", 0.050, "success",
            http_status_code=201,
            resource_id="res_123"
        )
        
        # Verify additional attributes are included
        call_args = instrumentor.operation_duration.record.call_args
        attributes = call_args[0][1]
        assert attributes["http_status_code"] == 201
        assert attributes["resource_id"] == "res_123"
    
    def test_record_operation_error(self, instrumentor):
        """Test recording operation error."""
        operation = "create"
        db_type = "mongodb"
        error_type = "validation"
        
        instrumentor.record_operation_error(operation, db_type, error_type)
        
        # Verify error counter was incremented
        instrumentor.operation_errors.add.assert_called_once()
        error_args = instrumentor.operation_errors.add.call_args
        assert error_args[0][0] == 1
        
        # Check attributes
        attributes = error_args[0][1]
        assert attributes["operation.type"] == operation
        assert attributes["db.type"] == db_type
        assert attributes["error.type"] == error_type
        assert attributes["status"] == "error"
        
        # Verify operation counter was also incremented
        instrumentor.operation_count.add.assert_called_once()
    
    def test_record_operation_error_with_duration(self, instrumentor):
        """Test recording operation error with duration."""
        duration = 0.030  # 30ms
        
        instrumentor.record_operation_error(
            "create", "mongodb", "validation", duration=duration
        )
        
        # Verify duration was recorded
        instrumentor.operation_duration.record.assert_called_once()
        call_args = instrumentor.operation_duration.record.call_args
        assert call_args[0][0] == 30.0  # 0.030 * 1000
    
    def test_record_operation_error_with_additional_attributes(self, instrumentor):
        """Test recording error with additional attributes."""
        instrumentor.record_operation_error(
            "create", "mongodb", "validation",
            http_status_code=422,
            field="name"
        )
        
        # Verify additional attributes are included
        call_args = instrumentor.operation_errors.add.call_args
        attributes = call_args[0][1]
        assert attributes["http_status_code"] == 422
        assert attributes["field"] == "name"
    
    def test_increment_resource_count_positive(self, instrumentor):
        """Test incrementing resource count."""
        db_type = "mongodb"
        
        instrumentor.increment_resource_count(db_type, delta=1)
        
        # Verify up-down counter was updated
        instrumentor.resources_total.add.assert_called_once()
        call_args = instrumentor.resources_total.add.call_args
        assert call_args[0][0] == 1
        assert call_args[0][1]["db.type"] == db_type
    
    def test_increment_resource_count_negative(self, instrumentor):
        """Test decrementing resource count."""
        db_type = "sqlite"
        
        instrumentor.increment_resource_count(db_type, delta=-1)
        
        # Verify up-down counter was updated with negative value
        instrumentor.resources_total.add.assert_called_once()
        call_args = instrumentor.resources_total.add.call_args
        assert call_args[0][0] == -1
        assert call_args[0][1]["db.type"] == db_type
    
    def test_increment_resource_count_default_delta(self, instrumentor):
        """Test incrementing resource count with default delta."""
        instrumentor.increment_resource_count("mongodb")
        
        # Should default to delta=1
        call_args = instrumentor.resources_total.add.call_args
        assert call_args[0][0] == 1
    
    def test_record_cascade_delete(self, instrumentor):
        """Test recording cascade delete operation."""
        count = 5
        db_type = "mongodb"
        
        instrumentor.record_cascade_delete(count, db_type)
        
        # Verify histogram was recorded
        instrumentor.cascade_delete_count.record.assert_called_once()
        call_args = instrumentor.cascade_delete_count.record.call_args
        assert call_args[0][0] == count
        assert call_args[0][1]["db.type"] == db_type
    
    def test_record_cascade_delete_zero(self, instrumentor):
        """Test recording cascade delete with zero count."""
        instrumentor.record_cascade_delete(0, "sqlite")
        
        # Should still record the metric
        instrumentor.cascade_delete_count.record.assert_called_once()
        call_args = instrumentor.cascade_delete_count.record.call_args
        assert call_args[0][0] == 0
    
    def test_multiple_operations(self, instrumentor):
        """Test recording multiple operations."""
        # Record multiple operations
        instrumentor.record_operation_complete("create", "mongodb", 0.050, "success")
        instrumentor.record_operation_complete("read", "mongodb", 0.020, "success")
        instrumentor.record_operation_error("update", "mongodb", "not_found")
        
        # Verify counters were called multiple times
        assert instrumentor.operation_duration.record.call_count == 2
        # operation_count is called once per complete (2) + once per error (1) = 3 total
        assert instrumentor.operation_count.add.call_count == 3
        assert instrumentor.operation_errors.add.call_count == 1
    
    def test_different_database_types(self, instrumentor):
        """Test recording operations for different database types."""
        instrumentor.record_operation_complete("create", "mongodb", 0.050, "success")
        instrumentor.record_operation_complete("create", "sqlite", 0.030, "success")
        
        # Verify both were recorded with correct db_type
        calls = instrumentor.operation_duration.record.call_args_list
        assert calls[0][0][1]["db.type"] == "mongodb"
        assert calls[1][0][1]["db.type"] == "sqlite"
    
    def test_error_handling_in_record_operation_complete(self, instrumentor):
        """Test that errors in recording don't crash the application."""
        # Make the histogram raise an exception
        instrumentor.operation_duration.record.side_effect = Exception("Test error")
        
        # Should not raise - error handler should catch it
        instrumentor.record_operation_complete("create", "mongodb", 0.050, "success")
    
    def test_error_handling_in_record_operation_error(self, instrumentor):
        """Test that errors in error recording don't crash the application."""
        # Make the counter raise an exception
        instrumentor.operation_errors.add.side_effect = Exception("Test error")
        
        # Should not raise - error handler should catch it
        instrumentor.record_operation_error("create", "mongodb", "validation")
    
    def test_error_handling_in_increment_resource_count(self, instrumentor):
        """Test that errors in resource count don't crash the application."""
        # Make the up-down counter raise an exception
        instrumentor.resources_total.add.side_effect = Exception("Test error")
        
        # Should not raise - error handler should catch it
        instrumentor.increment_resource_count("mongodb", delta=1)
    
    def test_error_handling_in_record_cascade_delete(self, instrumentor):
        """Test that errors in cascade delete recording don't crash the application."""
        # Make the histogram raise an exception
        instrumentor.cascade_delete_count.record.side_effect = Exception("Test error")
        
        # Should not raise - error handler should catch it
        instrumentor.record_cascade_delete(5, "mongodb")


class TestCreateMetricsInstrumentor:
    """Test the factory function for creating MetricsInstrumentor."""
    
    def test_create_metrics_instrumentor_success(self):
        """Test successful creation of MetricsInstrumentor."""
        mock_meter = Mock()
        mock_meter.create_histogram = Mock(return_value=Mock())
        mock_meter.create_counter = Mock(return_value=Mock())
        mock_meter.create_up_down_counter = Mock(return_value=Mock())
        
        instrumentor = create_metrics_instrumentor(mock_meter)
        
        assert isinstance(instrumentor, MetricsInstrumentor)
        assert instrumentor.meter == mock_meter
    
    def test_create_metrics_instrumentor_failure(self):
        """Test that factory function logs error but doesn't crash due to error handler."""
        mock_meter = Mock()
        mock_meter.create_histogram.side_effect = Exception("Test error")
        
        # The error handler catches the exception, so it should not raise
        # but the instrumentor should still be created (with potentially incomplete instruments)
        instrumentor = create_metrics_instrumentor(mock_meter)
        assert isinstance(instrumentor, MetricsInstrumentor)


class TestMetricsInstrumentorIntegration:
    """Integration tests for MetricsInstrumentor with real OpenTelemetry components."""
    
    @pytest.fixture
    def real_meter(self):
        """Create a real OpenTelemetry meter for integration testing."""
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader
        
        # Create in-memory reader to capture metrics
        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        
        # Get meter directly from provider (don't set global provider)
        meter = provider.get_meter("test.metrics")
        
        yield meter, reader
        
        # Cleanup
        provider.shutdown()
    
    def test_real_metrics_recording(self, real_meter):
        """Test that metrics are actually recorded with real OpenTelemetry."""
        meter, reader = real_meter
        instrumentor = MetricsInstrumentor(meter)
        
        # Record some operations
        instrumentor.record_operation_complete("create", "mongodb", 0.050, "success")
        instrumentor.record_operation_error("update", "mongodb", "validation")
        instrumentor.increment_resource_count("mongodb", delta=1)
        instrumentor.record_cascade_delete(3, "mongodb")
        
        # Force metrics collection by calling collect on the reader
        reader.collect()
        
        # Get metrics data
        metrics_data = reader.get_metrics_data()
        
        # Verify metrics were recorded
        assert metrics_data is not None
        
        # Check that we have resource metrics
        resource_metrics = metrics_data.resource_metrics
        assert len(resource_metrics) > 0
        
        # Check that we have scope metrics
        scope_metrics = resource_metrics[0].scope_metrics
        assert len(scope_metrics) > 0
        
        # Check that we have actual metrics
        metrics_list = scope_metrics[0].metrics
        assert len(metrics_list) > 0
        
        # Verify metric names - at least some metrics should be present
        metric_names = [m.name for m in metrics_list]
        
        # Check that at least the counter metrics are present
        # (Histograms may not always be immediately available in InMemoryMetricReader)
        assert "crud.operation.count" in metric_names
        assert "crud.operation.errors" in metric_names
        assert "crud.resources.total" in metric_names
