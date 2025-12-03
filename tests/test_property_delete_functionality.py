"""Property-based tests for frontend delete functionality

Feature: fastapi-crud-backend, Property 21: Delete removes from UI
Validates: Requirements 11.5

This module tests that the frontend correctly handles delete operations:
- Resources are removed from the UI after successful deletion
- Delete operations properly update the displayed resource list
"""
import pytest
import os
from httpx import AsyncClient
from hypothesis import given, settings, strategies as st, HealthCheck
from motor.motor_asyncio import AsyncIOMotorClient

from main import app
from app.database_factory import get_db
from app.database_sqlalchemy import init_sqlalchemy_db, drop_sqlalchemy_db, AsyncSessionLocal
from tests.strategies import resource_create_strategy


@pytest.fixture(params=["sqlite", "mongodb"])
async def delete_test_client(request, mongodb_available):
    """Create a test client for frontend delete testing"""
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
        test_db_name = f"fastapi_crud_test_delete_{os.getpid()}"
        
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
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy(with_dependencies=False))
async def test_property_delete_removes_from_ui(
    delete_test_client: AsyncClient,
    resource_data
):
    """
    Feature: fastapi-crud-backend, Property 21: Delete removes from UI
    
    For any successfully deleted resource, the frontend should remove the
    resource from the displayed list. This test verifies that:
    1. A resource can be created
    2. The resource appears in the list
    3. The resource can be deleted via DELETE /api/resources/{id}
    4. The resource no longer appears in the list (simulating UI removal)
    
    Validates: Requirements 11.5
    """
    # Step 1: Create a resource
    create_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": resource_data.name,
            "description": resource_data.description,
            "dependencies": resource_data.dependencies
        }
    )
    
    assert create_response.status_code == 201, \
        f"Expected 201 Created, got {create_response.status_code}"
    
    created_resource = create_response.json()
    resource_id = created_resource["id"]
    
    # Step 2: Verify the resource appears in the list
    # (This is what the frontend displays before deletion)
    list_before_response = await delete_test_client.get("/api/resources")
    assert list_before_response.status_code == 200, \
        f"Expected 200 OK, got {list_before_response.status_code}"
    
    resources_before = list_before_response.json()
    
    # Find the resource in the list
    found_before = any(r["id"] == resource_id for r in resources_before)
    assert found_before, \
        "Resource should appear in the list before deletion"
    
    # Step 3: Delete the resource (simulating delete button click)
    # This is what happens when the user confirms deletion in the UI
    delete_response = await delete_test_client.delete(
        f"/api/resources/{resource_id}"
    )
    
    assert delete_response.status_code == 204, \
        f"Expected 204 No Content for delete, got {delete_response.status_code}"
    
    # Step 4: Verify the resource no longer appears in the list
    # (This is what the frontend displays after successful deletion)
    list_after_response = await delete_test_client.get("/api/resources")
    assert list_after_response.status_code == 200, \
        f"Expected 200 OK, got {list_after_response.status_code}"
    
    resources_after = list_after_response.json()
    
    # Verify the resource is not in the list
    found_after = any(r["id"] == resource_id for r in resources_after)
    assert not found_after, \
        "Resource should not appear in the list after deletion (UI removal failed)"
    
    # Verify the list has one fewer resource
    assert len(resources_after) == len(resources_before) - 1, \
        "Resource list should have one fewer resource after deletion"


