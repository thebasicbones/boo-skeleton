# FastAPI CRUD CLI

**⚡ Generate production-ready FastAPI backends in seconds, not hours**

[![PyPI version](https://img.shields.io/pypi/v/fastapi-crud-cli?color=blue&label=PyPI)](https://pypi.org/project/fastapi-crud-cli/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-crud-cli?color=blue)](https://pypi.org/project/fastapi-crud-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## What is FastAPI CRUD CLI?

A powerful command-line scaffolding tool that generates complete, production-ready FastAPI projects with your choice of database backend. Stop writing boilerplate—start building features.

**One command. Complete backend. Ready to run.**

```bash
pip install fastapi-crud-cli
fastapi-crud create
```

---

## ✨ Features

### Core Features
- **🎨 Interactive CLI** — Beautiful prompts with colors, progress indicators, and formatted output
- **🗄️ Multi-Database Support** — SQLite, MongoDB, or PostgreSQL—your choice
- **🏗️ Production Architecture** — Repository pattern, service layer, dependency injection
- **⚡ Zero to Running in 60s** — Auto-creates virtualenv, installs dependencies, configures `.env`
- **🧪 Testing Built-In** — Pytest fixtures and property-based tests with Hypothesis
- **📝 Auto Documentation** — Swagger UI and ReDoc included automatically

### 📊 Topological Sorting & Dependency Management
- **Intelligent Resource Ordering** — Automatically sorts resources based on their dependencies using Kahn's algorithm
- **Circular Dependency Detection** — Prevents invalid dependency chains before they cause issues
- **Cascade Delete** — Automatically removes dependent resources when a parent is deleted
- **Dependency Validation** — Validates that all resource dependencies exist before creation

### 📈 OpenTelemetry Observability (OTEL)

Full observability stack with **metrics**, **logs**, and **traces**:

**Metrics:**
- CRUD operation duration histograms
- Operation success/failure counters
- Resource count tracking
- Cascade delete metrics

**Structured Logging:**
- JSON-formatted logs with trace correlation
- Automatic trace ID and span ID injection
- Operation-specific logging (create, read, update, delete, search)
- Validation error and circular dependency logging

**Distributed Tracing:**
- Full request tracing across services
- Span context propagation
- Trace sampling configuration

### 📊 Dashboard Integration

Pre-configured observability stack:

- **Grafana Dashboard** — Ready-to-import dashboard for CRUD metrics visualization
- **Prometheus** — Metrics collection and alerting rules
- **OpenTelemetry Collector** — Unified telemetry collection pipeline
- **One-command setup** — `./start_local_observability.sh` to spin up the entire stack

---

## 🚀 Quick Start

### Install

```bash
pip install fastapi-crud-cli
```

Or with pipx for isolated installation:

```bash
pipx install fastapi-crud-cli
```

### Create a Project

```bash
fastapi-crud create
```

Follow the interactive prompts to configure your project. The CLI will:

1. ✓ Generate a complete project structure
2. ✓ Create a virtual environment
3. ✓ Install all dependencies
4. ✓ Configure your `.env` file

### Run Your API

```bash
cd your-project-name
source venv/bin/activate   # Windows: venv\Scripts\activate
python main.py
```

Visit `http://localhost:8000/docs` to see your API documentation!

---

## 🗄️ Supported Databases

| Database | Best For | Key Features |
|----------|----------|--------------|
| **SQLite** | Development, prototyping | Zero config, file-based, no server needed |
| **MongoDB** | Flexible schemas, scaling | Document store, async Motor driver, cloud-ready |
| **PostgreSQL** | Production, complex queries | Full SQL, ACID compliant, JSON support |

```bash
# Get info about a specific database
fastapi-crud info mongodb

# List all available options
fastapi-crud list
```

---

## 📁 Generated Project Structure

```
your-project/
├── app/
│   ├── models/           # Database models
│   ├── repositories/     # Data access layer
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic & topological sorting
│   ├── observability/    # OTEL metrics, logs, traces
│   ├── database_factory.py
│   ├── exceptions.py
│   ├── error_handlers.py
│   └── schemas.py
├── config/
│   └── settings.py       # Configuration management
├── tests/
│   ├── conftest.py       # Test fixtures
│   └── test_*.py         # Test suite
├── observability/        # Grafana, Prometheus, OTEL configs
│   ├── grafana-dashboard.json
│   ├── prometheus.yml
│   ├── otel-collector-config.yaml
│   └── start_local_observability.sh
├── venv/                 # Virtual environment (auto-created)
├── .env                  # Environment config (auto-generated)
├── requirements.txt
├── main.py
└── README.md
```

---

## 📡 Generated API Endpoints

Every project includes a complete RESTful API:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/resources` | Create a new resource |
| `GET` | `/resources` | List all resources |
| `GET` | `/resources/{id}` | Get a specific resource |
| `PUT` | `/resources/{id}` | Update a resource |
| `DELETE` | `/resources/{id}` | Delete a resource (with cascade) |
| `GET` | `/resources/search?q=` | Search resources |
| `GET` | `/resources/sorted` | Get resources in topological order |

---

## 🔄 Topological Sorting

Resources can have dependencies on other resources. The topological sort feature ensures:

```
Resource A (no dependencies)
    ↓
Resource B (depends on A)
    ↓
Resource C (depends on A and B)
```

**Key capabilities:**

- **Kahn's Algorithm** — Efficient O(V+E) topological ordering
- **Cycle Detection** — Identifies and reports circular dependencies with full cycle path
- **Dependency Validation** — Prevents creation of resources with invalid dependencies
- **Cascade Deletion** — Removes all dependent resources when a parent is deleted

**Example API response for `/resources/sorted`:**
```json
[
  {"id": "database", "name": "PostgreSQL", "dependencies": []},
  {"id": "backend", "name": "FastAPI", "dependencies": ["database"]},
  {"id": "frontend", "name": "React", "dependencies": ["backend"]}
]
```

---

## 📊 OpenTelemetry Integration

### Metrics

All CRUD operations are instrumented with OpenTelemetry metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `crud.operation.duration` | Histogram | Operation latency in milliseconds |
| `crud.operation.count` | Counter | Total operations by type and status |
| `crud.operation.errors` | Counter | Failed operations by error type |
| `crud.resources.total` | UpDownCounter | Current resource count |
| `crud.cascade.delete.count` | Histogram | Resources deleted in cascade operations |

### Structured Logging

JSON-formatted logs with automatic trace correlation:

```json
{
  "timestamp": "2024-12-05T10:30:00.000Z",
  "level": "INFO",
  "message": "Completed create operation in 45.23ms",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "operation_type": "create",
  "resource_id": "res_001",
  "duration_ms": 45.23,
  "status": "success"
}
```

### Distributed Tracing

Full request tracing with configurable sampling:

- Trace context propagation across services
- Span attributes for operation details
- Integration with Jaeger, Zipkin, or any OTLP-compatible backend

---

## 📈 Grafana Dashboard

The generated project includes a pre-built Grafana dashboard with:

- **Operation Rate** — Requests per second by operation type
- **Latency Percentiles** — p50, p90, p99 response times
- **Error Rate** — Failed operations over time
- **Resource Count** — Current number of resources
- **Cascade Deletes** — Cascade operation statistics
- **Database Performance** — Backend-specific metrics

### Quick Start for Local Observability

```bash
cd your-project/observability

# Start Grafana, Prometheus, and OTEL Collector
./start_local_observability.sh

# Access Grafana at http://localhost:3000
# Default credentials: admin/admin
```

---

## 🛠️ CLI Commands

```bash
fastapi-crud create      # Create a new project (interactive)
fastapi-crud list        # List available database backends
fastapi-crud info <db>   # Get details about a database
fastapi-crud --version   # Show version
fastapi-crud --help      # Show help
```

---

## ⚙️ Configuration

The CLI collects all settings during project creation and saves them to `.env`:

```bash
# Application Settings
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Database Settings
DATABASE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=my_database

# OpenTelemetry Settings
OTEL_ENABLED=true
OTEL_SERVICE_NAME=my-awesome-api
OTEL_OTLP_ENDPOINT=http://localhost:4317
OTEL_TRACES_SAMPLE_RATE=1.0
OTEL_METRICS_EXPORT_INTERVAL_MS=60000
```

---

## 🧪 Testing

Generated projects include comprehensive tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run property-based tests
pytest tests/test_property_*.py
```

**Test coverage includes:**
- Topological sort algorithm correctness
- Circular dependency detection
- Cascade delete behavior
- CRUD operation consistency
- API endpoint integration tests

---

## 🔧 Optional Development Tools

Enable during project creation:

- **Black** — Code formatting
- **Ruff** — Fast linting
- **MyPy** — Static type checking
- **Pre-commit** — Git hooks
- **Hypothesis** — Property-based testing

---

## 📋 Requirements

- Python 3.10 or higher
- pip or pipx

---

## 🏛️ Architecture

Generated projects follow a clean layered architecture:

```
API Layer (Routers)
    ↓
Service Layer (Business Logic + Topological Sort)
    ↓
Repository Layer (Data Access)
    ↓
Database (SQLite / MongoDB / PostgreSQL)
    ↓
Observability (Metrics / Logs / Traces → OTEL Collector → Grafana)
```

This separation ensures:
- **Testability** — Each layer can be tested independently
- **Flexibility** — Swap databases without changing business logic
- **Observability** — Full visibility into application behavior
- **Maintainability** — Clear boundaries between concerns

---

## 💡 Common Issues

**Command not found after installation?**

```bash
# Use pipx for isolated installation
pipx install fastapi-crud-cli

# Or ensure pip scripts are in PATH
python -m pip install --user fastapi-crud-cli
```

**Virtual environment creation fails?**

```bash
cd your-project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome! Please see the CONTRIBUTING.md file in the repository for guidelines.

---

## 📄 License

MIT License

---

## 🔗 Links

- **Source Code**: [GitHub Repository](https://github.com/yourusername/fastapi-crud-cli)
- **Issue Tracker**: [GitHub Issues](https://github.com/yourusername/fastapi-crud-cli/issues)
- **Changelog**: [CHANGELOG.md](https://github.com/yourusername/fastapi-crud-cli/blob/main/CHANGELOG.md)

---

**Built with ❤️ using FastAPI, Click, Rich, Jinja2, and OpenTelemetry**
