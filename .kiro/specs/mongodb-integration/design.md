# Design Document: MongoDB Integration

## Overview

This design adds MongoDB as an alternative database backend to the existing FastAPI CRUD application. The system currently uses SQLite with SQLAlchemy ORM for data persistence. This feature introduces a pluggable database architecture that allows users to choose between SQLite (via SQLAlchemy) and MongoDB (via Motor) at application startup through configuration.

The design maintains the existing API contracts and business logic while abstracting database-specific operations behind a common repository interface. This ensures that services (e.g., `ResourceService`), routers (e.g., `resources.py`), and API endpoints remain unchanged regardless of the database backend. These components are intentionally generic and database-agnostic.

## Architecture

### High-Level Architecture

The application follows a layered architecture:

```
API Layer (FastAPI Routers)
         ↓
Service Layer (Business Logic)
         ↓
Repository Layer (Data Access) ← **Abstraction Point**
         ↓
Database Layer (SQLite or MongoDB)
```

### Database Backend Selection

The database backend is selected at application startup based on an environment variable:

- `DATABASE_TYPE`: Either "sqlite" or "mongodb" (default: "sqlite")
- `DATABASE_URL`: Connection string for the selected database

### Configuration Examples

**SQLite:**
```
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

**MongoDB:**
```
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud  # MongoDB-specific: database name
```

## Components and Interfaces

### Naming Convention Summary

| Component Type | Generic (Backend-Agnostic) | SQLite-Specific | MongoDB-Specific |
|----------------|---------------------------|-----------------|------------------|
| **Database Connection** | `database_factory.py` | `database_sqlalchemy.py` | `database_mongodb.py` |
| **Repository Interface** | `base_resource_repository.py` | - | - |
| **Repository Implementation** | - | `sqlalchemy_resource_repository.py` | `mongodb_resource_repository.py` |
| **Data Models** | `schemas.py` (Pydantic) | `sqlalchemy_resource.py` (ORM) | (dictionaries, no file) |
| **Services** | `resource_service.py` | - | - |
| **Routers** | `resources.py` | - | - |
| **Test Database** | - | `:memory:` | `fastapi_crud_test_mongodb` |

### 1. Database Factory

A new `DatabaseFactory` class will instantiate the appropriate database connection and repository based on configuration.

**Location:** `app/database_factory.py`

**Responsibilities:**
- Read database configuration from environment variables
- Initialize the appropriate database connection (SQLAlchemy or Motor)
- Provide dependency injection functions for repositories
- Handle graceful shutdown of database connections

### 2. Abstract Repository Interface

Define an abstract base class that both SQLAlchemy and MongoDB repositories implement.

**Location:** `app/repositories/base_resource_repository.py`

**Class Name:** `BaseResourceRepository` (abstract base class)

**Interface Methods:**
- `get_all() -> List[Resource]`
- `get_by_id(resource_id: str) -> Optional[Resource]`
- `create(data: ResourceCreate) -> Resource`
- `update(resource_id: str, data: ResourceUpdate) -> Optional[Resource]`
- `delete(resource_id: str, cascade: bool) -> bool`
- `search(query: Optional[str]) -> List[Resource]`

### 3. MongoDB Repository Implementation

A new repository implementation using Motor (async MongoDB driver).

**Location:** `app/repositories/mongodb_resource_repository.py`

**Class Name:** `MongoDBResourceRepository` (implements `BaseResourceRepository`)

**Key Design Decisions:**
- Use Motor's `AsyncIOMotorClient` for async operations
- Store resources in a `resources` collection
- Use MongoDB's `_id` field but expose it as `id` in the application
- Store dependencies as an array of resource IDs within each document
- Implement cascade delete by recursively finding and deleting dependents

**Document Schema:**
```python
{
    "_id": "uuid-string",  # Mapped to 'id' in application
    "name": "Resource Name",
    "description": "Description text",
    "dependencies": ["dep-id-1", "dep-id-2"],  # Array of resource IDs
    "created_at": ISODate("2024-01-01T00:00:00Z"),
    "updated_at": ISODate("2024-01-01T00:00:00Z")
}
```

### 4. Refactored SQLAlchemy Repository

The existing `ResourceRepository` will be renamed to `SQLAlchemyResourceRepository` and will implement the abstract repository interface.

**Location:** `app/repositories/sqlalchemy_resource_repository.py`

**Class Name:** `SQLAlchemyResourceRepository` (implements `BaseResourceRepository`)

### 5. Database Connection Management

**SQLAlchemy Connection (existing):**
- Currently managed by `app/database.py` (will be refactored to `app/database_sqlalchemy.py` for clarity)
- Uses `AsyncSession` with session factory
- Dependency injection via `get_sqlalchemy_db()`

**MongoDB Connection (new):**
- Managed by `app/database_mongodb.py`
- Uses Motor's `AsyncIOMotorClient`
- Single client instance shared across requests
- Dependency injection via `get_mongodb_db()`

**Unified Database Access:**
- `app/database_factory.py` provides a unified `get_db()` function that returns the appropriate database session/client based on the `DATABASE_TYPE` configuration
- This allows the rest of the application to use a single `get_db()` dependency without knowing which backend is active

### 6. Data Model Mapping

**SQLAlchemy Model (existing):**
- `app/models/resource.py` will be refactored to `app/models/sqlalchemy_resource.py` for clarity
- Contains SQLAlchemy ORM model definition
- Used only by SQLAlchemy backend

**MongoDB Document Model (new):**
- No ORM model file needed
- Documents are plain dictionaries
- Conversion functions in `app/repositories/mongodb_resource_repository.py`
- Helper functions for document-to-model and model-to-document transformations

**Shared Pydantic Schemas (Backend-Agnostic):**
- `app/schemas.py` - Request/response schemas (ResourceCreate, ResourceUpdate, ResourceResponse)
- Remain unchanged and work with both backends
- These schemas are intentionally generic - they define the API contract independent of database backend
- No database-specific fields or logic

## Data Models

### Resource Entity

Both backends store the same logical resource entity:

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| name | string | Resource name (max 100 chars) |
| description | string | Optional description (max 500 chars) |
| dependencies | list[string] | List of resource IDs this resource depends on |
| created_at | datetime | Timestamp of creation (UTC) |
| updated_at | datetime | Timestamp of last update (UTC) |

### MongoDB Indexes

To maintain query performance equivalent to SQLite:

```python
# Unique index on _id (automatic)
# Index on name for search queries
db.resources.create_index("name")
# Index on dependencies for relationship queries
db.resources.create_index("dependencies")
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

