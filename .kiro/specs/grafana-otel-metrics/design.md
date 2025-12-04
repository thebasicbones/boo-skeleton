# Design Document: OpenTelemetry Observability Integration

## Overview

This design document outlines the integration of OpenTelemetry (OTEL) observability into the FastAPI CRUD backend. The solution provides comprehensive monitoring through three pillars of observability: metrics, distributed traces, and structured logs. All telemetry data will be exported via OTLP (OpenTelemetry Protocol) to Grafana for visualization and analysis.

The implementation follows a layered approach:
1. **Initialization Layer**: Bootstrap OpenTelemetry providers and exporters during application startup
2. **Instrumentation Layer**: Automatic and manual instrumentation of FastAPI endpoints and service methods
3. **Export Layer**: OTLP exporters for metrics, traces, and logs
4. **Visualization Layer**: Pre-built Grafana dashboards and alert rules

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │         OpenTelemetry Instrumentation                 │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │  Metrics   │  │   Traces   │  │    Logs    │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │              OTLP Exporters                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │  Metrics   │  │   Traces   │  │    Logs    │     │  │
│  │  │  Exporter  │  │  Exporter  │  │  Exporter  │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector (Optional)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Grafana Stack                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Prometheus │  │     Tempo    │  │     Loki     │     │
│  │   (Metrics)  │  │   (Traces)   │  │    (Logs)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Grafana Dashboards                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

1. **Application Startup** (`src/main.py`):
   - Initialize OpenTelemetry SDK
   - Configure providers and exporters
   - Set up automatic instrumentation

2. **Service Layer** (`src/app/services/resource_service.py`):
   - Manual span creation for business logic
   - Custom metrics recording
   - Structured logging with trace context

3. **Router Layer** (`src/app/routers/resources.py`):
   - Automatic HTTP instrumentation via FastAPI middleware
   - Additional context attributes

4. **Configuration** (`src/config/settings.py`):
   - OTLP endpoint configuration
   - Service name and environment
   - Export intervals and sampling rates

## Components and Interfaces

### 1. Observability Module (`src/app/observability/`)

New module structure:
```
src/app/observability/
├── __init__.py
├── config.py           # Observability configuration
├── metrics.py          # Metrics instrumentation
├── tracing.py          # Tracing instrumentation
├── logging.py          # Structured logging setup
└── middleware.py       # Custom middleware for correlation
```

### 2. Metrics Instrumentation

**Metrics to Collect:**

| Metric Name | Type | Description | Attributes |
|------------|------|-------------|------------|
| `crud.operation.duration` | Histogram | Time taken for CRUD operations | operation_type, db_type, status |
| `crud.operation.count` | Counter | Total CRUD operations | operation_type, db_type, status |
| `crud.operation.errors` | Counter | Failed operations | operation_type, error_type, db_type |
| `crud.resources.total` | UpDownCounter | Current resource count | db_type |
| `crud.cascade.delete.count` | Histogram | Resources deleted in cascade | - |
| `http.server.request.duration` | Histogram | HTTP request duration | method, route, status_code |
| `http.server.active_requests` | UpDownCounter | Active HTTP requests | method, route |

**Metrics Interface:**

```python
class MetricsInstrumentor:
    """Handles metrics collection for CRUD operations."""
    
    def __init__(self, meter: Meter):
        self.operation_duration: Histogram
        self.operation_count: Counter
        self.operation_errors: Counter
        self.resources_total: UpDownCounter
        self.cascade_delete_count: Histogram
    
    def record_operation_start(self, operation: str, db_type: str) -> float:
        """Record operation start time."""
        pass
    
    def record_operation_complete(
        self, 
        operation: str, 
        db_type: str, 
        duration: float, 
        status: str
    ):
        """Record successful operation completion."""
        pass
    
    def record_operation_error(
        self, 
        operation: str, 
        db_type: str, 
        error_type: str
    ):
        """Record operation failure."""
        pass
    
    def increment_resource_count(self, db_type: str, delta: int = 1):
        """Update resource count."""
        pass
```

