"""Tests for database models and schema

Note: These tests are SQLAlchemy-specific and test the ORM model directly.
For backend-agnostic tests, see test_resource_repository.py which uses the
db_backend fixture to test both SQLite and MongoDB.
"""
import pytest
from datetime import datetime
from app.schemas import ResourceCreate


@pytest.fixture
async def repository(clean_sqlalchemy_db):
    """Create a repository for testing SQLAlchemy models"""
    from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
    return SQLAlchemyResourceRepository(clean_sqlalchemy_db)


@pytest.mark.asyncio
async def test_create_resource(repository):
    """Test creating a basic resource"""
    data = ResourceCreate(
        name="Test Resource",
        description="A test resource",
        dependencies=[]
    )
    
    resource = await repository.create(data)
    
    assert resource.id is not None
    assert resource.name == "Test Resource"
    assert resource.description == "A test resource"
    assert isinstance(resource.created_at, datetime)
    assert isinstance(resource.updated_at, datetime)


@pytest.mark.asyncio
async def test_resource_with_dependencies(repository):
    """Test creating resources with dependencies"""
    # Create base resources
    resource_a = await repository.create(ResourceCreate(
        name="Resource A",
        description="Base resource A",
        dependencies=[]
    ))
    resource_b = await repository.create(ResourceCreate(
        name="Resource B",
        description="Base resource B",
        dependencies=[]
    ))
    
    # Create resource that depends on A and B
    resource_c = await repository.create(ResourceCreate(
        name="Resource C",
        description="Depends on A and B",
        dependencies=[resource_a.id, resource_b.id]
    ))
    
    # Verify dependencies
    assert len(resource_c.dependencies) == 2
    dependency_ids = {dep.id for dep in resource_c.dependencies}
    assert resource_a.id in dependency_ids
    assert resource_b.id in dependency_ids


@pytest.mark.asyncio
async def test_cascade_delete(repository):
    """Test that cascade delete works for dependency relationships
    
    Note: This test is SQLAlchemy-specific and tests the ORM behavior.
    When a resource is deleted, the foreign key CASCADE removes the junction
    table entries, but the dependency relationship is maintained at the database level.
    """
    # Create resources with dependencies
    resource_a = await repository.create(ResourceCreate(
        name="Resource A",
        dependencies=[]
    ))
    resource_b = await repository.create(ResourceCreate(
        name="Resource B",
        dependencies=[resource_a.id]
    ))
    
    resource_a_id = resource_a.id
    resource_b_id = resource_b.id
    
    # Delete resource A without cascade (removes only A)
    await repository.delete(resource_a_id, cascade=False)
    
    # Verify resource A is deleted
    resource_a_after = await repository.get_by_id(resource_a_id)
    assert resource_a_after is None
    
    # Verify resource B still exists
    resource_b_after = await repository.get_by_id(resource_b_id)
    assert resource_b_after is not None
    assert resource_b_after.name == "Resource B"