Before defining the final properties, we identify and eliminate redundancy:

- Properties 2.2-2.6 (CRUD operations) can be consolidated into comprehensive backend equivalence properties
- Properties 3.1, 3.2, and 3.3 all relate to data consistency between backends and can be combined into round-trip properties
- Property 1.1 (configuration reading) is subsumed by properties 1.2 and 1.3 (backend initialization)
- Properties 6.1 and 6.2 can be combined into a general error handling property

### Core Properties

**Property 1: Backend initialization from configuration**
*For any* valid database configuration (SQLite or MongoDB), when the application initializes, the application should successfully establish a connection to the specified database backend and be ready to handle requests.
**Validates: Requirements 1.2, 1.3**

**Property 2: Invalid configuration rejection**
*For any* invalid MongoDB connection string or unreachable MongoDB server, when the application attempts to initialize, the application should fail to start and produce a descriptive error message.
**Validates: Requirements 1.4**

**Property 3: Graceful connection cleanup**
*For any* initialized application instance, when the application shuts down, all database connections should be closed without errors or resource leaks.
**Validates: Requirements 1.5**

**Property 4: Backend abstraction transparency**
*For any* repository operation (create, read, update, delete, list, search) and any valid input data, the operation should produce identical results regardless of whether SQLite or MongoDB is the configured backend.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

**Property 5: CRUD round-trip consistency**
*For any* valid resource data, creating a resource in either backend and then immediately retrieving it should return a resource with identical field values (except for system-generated timestamps).
**Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3**