### 3. Tracing Instrumentation

**Span Hierarchy:**

```
HTTP Request Span (automatic)
└── CRUD Operation Span (manual)
    ├── Validation Span
    ├── Circular Dependency Check Span
    └── Repository Operation Span
        └── Database Query Span (automatic)
```

**Span Attributes:**

| Attribute | Description | Example |
|-----------|-------------|---------|
| `operation.type` | CRUD operation type | "create", "read", "update", "delete", "search" |
| `resource.id` | Resource identifier | "abc123" |
| `resource.name` | Resource name | "Frontend App" |
| `db.type` | Database backend | "sqlite", "mongodb" |
| `db.operation` | Database operation | "insert", "select", "update", "delete" |
| `error.type` | Error category | "validation", "not_found", "circular_dependency" |
| `cascade.enabled` | Cascade delete flag | true, false |
| `search.query` | Search query string | "frontend" |

**Tracing Interface:**

```python
class TracingInstrumentor:
    """Handles distributed tracing for CRUD operations."""
    
    def __init__(self, tracer: Tracer):
        self.tracer = tracer
    
    @contextmanager
    def trace_operation(
        self, 
        operation: str, 
        resource_id: str | None = None,
        **attributes
    ) -> Span:
        """Create a span for a CRUD operation."""
        pass
    
    def add_event(self, span: Span, name: str, attributes: dict):
        """Add an event to the current span."""
        pass
    
    def record_exception(self, span: Span, exception: Exception):
        """Record an exception in the span."""
        pass
```

### 4. Structured Logging

**Log Format (JSON):**

```json
{
  "timestamp": "2024-12-04T10:30:45.123Z",
  "level": "INFO",
  "message": "Resource created successfully",
  "trace_id": "abc123def456",
  "span_id": "789ghi012jkl",
  "service.name": "fastapi-crud-backend",
  "operation.type": "create",
  "resource.id": "res_001",
  "resource.name": "Frontend App",
  "db.type": "mongodb",
  "duration_ms": 45.2,
  "status": "success"
}
```

**Logging Interface:**

```python
class StructuredLogger:
    """Provides structured logging with trace correlation."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_operation_start(
        self, 
        operation: str, 
        resource_id: str | None = None,
        **context
    ):
        """Log operation start with trace context."""
        pass
    
    def log_operation_complete(
        self, 
        operation: str, 
        duration: float,
        **context
    ):
        """Log operation completion."""
        pass
    
    def log_error(
        self, 
        operation: str, 
        error: Exception,
        **context
    ):
        """Log error with full context."""
        pass
```

### 5. Middleware

**Correlation Middleware:**

```python
class CorrelationMiddleware:
    """Middleware to inject trace context into logs and responses."""
    
    async def __call__(self, request: Request, call_next):
        # Extract or generate trace context
        # Inject into logging context
        # Add trace headers to response
        pass
```

## Data Models

### Configuration Model

```python
class ObservabilitySettings(BaseModel):
    """OpenTelemetry configuration settings."""
    
    # Enable/disable observability
    otel_enabled: bool = True
    
    # Service identification
    service_name: str = "fastapi-crud-backend"
    service_version: str = "1.0.0"
    deployment_environment: str = "development"
    
    # OTLP Endpoints
    otlp_endpoint: str = "http://localhost:4317"
    otlp_metrics_endpoint: str | None = None
    otlp_traces_endpoint: str | None = None
    otlp_logs_endpoint: str | None = None
    
    # Export configuration
    metrics_export_interval_ms: int = 60000  # 60 seconds
    traces_export_batch_size: int = 512
    logs_export_batch_size: int = 512
    
    # Sampling
    traces_sample_rate: float = 1.0  # 100% in dev, lower in prod
    
    # Insecure mode (for local development)
    otlp_insecure: bool = True
```

### Instrumentation Context

```python
@dataclass
class OperationContext:
    """Context for a single CRUD operation."""
    
    operation_type: str
    resource_id: str | None
    db_type: str
    start_time: float
    span: Span | None
    attributes: dict[str, Any]
```

