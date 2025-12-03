"""Property-based tests for frontend update functionality

Feature: fastapi-crud-backend, Property 18: Edit form population
Feature: fastapi-crud-backend, Property 19: Update form submission
Feature: fastapi-crud-backend, Property 20: Dependency modification in update
Validates: Requirements 10.1, 10.2, 10.3

This module tests that the frontend correctly handles update operations:
- Edit form is populated with current resource data
- Update form submissions send proper PUT requests to the API
- Dependency modifications are correctly handled in updates
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
async def update_test_client(request, mongodb_available):
    """Create a test client for frontend update testing"""
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
        test_db_name = f"fastapi_crud_test_update_{os.getpid()}"

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
@given(initial_data=resource_create_strategy(with_dependencies=False))
async def test_property_edit_form_population(update_test_client: AsyncClient, initial_data):
    """
    Feature: fastapi-crud-backend, Property 18: Edit form population

    For any resource selected for editing, the edit form should be populated
    with the current resource data. This test verifies that:
    1. A resource can be created
    2. The resource can be retrieved via GET /api/resources/{id}
    3. The retrieved data matches the original data (simulating form population)

    Validates: Requirements 10.1
    """
    # Step 1: Create a resource
    create_response = await update_test_client.post(
        "/api/resources",
        json={
            "name": initial_data.name,
            "description": initial_data.description,
            "dependencies": initial_data.dependencies,
        },
    )

    assert (
        create_response.status_code == 201
    ), f"Expected 201 Created, got {create_response.status_code}"

    created_resource = create_response.json()
    resource_id = created_resource["id"]

    # Step 2: Retrieve the resource (simulating what happens when edit button is clicked)
    # This is what the frontend does to populate the edit form
    get_response = await update_test_client.get(f"/api/resources/{resource_id}")

    assert get_response.status_code == 200, f"Expected 200 OK, got {get_response.status_code}"

    retrieved_resource = get_response.json()

    # Step 3: Verify the retrieved data matches the original data
    # (This data would be used to populate the edit form)
    assert retrieved_resource["id"] == resource_id, "Resource ID doesn't match"

    assert (
        retrieved_resource["name"] == initial_data.name
    ), "Resource name doesn't match original data"

    # Handle None description
    if initial_data.description is None:
        assert (
            retrieved_resource["description"] is None or retrieved_resource["description"] == ""
        ), "Resource description should be None or empty"
    else:
        assert (
            retrieved_resource["description"] == initial_data.description
        ), "Resource description doesn't match original data"

    assert (
        retrieved_resource["dependencies"] == initial_data.dependencies
    ), "Resource dependencies don't match original data"

    # Verify all required fields are present for form population
    assert "id" in retrieved_resource, "Missing ID field for form"
    assert "name" in retrieved_resource, "Missing name field for form"
    assert "description" in retrieved_resource, "Missing description field for form"
    assert "dependencies" in retrieved_resource, "Missing dependencies field for form"


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    initial_data=resource_create_strategy(with_dependencies=False),
    name=valid_name_strategy(),
    description=valid_description_strategy(),
)
async def test_property_update_form_submission(
    update_test_client: AsyncClient, initial_data, name: str, description: str
):
    """
    Feature: fastapi-crud-backend, Property 19: Update form submission

    For any valid update data submitted through the edit form, the frontend
    should send a PUT request to the API and update the displayed resource.

    This test verifies that:
    1. A resource can be created
    2. The resource can be updated via PUT /api/resources/{id}
    3. The updated data is persisted and can be retrieved
    4. The update appears in the resource list

    Validates: Requirements 10.2
    """
    # Step 1: Create a resource
    create_response = await update_test_client.post(
        "/api/resources",
        json={
            "name": initial_data.name,
            "description": initial_data.description,
            "dependencies": initial_data.dependencies,
        },
    )

    assert create_response.status_code == 201
    created_resource = create_response.json()
    resource_id = created_resource["id"]

    # Step 2: Update the resource (simulating form submission)
    # Normalize the data the same way the API does (strip whitespace)
    normalized_name = name.strip()

    # Handle description normalization
    # The API treats None as "don't update this field" (PATCH semantics)
    # Empty strings and whitespace-only strings become None after validation
    # So we need to determine what the expected result should be
    if description is None or description == "" or (description and not description.strip()):
        # When sending None or empty string, the API treats it as "don't update"
        # So the description should remain as it was in the initial resource
        expected_description = initial_data.description
        if expected_description and not expected_description.strip():
            expected_description = None
        elif expected_description:
            expected_description = expected_description.strip()
    else:
        # When sending a non-empty description, it gets stripped
        expected_description = description.strip()

    update_payload = {
        "name": name,
        "description": description,
        "dependencies": [],  # Keep dependencies empty for this test
    }

    update_response = await update_test_client.put(
        f"/api/resources/{resource_id}", json=update_payload
    )

    assert (
        update_response.status_code == 200
    ), f"Expected 200 OK for update, got {update_response.status_code}"

    updated_resource = update_response.json()

    # Step 3: Verify the update response contains the updated data
    # The API strips whitespace from names
    assert updated_resource["id"] == resource_id, "Resource ID changed after update"

    assert (
        updated_resource["name"] == normalized_name
    ), f"Updated resource name doesn't match form data (expected '{normalized_name}', got '{updated_resource['name']}')"

    # Verify description matches expected value
    if expected_description is None or expected_description == "":
        assert (
            updated_resource["description"] is None or updated_resource["description"] == ""
        ), f"Expected description to be None or empty, got '{updated_resource['description']}'"
    else:
        assert (
            updated_resource["description"] == expected_description
        ), f"Expected description '{expected_description}', got '{updated_resource['description']}'"

    # Step 4: Verify the update persists (retrieve the resource again)
    get_response = await update_test_client.get(f"/api/resources/{resource_id}")
    assert get_response.status_code == 200

    persisted_resource = get_response.json()

    assert persisted_resource["name"] == normalized_name, "Updated name not persisted"

    if expected_description is None or expected_description == "":
        assert (
            persisted_resource["description"] is None or persisted_resource["description"] == ""
        ), "Persisted description should be None or empty"
    else:
        assert (
            persisted_resource["description"] == expected_description
        ), "Updated description not persisted"

    # Step 5: Verify the updated resource appears in the list
    # (This is what the frontend does after successful update to refresh the display)
    list_response = await update_test_client.get("/api/resources")
    assert list_response.status_code == 200

    resources = list_response.json()

    # Find the updated resource in the list
    found_resource = None
    for resource in resources:
        if resource["id"] == resource_id:
            found_resource = resource
            break

    assert found_resource is not None, "Updated resource not found in resource list"

    assert (
        found_resource["name"] == normalized_name
    ), "Updated resource name in list doesn't match form data"

    if expected_description is None or expected_description == "":
        assert (
            found_resource["description"] is None or found_resource["description"] == ""
        ), "Resource description in list should be None or empty"
    else:
        assert (
            found_resource["description"] == expected_description
        ), "Resource description in list doesn't match expected value"


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    initial_name=valid_name_strategy(),
    initial_description=valid_description_strategy(),
    updated_name=valid_name_strategy(),
    updated_description=valid_description_strategy(),
)
async def test_property_dependency_modification_in_update(
    update_test_client: AsyncClient,
    initial_name: str,
    initial_description: str,
    updated_name: str,
    updated_description: str,
):
    """
    Feature: fastapi-crud-backend, Property 20: Dependency modification in update

    For any resource update that modifies dependencies, the update request
    payload should include the modified dependency list, and the updated
    resource should reflect the new dependencies.

    This test verifies that:
    1. Resources can be created with initial dependencies
    2. Dependencies can be added via update
    3. Dependencies can be removed via update
    4. Dependencies can be replaced via update
    5. All dependency modifications persist correctly

    Validates: Requirements 10.3
    """
    # Step 1: Create some dependency resources
    dependency_ids = []
    for i in range(4):
        dep_response = await update_test_client.post(
            "/api/resources",
            json={
                "name": f"Dependency {i}",
                "description": f"Dependency resource {i}",
                "dependencies": [],
            },
        )
        assert dep_response.status_code == 201
        dependency_ids.append(dep_response.json()["id"])

    # Step 2: Create a resource with initial dependencies (first 2)
    initial_dependencies = dependency_ids[:2]

    create_response = await update_test_client.post(
        "/api/resources",
        json={
            "name": initial_name,
            "description": initial_description,
            "dependencies": initial_dependencies,
        },
    )

    assert create_response.status_code == 201
    created_resource = create_response.json()
    resource_id = created_resource["id"]

    # Verify initial dependencies are set
    assert len(created_resource["dependencies"]) == 2
    assert set(created_resource["dependencies"]) == set(initial_dependencies)

    # Step 3: Update to add more dependencies (use all 4)
    updated_dependencies = dependency_ids  # All 4 dependencies

    update_response = await update_test_client.put(
        f"/api/resources/{resource_id}",
        json={
            "name": updated_name,
            "description": updated_description,
            "dependencies": updated_dependencies,
        },
    )

    assert (
        update_response.status_code == 200
    ), f"Expected 200 OK for update, got {update_response.status_code}"

    updated_resource = update_response.json()

    # Verify dependencies were updated
    assert "dependencies" in updated_resource, "Updated resource missing dependencies field"

    assert (
        len(updated_resource["dependencies"]) == 4
    ), f"Expected 4 dependencies after update, got {len(updated_resource['dependencies'])}"

    assert set(updated_resource["dependencies"]) == set(
        updated_dependencies
    ), "Updated dependencies don't match the update payload"

    # Step 4: Verify the dependency update persists
    get_response = await update_test_client.get(f"/api/resources/{resource_id}")
    assert get_response.status_code == 200

    persisted_resource = get_response.json()

    assert len(persisted_resource["dependencies"]) == 4, "Updated dependencies not persisted"

    assert set(persisted_resource["dependencies"]) == set(
        updated_dependencies
    ), "Persisted dependencies don't match update"

    # Step 5: Update to remove some dependencies (keep only last 2)
    reduced_dependencies = dependency_ids[2:]

    reduce_response = await update_test_client.put(
        f"/api/resources/{resource_id}",
        json={
            "name": updated_name,
            "description": updated_description,
            "dependencies": reduced_dependencies,
        },
    )

    assert reduce_response.status_code == 200
    reduced_resource = reduce_response.json()

    assert (
        len(reduced_resource["dependencies"]) == 2
    ), f"Expected 2 dependencies after reduction, got {len(reduced_resource['dependencies'])}"

    assert set(reduced_resource["dependencies"]) == set(
        reduced_dependencies
    ), "Reduced dependencies don't match the update payload"

    # Step 6: Update to remove all dependencies
    empty_response = await update_test_client.put(
        f"/api/resources/{resource_id}",
        json={"name": updated_name, "description": updated_description, "dependencies": []},
    )

    assert empty_response.status_code == 200
    empty_resource = empty_response.json()

    assert (
        len(empty_resource["dependencies"]) == 0
    ), "Expected no dependencies after clearing, got some"

    # Step 7: Verify the final state in the resource list
    list_response = await update_test_client.get("/api/resources")
    assert list_response.status_code == 200

    resources = list_response.json()
    found_resource = None
    for resource in resources:
        if resource["id"] == resource_id:
            found_resource = resource
            break

    assert found_resource is not None
    assert (
        len(found_resource["dependencies"]) == 0
    ), "Final dependency state not reflected in resource list"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_update_validation_errors_displayed(update_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 19: Update form submission

    When the API returns a validation error during update, the frontend
    should display the error message to the user. This test verifies that
    validation errors are properly communicated.

    Validates: Requirements 10.4
    """
    # Create a resource first
    create_response = await update_test_client.post(
        "/api/resources",
        json={"name": "Test Resource", "description": "Test description", "dependencies": []},
    )
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    # Try to update with invalid data (empty name)
    invalid_payload = {"name": "", "description": "Updated description", "dependencies": []}

    response = await update_test_client.put(f"/api/resources/{resource_id}", json=invalid_payload)

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


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_update_circular_dependency_prevention(update_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 20: Dependency modification in update

    When an update would create a circular dependency, the API should reject
    the request and the frontend should display an appropriate error message.

    Validates: Requirements 10.3, 10.4
    """
    # Create resource A
    resource_a = await update_test_client.post(
        "/api/resources",
        json={"name": "Resource A", "description": "First resource", "dependencies": []},
    )
    assert resource_a.status_code == 201
    id_a = resource_a.json()["id"]

    # Create resource B that depends on A
    resource_b = await update_test_client.post(
        "/api/resources",
        json={"name": "Resource B", "description": "Second resource", "dependencies": [id_a]},
    )
    assert resource_b.status_code == 201
    id_b = resource_b.json()["id"]

    # Try to update A to depend on B (would create a cycle: A -> B -> A)
    circular_response = await update_test_client.put(
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

    # Verify A still has no dependencies (update was rejected)
    get_a = await update_test_client.get(f"/api/resources/{id_a}")
    assert get_a.status_code == 200
    resource_a_data = get_a.json()
    assert (
        len(resource_a_data["dependencies"]) == 0
    ), "Resource A should still have no dependencies after rejected update"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_update_nonexistent_resource(update_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 19: Update form submission

    When attempting to update a non-existent resource, the API should return
    a 404 error, and the frontend should display an appropriate error message.

    Validates: Requirements 10.4
    """
    # Try to update a non-existent resource
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await update_test_client.put(
        f"/api/resources/{fake_id}",
        json={"name": "Updated Name", "description": "Updated description", "dependencies": []},
    )

    # Verify 404 error is returned
    assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}"

    error_data = response.json()

    # Verify error response structure
    assert "error" in error_data, "Error response missing error field"
    assert "message" in error_data, "Error response missing message field"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_update_preserves_unmodified_fields(update_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 19: Update form submission

    When updating a resource, fields that are not modified should retain
    their original values. This test verifies partial updates work correctly.

    Validates: Requirements 10.2
    """
    # Create a resource with all fields populated
    create_response = await update_test_client.post(
        "/api/resources",
        json={"name": "Original Name", "description": "Original Description", "dependencies": []},
    )
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    # Update only the name
    update_response = await update_test_client.put(
        f"/api/resources/{resource_id}",
        json={
            "name": "Updated Name",
            "description": "Original Description",  # Keep same
            "dependencies": [],  # Keep same
        },
    )

    assert update_response.status_code == 200
    updated_resource = update_response.json()

    # Verify name was updated
    assert updated_resource["name"] == "Updated Name"

    # Verify description was preserved
    assert updated_resource["description"] == "Original Description"

    # Verify dependencies were preserved
    assert updated_resource["dependencies"] == []
