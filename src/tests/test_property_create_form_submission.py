"""Property-based tests for frontend create form submission

Feature: fastapi-crud-backend, Property 15: Create form submission
Feature: fastapi-crud-backend, Property 16: Dependency inclusion in create
Validates: Requirements 9.1, 9.2, 9.4

This module tests that the frontend correctly handles create form submissions,
sends proper POST requests to the API, and displays newly created resources.
"""

import os

import pytest
from httpx import AsyncClient
from hypothesis import HealthCheck, given, settings
from motor.motor_asyncio import AsyncIOMotorClient

from app.database_factory import get_db
from app.database_sqlalchemy import AsyncSessionLocal, drop_sqlalchemy_db, init_sqlalchemy_db
from main import app
from tests.strategies import (
    resource_create_strategy,
    valid_description_strategy,
    valid_name_strategy,
)


@pytest.fixture(params=["sqlite", "mongodb"])
async def form_test_client(request, mongodb_available):
    """Create a test client for frontend form testing"""
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
        test_db_name = f"fastapi_crud_test_form_{os.getpid()}"

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


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(resource_data=resource_create_strategy(with_dependencies=False))
async def test_property_create_form_submission_without_dependencies(
    form_test_client: AsyncClient, resource_data
):
    """
    Feature: fastapi-crud-backend, Property 15: Create form submission

    For any valid form data submitted through the create form, the frontend
    should send a POST request to the API and display the newly created resource
    in the list.

    This test simulates the form submission process:
    1. Submit valid form data via POST /api/resources
    2. Verify the resource is created (201 status)
    3. Verify the resource appears in the list (GET /api/resources)
    4. Verify all form data is preserved in the created resource

    Validates: Requirements 9.1, 9.4
    """
    # Simulate form submission by calling the API endpoint
    # (This is what the frontend JavaScript does when the form is submitted)
    form_payload = {
        "name": resource_data.name,
        "description": resource_data.description,
        "dependencies": resource_data.dependencies,
    }

    # Step 1: Submit the form data (POST request)
    create_response = await form_test_client.post("/api/resources", json=form_payload)

    # Verify the resource was created successfully
    assert (
        create_response.status_code == 201
    ), f"Expected 201 Created, got {create_response.status_code}"

    created_resource = create_response.json()

    # Verify the response contains the created resource with an ID
    assert "id" in created_resource, "Created resource missing ID"
    assert (
        created_resource["name"] == resource_data.name
    ), "Created resource name doesn't match form data"

    # Handle None description
    if resource_data.description is None:
        assert (
            created_resource["description"] is None or created_resource["description"] == ""
        ), "Created resource description should be None or empty"
    else:
        assert (
            created_resource["description"] == resource_data.description
        ), "Created resource description doesn't match form data"

    assert (
        created_resource["dependencies"] == resource_data.dependencies
    ), "Created resource dependencies don't match form data"

    # Step 2: Verify the resource appears in the list
    # (This is what the frontend does after successful creation to refresh the display)
    list_response = await form_test_client.get("/api/resources")
    assert (
        list_response.status_code == 200
    ), f"Expected 200 OK for list, got {list_response.status_code}"

    resources = list_response.json()

    # Find the newly created resource in the list
    found_resource = None
    for resource in resources:
        if resource["id"] == created_resource["id"]:
            found_resource = resource
            break

    assert found_resource is not None, "Newly created resource not found in resource list"

    # Verify the resource in the list matches what was created
    assert (
        found_resource["name"] == resource_data.name
    ), "Resource name in list doesn't match form data"

    if resource_data.description is None:
        assert (
            found_resource["description"] is None or found_resource["description"] == ""
        ), "Resource description in list should be None or empty"
    else:
        assert (
            found_resource["description"] == resource_data.description
        ), "Resource description in list doesn't match form data"

    assert (
        found_resource["dependencies"] == resource_data.dependencies
    ), "Resource dependencies in list don't match form data"


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(name=valid_name_strategy(), description=valid_description_strategy())
async def test_property_create_form_submission_with_dependencies(
    form_test_client: AsyncClient, name: str, description: str
):
    """
    Feature: fastapi-crud-backend, Property 16: Dependency inclusion in create

    For any resource created with dependencies specified, the create request
    payload should include the dependency IDs, and the created resource should
    preserve those dependencies.

    This test verifies that:
    1. Dependencies can be selected in the form
    2. The POST request includes the dependency IDs
    3. The created resource has the correct dependencies
    4. The dependencies are displayed when the resource list is refreshed

    Validates: Requirements 9.2
    """
    # First, create some resources to use as dependencies
    dependency_ids = []
    for i in range(3):
        dep_response = await form_test_client.post(
            "/api/resources",
            json={
                "name": f"Dependency {i}",
                "description": f"Dependency resource {i}",
                "dependencies": [],
            },
        )
        assert dep_response.status_code == 201
        dependency_ids.append(dep_response.json()["id"])

    # Now create a resource with dependencies
    # Simulate selecting 1-3 dependencies from the dropdown
    num_deps = min(len(dependency_ids), 3)
    selected_dependencies = dependency_ids[:num_deps]

    form_payload = {"name": name, "description": description, "dependencies": selected_dependencies}

    # Submit the form with dependencies
    create_response = await form_test_client.post("/api/resources", json=form_payload)

    # Verify the resource was created successfully
    assert (
        create_response.status_code == 201
    ), f"Expected 201 Created, got {create_response.status_code}"

    created_resource = create_response.json()

    # Verify the dependencies are included in the response
    assert "dependencies" in created_resource, "Created resource missing dependencies field"

    assert len(created_resource["dependencies"]) == len(
        selected_dependencies
    ), f"Expected {len(selected_dependencies)} dependencies, got {len(created_resource['dependencies'])}"

    # Verify all selected dependencies are present
    for dep_id in selected_dependencies:
        assert (
            dep_id in created_resource["dependencies"]
        ), f"Dependency {dep_id} not found in created resource"

    # Verify the resource appears in the list with dependencies
    list_response = await form_test_client.get("/api/resources")
    assert list_response.status_code == 200

    resources = list_response.json()
    found_resource = None
    for resource in resources:
        if resource["id"] == created_resource["id"]:
            found_resource = resource
            break

    assert found_resource is not None, "Newly created resource not found in resource list"

    # Verify dependencies are preserved in the list
    assert len(found_resource["dependencies"]) == len(
        selected_dependencies
    ), "Dependencies not preserved in resource list"

    for dep_id in selected_dependencies:
        assert (
            dep_id in found_resource["dependencies"]
        ), f"Dependency {dep_id} not found in resource list"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_create_form_clears_after_submission(form_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 15: Create form submission

    After a successful create operation, the form should be cleared and ready
    for the next entry. This test verifies that the API supports multiple
    sequential create operations.

    Validates: Requirements 9.4
    """
    # Create first resource
    first_payload = {
        "name": "First Resource",
        "description": "First description",
        "dependencies": [],
    }

    first_response = await form_test_client.post("/api/resources", json=first_payload)
    assert first_response.status_code == 201
    first_id = first_response.json()["id"]

    # Create second resource (simulating form being cleared and reused)
    second_payload = {
        "name": "Second Resource",
        "description": "Second description",
        "dependencies": [],
    }

    second_response = await form_test_client.post("/api/resources", json=second_payload)
    assert second_response.status_code == 201
    second_id = second_response.json()["id"]

    # Verify both resources exist and are distinct
    assert first_id != second_id, "Resources should have unique IDs"

    list_response = await form_test_client.get("/api/resources")
    assert list_response.status_code == 200
    resources = list_response.json()

    # Find both resources
    found_first = any(r["id"] == first_id for r in resources)
    found_second = any(r["id"] == second_id for r in resources)

    assert found_first, "First resource not found in list"
    assert found_second, "Second resource not found in list"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_create_form_validation_errors_displayed(form_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 15: Create form submission

    When the API returns a validation error, the frontend should display
    the error message to the user. This test verifies that validation
    errors are properly communicated.

    Validates: Requirements 9.3
    """
    # Submit invalid data (empty name)
    invalid_payload = {"name": "", "description": "Test description", "dependencies": []}

    response = await form_test_client.post("/api/resources", json=invalid_payload)

    # Verify validation error is returned
    assert (
        response.status_code == 422
    ), f"Expected 422 Unprocessable Entity, got {response.status_code}"

    error_data = response.json()

    # Verify error response has the expected structure
    assert "error" in error_data, "Error response missing error field"
    assert "message" in error_data, "Error response missing message field"
    assert "details" in error_data, "Error response missing details field"

    # Verify it's a validation error
    assert (
        error_data["error"] == "ValidationError"
    ), f"Expected ValidationError, got {error_data['error']}"

    # The frontend should display this error to the user
    # We verify that the API provides the necessary error information


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_create_form_circular_dependency_error(form_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 16: Dependency inclusion in create

    When a circular dependency would be created, the API should reject the
    request and the frontend should display an appropriate error message.

    Validates: Requirements 9.2, 9.3
    """
    # Create resource A
    resource_a = await form_test_client.post(
        "/api/resources",
        json={"name": "Resource A", "description": "First resource", "dependencies": []},
    )
    assert resource_a.status_code == 201
    id_a = resource_a.json()["id"]

    # Create resource B that depends on A
    resource_b = await form_test_client.post(
        "/api/resources",
        json={"name": "Resource B", "description": "Second resource", "dependencies": [id_a]},
    )
    assert resource_b.status_code == 201
    id_b = resource_b.json()["id"]

    # Try to update A to depend on B (would create a cycle)
    circular_response = await form_test_client.put(
        f"/api/resources/{id_a}",
        json={"name": "Resource A", "description": "First resource", "dependencies": [id_b]},
    )

    # Verify the circular dependency is rejected
    assert circular_response.status_code in [
        400,
        422,
    ], f"Expected 400 or 422 for circular dependency, got {circular_response.status_code}"

    error_data = circular_response.json()

    # Verify error message indicates circular dependency
    error_message = str(error_data).lower()
    assert (
        "circular" in error_message or "cycle" in error_message
    ), "Error message should indicate circular dependency"
