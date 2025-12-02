"""Tests for database models and schema"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.resource import Base, Resource
from datetime import datetime


@pytest.fixture
async def db_session():
    """Create a test database session"""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
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


@pytest.mark.asyncio
async def test_create_resource(db_session):
    """Test creating a basic resource"""
    resource = Resource(
        name="Test Resource",
        description="A test resource"
    )
    
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)
    
    assert resource.id is not None
    assert resource.name == "Test Resource"
    assert resource.description == "A test resource"
    assert isinstance(resource.created_at, datetime)
    assert isinstance(resource.updated_at, datetime)


@pytest.mark.asyncio
async def test_resource_with_dependencies(db_session):
    """Test creating resources with dependencies"""
    # Create base resources
    resource_a = Resource(name="Resource A", description="Base resource A")
    resource_b = Resource(name="Resource B", description="Base resource B")
    
    db_session.add(resource_a)
    db_session.add(resource_b)
    await db_session.commit()
    await db_session.refresh(resource_a)
    await db_session.refresh(resource_b)
    
    # Create resource that depends on A and B
    resource_c = Resource(
        name="Resource C",
        description="Depends on A and B"
    )
    resource_c.dependencies.append(resource_a)
    resource_c.dependencies.append(resource_b)
    
    db_session.add(resource_c)
    await db_session.commit()
    await db_session.refresh(resource_c)
    
    # Verify dependencies
    assert len(resource_c.dependencies) == 2
    dependency_names = {dep.name for dep in resource_c.dependencies}
    assert "Resource A" in dependency_names
    assert "Resource B" in dependency_names


@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    """Test that cascade delete works for dependency relationships"""
    # Create resources with dependencies
    resource_a = Resource(name="Resource A")
    resource_b = Resource(name="Resource B")
    resource_b.dependencies.append(resource_a)
    
    db_session.add(resource_a)
    db_session.add(resource_b)
    await db_session.commit()
    
    resource_a_id = resource_a.id
    resource_b_id = resource_b.id
    
    # Delete resource A
    await db_session.delete(resource_a)
    await db_session.commit()
    
    # Verify resource A is deleted
    from sqlalchemy import select
    result_a = await db_session.execute(
        select(Resource).where(Resource.id == resource_a_id)
    )
    resource_a_after = result_a.scalar_one_or_none()
    assert resource_a_after is None
    
    # Verify resource B still exists
    result_b = await db_session.execute(
        select(Resource).where(Resource.id == resource_b_id)
    )
    resource_b_after = result_b.scalar_one_or_none()
    assert resource_b_after is not None
    
    # The dependency relationship should be automatically removed by CASCADE
    # This is handled at the database level by the foreign key constraint