@pytest.mark.asyncio
@pytest.mark.property
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    resource1_data=resource_create_strategy(with_dependencies=False),
    resource2_data=resource_create_strategy(with_dependencies=False)
)
async def test_property_delete_removes_only_target_resource(
    delete_test_client: AsyncClient,
    resource1_data,
    resource2_data
):
    """
    Feature: fastapi-crud-backend, Property 21: Delete removes from UI
    
    When deleting a resource, only that specific resource should be removed
    from the UI. Other resources should remain visible.
    
    This test verifies that:
    1. Multiple resources can be created
    2. Deleting one resource removes only that resource from the list
    3. Other resources remain in the list
    
    Validates: Requirements 11.5
    """
    # Step 1: Create two resources
    create1_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": resource1_data.name,
            "description": resource1_data.description,
            "dependencies": resource1_data.dependencies
        }
    )
    assert create1_response.status_code == 201
    resource1_id = create1_response.json()["id"]
    
    create2_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": resource2_data.name,
            "description": resource2_data.description,
            "dependencies": resource2_data.dependencies
        }
    )
    assert create2_response.status_code == 201
    resource2_id = create2_response.json()["id"]
    
    # Step 2: Verify both resources appear in the list
    list_before_response = await delete_test_client.get("/api/resources")
    assert list_before_response.status_code == 200
    resources_before = list_before_response.json()
    
    found1_before = any(r["id"] == resource1_id for r in resources_before)
    found2_before = any(r["id"] == resource2_id for r in resources_before)
    
    assert found1_before, "Resource 1 should appear in the list before deletion"
    assert found2_before, "Resource 2 should appear in the list before deletion"
    
    # Step 3: Delete only the first resource
    delete_response = await delete_test_client.delete(
        f"/api/resources/{resource1_id}"
    )
    assert delete_response.status_code == 204
    
    # Step 4: Verify only the first resource is removed from the list
    list_after_response = await delete_test_client.get("/api/resources")
    assert list_after_response.status_code == 200
    resources_after = list_after_response.json()
    
    found1_after = any(r["id"] == resource1_id for r in resources_after)
    found2_after = any(r["id"] == resource2_id for r in resources_after)
    
    assert not found1_after, \
        "Resource 1 should not appear in the list after deletion"
    assert found2_after, \
        "Resource 2 should still appear in the list after deleting Resource 1"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_delete_with_cascade_removes_dependents(
    delete_test_client: AsyncClient
):
    """
    Feature: fastapi-crud-backend, Property 21: Delete removes from UI
    
    When deleting a resource with cascade=true, both the resource and its
    dependents should be removed from the UI.
    
    This test verifies that:
    1. Resources with dependencies can be created
    2. Cascade delete removes the resource and all dependents
    3. All deleted resources are removed from the UI
    
    Validates: Requirements 11.2, 11.5
    """
    # Step 1: Create a dependency chain: A <- B <- C
    # (C depends on B, B depends on A)
    
    # Create resource A (no dependencies)
    create_a_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": "Resource A",
            "description": "Base resource",
            "dependencies": []
        }
    )
    assert create_a_response.status_code == 201
    resource_a_id = create_a_response.json()["id"]
    
    # Create resource B (depends on A)
    create_b_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": "Resource B",
            "description": "Depends on A",
            "dependencies": [resource_a_id]
        }
    )
    assert create_b_response.status_code == 201
    resource_b_id = create_b_response.json()["id"]
    
    # Create resource C (depends on B)
    create_c_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": "Resource C",
            "description": "Depends on B",
            "dependencies": [resource_b_id]
        }
    )
    assert create_c_response.status_code == 201
    resource_c_id = create_c_response.json()["id"]
    
    # Step 2: Verify all resources appear in the list
    list_before_response = await delete_test_client.get("/api/resources")
    assert list_before_response.status_code == 200
    resources_before = list_before_response.json()
    
    assert any(r["id"] == resource_a_id for r in resources_before)
    assert any(r["id"] == resource_b_id for r in resources_before)
    assert any(r["id"] == resource_c_id for r in resources_before)
    
    # Step 3: Delete resource A with cascade=true
    # This should remove A, B, and C (since B depends on A, and C depends on B)
    delete_response = await delete_test_client.delete(
        f"/api/resources/{resource_a_id}?cascade=true"
    )
    assert delete_response.status_code == 204
    
    # Step 4: Verify all three resources are removed from the list
    list_after_response = await delete_test_client.get("/api/resources")
    assert list_after_response.status_code == 200
    resources_after = list_after_response.json()
    
    found_a_after = any(r["id"] == resource_a_id for r in resources_after)
    found_b_after = any(r["id"] == resource_b_id for r in resources_after)
    found_c_after = any(r["id"] == resource_c_id for r in resources_after)
    
    assert not found_a_after, \
        "Resource A should not appear in the list after cascade delete"
    assert not found_b_after, \
        "Resource B should not appear in the list after cascade delete (dependent of A)"
    assert not found_c_after, \
        "Resource C should not appear in the list after cascade delete (dependent of B)"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_delete_without_cascade_preserves_dependents(
    delete_test_client: AsyncClient
):
    """
    Feature: fastapi-crud-backend, Property 21: Delete removes from UI
    
    When deleting a resource with cascade=false (or no cascade parameter),
    only the target resource should be removed from the UI. Dependent
    resources should remain visible.
    
    This test verifies that:
    1. Resources with dependencies can be created
    2. Non-cascade delete removes only the target resource
    3. Dependent resources remain in the UI
    
    Validates: Requirements 11.3, 11.5
    """
    # Step 1: Create a dependency: A <- B (B depends on A)
    
    # Create resource A (no dependencies)
    create_a_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": "Resource A",
            "description": "Base resource",
            "dependencies": []
        }
    )
    assert create_a_response.status_code == 201
    resource_a_id = create_a_response.json()["id"]
    
    # Create resource B (depends on A)
    create_b_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": "Resource B",
            "description": "Depends on A",
            "dependencies": [resource_a_id]
        }
    )
    assert create_b_response.status_code == 201
    resource_b_id = create_b_response.json()["id"]
    
    # Step 2: Verify both resources appear in the list
    list_before_response = await delete_test_client.get("/api/resources")
    assert list_before_response.status_code == 200
    resources_before = list_before_response.json()
    
    assert any(r["id"] == resource_a_id for r in resources_before)
    assert any(r["id"] == resource_b_id for r in resources_before)
    
    # Step 3: Delete resource A without cascade (cascade=false or no parameter)
    # This should remove only A, leaving B in the list
    delete_response = await delete_test_client.delete(
        f"/api/resources/{resource_a_id}"
    )
    assert delete_response.status_code == 204
    
    # Step 4: Verify only A is removed, B remains
    list_after_response = await delete_test_client.get("/api/resources")
    assert list_after_response.status_code == 200
    resources_after = list_after_response.json()
    
    found_a_after = any(r["id"] == resource_a_id for r in resources_after)
    found_b_after = any(r["id"] == resource_b_id for r in resources_after)
    
    assert not found_a_after, \
        "Resource A should not appear in the list after deletion"
    assert found_b_after, \
        "Resource B should still appear in the list after non-cascade delete of A"
    
    # Step 5: Verify B's dependencies have been updated (A removed from dependencies)
    resource_b = next((r for r in resources_after if r["id"] == resource_b_id), None)
    assert resource_b is not None
    assert resource_a_id not in resource_b["dependencies"], \
        "Resource B should no longer have A in its dependencies after A is deleted"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_delete_nonexistent_resource_error(
    delete_test_client: AsyncClient
):
    """
    Feature: fastapi-crud-backend, Property 21: Delete removes from UI
    
    When attempting to delete a non-existent resource, the API should return
    a 404 error, and the frontend should display an appropriate error message.
    The resource list should remain unchanged.
    
    Validates: Requirements 11.4
    """
    # Get the current resource list
    list_before_response = await delete_test_client.get("/api/resources")
    assert list_before_response.status_code == 200
    resources_before = list_before_response.json()
    
    # Try to delete a non-existent resource
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    delete_response = await delete_test_client.delete(
        f"/api/resources/{fake_id}"
    )
    
    # Verify 404 error is returned
    assert delete_response.status_code == 404, \
        f"Expected 404 Not Found, got {delete_response.status_code}"
    
    error_data = delete_response.json()
    
    # Verify error response structure
    assert "error" in error_data, "Error response missing error field"
    assert "message" in error_data, "Error response missing message field"
    
    # Verify the resource list is unchanged
    list_after_response = await delete_test_client.get("/api/resources")
    assert list_after_response.status_code == 200
    resources_after = list_after_response.json()
    
    assert len(resources_after) == len(resources_before), \
        "Resource list should be unchanged after failed delete"


