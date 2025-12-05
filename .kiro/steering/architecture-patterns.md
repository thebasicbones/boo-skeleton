---
inclusion: always
---

# Architecture Patterns and Guidelines

## Layered Architecture

The application follows a strict layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│         Routers (API Layer)         │  ← HTTP requests/responses
├─────────────────────────────────────┤
│      Services (Business Logic)      │  ← Orchestration, validation
├─────────────────────────────────────┤
│   Repositories (Data Access Layer)  │  ← Database operations
├─────────────────────────────────────┤
│     Models/Schemas (Data Layer)     │  ← Data structures
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Routers (`app/routers/`)
- Define API endpoints and HTTP methods
- Handle request/response serialization
- Perform basic request validation
- Delegate business logic to services
- Return appropriate HTTP status codes

**Example:**
```python
@router.post("/resources", status_code=201)
async def create_resource(
    data: ResourceCreate,
    service: ResourceService = Depends(get_resource_service)
) -> ResourceResponse:
    """Create a new resource."""
    return await service.create_resource(data)
```

#### 2. Services (`app/services/`)
- Implement business logic and rules
- Orchestrate operations across repositories
- Perform complex validations (e.g., circular dependency detection)
- Handle transactions and error recovery
- Transform data between layers

**Example:**
```python
async def create_resource(self, data: ResourceCreate) -> ResourceResponse:
    """Create resource with dependency validation."""
    # Validate dependencies exist
    await self._validate_dependencies(data.dependencies)
    
    # Check for circular dependencies
    await self._check_circular_dependencies(data)
    
    # Create resource
    return await self.repository.create(data)
```

#### 3. Repositories (`app/repositories/`)
- Abstract database operations
- Provide CRUD operations
- Handle database-specific logic
- Implement query optimization
- Manage database sessions/connections

**Example:**
```python
class ResourceRepository(ABC):
    @abstractmethod
    async def create(self, data: ResourceCreate) -> ResourceResponse:
        """Create a new resource."""
        pass
    
    @abstractmethod
    async def get(self, resource_id: str) -> ResourceResponse:
        """Get resource by ID."""
        pass
```

#### 4. Models and Schemas
- **Models** (`app/models/`): SQLAlchemy ORM models for relational databases
- **Schemas** (`app/schemas.py`): Pydantic models for validation and serialization

## Repository Pattern

### Abstract Base Repository

All repositories inherit from an abstract base class to ensure consistent interface:

```python
from abc import ABC, abstractmethod

class ResourceRepository(ABC):
    @abstractmethod
    async def create(self, data: ResourceCreate) -> ResourceResponse:
        pass
    
    @abstractmethod
    async def get(self, resource_id: str) -> ResourceResponse:
        pass
    
    @abstractmethod
    async def get_all(self) -> list[ResourceResponse]:
        pass
    
    @abstractmethod
    async def update(self, resource_id: str, data: ResourceUpdate) -> ResourceResponse:
        pass
    
    @abstractmethod
    async def delete(self, resource_id: str) -> None:
        pass
    
    @abstractmethod
    async def search(self, query: str) -> list[ResourceResponse]:
        pass
```

### Implementation Pattern

Each database backend implements the repository interface:

- `SQLAlchemyResourceRepository` - SQLite/PostgreSQL implementation
- `MongoDBResourceRepository` - MongoDB implementation

### Factory Pattern

The `database_factory.py` module provides a factory function to instantiate the correct repository based on configuration:

```python
def get_repository() -> ResourceRepository:
    """Get the appropriate repository based on DATABASE_TYPE."""
    settings = get_settings()
    
    if settings.database_type == "sqlite":
        return SQLAlchemyResourceRepository()
    elif settings.database_type == "mongodb":
        return MongoDBResourceRepository()
    else:
        raise ValueError(f"Unsupported database type: {settings.database_type}")
```

## Dependency Injection

### FastAPI Dependencies

Use FastAPI's dependency injection for:
- Database sessions/connections
- Repository instances
- Service instances
- Configuration

```python
# In routers
async def endpoint(
    repository: ResourceRepository = Depends(get_repository),
    service: ResourceService = Depends(get_resource_service)
):
    pass
```

