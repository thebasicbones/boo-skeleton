"""Tests for ResourceRepository

These tests use the db_backend fixture to run against both SQLite and MongoDB,
ensuring backend abstraction transparency.
"""
import pytest
from typing import Union, Dict, Any, List
from app.schemas import ResourceCreate, ResourceUpdate


def get_field(obj: Union[Dict, Any], field: str) -> Any:
    """
    Get a field value from either a dictionary or an object.
    
    This helper function allows tests to work with both MongoDB (dict) and
    SQLAlchemy (object) return values in a backend-agnostic way.
    
    Args:
        obj: Dictionary or object to get field from
        field: Field name to retrieve
        
    Returns:
        Field value
    """
    if isinstance(obj, dict):
        return obj.get(field)
    else:
        return getattr(obj, field)


def get_dependencies(obj: Union[Dict, Any]) -> List[str]:
    """
    Get dependency IDs from either a dictionary or an object.
    
    For MongoDB: dependencies are stored as a list of strings
    For SQLAlchemy: dependencies are Resource objects with .id attributes
    
    Args:
        obj: Dictionary or object to get dependencies from
        
    Returns:
        List of dependency IDs
    """
    if isinstance(obj, dict):
        return obj.get('dependencies', [])
    else:
        deps = getattr(obj, 'dependencies', [])
        return [d.id for d in deps]


@pytest.mark.asyncio
async def test_create_resource(db_backend):
    """Test creating a resource"""
    backend_name, repository = db_backend
    
    data = ResourceCreate(
        name="Test Resource",
        description="A test resource",
        dependencies=[]
    )
    
    resource = await repository.create(data)
    
    assert get_field(resource, 'id') is not None
    assert get_field(resource, 'name') == "Test Resource"
    assert get_field(resource, 'description') == "A test resource"
    assert get_dependencies(resource) == []


@pytest.mark.asyncio
async def test_get_by_id(db_backend):
    """Test retrieving a resource by ID"""
    backend_name, repository = db_backend
    
    # Create a resource
    data = ResourceCreate(name="Test Resource", description="Test", dependencies=[])
    created = await repository.create(data)
    created_id = get_field(created, 'id')
    
    # Retrieve it
    retrieved = await repository.get_by_id(created_id)
    
    assert retrieved is not None
    assert get_field(retrieved, 'id') == created_id
    assert get_field(retrieved, 'name') == get_field(created, 'name')


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_backend):
    """Test retrieving a non-existent resource"""
    backend_name, repository = db_backend
    
    result = await repository.get_by_id("non-existent-id")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(db_backend):
    """Test retrieving all resources"""
    backend_name, repository = db_backend
    
    # Create multiple resources
    data1 = ResourceCreate(name="Resource 1", dependencies=[])
    data2 = ResourceCreate(name="Resource 2", dependencies=[])
    
    await repository.create(data1)
    await repository.create(data2)
    
    # Get all
    resources = await repository.get_all()
    
    assert len(resources) == 2
    assert any(get_field(r, 'name') == "Resource 1" for r in resources)
    assert any(get_field(r, 'name') == "Resource 2" for r in resources)


@pytest.mark.asyncio
async def test_update_resource(db_backend):
    """Test updating a resource"""
    backend_name, repository = db_backend
    
    # Create a resource
    data = ResourceCreate(name="Original Name", description="Original", dependencies=[])
    created = await repository.create(data)
    created_id = get_field(created, 'id')
    
    # Update it
    update_data = ResourceUpdate(name="Updated Name", description="Updated description")
    updated = await repository.update(created_id, update_data)
    
    assert updated is not None
    assert get_field(updated, 'id') == created_id
    assert get_field(updated, 'name') == "Updated Name"
    assert get_field(updated, 'description') == "Updated description"


