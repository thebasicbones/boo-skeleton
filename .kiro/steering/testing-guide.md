---
inclusion: always
---

# Testing Guide

## Testing Philosophy

This project follows a comprehensive testing strategy with three levels:
1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test API endpoints end-to-end
3. **Property-Based Tests** - Test universal properties with Hypothesis

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── strategies.py                        # Hypothesis strategies
├── test_api_endpoints.py               # API integration tests
├── test_resource_service.py            # Service unit tests
├── test_resource_repository.py         # Repository unit tests
├── test_schemas.py                     # Schema validation tests
├── test_topological_sort_service.py    # Algorithm tests
└── test_property_*.py                  # Property-based tests
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_resource_service.py -v

# Run tests matching pattern
pytest -k "create" -v

# Run only property tests
pytest tests/test_property_*.py -v
```

### Advanced Options

```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb
```

## Writing Unit Tests

### Test Naming Convention

```python
# Pattern: test_<function>_<scenario>_<expected_result>
async def test_create_resource_with_valid_data_returns_resource():
    pass

async def test_get_resource_with_invalid_id_raises_not_found():
    pass

async def test_update_resource_with_circular_dependency_raises_error():
    pass
```

### Unit Test Example

```python
import pytest
from app.schemas import ResourceCreate
from app.exceptions import NotFoundError

async def test_create_resource_with_valid_data():
    """Test creating a resource with valid data."""
    # Arrange
    data = ResourceCreate(
        name="Test Resource",
        description="Test description",
        dependencies=[]
    )
    
    # Act
    result = await service.create_resource(data)
    
    # Assert
    assert result.name == "Test Resource"
    assert result.description == "Test description"
    assert result.dependencies == []
    assert result.id is not None
```


### Testing Async Functions

```python
# All test functions must be async when testing async code
async def test_async_operation():
    result = await async_function()
    assert result is not None

# pytest-asyncio handles async test execution automatically
```

### Using Fixtures

```python
# Use fixtures from conftest.py
async def test_with_database(db_session):
    """Test using database session fixture."""
    resource = await repository.create(data)
    assert resource.id is not None

async def test_with_client(client):
    """Test using FastAPI test client."""
    response = await client.post("/api/resources", json=data)
    assert response.status_code == 201
```

### Testing Exceptions

```python
async def test_get_nonexistent_resource_raises_not_found():
    """Test that getting a nonexistent resource raises NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_resource("nonexistent-id")
    
    assert exc_info.value.resource_id == "nonexistent-id"

async def test_circular_dependency_raises_error():
    """Test that circular dependencies are detected."""
    with pytest.raises(CircularDependencyError) as exc_info:
        await service.create_resource(circular_data)
    
    assert "cycle" in str(exc_info.value).lower()
```

## Writing Integration Tests

### API Endpoint Testing

```python
import httpx
from fastapi.testclient import TestClient

async def test_create_resource_endpoint(client: httpx.AsyncClient):
    """Test POST /api/resources endpoint."""
    # Arrange
    payload = {
        "name": "Test Resource",
        "description": "Test description",
        "dependencies": []
    }
    
    # Act
    response = await client.post("/api/resources", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Resource"
    assert "id" in data
    assert "created_at" in data

async def test_get_resource_endpoint(client: httpx.AsyncClient):
    """Test GET /api/resources/{id} endpoint."""
    # Create a resource first
    create_response = await client.post("/api/resources", json={
        "name": "Test Resource",
        "dependencies": []
    })
    resource_id = create_response.json()["id"]
    
    # Get the resource
    response = await client.get(f"/api/resources/{resource_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == resource_id
```

### Testing Error Responses

```python
async def test_get_nonexistent_resource_returns_404(client: httpx.AsyncClient):
    """Test that getting a nonexistent resource returns 404."""
    response = await client.get("/api/resources/nonexistent-id")
    
    assert response.status_code == 404
    error = response.json()
    assert error["error"] == "NotFoundError"
    assert "not found" in error["message"].lower()

async def test_create_resource_with_invalid_data_returns_422(client: httpx.AsyncClient):
    """Test that invalid data returns 422."""
    response = await client.post("/api/resources", json={
        "name": "",  # Invalid: empty name
        "dependencies": []
    })
    
    assert response.status_code == 422
```

## Writing Property-Based Tests

### What Are Property Tests?

Property tests verify that certain properties hold true for all possible inputs, not just specific examples. They use Hypothesis to generate random test data.

### Hypothesis Strategies

Define strategies in `tests/strategies.py`:

```python
from hypothesis import strategies as st

def resource_strategy():
    """Generate random resource data."""
    return st.fixed_dictionaries({
        "name": st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        "description": st.one_of(st.none(), st.text(max_size=500)),
        "dependencies": st.lists(st.uuids().map(str), max_size=5)
    })

def resource_name_strategy():
    """Generate valid resource names."""
    return st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd")),
        min_size=1,
        max_size=100
    ).filter(lambda x: x.strip())
```

### Property Test Examples

```python
from hypothesis import given, settings
from tests.strategies import resource_strategy

@given(resource_data=resource_strategy())
@settings(max_examples=100)
async def test_resource_creation_roundtrip(resource_data):
    """
    Property: Any resource that is created can be retrieved with the same data.
    
    This tests the fundamental CRUD round-trip property.
    """
    # Create resource
    created = await service.create_resource(ResourceCreate(**resource_data))
    
    # Retrieve resource
    retrieved = await service.get_resource(created.id)
    
    # Verify data matches
    assert created.name == retrieved.name
    assert created.description == retrieved.description
    assert created.dependencies == retrieved.dependencies

@given(resource_data=resource_strategy())
async def test_update_is_persistent(resource_data):
    """
    Property: Updates to resources persist across reads.
    """
    # Create initial resource
    created = await service.create_resource(ResourceCreate(
        name="Original",
        dependencies=[]
    ))
    
    # Update resource
    updated = await service.update_resource(
        created.id,
        ResourceUpdate(**resource_data)
    )
    
    # Retrieve and verify
    retrieved = await service.get_resource(created.id)
    assert retrieved.name == updated.name
    assert retrieved.description == updated.description
```

### Property Test Patterns

#### 1. Round-Trip Property
```python
@given(data=strategy())
async def test_roundtrip(data):
    """Create → Read → Verify data matches."""
    created = await create(data)
    retrieved = await read(created.id)
    assert created == retrieved
```

#### 2. Idempotency Property
```python
@given(data=strategy())
async def test_idempotency(data):
    """Multiple identical operations produce same result."""
    result1 = await operation(data)
    result2 = await operation(data)
    assert result1 == result2
```

#### 3. Invariant Property
```python
@given(data=strategy())
async def test_invariant(data):
    """Certain properties always hold."""
    result = await operation(data)
    assert invariant_condition(result)
```

#### 4. Inverse Property
```python
@given(data=strategy())
async def test_inverse(data):
    """Operation and its inverse cancel out."""
    original = await create(data)
    transformed = await transform(original)
    restored = await inverse_transform(transformed)
    assert original == restored
```

## Test Fixtures

### Common Fixtures (conftest.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    """Provide async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    """Provide database session for testing."""
    # Setup
    session = await create_test_session()
    yield session
    # Teardown
    await session.close()

