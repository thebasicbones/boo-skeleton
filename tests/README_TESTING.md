# Testing Infrastructure Guide

This guide explains how to use the dual-backend testing infrastructure for property-based testing with both SQLite and MongoDB backends.

## Overview

The testing infrastructure provides:

1. **Parameterized Fixtures** (`conftest.py`) - Fixtures for testing against both SQLite and MongoDB backends
2. **Hypothesis Strategies** (`strategies.py`) - Custom strategies for generating valid test data
3. **Demo Tests** (`test_fixtures_demo.py`) - Examples showing how to use the infrastructure

## Fixtures

### Individual Backend Fixtures

Use these fixtures when you want to test a specific backend:

```python
@pytest.mark.asyncio
async def test_with_sqlite(sqlalchemy_repository):
    """Test using SQLite backend"""
    resource = await sqlalchemy_repository.create(resource_data)
    assert resource is not None

@pytest.mark.asyncio
async def test_with_mongodb(mongodb_repository):
    """Test using MongoDB backend"""
    resource = await mongodb_repository.create(resource_data)
    assert resource is not None
```

### Parameterized Backend Fixture

Use the `db_backend` fixture to automatically test both backends:

```python
@pytest.mark.asyncio
async def test_both_backends(db_backend):
    """Test runs automatically against both SQLite and MongoDB"""
    backend_name, repository = db_backend
    
    resource = await repository.create(resource_data)
    assert resource is not None
    print(f"✓ Test passed for {backend_name}")
```

### Database Access Fixtures

For tests that need direct database access:

```python
@pytest.mark.asyncio
async def test_with_db_session(clean_sqlalchemy_db):
    """Direct SQLAlchemy session access"""
    # Use session directly
    pass

@pytest.mark.asyncio
async def test_with_mongodb_db(clean_mongodb_db):
    """Direct MongoDB database access"""
    # Use MongoDB database directly
    pass
```

## Hypothesis Strategies

### Basic Strategies

```python
from tests.strategies import (
    valid_name_strategy,
    valid_description_strategy,
    resource_id_strategy,
    dependency_list_strategy,
)

# Generate valid resource names (1-100 chars, non-empty)
name = valid_name_strategy()

# Generate valid descriptions (optional, max 500 chars)
description = valid_description_strategy()

# Generate valid UUIDs
resource_id = resource_id_strategy()

# Generate dependency lists (0-5 unique IDs)
dependencies = dependency_list_strategy()
```

### Resource Strategies

```python
from tests.strategies import (
    resource_create_strategy,
    resource_update_strategy,
)

# Generate ResourceCreate objects
@given(resource_data=resource_create_strategy())
async def test_create(resource_data):
    # resource_data is a valid ResourceCreate object
    pass

# Generate ResourceUpdate objects
@given(update_data=resource_update_strategy())
async def test_update(update_data):
    # update_data is a valid ResourceUpdate object
    pass
```

### Advanced Strategies

```python
from tests.strategies import (
    resource_create_with_existing_dependencies_strategy,
    invalid_name_strategy,
    invalid_description_strategy,
)

# Generate resources with dependencies from existing resources
existing_ids = ["id1", "id2", "id3"]
resource_data = resource_create_with_existing_dependencies_strategy(existing_ids)

# Generate invalid data for validation testing
invalid_name = invalid_name_strategy()
invalid_description = invalid_description_strategy()
```

### Convenience Strategies

Pre-configured strategies for common scenarios:

```python
from tests.strategies import (
    simple_resource_strategy,          # No dependencies
    resource_with_deps_strategy,       # May have dependencies
    name_only_update_strategy,         # Only updates name
    description_only_update_strategy,  # Only updates description
    full_update_strategy,              # Updates all fields
)
```

## Property-Based Testing Examples

### Testing a Single Backend

```python
from hypothesis import given, settings
from tests.strategies import resource_create_strategy

@pytest.mark.asyncio
@pytest.mark.property
@settings(max_examples=100)
@given(resource_data=resource_create_strategy())
async def test_create_roundtrip(sqlalchemy_repository, resource_data):
    """
    Feature: mongodb-integration, Property 5: CRUD round-trip consistency
    Validates: Requirements 2.2, 2.3
    """
    # Create resource
    created = await sqlalchemy_repository.create(resource_data)
    
    # Retrieve resource
    retrieved = await sqlalchemy_repository.get_by_id(created.id)
    
    # Verify round-trip
    assert retrieved.name == created.name
    assert retrieved.description == created.description
```