@pytest.mark.asyncio
async def test_update_non_existent(db_backend):
    """Test updating a non-existent resource"""
    backend_name, repository = db_backend
    
    update_data = ResourceUpdate(name="Updated Name")
    result = await repository.update("non-existent-id", update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_resource(db_backend):
    """Test deleting a resource"""
    backend_name, repository = db_backend
    
    # Create a resource
    data = ResourceCreate(name="To Delete", dependencies=[])
    created = await repository.create(data)
    created_id = get_field(created, 'id')
    
    # Delete it
    result = await repository.delete(created_id)
    assert result is True
    
    # Verify it's gone
    retrieved = await repository.get_by_id(created_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_non_existent(db_backend):
    """Test deleting a non-existent resource"""
    backend_name, repository = db_backend
    
    result = await repository.delete("non-existent-id")
    assert result is False


@pytest.mark.asyncio
async def test_create_with_dependencies(db_backend):
    """Test creating a resource with dependencies"""
    backend_name, repository = db_backend
    
    # Create dependency resources
    dep1 = await repository.create(ResourceCreate(name="Dependency 1", dependencies=[]))
    dep2 = await repository.create(ResourceCreate(name="Dependency 2", dependencies=[]))
    dep1_id = get_field(dep1, 'id')
    dep2_id = get_field(dep2, 'id')
    
    # Create resource with dependencies
    data = ResourceCreate(
        name="Main Resource",
        description="Has dependencies",
        dependencies=[dep1_id, dep2_id]
    )
    resource = await repository.create(data)
    
    dep_ids = get_dependencies(resource)
    assert len(dep_ids) == 2
    assert dep1_id in dep_ids
    assert dep2_id in dep_ids


@pytest.mark.asyncio
async def test_update_dependencies(db_backend):
    """Test updating resource dependencies"""
    backend_name, repository = db_backend
    
    # Create resources
    dep1 = await repository.create(ResourceCreate(name="Dep 1", dependencies=[]))
    dep2 = await repository.create(ResourceCreate(name="Dep 2", dependencies=[]))
    dep1_id = get_field(dep1, 'id')
    dep2_id = get_field(dep2, 'id')
    
    resource = await repository.create(ResourceCreate(name="Main", dependencies=[dep1_id]))
    resource_id = get_field(resource, 'id')
    
    # Update dependencies
    update_data = ResourceUpdate(dependencies=[dep2_id])
    updated = await repository.update(resource_id, update_data)
    
    updated_deps = get_dependencies(updated)
    assert len(updated_deps) == 1
    assert dep2_id in updated_deps


@pytest.mark.asyncio
async def test_search_by_name(db_backend):
    """Test searching resources by name"""
    backend_name, repository = db_backend
    
    await repository.create(ResourceCreate(name="Frontend Service", dependencies=[]))
    await repository.create(ResourceCreate(name="Backend Service", dependencies=[]))
    await repository.create(ResourceCreate(name="Database", dependencies=[]))
    
    results = await repository.search("Service")
    
    assert len(results) == 2
    assert all("Service" in get_field(r, 'name') for r in results)


@pytest.mark.asyncio
async def test_search_by_description(db_backend):
    """Test searching resources by description"""
    backend_name, repository = db_backend
    
    await repository.create(ResourceCreate(
        name="Service A",
        description="Python backend",
        dependencies=[]
    ))
    await repository.create(ResourceCreate(
        name="Service B",
        description="React frontend",
        dependencies=[]
    ))
    
    results = await repository.search("Python")
    
    assert len(results) == 1
    assert get_field(results[0], 'name') == "Service A"


@pytest.mark.asyncio
async def test_search_empty_query(db_backend):
    """Test search with empty query returns all resources"""
    backend_name, repository = db_backend
    
    await repository.create(ResourceCreate(name="Resource 1", dependencies=[]))
    await repository.create(ResourceCreate(name="Resource 2", dependencies=[]))
    
    results = await repository.search("")
    
    assert len(results) == 2


@pytest.mark.asyncio
async def test_delete_cascade(db_backend):
    """Test cascade delete removes dependents"""
    backend_name, repository = db_backend
    
    # Create dependency chain: A -> B -> C
    resource_a = await repository.create(ResourceCreate(name="A", dependencies=[]))
    resource_a_id = get_field(resource_a, 'id')
    
    resource_b = await repository.create(ResourceCreate(
        name="B",
        dependencies=[resource_a_id]
    ))
    resource_b_id = get_field(resource_b, 'id')
    
    resource_c = await repository.create(ResourceCreate(
        name="C",
        dependencies=[resource_b_id]
    ))
    resource_c_id = get_field(resource_c, 'id')
    
    # Delete A with cascade
    await repository.delete(resource_a_id, cascade=True)
    
    # Verify A, B, and C are all deleted
    assert await repository.get_by_id(resource_a_id) is None
    assert await repository.get_by_id(resource_b_id) is None
    assert await repository.get_by_id(resource_c_id) is None


@pytest.mark.asyncio
async def test_delete_non_cascade(db_backend):
    """Test non-cascade delete preserves dependents"""
    backend_name, repository = db_backend
    
    # Create dependency: B -> A (B depends on A)
    resource_a = await repository.create(ResourceCreate(name="A", dependencies=[]))
    resource_a_id = get_field(resource_a, 'id')
    
    resource_b = await repository.create(ResourceCreate(
        name="B",
        dependencies=[resource_a_id]
    ))
    resource_b_id = get_field(resource_b, 'id')
    
    # Verify B depends on A initially
    b_deps = get_dependencies(resource_b)
    assert len(b_deps) == 1
    assert resource_a_id in b_deps
    
    # Delete A without cascade
    await repository.delete(resource_a_id, cascade=False)
    
    # Verify A is deleted
    assert await repository.get_by_id(resource_a_id) is None
    
    # B should still exist (non-cascade means we don't delete the dependent resource B)
    b_after = await repository.get_by_id(resource_b_id)
    assert b_after is not None
    assert get_field(b_after, 'name') == "B"