@pytest.fixture
async def sample_resource(client):
    """Create a sample resource for testing."""
    response = await client.post("/api/resources", json={
        "name": "Sample Resource",
        "description": "For testing",
        "dependencies": []
    })
    return response.json()
```

### Fixture Scopes

```python
# Function scope (default) - runs for each test
@pytest.fixture
async def function_fixture():
    pass

# Module scope - runs once per test module
@pytest.fixture(scope="module")
async def module_fixture():
    pass

# Session scope - runs once per test session
@pytest.fixture(scope="session")
async def session_fixture():
    pass
```

## Test Coverage

### Measuring Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html

# Show missing lines in terminal
pytest --cov=app --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

### Coverage Goals

- **Minimum**: 80% overall coverage
- **Target**: 90%+ for critical paths
- **Focus areas**:
  - Business logic (services)
  - Data access (repositories)
  - API endpoints (routers)
  - Error handling

### What to Test

**High Priority:**
- All business logic in services
- All repository CRUD operations
- All API endpoints
- Error handling paths
- Validation logic

**Medium Priority:**
- Edge cases
- Boundary conditions
- Complex algorithms (topological sort)

**Low Priority:**
- Simple getters/setters
- Configuration loading
- Logging statements

## Testing Best Practices

### 1. Arrange-Act-Assert Pattern

```python
async def test_example():
    # Arrange - Set up test data and conditions
    data = ResourceCreate(name="Test", dependencies=[])
    
    # Act - Perform the operation
    result = await service.create_resource(data)
    
    # Assert - Verify the outcome
    assert result.name == "Test"
```

### 2. Test One Thing

```python
# Good - tests one specific behavior
async def test_create_resource_generates_id():
    result = await service.create_resource(data)
    assert result.id is not None

# Bad - tests multiple things
async def test_create_resource():
    result = await service.create_resource(data)
    assert result.id is not None
    assert result.name == data.name
    assert result.created_at is not None
    # ... too many assertions
```

### 3. Use Descriptive Names

```python
# Good
async def test_create_resource_with_duplicate_dependencies_raises_validation_error():
    pass

# Bad
async def test_create():
    pass
```

### 4. Avoid Test Interdependence

```python
# Good - each test is independent
async def test_create_resource():
    resource = await create_test_resource()
    assert resource.id is not None

async def test_update_resource():
    resource = await create_test_resource()  # Create own data
    updated = await update_resource(resource.id, new_data)
    assert updated.name == new_data.name

# Bad - tests depend on each other
resource_id = None

async def test_create_resource():
    global resource_id
    resource = await create_test_resource()
    resource_id = resource.id  # Shared state!

async def test_update_resource():
    global resource_id
    updated = await update_resource(resource_id, new_data)  # Depends on previous test
```

### 5. Clean Up Test Data

```python
@pytest.fixture
async def test_resource():
    # Setup
    resource = await create_test_resource()
    yield resource
    # Teardown
    await delete_test_resource(resource.id)
```

## Debugging Tests

### Print Debugging

```bash
# Show print statements
pytest -s

# Show more verbose output
pytest -vv
```

### Using Debugger

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace
```

```python
# Add breakpoint in test
async def test_example():
    data = create_data()
    breakpoint()  # Execution pauses here
    result = await operation(data)
```

### Hypothesis Debugging

```python
# Print generated examples
@given(data=strategy())
@settings(verbosity=Verbosity.verbose)
async def test_example(data):
    print(f"Testing with: {data}")
    # ... test code
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Maintenance

### When Tests Fail

1. **Read the error message** - Understand what failed
2. **Check recent changes** - What code changed?
3. **Reproduce locally** - Run the failing test
4. **Debug** - Use print statements or debugger
5. **Fix** - Update code or test as needed
6. **Verify** - Ensure all tests pass

### Updating Tests

When changing functionality:
1. Update tests first (TDD approach)
2. Run tests to see failures
3. Update implementation
4. Verify tests pass
5. Check coverage hasn't decreased

### Removing Flaky Tests

If a test is flaky (passes/fails randomly):
1. Identify the source of non-determinism
2. Fix timing issues (use proper async/await)
3. Remove external dependencies
4. Use fixtures for consistent state
5. If unfixable, mark with `@pytest.mark.flaky`