**Property 6: Update persistence**
*For any* existing resource and any valid update data, updating the resource in either backend and then retrieving it should return the resource with the updated values applied.
**Validates: Requirements 2.4, 3.3**

**Property 7: Delete completeness**
*For any* existing resource, deleting the resource from either backend should result in subsequent retrieval attempts returning not found.
**Validates: Requirements 2.5**

**Property 8: Relationship preservation**
*For any* resource with dependencies, storing the resource in either backend and then retrieving it should return the resource with the same dependency IDs in the dependencies array.
**Validates: Requirements 3.4**

**Property 9: Schema field completeness**
*For any* resource stored in MongoDB, the MongoDB document should contain all required fields (id, name, description, dependencies, created_at, updated_at) with appropriate data types.
**Validates: Requirements 3.1**

**Property 10: Connection error handling**
*For any* MongoDB operation that fails due to connection issues, the application should return an HTTP 503 Service Unavailable response and log the underlying error.
**Validates: Requirements 6.1**

**Property 11: Validation error handling**
*For any* MongoDB operation that fails due to data validation errors, the application should return an HTTP 400 Bad Request response with details about the validation failure.
**Validates: Requirements 6.2**

## Error Handling

### MongoDB-Specific Errors

The MongoDB repository implementation will handle the following error categories:

1. **Connection Errors** (`pymongo.errors.ConnectionFailure`, `pymongo.errors.ServerSelectionTimeoutError`)
   - Log the full error with connection details
   - Raise a custom `DatabaseConnectionError` exception
   - API layer translates to HTTP 503

2. **Validation Errors** (`pymongo.errors.WriteError` with validation failure)
   - Extract validation failure details
   - Raise a custom `ValidationError` exception
   - API layer translates to HTTP 400

3. **Duplicate Key Errors** (`pymongo.errors.DuplicateKeyError`)
   - Extract the duplicate key information
   - Raise a custom `DuplicateResourceError` exception
   - API layer translates to HTTP 409

4. **Timeout Errors** (`pymongo.errors.ExecutionTimeout`)
   - Log the operation that timed out
   - Raise a custom `DatabaseTimeoutError` exception
   - API layer translates to HTTP 503

### Error Mapping Strategy

Create a new exception hierarchy in `app/exceptions.py`:

```python
class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""
    pass

class DatabaseTimeoutError(DatabaseError):
    """Database operation timed out"""
    pass

class DuplicateResourceError(DatabaseError):
    """Resource with same identifier already exists"""
    pass
```

The repository layer catches backend-specific exceptions and raises these custom exceptions. The API error handlers (already existing in `app/error_handlers.py`) will be extended to handle these new exception types.

## Testing Strategy

### Dual Backend Testing Approach

All tests will be parameterized to run against both SQLite and MongoDB backends. This ensures that both implementations satisfy the same correctness properties.

**Test Fixture Pattern:**
```python
@pytest.fixture(params=["sqlite", "mongodb"])
def db_backend(request):
    """Fixture that provides both database backends"""
    backend_type = request.param
    # Setup appropriate backend
    yield backend
    # Cleanup
```

### Unit Tests

Unit tests will verify specific functionality:

- **Configuration Loading**: Test that environment variables are correctly parsed
- **Repository Factory**: Test that the correct repository type is instantiated
- **MongoDB Connection**: Test connection establishment and error handling
- **Document Mapping**: Test conversion between MongoDB documents and application models
- **Index Creation**: Test that MongoDB indexes are created correctly
- **Error Translation**: Test that MongoDB exceptions are correctly translated to custom exceptions

### Property-Based Tests

Property-based tests will use the Hypothesis library (already in use based on `.hypothesis` directory) to verify universal properties:

**Library**: Hypothesis for Python
**Configuration**: Minimum 100 iterations per property test

Each property-based test will:
1. Be tagged with a comment referencing the design document property: `# Feature: mongodb-integration, Property X: <property text>`
2. Generate random valid resource data using Hypothesis strategies
3. Execute operations against both SQLite and MongoDB backends
4. Assert that results are equivalent