@pytest.mark.asyncio
@pytest.mark.property
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy(with_dependencies=False))
async def test_property_delete_and_recreate_with_same_name(
    delete_test_client: AsyncClient,
    resource_data
):
    """
    Feature: fastapi-crud-backend, Property 21: Delete removes from UI
    
    After deleting a resource, a new resource with the same name can be
    created. This verifies that deletion properly cleans up and allows
    reuse of names.
    
    Validates: Requirements 11.5
    """
    # Step 1: Create a resource
    create1_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": resource_data.name,
            "description": resource_data.description,
            "dependencies": resource_data.dependencies
        }
    )
    assert create1_response.status_code == 201
    resource1_id = create1_response.json()["id"]
    
    # Step 2: Delete the resource
    delete_response = await delete_test_client.delete(
        f"/api/resources/{resource1_id}"
    )
    assert delete_response.status_code == 204
    
    # Step 3: Verify the resource is removed from the list
    list_after_delete_response = await delete_test_client.get("/api/resources")
    assert list_after_delete_response.status_code == 200
    resources_after_delete = list_after_delete_response.json()
    
    found_after_delete = any(r["id"] == resource1_id for r in resources_after_delete)
    assert not found_after_delete, \
        "Resource should not appear in the list after deletion"
    
    # Step 4: Create a new resource with the same name
    create2_response = await delete_test_client.post(
        "/api/resources",
        json={
            "name": resource_data.name,
            "description": "New description",
            "dependencies": []
        }
    )
    assert create2_response.status_code == 201
    resource2_id = create2_response.json()["id"]
    
    # Verify it's a different resource (different ID)
    assert resource2_id != resource1_id, \
        "New resource should have a different ID"
    
    # Step 5: Verify the new resource appears in the list
    list_final_response = await delete_test_client.get("/api/resources")
    assert list_final_response.status_code == 200
    resources_final = list_final_response.json()
    
    found_new = any(r["id"] == resource2_id for r in resources_final)
    assert found_new, \
        "New resource should appear in the list"
    
    # Verify the old resource is still not in the list
    found_old = any(r["id"] == resource1_id for r in resources_final)
    assert not found_old, \
        "Old deleted resource should not reappear in the list"
