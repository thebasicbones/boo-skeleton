"""Property-based tests for frontend error message display

Feature: fastapi-crud-backend, Property 17: Error message display
Validates: Requirements 9.3

This module tests that the frontend correctly displays error messages
when the API returns errors (validation errors, not found errors, etc.).
"""
import pytest
import os
from httpx import AsyncClient
from hypothesis import given, settings, strategies as st, HealthCheck
from motor.motor_asyncio import AsyncIOMotorClient

from main import app
from app.database_factory import get_db
from app.database_sqlalchemy import init_sqlalchemy_db, drop_sqlalchemy_db, AsyncSessionLocal
from tests.strategies import valid_name_strategy, valid_description_strategy


@pytest.fixture(params=["sqlite", "mongodb"])
async def error_test_client(request, mongodb_available):
    """Create a test client for frontend error display testing"""
    backend = request.param
    
    if backend == "sqlite":
        # Setup SQLite
        await drop_sqlalchemy_db()
        await init_sqlalchemy_db()
        
        async def override_get_db():
            async with AsyncSessionLocal() as session:
                yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
        
        app.dependency_overrides.clear()
        await drop_sqlalchemy_db()
        
    elif backend == "mongodb":
        if not mongodb_available:
            pytest.skip("MongoDB is not available for testing")
        
        # Setup MongoDB
        mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
        test_db_name = f"fastapi_crud_test_error_{os.getpid()}"
        
        client_instance = AsyncIOMotorClient(mongodb_url)
        db = client_instance[test_db_name]
        
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")
        
        async def override_get_db():
            yield db
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
        
        app.dependency_overrides.clear()
        
        # Cleanup
        await client_instance.drop_database(test_db_name)
        client_instance.close()


# Strategy for generating invalid resource data that will cause validation errors
@st.composite
def invalid_resource_data_strategy(draw):
    """Generate invalid resource data for testing error responses"""
    error_type = draw(st.sampled_from([
        'empty_name',
        'name_too_long',
        'description_too_long',
        'invalid_dependencies'
    ]))
    
    if error_type == 'empty_name':
        return {
            'name': '',
            'description': 'Valid description',
            'dependencies': []
        }
    elif error_type == 'name_too_long':
        return {
            'name': 'a' * 101,  # Max is 100
            'description': 'Valid description',
            'dependencies': []
        }
    elif error_type == 'description_too_long':
        return {
            'name': 'Valid name',
            'description': 'a' * 501,  # Max is 500
            'dependencies': []
        }
    elif error_type == 'invalid_dependencies':
        return {
            'name': 'Valid name',
            'description': 'Valid description',
            'dependencies': ['non-existent-id-12345']
        }


