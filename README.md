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

## Running the Application

### Option 1: Using the startup script

```bash
./run.sh
```

### Option 2: Using Python directly

```bash
python main.py
```

### Option 3: Using Uvicorn directly

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at:
- **API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Resources

- `POST /api/resources` - Create a new resource
- `GET /api/resources` - List all resources
- `GET /api/resources/{id}` - Get a specific resource
- `PUT /api/resources/{id}` - Update a resource
- `DELETE /api/resources/{id}?cascade=true` - Delete a resource (with optional cascade)
- `GET /api/search?q=query` - Search resources with topological sorting

### System

- `GET /` - API information
- `GET /health` - Health check endpoint

## Testing

Run all tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_api_endpoints.py -v
```

Run property-based tests only:

```bash
pytest tests/test_property_*.py -v
```

### MongoDB Testing

Some property-based tests require MongoDB to be running. If MongoDB is not available, these tests will be automatically skipped.

To run MongoDB tests, ensure MongoDB is running locally:

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Or install MongoDB locally and start the service
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

Set the test database environment variable:

```bash
export MONGODB_DATABASE=fastapi_crud_test
```

Then run the tests:

```bash
pytest tests/test_property_mongodb_*.py -v
```