## 
Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the requirements analysis, the following correctness properties must hold for the observability system:

### Metrics Properties

**Property 1: Operation duration recording**
*For any* CRUD operation (create, read, update, delete, search), when the operation executes, the system should record the operation duration in a histogram metric with the operation type as an attribute.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

**Property 2: Success counter increment**
*For any* CRUD operation that completes successfully, the system should increment a success counter with the operation type attribute.
**Validates: Requirements 3.1**

**Property 3: Failure counter increment**
*For any* CRUD operation that fails with an exception, the system should increment a failure counter with both operation type and error type attributes.
**Validates: Requirements 3.2, 3.3**

**Property 4: Metric attributes completeness**
*For any* metric recorded, the system should include operation type and database backend type as attributes.
**Validates: Requirements 4.1, 4.2**

**Property 5: Resource count tracking**
*For any* resource creation, the total resources counter should increase by 1, and for any resource deletion, it should decrease by 1.
**Validates: Requirements 5.1, 5.2**

**Property 6: Cascade delete recording**
*For any* cascade delete operation, the system should record the number of resources deleted in a histogram metric.
**Validates: Requirements 5.3**

### Tracing Properties

**Property 7: Span creation for operations**
*For any* CRUD operation that begins, the system should create a trace span for that operation.
**Validates: Requirements 8.1**

**Property 8: Span attributes completeness**
*For any* span created for a CRUD operation, the span should include operation type, resource ID (if applicable), and database type as attributes.
**Validates: Requirements 8.2**

**Property 9: Child span creation**
*For any* CRUD operation that calls the repository layer, the system should create a child span for the database operation with the correct parent context.
**Validates: Requirements 8.3**

**Property 10: Span closure and status**
*For any* CRUD operation that completes (successfully or with error), all associated spans should be closed and record the final status.
**Validates: Requirements 8.4**

**Property 11: Error span marking**
*For any* operation that raises an exception, the associated span should be marked as error and include exception details.
**Validates: Requirements 8.5**

**Property 12: Trace context propagation**
*For any* request processed through multiple layers, child spans should have trace context that correctly references their parent spans.
**Validates: Requirements 8.6**

**Property 13: HTTP span creation**
*For any* HTTP request received by the application, the system should automatically create a trace span with HTTP method, path, status code, and duration.
**Validates: Requirements 10.2, 10.3, 10.4**

**Property 14: Instrumentation coexistence**
*For any* request with automatic HTTP instrumentation, manual service-layer spans should still be created and properly nested within the HTTP span.
**Validates: Requirements 10.5**

### Logging Properties

**Property 15: Operation start logging**
*For any* CRUD operation that starts, the system should log the operation start with structured fields including operation type and resource ID.
**Validates: Requirements 9.1**

**Property 16: Operation completion logging**
*For any* CRUD operation that completes, the system should log the completion with duration and outcome.
**Validates: Requirements 9.2**

**Property 17: Log trace correlation**
*For any* log entry created during request processing, the log should include trace ID and span ID for correlation.
**Validates: Requirements 9.3**

**Property 18: Log field completeness**
*For any* log entry, the system should include operation type, resource ID (if applicable), and timestamp.
**Validates: Requirements 9.4**

**Property 19: Error logging**
*For any* operation that raises an exception, the system should log the error with full exception details and stack trace.
**Validates: Requirements 9.5**

**Property 20: JSON log format**
*For any* log entry produced by the observability system, the log should be valid JSON with expected structured fields.
**Validates: Requirements 9.6**

### Configuration Properties

**Property 21: Configuration loading**
*For any* observability configuration setting (OTLP endpoints, service name, export interval), when the setting is provided via environment variable, the system should use that value.
**Validates: Requirements 6.1, 6.3, 6.6, 1.2, 1.5**

**Property 22: Observability disable**
*For any* operation when observability is disabled via configuration, the system should not collect or export any telemetry data.
**Validates: Requirements 6.5**

### Resilience Properties