@pytest.mark.asyncio
@pytest.mark.property
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(invalid_data=invalid_resource_data_strategy())
async def test_property_validation_error_display(
    error_test_client: AsyncClient,
    invalid_data
):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    For any API validation error response, the frontend should receive
    error information in a consistent format that can be displayed to the user.
    
    This test verifies that:
    1. Invalid data triggers validation errors (422 status)
    2. Error responses have consistent structure (error, message, details)
    3. The error information is suitable for display in the UI
    
    Validates: Requirements 9.3
    """
    # Attempt to create a resource with invalid data
    response = await error_test_client.post(
        "/api/resources",
        json=invalid_data
    )
    
    # Verify validation error is returned
    assert response.status_code == 422, \
        f"Expected 422 for invalid data, got {response.status_code}"
    
    error_data = response.json()
    
    # Verify error response has the expected structure for display
    assert "error" in error_data, \
        "Error response missing 'error' field - frontend cannot identify error type"
    
    assert "message" in error_data, \
        "Error response missing 'message' field - frontend cannot display error to user"
    
    assert "details" in error_data, \
        "Error response missing 'details' field - frontend cannot show specific field errors"
    
    # Verify error type is ValidationError
    assert error_data["error"] == "ValidationError", \
        f"Expected ValidationError, got {error_data['error']}"
    
    # Verify message is a non-empty string
    assert isinstance(error_data["message"], str), \
        "Error message must be a string for display"
    
    assert len(error_data["message"]) > 0, \
        "Error message must not be empty for display"
    
    # Verify details is present (can be dict or other structure)
    assert error_data["details"] is not None, \
        "Error details must be present for field-specific error display"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_not_found_error_display(error_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    When a resource is not found (404 error), the API should return
    error information in a consistent format for display.
    
    Validates: Requirements 9.3
    """
    # Try to fetch a non-existent resource
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    
    response = await error_test_client.get(f"/api/resources/{non_existent_id}")
    
    # Verify not found error is returned
    assert response.status_code == 404, \
        f"Expected 404 for non-existent resource, got {response.status_code}"
    
    error_data = response.json()
    
    # Verify error response has the expected structure
    assert "error" in error_data, \
        "Error response missing 'error' field"
    
    assert "message" in error_data, \
        "Error response missing 'message' field"
    
    # Verify message is displayable
    assert isinstance(error_data["message"], str), \
        "Error message must be a string"
    
    assert len(error_data["message"]) > 0, \
        "Error message must not be empty"
    
    # Verify the error message mentions the resource not being found
    message_lower = error_data["message"].lower()
    assert "not found" in message_lower or "does not exist" in message_lower, \
        "Error message should indicate resource was not found"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_circular_dependency_error_display(error_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    When a circular dependency would be created, the API should return
    error information in a format that can be displayed to the user.
    
    Validates: Requirements 9.3
    """
    # Create resource A
    resource_a = await error_test_client.post(
        "/api/resources",
        json={
            "name": "Resource A",
            "description": "First resource",
            "dependencies": []
        }
    )
    assert resource_a.status_code == 201
    id_a = resource_a.json()["id"]
    
    # Create resource B that depends on A
    resource_b = await error_test_client.post(
        "/api/resources",
        json={
            "name": "Resource B",
            "description": "Second resource",
            "dependencies": [id_a]
        }
    )
    assert resource_b.status_code == 201
    id_b = resource_b.json()["id"]
    
    # Try to update A to depend on B (would create a cycle)
    circular_response = await error_test_client.put(
        f"/api/resources/{id_a}",
        json={
            "name": "Resource A",
            "description": "First resource",
            "dependencies": [id_b]
        }
    )
    
    # Verify the circular dependency is rejected
    assert circular_response.status_code in [400, 422], \
        f"Expected 400 or 422 for circular dependency, got {circular_response.status_code}"
    
    error_data = circular_response.json()
    
    # Verify error response has the expected structure
    assert "error" in error_data, \
        "Error response missing 'error' field"
    
    assert "message" in error_data, \
        "Error response missing 'message' field"
    
    # Verify message is displayable
    assert isinstance(error_data["message"], str), \
        "Error message must be a string"
    
    assert len(error_data["message"]) > 0, \
        "Error message must not be empty"
    
    # Verify the error message indicates circular dependency
    message_lower = error_data["message"].lower()
    assert "circular" in message_lower or "cycle" in message_lower, \
        "Error message should indicate circular dependency"


@pytest.mark.asyncio
@pytest.mark.property
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    name=valid_name_strategy(),
    description=valid_description_strategy()
)
async def test_property_update_not_found_error_display(
    error_test_client: AsyncClient,
    name: str,
    description: str
):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    When attempting to update a non-existent resource, the API should
    return error information in a consistent format for display.
    
    Validates: Requirements 9.3
    """
    # Try to update a non-existent resource
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    
    response = await error_test_client.put(
        f"/api/resources/{non_existent_id}",
        json={
            "name": name,
            "description": description,
            "dependencies": []
        }
    )
    
    # Verify not found error is returned
    assert response.status_code == 404, \
        f"Expected 404 for non-existent resource, got {response.status_code}"
    
    error_data = response.json()
    
    # Verify error response structure
    assert "error" in error_data, "Error response missing 'error' field"
    assert "message" in error_data, "Error response missing 'message' field"
    
    # Verify message is displayable
    assert isinstance(error_data["message"], str)
    assert len(error_data["message"]) > 0


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_delete_not_found_error_display(error_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    When attempting to delete a non-existent resource, the API should
    return error information in a consistent format for display.
    
    Validates: Requirements 9.3
    """
    # Try to delete a non-existent resource
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    
    response = await error_test_client.delete(f"/api/resources/{non_existent_id}")
    
    # Verify not found error is returned
    assert response.status_code == 404, \
        f"Expected 404 for non-existent resource, got {response.status_code}"
    
    error_data = response.json()
    
    # Verify error response structure
    assert "error" in error_data, "Error response missing 'error' field"
    assert "message" in error_data, "Error response missing 'message' field"
    
    # Verify message is displayable
    assert isinstance(error_data["message"], str)
    assert len(error_data["message"]) > 0


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_error_response_consistency_across_endpoints(error_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    All error responses across different endpoints should follow the same
    consistent format, making it easy for the frontend to display errors.
    
    This test verifies that error responses from different endpoints
    (create, read, update, delete) all have the same structure.
    
    Validates: Requirements 9.3
    """
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    
    # Collect error responses from different endpoints
    error_responses = []
    
    # GET error (not found)
    get_response = await error_test_client.get(f"/api/resources/{non_existent_id}")
    if get_response.status_code >= 400:
        error_responses.append(("GET", get_response.json()))
    
    # POST error (validation)
    post_response = await error_test_client.post(
        "/api/resources",
        json={"name": "", "description": "test", "dependencies": []}
    )
    if post_response.status_code >= 400:
        error_responses.append(("POST", post_response.json()))
    
    # PUT error (not found)
    put_response = await error_test_client.put(
        f"/api/resources/{non_existent_id}",
        json={"name": "test", "description": "test", "dependencies": []}
    )
    if put_response.status_code >= 400:
        error_responses.append(("PUT", put_response.json()))
    
    # DELETE error (not found)
    delete_response = await error_test_client.delete(f"/api/resources/{non_existent_id}")
    if delete_response.status_code >= 400:
        error_responses.append(("DELETE", delete_response.json()))
    
    # Verify we got error responses
    assert len(error_responses) > 0, "Should have received error responses"
    
    # Verify all error responses have the same structure
    for endpoint, error_data in error_responses:
        assert "error" in error_data, \
            f"{endpoint} error response missing 'error' field"
        
        assert "message" in error_data, \
            f"{endpoint} error response missing 'message' field"
        
        # Verify message is displayable
        assert isinstance(error_data["message"], str), \
            f"{endpoint} error message must be a string"
        
        assert len(error_data["message"]) > 0, \
            f"{endpoint} error message must not be empty"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_error_message_contains_useful_information(error_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 17: Error message display
    
    Error messages should contain useful information that helps users
    understand what went wrong and how to fix it.
    
    Validates: Requirements 9.3
    """
    # Test validation error with empty name
    response = await error_test_client.post(
        "/api/resources",
        json={"name": "", "description": "test", "dependencies": []}
    )
    
    assert response.status_code == 422
    error_data = response.json()
    
    # Verify the error message mentions the field that's invalid
    message = error_data["message"].lower()
    details = str(error_data.get("details", "")).lower()
    
    # The error should mention "name" since that's the invalid field
    assert "name" in message or "name" in details, \
        "Error message should mention the invalid field (name)"
    
    # Test not found error
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = await error_test_client.get(f"/api/resources/{non_existent_id}")
    
    assert response.status_code == 404
    error_data = response.json()
    
    # Verify the error message indicates what wasn't found
    message = error_data["message"].lower()
    assert "not found" in message or "does not exist" in message, \
        "Error message should indicate resource was not found"
