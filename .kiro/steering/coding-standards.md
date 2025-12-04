---
inclusion: manual
---

# Coding Standards and Best Practices

## Code Style

### Python Version
- **Target**: Python 3.11+
- **Minimum**: Python 3.10

### Formatting
- **Line Length**: 100 characters (configured in pyproject.toml)
- **Formatter**: Black (automatic formatting via pre-commit)
- **Import Sorting**: Ruff with isort rules

### Type Hints
- **Required**: All functions must have complete type hints
- **Tool**: MyPy for static type checking
- **Strictness**: Strict mode enabled (no implicit Any, no untyped defs)

```python
# Good
async def get_resource(resource_id: str) -> ResourceResponse:
    """Get a resource by ID."""
    pass

# Bad - missing return type
async def get_resource(resource_id: str):
    pass
```

## Naming Conventions

### Files and Modules
- Use snake_case: `resource_service.py`, `database_factory.py`
- Test files: `test_*.py` (e.g., `test_resource_service.py`)
- Property tests: `test_property_*.py`

### Classes
- Use PascalCase: `ResourceService`, `ResourceRepository`
- Exception classes end with `Error`: `NotFoundError`, `ValidationError`
- Pydantic schemas: `ResourceCreate`, `ResourceUpdate`, `ResourceResponse`

### Functions and Variables
- Use snake_case: `get_resource`, `resource_id`, `created_at`
- Async functions: prefix with `async def`
- Private methods: prefix with underscore `_internal_method`

### Constants
- Use UPPER_SNAKE_CASE: `MAX_RETRIES`, `DEFAULT_TIMEOUT`

## Documentation

### Docstrings
- **Required**: All public functions, classes, and modules
- **Format**: Google-style docstrings
- **Content**: Brief description, parameters, returns, raises

```python
async def create_resource(data: ResourceCreate) -> ResourceResponse:
    """
    Create a new resource with dependency validation.
    
    Args:
        data: Resource creation data including name, description, and dependencies
        
    Returns:
        ResourceResponse: Created resource with generated ID and timestamps
        
    Raises:
        ValidationError: If resource data is invalid
        CircularDependencyError: If dependencies form a cycle
        DatabaseError: If database operation fails
    """
    pass
```

### Comments
- Use comments sparingly - prefer self-documenting code
- Explain **why**, not **what**
- Keep comments up-to-date with code changes

## Error Handling

### Custom Exceptions
Use project-specific exceptions from `app/exceptions.py`:
- `NotFoundError` - Resource not found
- `ValidationError` - Invalid data
- `CircularDependencyError` - Dependency cycle detected
- `DatabaseError` - Database operation failure

### Exception Handling Pattern
```python
try:
    resource = await repository.get(resource_id)
except NotFoundError:
    raise  # Re-raise custom exceptions
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise DatabaseError("Failed to retrieve resource")
```

### Error Responses
All errors return consistent JSON structure via `ErrorResponse` schema:
```json
{
  "error": "NotFoundError",
  "message": "Resource not found",
  "details": {"resource_id": "123"}
}
```

## Async/Await

### Always Use Async
- All database operations are async
- All service methods are async
- All repository methods are async
- Use `await` for all async calls

```python
# Good
async def get_all_resources() -> list[ResourceResponse]:
    resources = await repository.get_all()
    return resources

# Bad - missing await
async def get_all_resources() -> list[ResourceResponse]:
    resources = repository.get_all()  # This returns a coroutine!
    return resources
```

## Dependency Injection

### FastAPI Dependencies
Use FastAPI's dependency injection system:

```python
from fastapi import Depends
from app.database_factory import get_repository

@router.get("/resources")
async def list_resources(
    repository: ResourceRepository = Depends(get_repository)
) -> list[ResourceResponse]:
    return await repository.get_all()
```

## Testing Standards

### Test Organization
- Unit tests: Test individual components in isolation
- Integration tests: Test API endpoints end-to-end
- Property tests: Test universal properties with Hypothesis

### Test Naming
```python
# Unit test
async def test_create_resource_with_valid_data():
    pass

# Property test
@given(resource_data=resource_strategy())
async def test_resource_creation_roundtrip(resource_data):
    pass
```

### Test Coverage
- Minimum coverage: 80%
- Run with: `pytest --cov=app --cov-report=html`

## Code Quality Tools

### Pre-commit Hooks
All code must pass pre-commit checks:
- Black (formatting)
- Ruff (linting)
- MyPy (type checking)
- Trailing whitespace removal
- YAML syntax validation

### Running Checks Manually
```bash
# Format code
black .

# Lint code
ruff check . --fix

# Type check
mypy app/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Import Organization

### Import Order (enforced by Ruff)
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import logging
from datetime import datetime
from typing import Any

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# Local
from app.exceptions import NotFoundError
from app.repositories.base import ResourceRepository
from app.schemas import ResourceCreate, ResourceResponse
```

## Performance Considerations

### Database Queries
- Use async operations for all database calls
- Avoid N+1 queries - fetch related data efficiently
- Use connection pooling (configured in database modules)

### Caching
- Consider caching for frequently accessed data
- Use appropriate cache invalidation strategies

### Logging
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include context in log messages
- Avoid logging sensitive information

## Security Best Practices

### Input Validation
- All input validated via Pydantic schemas
- Sanitize user input to prevent injection attacks
- Validate dependencies exist before creating relationships

### Configuration
- Never commit secrets to version control
- Use environment variables for sensitive data
- Change default secret keys in production

### CORS
- Configure allowed origins appropriately
- Avoid `allow_origins=["*"]` in production