**Property 23: Export failure resilience**
*For any* telemetry export failure, the system should log the error and continue normal CRUD operation without blocking or crashing.
**Validates: Requirements 7.2**

**Property 24: Endpoint unavailability resilience**
*For any* CRUD operation when the OTLP endpoint is unavailable, the operation should complete successfully without blocking.
**Validates: Requirements 7.3**

## Error Handling

### Error Categories

1. **Configuration Errors**:
   - Invalid OTLP endpoint URLs
   - Missing required configuration
   - Invalid export intervals or sample rates
   - **Handling**: Log error, use defaults, continue with degraded observability

2. **Export Errors**:
   - Network failures to OTLP endpoint
   - Authentication failures
   - Timeout errors
   - **Handling**: Log error, buffer data (with limits), retry with exponential backoff

3. **Instrumentation Errors**:
   - Span creation failures
   - Metric recording failures
   - Log formatting errors
   - **Handling**: Log error, continue operation, emit internal error metric

4. **Resource Errors**:
   - Memory pressure from buffered telemetry
   - CPU overhead from instrumentation
   - **Handling**: Implement sampling, reduce batch sizes, disable non-critical telemetry

### Error Handling Strategy

```python
class ObservabilityErrorHandler:
    """Centralized error handling for observability operations."""
    
    def handle_export_error(self, error: Exception, telemetry_type: str):
        """Handle errors during telemetry export."""
        # Log error
        # Increment internal error counter
        # Apply backoff strategy
        # Continue normal operation
        pass
    
    def handle_instrumentation_error(self, error: Exception, context: dict):
        """Handle errors during instrumentation."""
        # Log error with context
        # Emit internal error metric
        # Continue without blocking operation
        pass
    
    def handle_configuration_error(self, error: Exception):
        """Handle configuration errors."""
        # Log error
        # Use default configuration
        # Set degraded mode flag
        pass
```

### Graceful Degradation

The system should degrade gracefully when observability components fail:

1. **Level 1 - Full Observability**: All metrics, traces, and logs collected and exported
2. **Level 2 - Partial Observability**: Only critical metrics and error logs collected
3. **Level 3 - Minimal Observability**: Only error logs to local file
4. **Level 4 - No Observability**: All observability disabled, application continues normally

## Testing Strategy

### Unit Testing

Unit tests will verify individual components:

1. **Configuration Tests**:
   - Test loading from environment variables
   - Test default values
   - Test validation logic

2. **Metrics Tests**:
   - Test metric creation and recording
   - Test attribute attachment
   - Test counter/histogram behavior

3. **Tracing Tests**:
   - Test span creation and closure
   - Test attribute attachment
   - Test parent-child relationships

4. **Logging Tests**:
   - Test JSON formatting
   - Test field inclusion
   - Test trace context injection

### Property-Based Testing

Property-based tests will use **Hypothesis** library to verify universal properties across many randomly generated inputs:

1. **Operation Properties**:
   - Generate random CRUD operations
   - Verify metrics are recorded with correct attributes
   - Verify spans are created and closed
   - Verify logs contain required fields

2. **Configuration Properties**:
   - Generate random configuration values
   - Verify they are correctly applied
   - Verify defaults are used when not provided

3. **Error Handling Properties**:
   - Generate random error scenarios
   - Verify system continues operation
   - Verify errors are logged appropriately

4. **Trace Context Properties**:
   - Generate nested operation calls
   - Verify trace context propagates correctly
   - Verify parent-child span relationships

### Integration Testing

Integration tests will verify end-to-end observability:

1. **OTLP Export Tests**:
   - Use test OTLP collector
   - Verify metrics, traces, and logs are exported
   - Verify correct format and attributes

2. **FastAPI Integration Tests**:
   - Make HTTP requests to endpoints
   - Verify automatic instrumentation works
   - Verify manual instrumentation coexists

3. **Database Backend Tests**:
   - Test with both SQLite and MongoDB
   - Verify db_type attribute is correct
   - Verify repository spans are created

### Test Configuration