### Benefits
- Testability: Easy to mock dependencies
- Flexibility: Swap implementations without changing code
- Lifecycle management: FastAPI handles cleanup

## Error Handling Strategy

### Exception Hierarchy

```
Exception
├── NotFoundError          # Resource not found (404)
├── ValidationError        # Invalid input (422)
├── CircularDependencyError # Dependency cycle (422)
└── DatabaseError          # Database issues (500)
```

### Error Handler Registration

Global error handlers in `app/error_handlers.py` convert exceptions to HTTP responses:

```python
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "NotFoundError",
            "message": str(exc),
            "details": {"resource_id": exc.resource_id}
        }
    )
```

### Error Propagation

- Repositories raise domain exceptions
- Services catch and re-raise or transform exceptions
- Routers let exceptions bubble up to global handlers
- Never catch `Exception` without re-raising or logging

## Configuration Management

### Pydantic Settings

Configuration uses Pydantic Settings for type-safe, validated configuration:

```python
class Settings(BaseSettings):
    database_type: Literal["sqlite", "mongodb"] = "sqlite"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    environment: Literal["development", "staging", "production"] = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
```

### Environment-Specific Configuration

- Development: Debug enabled, auto-reload, verbose logging
- Staging: Production-like settings with additional logging
- Production: Optimized, secure defaults, minimal logging

### Singleton Pattern

Settings are loaded once and cached:

```python
_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

## Database Connection Management

### Lifespan Events

Database connections are managed via FastAPI's lifespan context:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    yield
    # Shutdown
    await close_database()
```

### Connection Pooling

- SQLite: Managed by SQLAlchemy
- MongoDB: Managed by Motor driver

## Topological Sorting Algorithm

### Purpose
Order resources by dependencies so dependencies appear before dependents.

### Implementation
Located in `app/services/topological_sort_service.py`:

1. Build adjacency list from dependencies
2. Perform depth-first search (DFS)
3. Detect cycles during traversal
4. Return resources in topological order

### Usage
```python
sorted_resources = await topological_sort_service.sort(resources)
# Returns: [no-deps, depends-on-first, depends-on-second, ...]
```

## Testing Architecture

### Test Pyramid

```
        ┌─────────────┐
        │  Property   │  ← Hypothesis tests (universal properties)
        │   Tests     │
        ├─────────────┤
        │ Integration │  ← API endpoint tests
        │   Tests     │
        ├─────────────┤
        │    Unit     │  ← Service/repository tests
        │   Tests     │
        └─────────────┘
```

### Test Fixtures

Shared fixtures in `tests/conftest.py`:
- `db_session` - Database session
- `client` - FastAPI test client
- `sample_resource` - Pre-created test data

### Property-Based Testing

Use Hypothesis to test universal properties:
- Round-trip: Create → Read → Verify
- Idempotency: Multiple identical operations produce same result
- Invariants: Properties that always hold

## Adding New Features

### Step-by-Step Process

1. **Define Schema** - Add Pydantic models in `app/schemas.py`
2. **Update Repository Interface** - Add abstract method to base repository
3. **Implement Repository** - Implement for both SQLite and MongoDB
4. **Add Service Logic** - Implement business logic in service layer
5. **Create Router Endpoint** - Add API endpoint in router
6. **Write Tests** - Add unit tests and property tests
7. **Update Documentation** - Update README and API docs

### Example: Adding a New Field

```python
# 1. Update schema
class ResourceCreate(BaseModel):
    name: str
    description: str | None
    dependencies: list[str]
    tags: list[str] = []  # New field

# 2. Update model (SQLAlchemy)
class Resource(Base):
    # ... existing fields
    tags = Column(JSON, default=list)

# 3. Update repository implementations
# 4. No service changes needed (passes through)
# 5. No router changes needed (uses schema)
# 6. Add tests for new field
# 7. Update API documentation
```

## Performance Optimization

### Database Queries
- Use async operations throughout
- Batch operations when possible
- Index frequently queried fields
- Avoid N+1 queries

### Caching Strategy
- Cache topological sort results
- Invalidate cache on resource updates
- Use Redis for distributed caching (future enhancement)

### Monitoring
- Log slow queries (>100ms)
- Track API endpoint response times
- Monitor database connection pool usage
