# FastAPI CRUD Backend

A RESTful API backend with topological sorting capabilities for managing resources with dependencies.

## Project Structure

```
.
├── app/
│   ├── models/          # SQLAlchemy database models
│   ├── repositories/    # Data access layer
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── static/              # Frontend HTML/CSS/JS files
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── venv/               # Virtual environment
```

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **Pytest**: Testing framework
- **Hypothesis**: Property-based testing library
- **HTTPx**: HTTP client for testing

## Development

The virtual environment has been set up and all dependencies are installed. You can now proceed with implementing the application components.

## Testing

Run tests with:

```bash
pytest
```

Run property-based tests with:

```bash
pytest -v tests/
```