```python
# pytest.ini additions
[pytest]
markers =
    observability: marks tests for observability features
    property: marks property-based tests
    integration: marks integration tests requiring external services
```

## Implementation Details

### Dependencies

Add to `requirements.txt`:

```
# OpenTelemetry Core
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0

# OpenTelemetry Instrumentation
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-pymongo==0.42b0

# OTLP Exporters
opentelemetry-exporter-otlp-proto-grpc==1.21.0
opentelemetry-exporter-otlp-proto-http==1.21.0

# Logging integration
opentelemetry-instrumentation-logging==0.42b0
python-json-logger==2.0.7
```

### Configuration Updates

Add to `src/config/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # OpenTelemetry Configuration
    otel_enabled: bool = Field(default=True, description="Enable OpenTelemetry observability")
    otel_service_name: str = Field(default="fastapi-crud-backend", description="Service name for telemetry")
    otel_service_version: str = Field(default="1.0.0", description="Service version")
    
    # OTLP Endpoints
    otel_otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP gRPC endpoint for all telemetry"
    )
    otel_otlp_metrics_endpoint: str | None = Field(
        default=None,
        description="Separate OTLP endpoint for metrics (optional)"
    )
    otel_otlp_traces_endpoint: str | None = Field(
        default=None,
        description="Separate OTLP endpoint for traces (optional)"
    )
    otel_otlp_logs_endpoint: str | None = Field(
        default=None,
        description="Separate OTLP endpoint for logs (optional)"
    )
    
    # Export Configuration
    otel_metrics_export_interval_ms: int = Field(
        default=60000,
        description="Metrics export interval in milliseconds"
    )
    otel_traces_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Trace sampling rate (0.0 to 1.0)"
    )
    
    # Connection settings
    otel_otlp_insecure: bool = Field(
        default=True,
        description="Use insecure connection (no TLS)"
    )
```

### Initialization Flow

```python
# In src/main.py

from app.observability import init_observability, shutdown_observability

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager with observability."""
    # Startup
    logger.info("Starting up application...")
    
    # Initialize observability first
    if settings.otel_enabled:
        init_observability(settings)
        logger.info("OpenTelemetry initialized")
    
    # Initialize database
    await init_database()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_database()
    
    # Shutdown observability last
    if settings.otel_enabled:
        shutdown_observability()
        logger.info("OpenTelemetry shutdown complete")
```

### Service Layer Instrumentation

```python
# In src/app/services/resource_service.py

from app.observability import get_tracer, get_meter, get_logger

class ResourceService:
    def __init__(self, db: AsyncSession | AsyncIOMotorDatabase):
        self.db = db
        self.repository = get_repository(db)
        self.topo_service = TopologicalSortService()
        
        # Observability components
        self.tracer = get_tracer(__name__)
        self.metrics = get_meter(__name__)
        self.logger = get_logger(__name__)
        
        # Initialize metrics
        self.operation_duration = self.metrics.create_histogram(
            "crud.operation.duration",
            description="Duration of CRUD operations",
            unit="ms"
        )
        self.operation_counter = self.metrics.create_counter(
            "crud.operation.count",
            description="Count of CRUD operations"
        )
    
    async def create_resource(self, data: ResourceCreate) -> ResourceResponse:
        """Create resource with full observability."""
        start_time = time.time()
        db_type = "mongodb" if isinstance(self.db, AsyncIOMotorDatabase) else "sqlite"
        
        with self.tracer.start_as_current_span(
            "create_resource",
            attributes={
                "operation.type": "create",
                "resource.name": data.name,
                "db.type": db_type
            }
        ) as span:
            try:
                self.logger.info(
                    "Creating resource",
                    extra={
                        "operation.type": "create",
                        "resource.name": data.name,
                        "db.type": db_type
                    }
                )
                
                # Business logic
                temp_id = "temp_new_resource_id"
                await self._validate_and_check_cycles(temp_id, data.dependencies)
                resource = await self.repository.create(data)
                
                # Record success
                duration_ms = (time.time() - start_time) * 1000
                self.operation_duration.record(
                    duration_ms,
                    {"operation.type": "create", "db.type": db_type, "status": "success"}
                )
                self.operation_counter.add(
                    1,
                    {"operation.type": "create", "db.type": db_type, "status": "success"}
                )
                
                span.set_attribute("resource.id", resource.id)
                span.set_status(Status(StatusCode.OK))
                
                self.logger.info(
                    "Resource created successfully",
                    extra={
                        "operation.type": "create",
                        "resource.id": resource.id,
                        "duration_ms": duration_ms
                    }
                )
                
                return self._resource_to_response(resource)
                
            except Exception as e:
                # Record failure
                duration_ms = (time.time() - start_time) * 1000
                error_type = type(e).__name__
                
                self.operation_duration.record(
                    duration_ms,
                    {"operation.type": "create", "db.type": db_type, "status": "error"}
                )
                self.operation_counter.add(
                    1,
                    {"operation.type": "create", "db.type": db_type, "status": "error", "error.type": error_type}
                )
                
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                self.logger.error(
                    "Failed to create resource",
                    extra={
                        "operation.type": "create",
                        "error.type": error_type,
                        "duration_ms": duration_ms
                    },
                    exc_info=True
                )
                
                raise
```

