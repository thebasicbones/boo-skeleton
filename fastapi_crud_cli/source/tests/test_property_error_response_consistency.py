"""Property-based tests for error response consistency

Feature: fastapi-crud-backend, Property 11: Consistent error format
Validates: Requirements 7.4

For any error response across all endpoints, the response should follow
the same JSON structure with consistent fields (error, message, details).
"""

import pytest
from httpx import AsyncClient
from hypothesis import given, settings
from hypothesis import strategies as st

from app.database_sqlalchemy import (
    AsyncSessionLocal,
)
from app.database_sqlalchemy import (
    drop_sqlalchemy_db as drop_db,
)
from app.database_sqlalchemy import (
    get_sqlalchemy_db as get_db,
)
from app.database_sqlalchemy import (
    init_sqlalchemy_db as init_db,
)
from main import app


# Strategy for generating invalid resource names
@st.composite
def invalid_name_strategy(draw):
    """Generate invalid resource names"""
    choice = draw(st.integers(min_value=0, max_value=2))

    if choice == 0:
        # Empty string
        return ""
    elif choice == 1:
        # Whitespace only
        return draw(st.text(alphabet=" \t\n\r", min_size=1, max_size=10))
    else:
        # Too long (> 100 characters)
        return draw(st.text(min_size=101, max_size=200))


# Strategy for generating invalid descriptions
@st.composite
def invalid_description_strategy(draw):
    """Generate invalid descriptions"""
    # Too long (> 500 characters)
    return draw(st.text(min_size=501, max_size=1000))


# Strategy for generating non-existent resource IDs
non_existent_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), blacklist_characters=""),
    min_size=10,
    max_size=50,
)


def verify_error_response_format(response_json: dict) -> None:
    """
    Verify that an error response follows the consistent format.

    All error responses must have:
    - error: string (error type/name)
    - message: string (human-readable description)
    - details: dict (additional error details)
    """
    assert "error" in response_json, "Error response missing 'error' field"
    assert "message" in response_json, "Error response missing 'message' field"
    assert "details" in response_json, "Error response missing 'details' field"

    assert isinstance(response_json["error"], str), "'error' field must be a string"
    assert isinstance(response_json["message"], str), "'message' field must be a string"
    assert isinstance(response_json["details"], dict), "'details' field must be a dict"

    assert len(response_json["error"]) > 0, "'error' field must not be empty"
    assert len(response_json["message"]) > 0, "'message' field must not be empty"


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=20)
@given(invalid_name=invalid_name_strategy())
async def test_validation_error_format_invalid_name(invalid_name):
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any validation error (invalid name), the error response should
    follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to create resource with invalid name
            response = await client.post(
                "/api/resources",
                json={"name": invalid_name, "description": "Test description", "dependencies": []},
            )

            # Should return 422 for validation error
            assert (
                response.status_code == 422
            ), f"Expected status code 422 for validation error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=20)
@given(invalid_description=invalid_description_strategy())
async def test_validation_error_format_invalid_description(invalid_description):
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any validation error (invalid description), the error response should
    follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to create resource with invalid description
            response = await client.post(
                "/api/resources",
                json={"name": "Valid Name", "description": invalid_description, "dependencies": []},
            )

            # Should return 422 for validation error
            assert (
                response.status_code == 422
            ), f"Expected status code 422 for validation error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=20)
@given(non_existent_id=non_existent_id_strategy)
async def test_not_found_error_format_get(non_existent_id):
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any not found error (GET non-existent resource), the error response
    should follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to get non-existent resource
            response = await client.get(f"/api/resources/{non_existent_id}")

            # Should return 404 for not found
            assert (
                response.status_code == 404
            ), f"Expected status code 404 for not found error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=20)
@given(non_existent_id=non_existent_id_strategy)
async def test_not_found_error_format_update(non_existent_id):
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any not found error (UPDATE non-existent resource), the error response
    should follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to update non-existent resource
            response = await client.put(
                f"/api/resources/{non_existent_id}", json={"name": "Updated Name"}
            )

            # Should return 404 for not found
            assert (
                response.status_code == 404
            ), f"Expected status code 404 for not found error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=20)
@given(non_existent_id=non_existent_id_strategy)
async def test_not_found_error_format_delete(non_existent_id):
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any not found error (DELETE non-existent resource), the error response
    should follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to delete non-existent resource
            response = await client.delete(f"/api/resources/{non_existent_id}")

            # Should return 404 for not found
            assert (
                response.status_code == 404
            ), f"Expected status code 404 for not found error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
async def test_circular_dependency_error_format():
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any circular dependency error, the error response should follow
    the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create resource A
            response_a = await client.post(
                "/api/resources", json={"name": "Resource A", "dependencies": []}
            )
            assert response_a.status_code == 201
            resource_a_id = response_a.json()["id"]

            # Create resource B that depends on A
            response_b = await client.post(
                "/api/resources", json={"name": "Resource B", "dependencies": [resource_a_id]}
            )
            assert response_b.status_code == 201
            resource_b_id = response_b.json()["id"]

            # Try to update A to depend on B (creating a cycle: A -> B -> A)
            response = await client.put(
                f"/api/resources/{resource_a_id}", json={"dependencies": [resource_b_id]}
            )

            # Should return 422 for circular dependency
            assert (
                response.status_code == 422
            ), f"Expected status code 422 for circular dependency error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

            # Additionally verify it's specifically a circular dependency error
            assert (
                "circular" in response_json["message"].lower()
                or "circular" in response_json["error"].lower()
            ), "Error should indicate circular dependency"

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
async def test_missing_required_field_error_format():
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any validation error (missing required field), the error response
    should follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to create resource without required 'name' field
            response = await client.post(
                "/api/resources", json={"description": "Test description", "dependencies": []}
            )

            # Should return 422 for validation error
            assert (
                response.status_code == 422
            ), f"Expected status code 422 for validation error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=20)
@given(invalid_dep_id=non_existent_id_strategy)
async def test_invalid_dependency_error_format(invalid_dep_id):
    """
    Feature: fastapi-crud-backend, Property 11: Consistent error format
    Validates: Requirements 7.4

    For any validation error (invalid dependency reference), the error response
    should follow the consistent format with error, message, and details fields.
    """
    # Setup database
    await drop_db()
    await init_db()

    async with AsyncSessionLocal() as session:

        async def override_get_db():
            yield session

        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Attempt to create resource with non-existent dependency
            response = await client.post(
                "/api/resources",
                json={"name": "Resource with invalid dep", "dependencies": [invalid_dep_id]},
            )

            # Should return 422 for validation error
            assert (
                response.status_code == 422
            ), f"Expected status code 422 for validation error, got {response.status_code}"

            # Verify error response format
            response_json = response.json()
            verify_error_response_format(response_json)

        app.dependency_overrides.clear()

    await drop_db()
