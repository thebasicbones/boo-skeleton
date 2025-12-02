"""Tests for ResourceRepository"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.resource import Base, Resource
from app.repositories.resource_repository import ResourceRepository
from app.schemas import ResourceCreate, ResourceUpdate


@pytest.fixture
async def db_session():
    """Create a test database session"""
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
def repository(db_session):
    """Create a ResourceRepository instance"""
    return ResourceRepository(db_session)


@pytest.mark.asyncio
async def test_create_resource(repository):
    """Test creating a resource"""
    data = ResourceCreate(
        name="Test Resource",
        description="A test resource",
        dependencies=[]
    )
    
    resource = await repository.create(data)
    
    assert resource.id is not None
    assert resource.name == "Test Resource"
    assert resource.description == "A test resource"
    assert resource.dependencies == []


@pytest.mark.asyncio
async def test_get_by_id(repository):
    """Test retrieving a resource by ID"""
    # Create a resource
    data = ResourceCreate(name="Test Resource", description="Test", dependencies=[])
    created = await repository.create(data)
    
    # Retrieve it
    retrieved = await repository.get_by_id(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == created.name


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository):
    """Test retrieving a non-existent resource"""
    result = await repository.get_by_id("non-existent-id")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(repository):
    """Test retrieving all resources"""
    # Create multiple resources
    data1 = ResourceCreate(name="Resource 1", dependencies=[])
    data2 = ResourceCreate(name="Resource 2", dependencies=[])
    
    await repository.create(data1)
    await repository.create(data2)
    
    # Get all
    resources = await repository.get_all()
    
    assert len(resources) == 2
    assert any(r.name == "Resource 1" for r in resources)
    assert any(r.name == "Resource 2" for r in resources)


@pytest.mark.asyncio
async def test_update_resource(repository):
    """Test updating a resource"""
    # Create a resource
    data = ResourceCreate(name="Original Name", description="Original", dependencies=[])
    created = await repository.create(data)
    
    # Update it
    update_data = ResourceUpdate(name="Updated Name", description="Updated description")
    updated = await repository.update(created.id, update_data)
    
    assert updated is not None
    assert updated.id == created.id
    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"


@pytest.mark.asyncio
async def test_update_non_existent(repository):
    """Test updating a non-existent resource"""
    update_data = ResourceUpdate(name="Updated Name")
    result = await repository.update("non-existent-id", update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_resource(repository):
    """Test deleting a resource"""
    # Create a resource
    data = ResourceCreate(name="To Delete", dependencies=[])
    created = await repository.create(data)
    
    # Delete it
    result = await repository.delete(created.id)
    assert result is True
    
    # Verify it's gone
    retrieved = await repository.get_by_id(created.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_non_existent(repository):
    """Test deleting a non-existent resource"""
    result = await repository.delete("non-existent-id")
    assert result is False


@pytest.mark.asyncio
async def test_create_with_dependencies(repository):
    """Test creating a resource with dependencies"""
    # Create dependency resources
    dep1 = await repository.create(ResourceCreate(name="Dependency 1", dependencies=[]))
    dep2 = await repository.create(ResourceCreate(name="Dependency 2", dependencies=[]))
    
    # Create resource with dependencies
    data = ResourceCreate(
        name="Main Resource",
        description="Has dependencies",
        dependencies=[dep1.id, dep2.id]
    )
    resource = await repository.create(data)
    
    assert len(resource.dependencies) == 2
    dep_ids = [d.id for d in resource.dependencies]
    assert dep1.id in dep_ids
    assert dep2.id in dep_ids


@pytest.mark.asyncio
async def test_update_dependencies(repository):
    """Test updating resource dependencies"""
    # Create resources
    dep1 = await repository.create(ResourceCreate(name="Dep 1", dependencies=[]))
    dep2 = await repository.create(ResourceCreate(name="Dep 2", dependencies=[]))
    resource = await repository.create(ResourceCreate(name="Main", dependencies=[dep1.id]))
    
    # Update dependencies
    update_data = ResourceUpdate(dependencies=[dep2.id])
    updated = await repository.update(resource.id, update_data)
    
    assert len(updated.dependencies) == 1
    assert updated.dependencies[0].id == dep2.id


@pytest.mark.asyncio
async def test_search_by_name(repository):
    """Test searching resources by name"""
    await repository.create(ResourceCreate(name="Frontend Service", dependencies=[]))
    await repository.create(ResourceCreate(name="Backend Service", dependencies=[]))
    await repository.create(ResourceCreate(name="Database", dependencies=[]))
    
    results = await repository.search("Service")
    
    assert len(results) == 2
    assert all("Service" in r.name for r in results)


@pytest.mark.asyncio
async def test_search_by_description(repository):
    """Test searching resources by description"""
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
    assert results[0].name == "Service A"


@pytest.mark.asyncio
async def test_search_empty_query(repository):
    """Test search with empty query returns all resources"""
    await repository.create(ResourceCreate(name="Resource 1", dependencies=[]))
    await repository.create(ResourceCreate(name="Resource 2", dependencies=[]))
    
    results = await repository.search("")
    
    assert len(results) == 2


@pytest.mark.asyncio
async def test_delete_cascade(repository):
    """Test cascade delete removes dependents"""
    # Create dependency chain: A -> B -> C
    resource_a = await repository.create(ResourceCreate(name="A", dependencies=[]))
    resource_b = await repository.create(ResourceCreate(
        name="B",
        dependencies=[resource_a.id]
    ))
    resource_c = await repository.create(ResourceCreate(
        name="C",
        dependencies=[resource_b.id]
    ))
    
    # Delete A with cascade
    await repository.delete(resource_a.id, cascade=True)
    
    # Verify A, B, and C are all deleted
    assert await repository.get_by_id(resource_a.id) is None
    assert await repository.get_by_id(resource_b.id) is None
    assert await repository.get_by_id(resource_c.id) is None


@pytest.mark.asyncio
async def test_delete_non_cascade(repository):
    """Test non-cascade delete preserves dependents"""
    # Create dependency: B -> A (B depends on A)
    resource_a = await repository.create(ResourceCreate(name="A", dependencies=[]))
    resource_b = await repository.create(ResourceCreate(
        name="B",
        dependencies=[resource_a.id]
    ))
    
    # Verify B depends on A initially
    assert len(resource_b.dependencies) == 1
    assert resource_b.dependencies[0].id == resource_a.id
    
    # Delete A without cascade
    await repository.delete(resource_a.id, cascade=False)
    
    # Verify A is deleted
    assert await repository.get_by_id(resource_a.id) is None
    
    # B should still exist (non-cascade means we don't delete the dependent resource B)
    b_after = await repository.get_by_id(resource_b.id)
    assert b_after is not None
    assert b_after.name == "B"