## Grafana Dashboards

### Dashboard 1: CRUD Operations Overview

**Panels:**
1. **Request Rate**: Time series of CRUD operations per second by operation type
2. **Latency Percentiles**: P50, P95, P99 latency for each operation type
3. **Error Rate**: Percentage of failed operations by type
4. **Active Resources**: Current count of resources in the system
5. **Operation Distribution**: Pie chart of operation types

**File**: `grafana/dashboards/crud-operations-overview.json`

### Dashboard 2: Performance Analysis

**Panels:**
1. **Operation Duration Heatmap**: Distribution of operation durations over time
2. **Slowest Operations**: Table of slowest operations with resource IDs
3. **Database Performance**: Comparison of SQLite vs MongoDB operation times
4. **Cascade Delete Impact**: Histogram of resources deleted in cascade operations
5. **HTTP Request Duration**: P95 latency by endpoint

**File**: `grafana/dashboards/performance-analysis.json`

### Dashboard 3: Error Analysis

**Panels:**
1. **Error Rate by Type**: Time series of errors categorized by error type
2. **Error Distribution**: Pie chart of error types
3. **Failed Operations**: Table of recent failed operations with details
4. **Circular Dependency Events**: Count of circular dependency detections
5. **Validation Errors**: Count of validation failures by field

**File**: `grafana/dashboards/error-analysis.json`

### Dashboard 4: Distributed Tracing

**Panels:**
1. **Trace Timeline**: Gantt chart of spans for selected traces
2. **Span Duration**: Breakdown of time spent in each layer
3. **Service Map**: Visual representation of service dependencies
4. **Trace Search**: Search traces by operation, resource ID, or error
5. **Span Attributes**: Table of span attributes for debugging

**File**: `grafana/dashboards/distributed-tracing.json`

### Dashboard 5: Logs and Correlation

**Panels:**
1. **Log Stream**: Real-time log entries with filtering
2. **Logs by Level**: Count of logs by severity level
3. **Correlated Logs**: Logs linked to selected trace
4. **Error Logs**: Recent error logs with stack traces
5. **Operation Logs**: Logs filtered by operation type

**File**: `grafana/dashboards/logs-correlation.json`

## Alert Rules

### Alert 1: High Error Rate

```yaml
# grafana/alerts/high-error-rate.yaml
alert: HighCRUDErrorRate
expr: |
  (
    sum(rate(crud_operation_count{status="error"}[5m]))
    /
    sum(rate(crud_operation_count[5m]))
  ) > 0.05
for: 5m
labels:
  severity: warning
annotations:
  summary: "High CRUD operation error rate"
  description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
```

### Alert 2: Slow Operations

