# FastAPI CRUD Backend

A RESTful API backend with topological sorting capabilities for managing resources with dependencies. Supports both SQLite and MongoDB as database backends.

## Features

- 🚀 RESTful API with FastAPI
- 🔄 Topological sorting for dependency management
- 💾 Dual database backend support (SQLite and MongoDB)
- ✅ Comprehensive test suite with property-based testing
- 📊 Automatic API documentation (Swagger/ReDoc)
- 🔍 Resource search capabilities
- 🔗 Cascade delete for dependent resources

## Project Structure

```
.
├── app/
│   ├── models/          # Database models (SQLAlchemy)
│   ├── repositories/    # Data access layer (abstract + implementations)
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── database_factory.py      # Database backend selection
│   ├── database_sqlalchemy.py   # SQLite/SQLAlchemy connection
│   ├── database_mongodb.py      # MongoDB connection
│   ├── exceptions.py            # Custom exceptions
│   └── error_handlers.py        # Error handling
├── scripts/             # Utility scripts (migration, etc.)
├── static/              # Frontend HTML/CSS/JS files
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── venv/               # Virtual environment
```

## Quick Start

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

### 4. Configure Database Backend

Copy the example environment file and configure your database:

```bash
cp .env.example .env
```

Edit `.env` to choose your database backend (see [Database Configuration](#database-configuration) below).

## Database Configuration

The application supports two database backends: **SQLite** (default) and **MongoDB**. Choose the backend that best fits your deployment needs.

### SQLite Configuration (Default)

SQLite is the default backend, ideal for development and small deployments:

```bash
# .env file
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./app.db
```

**Advantages:**
- Zero configuration required
- File-based, no separate server needed
- Perfect for development and testing
- Included in Python standard library

### MongoDB Configuration

MongoDB is recommended for production deployments requiring scalability:

#### Local MongoDB

```bash
# .env file
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud
```

#### MongoDB Atlas (Cloud)

```bash
# .env file
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=fastapi_crud
```

#### MongoDB with Authentication

```bash
# .env file
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_AUTH_SOURCE=admin
```

### MongoDB Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_TYPE` | Database backend type (`sqlite` or `mongodb`) | Yes | `sqlite` |
| `DATABASE_URL` | Database connection URL | Yes | `sqlite:///./app.db` |
| `MONGODB_DATABASE` | MongoDB database name | Yes (for MongoDB) | - |
| `MONGODB_USERNAME` | MongoDB username | No | - |
| `MONGODB_PASSWORD` | MongoDB password | No | - |
| `MONGODB_AUTH_SOURCE` | Authentication database | No | `admin` |
| `MONGODB_TIMEOUT` | Connection timeout (milliseconds) | No | `5000` |

### Setting Up MongoDB

#### Option 1: Install MongoDB Locally (macOS)

```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Verify it's running
mongosh --eval "db.version()"
```

#### Option 2: Install MongoDB Locally (Linux)

```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option 3: Use Docker

```bash
# Pull and run MongoDB container
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Verify it's running
docker ps | grep mongodb

# Stop MongoDB
docker stop mongodb

# Start MongoDB again
docker start mongodb
```

#### Option 4: Use MongoDB Atlas (Cloud)

1. Sign up for a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier available)
3. Create a database user with read/write permissions
4. Whitelist your IP address or use `0.0.0.0/0` for development
5. Get your connection string from the "Connect" button
6. Update your `.env` file with the connection string

### Docker Compose Setup

For a complete development environment with MongoDB:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_TYPE=mongodb
      - DATABASE_URL=mongodb://mongodb:27017
      - MONGODB_DATABASE=fastapi_crud
    depends_on:
      - mongodb
    volumes:
      - .:/app

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=fastapi_crud

volumes:
  mongodb_data:
```

Run with:

```bash
docker-compose up -d
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **SQLAlchemy**: SQL toolkit and ORM (for SQLite backend)
- **Motor**: Async MongoDB driver (for MongoDB backend)
- **PyMongo**: MongoDB driver (Motor dependency)
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

#### Create Resource
```http
POST /api/resources
Content-Type: application/json

{
  "name": "Frontend App",
  "description": "React frontend application",
  "dependencies": ["backend-api-id", "database-id"]
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Frontend App",
  "description": "React frontend application",
  "dependencies": ["backend-api-id", "database-id"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### List All Resources
```http
GET /api/resources
```

**Response (200 OK):**
```json
[
  {
    "id": "database-id",
    "name": "PostgreSQL Database",
    "description": "Main application database",
    "dependencies": [],
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  },
  {
    "id": "backend-api-id",
    "name": "Backend API",
    "description": "FastAPI backend service",
    "dependencies": ["database-id"],
    "created_at": "2024-01-15T10:15:00Z",
    "updated_at": "2024-01-15T10:15:00Z"
  }
]
```

#### Get Single Resource
```http
GET /api/resources/{id}
```

**Response (200 OK):**
```json
{
  "id": "backend-api-id",
  "name": "Backend API",
  "description": "FastAPI backend service",
  "dependencies": ["database-id"],
  "created_at": "2024-01-15T10:15:00Z",
  "updated_at": "2024-01-15T10:15:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "ResourceNotFound",
  "message": "Resource with id 'invalid-id' not found",
  "details": {}
}
```

#### Update Resource
```http
PUT /api/resources/{id}
Content-Type: application/json

{
  "name": "Backend API v2",
  "description": "Updated FastAPI backend service",
  "dependencies": ["database-id", "cache-id"]
}
```

**Response (200 OK):**
```json
{
  "id": "backend-api-id",
  "name": "Backend API v2",
  "description": "Updated FastAPI backend service",
  "dependencies": ["database-id", "cache-id"],
  "created_at": "2024-01-15T10:15:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### Delete Resource
```http
DELETE /api/resources/{id}?cascade=false
```

**Response (204 No Content)**

Query Parameters:
- `cascade` (boolean, default: false): If true, deletes all resources that depend on this resource

**Examples:**
- `DELETE /api/resources/{id}?cascade=false` - Delete only this resource
- `DELETE /api/resources/{id}?cascade=true` - Delete this resource and all dependents

#### Search Resources (Topological Sort)
```http
GET /api/search?q=api
```

**Response (200 OK):**
```json
[
  {
    "id": "database-id",
    "name": "PostgreSQL Database",
    "description": "Main application database",
    "dependencies": [],
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  },
  {
    "id": "backend-api-id",
    "name": "Backend API",
    "description": "FastAPI backend service",
    "dependencies": ["database-id"],
    "created_at": "2024-01-15T10:15:00Z",
    "updated_at": "2024-01-15T10:15:00Z"
  },
  {
    "id": "frontend-id",
    "name": "Frontend App",
    "description": "React frontend application",
    "dependencies": ["backend-api-id"],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**Note:** Results are always returned in topological order, with dependencies appearing before dependents.

**Error Response (422 Unprocessable Entity) - Circular Dependency:**
```json
{
  "error": "CircularDependencyError",
  "message": "Circular dependency detected: A → B → C → A",
  "details": {
    "cycle": ["A", "B", "C", "A"]
  }
}
```

### System Endpoints

#### API Information
```http
GET /
```

**Response (200 OK):**
```json
{
  "message": "FastAPI CRUD Backend API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### Health Check
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "fastapi-crud-backend"
}
```

## Testing

The project includes a comprehensive test suite with both unit tests and property-based tests using Hypothesis.

### Running All Tests

```bash
pytest
```

### Running Tests with Verbose Output

```bash
pytest -v
```

### Running Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Running Specific Test Categories

**Run only unit tests:**
```bash
pytest tests/test_api_endpoints.py tests/test_resource_service.py tests/test_schemas.py -v
```

**Run only property-based tests:**
```bash
pytest tests/test_property_*.py -v
```

**Run specific property test:**
```bash
pytest tests/test_property_crud_roundtrip.py -v
```

**Run tests matching a pattern:**
```bash
pytest -k "crud" -v  # Runs all tests with "crud" in the name
pytest -k "property" -v  # Runs all property-based tests
```

### Test Categories

The test suite is organized into several categories:

1. **Unit Tests** (`test_*.py`):
   - `test_api_endpoints.py` - API endpoint integration tests
   - `test_resource_service.py` - Business logic tests
   - `test_resource_repository.py` - Data access layer tests
   - `test_schemas.py` - Pydantic schema validation tests
   - `test_topological_sort_service.py` - Topological sort algorithm tests
   - `test_database_factory.py` - Database factory tests
   - `test_database_models.py` - Database model tests

2. **Property-Based Tests** (`test_property_*.py`):
   - `test_property_crud_roundtrip.py` - Create/read round-trip properties
   - `test_property_cascade_delete.py` - Cascade delete behavior
   - `test_property_invalid_data_rejection.py` - Input validation
   - `test_property_http_status_codes.py` - HTTP status code correctness
   - `test_property_error_response_consistency.py` - Error format consistency
   - `test_property_update_persistence.py` - Update persistence
   - `test_property_delete_functionality.py` - Delete operations
   - `test_property_create_form_submission.py` - Frontend form submission
   - `test_property_resource_display.py` - Frontend display completeness
   - `test_property_search_display.py` - Search and topological sort
   - And more...

### Property-Based Testing

Property-based tests use Hypothesis to generate random test data and verify that properties hold across all inputs. Each test runs 100 iterations by default.

**Example property test output:**
```
tests/test_property_crud_roundtrip.py::test_resource_creation_roundtrip PASSED
  Hypothesis: 100 examples generated
```

**When a property test fails:**
```
tests/test_property_crud_roundtrip.py::test_resource_creation_roundtrip FAILED
  Falsifying example: test_resource_creation_roundtrip(
    resource_data={'name': 'A', 'description': '', 'dependencies': []}
  )
```

Hypothesis automatically finds the minimal failing example and saves it for regression testing.

### MongoDB Testing

Some property-based tests require MongoDB to be running. If MongoDB is not available, these tests will be automatically skipped.

**Setup MongoDB for testing:**

```bash
# Option 1: Using Docker
docker run -d -p 27017:27017 --name mongodb-test mongo:7.0

# Option 2: Using local MongoDB
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

**Set test database environment variable:**
```bash
export MONGODB_DATABASE=fastapi_crud_test
```

**Run MongoDB-specific tests:**
```bash
pytest tests/test_property_mongodb_*.py -v
```

**Run all tests including MongoDB tests:**
```bash
# Ensure MongoDB is running first
pytest -v
```

### Test Configuration

Test configuration is defined in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### Continuous Integration

For CI/CD pipelines, you can run tests with specific options:

```bash
# Run tests with JUnit XML output for CI systems
pytest --junitxml=test-results.xml

# Run tests with coverage and fail if coverage is below threshold
pytest --cov=app --cov-fail-under=80

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Debugging Tests

**Run tests with print statements visible:**
```bash
pytest -s
```

**Run tests with detailed output:**
```bash
pytest -vv
```

**Run tests and drop into debugger on failure:**
```bash
pytest --pdb
```

**Run only failed tests from last run:**
```bash
pytest --lf
```

**Run failed tests first, then others:**
```bash
pytest --ff
```

### Writing New Tests

When adding new functionality, follow these guidelines:

1. **Write unit tests** for specific examples and edge cases
2. **Write property tests** for universal properties that should hold across all inputs
3. **Tag property tests** with the design document property they validate:
   ```python
   # Feature: fastapi-crud-backend, Property 1: Resource creation round-trip
   @given(resource_data=resource_strategy())
   async def test_resource_creation_roundtrip(resource_data):
       # Test implementation
   ```

4. **Use appropriate test fixtures** from `conftest.py`
5. **Follow the existing test structure** for consistency

### Test Fixtures

Common fixtures available in `conftest.py`:

- `db_session` - Database session for tests
- `client` - FastAPI test client
- `sample_resource` - Pre-created sample resource
- `resource_strategy()` - Hypothesis strategy for generating resources
- `dependency_graph_strategy()` - Strategy for generating dependency graphs

## Migrating from SQLite to MongoDB

If you have existing data in SQLite and want to migrate to MongoDB, use the provided migration script.

### Quick Migration

```bash
# Ensure MongoDB is running
brew services start mongodb-community  # macOS
# or
docker start mongodb  # Docker

# Run migration with validation
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing
```

### Migration Options

The migration script supports several modes:

#### 1. Full Migration with Validation

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing
```

#### 2. Export SQLite Data to JSON

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --export-only \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --output backup.json
```

#### 3. Import JSON to MongoDB

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --import-only \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --input backup.json \
  --clear-existing
```

### Migration Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sqlite-url` | SQLite database URL | `sqlite+aiosqlite:///./app.db` |
| `--mongodb-url` | MongoDB connection URL | `mongodb://localhost:27017` |
| `--mongodb-db` | MongoDB database name | `fastapi_crud` |
| `--output` | Output JSON file for export | `resources_export.json` |
| `--input` | Input JSON file for import | `resources_export.json` |
| `--clear-existing` | Clear existing MongoDB data before import | `False` |
| `--validate` | Validate data integrity after migration | `True` |
| `--no-validate` | Skip validation after migration | `False` |
| `--export-only` | Only export SQLite data to JSON | `False` |
| `--import-only` | Only import JSON to MongoDB | `False` |

### Post-Migration Steps

After successful migration:

1. **Update your `.env` file:**
   ```bash
   DATABASE_TYPE=mongodb
   DATABASE_URL=mongodb://localhost:27017
   MONGODB_DATABASE=fastapi_crud
   ```

2. **Restart the application:**
   ```bash
   python main.py
   ```

3. **Verify the migration:**
   - Check the API documentation: http://localhost:8000/docs
   - Test resource retrieval: `GET /api/resources`
   - Verify resource counts match

For detailed migration documentation, see [scripts/README_MIGRATION.md](scripts/README_MIGRATION.md).

## Example Usage Scenarios

### Scenario 1: Building a Microservices Deployment Pipeline

Imagine you're managing a microservices architecture where services depend on each other. You can use this system to model and manage deployment order.

**Step 1: Create the database resource**
```bash
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PostgreSQL Database",
    "description": "Main application database",
    "dependencies": []
  }'
```

**Step 2: Create the backend API that depends on the database**
```bash
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Backend API",
    "description": "FastAPI backend service",
    "dependencies": ["<database-id>"]
  }'
```

**Step 3: Create the frontend that depends on the backend**
```bash
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Frontend App",
    "description": "React frontend application",
    "dependencies": ["<backend-api-id>"]
  }'
```

**Step 4: Get deployment order using topological sort**
```bash
curl http://localhost:8000/api/search
```

This returns resources in the correct deployment order: Database → Backend API → Frontend App

### Scenario 2: Managing Build Dependencies

Track build dependencies for a complex project with multiple components.

**Create build targets:**
```bash
# Create compiler
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Compiler", "description": "C++ compiler", "dependencies": []}'

# Create standard library (depends on compiler)
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Standard Library", "description": "C++ standard library", "dependencies": ["<compiler-id>"]}'

# Create application (depends on standard library)
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Application", "description": "Main application", "dependencies": ["<stdlib-id>"]}'
```

**Get build order:**
```bash
curl http://localhost:8000/api/search
```

### Scenario 3: Handling Circular Dependencies

The system automatically detects and prevents circular dependencies.

**Attempt to create a circular dependency:**
```bash
# Create Resource A
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Resource A", "dependencies": []}'

# Create Resource B depending on A
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Resource B", "dependencies": ["<resource-a-id>"]}'

# Try to update Resource A to depend on B (creates a cycle)
curl -X PUT http://localhost:8000/api/resources/<resource-a-id> \
  -H "Content-Type: application/json" \
  -d '{"name": "Resource A", "dependencies": ["<resource-b-id>"]}'
```

**Response (422 Unprocessable Entity):**
```json
{
  "error": "CircularDependencyError",
  "message": "Circular dependency detected: Resource A → Resource B → Resource A",
  "details": {
    "cycle": ["Resource A", "Resource B", "Resource A"]
  }
}
```

### Scenario 4: Cascade Delete

Remove a resource and all its dependents in one operation.

**Setup:**
```bash
# Create: Database → API → Frontend → Mobile App
# Database has no dependencies
# API depends on Database
# Frontend depends on API
# Mobile App depends on API
```

**Delete with cascade:**
```bash
# Delete the API and everything that depends on it
curl -X DELETE "http://localhost:8000/api/resources/<api-id>?cascade=true"
```

This removes: API, Frontend, and Mobile App (but keeps Database)

**Delete without cascade:**
```bash
# Delete only the API
curl -X DELETE "http://localhost:8000/api/resources/<api-id>?cascade=false"
```

This removes only the API and updates Frontend and Mobile App to remove the dependency.

### Scenario 5: Searching and Filtering

Search for specific resources while maintaining topological order.

**Search for all resources containing "api":**
```bash
curl "http://localhost:8000/api/search?q=api"
```

**Get all resources in topological order:**
```bash
curl http://localhost:8000/api/search
```

### Scenario 6: Using the Web Interface

1. **Open the web interface:**
   - Navigate to http://localhost:8000/static/index.html

2. **Create resources:**
   - Click "Add Resource" button
   - Fill in name, description, and select dependencies
   - Submit the form

3. **View dependency visualization:**
   - Resources are displayed with visual indicators showing dependencies
   - Dependencies are shown as badges or arrows

4. **Search with topological sort:**
   - Type in the search bar
   - Results automatically update in dependency order

5. **Update resources:**
   - Click "Edit" on any resource
   - Modify fields and dependencies
   - Save changes

6. **Delete resources:**
   - Click "Delete" on any resource
   - Choose whether to cascade delete
   - Confirm deletion

### Scenario 7: Python Client Example

```python
import httpx
import asyncio

async def main():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Create a resource
        response = await client.post(
            f"{base_url}/api/resources",
            json={
                "name": "My Resource",
                "description": "A test resource",
                "dependencies": []
            }
        )
        resource = response.json()
        print(f"Created resource: {resource['id']}")
        
        # Get all resources
        response = await client.get(f"{base_url}/api/resources")
        resources = response.json()
        print(f"Total resources: {len(resources)}")
        
        # Search with topological sort
        response = await client.get(f"{base_url}/api/search?q=test")
        results = response.json()
        print(f"Search results: {len(results)}")
        
        # Update resource
        response = await client.put(
            f"{base_url}/api/resources/{resource['id']}",
            json={
                "name": "Updated Resource",
                "description": "Updated description"
            }
        )
        updated = response.json()
        print(f"Updated: {updated['name']}")
        
        # Delete resource
        response = await client.delete(
            f"{base_url}/api/resources/{resource['id']}"
        )
        print(f"Deleted: {response.status_code == 204}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Scenario 8: JavaScript/Frontend Example

```javascript
// API client functions
const API_BASE = 'http://localhost:8000/api';

async function createResource(name, description, dependencies = []) {
  const response = await fetch(`${API_BASE}/resources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description, dependencies })
  });
  return response.json();
}

async function getAllResources() {
  const response = await fetch(`${API_BASE}/resources`);
  return response.json();
}

async function searchResources(query) {
  const url = query 
    ? `${API_BASE}/search?q=${encodeURIComponent(query)}`
    : `${API_BASE}/search`;
  const response = await fetch(url);
  return response.json();
}

async function updateResource(id, data) {
  const response = await fetch(`${API_BASE}/resources/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return response.json();
}

async function deleteResource(id, cascade = false) {
  const response = await fetch(
    `${API_BASE}/resources/${id}?cascade=${cascade}`,
    { method: 'DELETE' }
  );
  return response.status === 204;
}

// Example usage
async function example() {
  // Create resources
  const db = await createResource('Database', 'PostgreSQL database', []);
  const api = await createResource('API', 'Backend API', [db.id]);
  const frontend = await createResource('Frontend', 'React app', [api.id]);
  
  // Get topological order
  const sorted = await searchResources();
  console.log('Deployment order:', sorted.map(r => r.name));
  
  // Update a resource
  await updateResource(api.id, {
    name: 'API v2',
    description: 'Updated backend API'
  });
  
  // Delete with cascade
  await deleteResource(api.id, true); // Deletes API and Frontend
}
```

## Troubleshooting

### MongoDB Connection Issues

**Problem:** `Failed to connect to MongoDB`

**Solutions:**
- Verify MongoDB is running: `mongosh --eval "db.version()"`
- Check the connection URL in your `.env` file
- Ensure MongoDB is listening on the correct port (default: 27017)
- Check firewall settings
- For MongoDB Atlas, verify IP whitelist settings

**Problem:** `Authentication failed`

**Solutions:**
- Verify username and password are correct
- Check `MONGODB_AUTH_SOURCE` is set correctly (usually `admin`)
- Ensure the user has read/write permissions on the database
- For MongoDB Atlas, verify database user is created in the Atlas UI

### MongoDB Performance Issues

**Problem:** Slow queries or timeouts

**Solutions:**
- Increase `MONGODB_TIMEOUT` in your `.env` file
- Check MongoDB indexes are created: `mongosh fastapi_crud --eval "db.resources.getIndexes()"`
- Monitor MongoDB performance: `mongosh --eval "db.serverStatus()"`
- For large datasets, consider adding more indexes

### Migration Issues

**Problem:** Migration validation fails

**Solutions:**
- Ensure both SQLite and MongoDB are accessible during migration
- Check that no other processes are modifying the databases
- Review validation error messages for specific issues
- Try re-running the migration with `--clear-existing`

**Problem:** Duplicate key errors during migration

**Solutions:**
- Use `--clear-existing` flag to remove existing data before import
- Or manually clear the MongoDB collection:
  ```bash
  mongosh fastapi_crud --eval "db.resources.deleteMany({})"
  ```

### Application Startup Issues

**Problem:** Application fails to start with MongoDB

**Solutions:**
- Check all required environment variables are set
- Verify MongoDB connection string format
- Check application logs for detailed error messages
- Test MongoDB connection manually: `mongosh <your-connection-url>`

**Problem:** Tests are skipped

**Solutions:**
- Ensure MongoDB is running for MongoDB tests
- Set `MONGODB_DATABASE` environment variable for tests
- Check test output for skip reasons

### Data Consistency Issues

**Problem:** Data appears different between SQLite and MongoDB

**Solutions:**
- Run migration validation: use `--validate` flag
- Check that timestamps are in UTC
- Verify dependency relationships are preserved
- Compare resource counts: SQLite vs MongoDB

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ServerSelectionTimeoutError` | MongoDB not reachable | Start MongoDB service |
| `OperationFailure: Authentication failed` | Invalid credentials | Check username/password |
| `ConfigurationError: Invalid URI` | Malformed connection string | Verify DATABASE_URL format |
| `DuplicateKeyError` | Resource ID already exists | Use `--clear-existing` or check for duplicates |
| `NetworkTimeout` | Network issues or slow connection | Increase MONGODB_TIMEOUT |

### Getting Help

If you encounter issues not covered here:

1. Check the application logs in `app.log`
2. Review MongoDB logs: `mongosh --eval "db.adminCommand({ getLog: 'global' })"`
3. Verify your configuration matches the examples in `.env.example`
4. Check the [MongoDB documentation](https://docs.mongodb.com/)
5. Review the spec documents in `.kiro/specs/mongodb-integration/`

### Debug Mode

Enable debug logging for more detailed information:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Run application
python main.py
```

## Additional Resources

- **MongoDB Setup Guide**: [MONGODB_SETUP.md](MONGODB_SETUP.md)
- **Migration Guide**: [scripts/README_MIGRATION.md](scripts/README_MIGRATION.md)
- **Testing Guide**: [tests/README_TESTING.md](tests/README_TESTING.md)
- **Requirements Document**: [.kiro/specs/mongodb-integration/requirements.md](.kiro/specs/mongodb-integration/requirements.md)
- **Design Document**: [.kiro/specs/mongodb-integration/design.md](.kiro/specs/mongodb-integration/design.md)