### Testing Both Backends

```python
from hypothesis import given, settings, HealthCheck

@pytest.mark.asyncio
@pytest.mark.property
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(resource_data=resource_create_strategy())
async def test_backend_equivalence(resource_data):
    """
    Test that both backends produce equivalent results
    """
    # Setup both backends
    sqlalchemy_repo = ...  # Create SQLAlchemy repository
    mongodb_repo = ...     # Create MongoDB repository
    
    # Test both backends
    sqlalchemy_result = await sqlalchemy_repo.create(resource_data)
    mongodb_result = await mongodb_repo.create(resource_data)
    
    # Verify equivalence
    assert sqlalchemy_result.name == mongodb_result['name']
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run property-based tests only
```bash
pytest tests/ -m property
```

### Run tests for a specific backend
```bash
pytest tests/ -m sqlite
pytest tests/ -m mongodb
```

### Run with verbose output
```bash
pytest tests/ -v -s
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## MongoDB Availability

Tests that require MongoDB will automatically skip if MongoDB is not available:

```python
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
async def test_mongodb_feature(mongodb_repository):
    # This test only runs if MongoDB is available
    pass
```

## Test Isolation

Each test gets a clean database:

- **SQLite**: In-memory database created and disposed for each test
- **MongoDB**: Unique test database created and dropped for each test

This ensures:
- No test pollution
- Parallel test execution safety
- Consistent test results

## Best Practices

1. **Use property-based testing for universal properties**
   - Test behaviors that should hold for all valid inputs
   - Use `@given` decorator with appropriate strategies

2. **Use unit tests for specific examples**
   - Test edge cases and specific scenarios
   - Test error conditions

3. **Tag tests appropriately**
   - Use `@pytest.mark.property` for property-based tests
   - Use `@pytest.mark.mongodb` for MongoDB-specific tests
   - Use `@pytest.mark.integration` for integration tests

4. **Configure Hypothesis appropriately**
   - Set `max_examples=100` for property tests (minimum)
   - Suppress `function_scoped_fixture` health check for async fixtures
   - Set reasonable deadlines for database operations

5. **Document test properties**
   - Include feature name and property number in docstring
   - Reference requirements being validated
   - Explain what the test verifies

## Example: Complete Property Test

```python
"""Property-based test for CRUD operations

Feature: mongodb-integration, Property 5: CRUD round-trip consistency
Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3
"""
import pytest
from hypothesis import given, settings, HealthCheck
from tests.strategies import resource_create_strategy

@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(resource_data=resource_create_strategy())
async def test_crud_roundtrip(sqlalchemy_repository, resource_data):
    """
    For any valid resource data, creating a resource and then
    immediately retrieving it should return a resource with
    identical field values.
    """
    # CREATE
    created = await sqlalchemy_repository.create(resource_data)
    assert created is not None
    
    # READ
    retrieved = await sqlalchemy_repository.get_by_id(created.id)
    assert retrieved is not None
    
    # VERIFY ROUND-TRIP
    assert retrieved.id == created.id
    assert retrieved.name == created.name
    assert retrieved.description == created.description
    assert retrieved.dependencies == created.dependencies
```

## Troubleshooting

### MongoDB Connection Issues

If tests are skipping due to MongoDB unavailability:

1. Check MongoDB is running: `mongosh`
2. Check connection string: `echo $DATABASE_URL`
3. Verify network connectivity: `nc -zv localhost 27017`

### Hypothesis Warnings

If you see `NonInteractiveExampleWarning`:
- This is expected when using `.example()` in tests
- For actual tests, use `@given` decorator instead

### Async Fixture Issues

If you see health check failures:
- Add `suppress_health_check=[HealthCheck.function_scoped_fixture]`
- This is necessary for async fixtures with Hypothesis

## Additional Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Pytest Async Documentation](https://pytest-asyncio.readthedocs.io/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