**Example Property Test Structure:**
```python
# Feature: mongodb-integration, Property 4: Backend abstraction transparency
@given(resource_data=resource_strategy())
@settings(max_examples=100)
@pytest.mark.parametrize("backend", ["sqlite", "mongodb"])
def test_create_operation_backend_equivalence(backend, resource_data):
    """Verify create operation produces identical results across backends"""
    # Test implementation
```

### Integration Tests

Integration tests will verify end-to-end workflows:

- Create resource → Retrieve resource → Verify data
- Create resource with dependencies → Verify relationships
- Update resource → Verify changes persisted
- Delete resource → Verify removal
- Search resources → Verify results

These tests will also be parameterized to run against both backends.

### Test Database Management

**SQLite**: Use in-memory database (`sqlite:///:memory:`) for tests

**MongoDB**: Use a dedicated test database:
- Database name: `fastapi_crud_test_mongodb`
- Drop and recreate before each test
- Use Docker container for CI/CD environments
- Environment variable: `MONGODB_TEST_DATABASE=fastapi_crud_test_mongodb`

### Hypothesis Strategies

Define custom Hypothesis strategies for generating test data:

```python
@st.composite
def resource_create_strategy(draw):
    """Generate valid ResourceCreate data"""
    return ResourceCreate(
        name=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.one_of(st.none(), st.text(max_size=500))),
        dependencies=draw(st.lists(st.uuids().map(str), max_size=5))
    )
```

## Implementation Notes

### Migration Path

For users migrating from SQLite to MongoDB:

1. **Export SQLite Data**: Provide a script to export resources to JSON
2. **Import to MongoDB**: Provide a script to import JSON into MongoDB
3. **Validation**: Verify data integrity after migration

**Script Location**: `scripts/migrate_sqlite_to_mongodb.py` (specific to this migration direction)

### Performance Considerations

- **MongoDB Connection Pooling**: Motor handles connection pooling automatically
- **Batch Operations**: For bulk operations, use MongoDB's `insert_many` and `bulk_write`
- **Index Usage**: Ensure queries use indexes by running `explain()` during development
- **Async Operations**: Both backends use async operations to avoid blocking

### Backward Compatibility

- Existing SQLite deployments continue to work without changes
- Default configuration remains SQLite
- No breaking changes to API contracts
- Existing tests continue to pass with SQLite backend

### Dependencies

New Python packages required:

```
motor==3.3.2          # Async MongoDB driver
pymongo==4.6.1        # MongoDB driver (motor dependency)
```

These will be added to `requirements.txt`.

## Deployment Considerations

### Environment Variables

**Required for MongoDB:**
- `DATABASE_TYPE=mongodb`
- `DATABASE_URL=mongodb://host:port`
- `MONGODB_DATABASE=database_name`

**Optional:**
- `MONGODB_USERNAME=username`
- `MONGODB_PASSWORD=password`
- `MONGODB_AUTH_SOURCE=admin`
- `MONGODB_TIMEOUT=5000` (milliseconds)

### Docker Compose Example

```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_TYPE=mongodb
      - DATABASE_URL=mongodb://mongodb:27017
      - MONGODB_DATABASE=fastapi_crud
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

### Cloud Deployment

For MongoDB Atlas or other cloud providers:

```bash
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=fastapi_crud
```

## Security Considerations

1. **Connection String Security**: Never commit connection strings with credentials to version control
2. **Authentication**: Use MongoDB authentication in production environments
3. **Network Security**: Use TLS/SSL for MongoDB connections in production
4. **Input Validation**: Validate all input data before database operations to prevent injection attacks
5. **Least Privilege**: MongoDB user should have minimal required permissions (readWrite on specific database)

## Monitoring and Observability

### Logging

Add structured logging for MongoDB operations:

- Connection establishment/failure
- Query execution time
- Error details with context
- Slow query warnings (>100ms)

### Metrics

Track the following metrics:

- Database operation latency (p50, p95, p99)
- Error rates by error type
- Connection pool utilization (for MongoDB)
- Query counts by operation type

### Health Checks

Extend the application health check endpoint to verify database connectivity:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint that verifies database connectivity"""
    # Check database connection
    # Return 200 if healthy, 503 if database unavailable
```