```yaml
# grafana/alerts/slow-operations.yaml
alert: SlowCRUDOperations
expr: |
  histogram_quantile(0.95, 
    rate(crud_operation_duration_bucket[5m])
  ) > 1000
for: 10m
labels:
  severity: warning
annotations:
  summary: "CRUD operations are slow"
  description: "P95 latency is {{ $value }}ms (threshold: 1000ms)"
```

### Alert 3: Circular Dependency Detection

```yaml
# grafana/alerts/circular-dependency.yaml
alert: CircularDependencyDetected
expr: |
  increase(crud_operation_count{error_type="CircularDependencyError"}[5m]) > 0
for: 1m
labels:
  severity: critical
annotations:
  summary: "Circular dependency detected"
  description: "{{ $value }} circular dependencies detected in the last 5 minutes"
```

### Alert 4: Database Connection Issues

```yaml
# grafana/alerts/database-connection.yaml
alert: DatabaseConnectionFailures
expr: |
  increase(crud_operation_count{error_type="DatabaseError"}[5m]) > 5
for: 2m
labels:
  severity: critical
annotations:
  summary: "Database connection failures"
  description: "{{ $value }} database errors in the last 5 minutes"
```

### Alert 5: OTLP Export Failures

```yaml
# grafana/alerts/otlp-export-failures.yaml
alert: OTLPExportFailures
expr: |
  increase(otel_export_errors_total[5m]) > 10
for: 5m
labels:
  severity: warning
annotations:
  summary: "OpenTelemetry export failures"
  description: "{{ $value }} OTLP export failures in the last 5 minutes"
```

## Documentation

### Setup Guide

**File**: `docs/observability-setup.md`

Content will include:
1. Installing and configuring OpenTelemetry Collector
2. Setting up Grafana with Prometheus, Tempo, and Loki
3. Configuring OTLP endpoints
4. Importing dashboards and alert rules
5. Environment variable reference
6. Troubleshooting common issues

### Metrics Reference

**File**: `docs/metrics-reference.md`

Content will include:
- Complete list of all metrics
- Metric types and units
- Available attributes and their values
- Example PromQL queries
- Best practices for querying

### Tracing Guide

**File**: `docs/tracing-guide.md`

Content will include:
- Span hierarchy and relationships
- Span attributes reference
- How to search and filter traces
- Understanding trace timelines
- Debugging with traces

### Logging Reference

**File**: `docs/logging-reference.md`

Content will include:
- Log format specification
- Available log fields
- Log levels and when they're used
- Correlating logs with traces
- Example LogQL queries

## Deployment Considerations

### Docker Compose Setup

Provide a `docker-compose.yml` for local development:

```yaml
version: '3.8'

services:
  # Application
  fastapi-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OTEL_ENABLED=true
      - OTEL_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_SERVICE_NAME=fastapi-crud-backend
    depends_on:
      - otel-collector
  
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
  
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  # Tempo
  tempo:
    image: grafana/tempo:latest
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
    ports:
      - "3200:3200"   # Tempo
      - "4317"        # OTLP gRPC
  
  # Loki
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
  
  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
```

### Production Considerations

1. **Sampling**: Reduce trace sample rate in production (e.g., 0.1 for 10%)
2. **Batching**: Increase batch sizes for better performance
3. **Resource Limits**: Set memory limits for telemetry buffers
4. **Security**: Use TLS for OTLP connections in production
5. **High Availability**: Deploy multiple OTLP collectors
6. **Data Retention**: Configure appropriate retention policies

## Summary

This design provides comprehensive observability for the FastAPI CRUD backend through:

1. **Metrics**: Track operation performance, error rates, and resource counts
2. **Traces**: Understand request flow and identify latency bottlenecks
3. **Logs**: Structured logging with trace correlation for debugging
4. **Dashboards**: Pre-built Grafana dashboards for immediate visibility
5. **Alerts**: Proactive monitoring with configurable alert rules
6. **Resilience**: Graceful degradation when observability components fail

The implementation follows OpenTelemetry standards, ensuring compatibility with the broader observability ecosystem and enabling future enhancements like custom exporters or additional instrumentation.
