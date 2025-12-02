"""Property-based tests for SQLAlchemy backend abstraction baseline

Feature: mongodb-integration, Property 4: Backend abstraction transparency (SQLAlchemy baseline)
Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

This test establishes a baseline for the SQLAlchemy repository implementation
to ensure it correctly implements the BaseResourceRepository interface.
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.sqlalchemy_resource import Base, Resource
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.schemas import ResourceCreate, ResourceUpdate


# Strategy for generating valid resource names
@st.composite
def valid_name_strategy(draw):
    """Generate valid resource names (1-100 characters, non-empty after strip)"""
    name = draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
        min_size=1,
        max_size=100
    ))
    if not name.strip():
        name = draw(st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                blacklist_characters=' \t\n\r'
            ),
            min_size=1,
            max_size=100
        ))
    return name


# Strategy for generating ResourceCreate objects
@st.composite
def resource_create_strategy(draw):
    """Generate valid ResourceCreate data"""
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=[]  # No dependencies for baseline test
    )


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(resource_data=resource_create_strategy())
async def test_sqlalchemy_repository_crud_operations(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (SQLAlchemy baseline)
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
    
    For any valid resource data, the SQLAlchemy repository should correctly:
    - Create a resource (2.2)
    - Retrieve the resource by ID (2.3)
    - Update the resource (2.4)
    - Delete the resource (2.5)
    - List all resources (2.6)
    - Search for resources (2.6)
    
    This establishes a baseline for the repository interface implementation.
    """
    # Create in-memory database for this test
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        repository = SQLAlchemyResourceRepository(session)
        
        # Test CREATE (Requirement 2.2)
        created_resource = await repository.create(resource_data)
        assert created_resource is not None
        assert created_resource.id is not None
        assert created_resource.name == resource_data.name
        assert created_resource.description == resource_data.description
        assert created_resource.created_at is not None
        assert created_resource.updated_at is not None
        
        resource_id = created_resource.id
        
        # Test GET_BY_ID (Requirement 2.3)
        retrieved_resource = await repository.get_by_id(resource_id)
        assert retrieved_resource is not None
        assert retrieved_resource.id == resource_id
        assert retrieved_resource.name == resource_data.name
        assert retrieved_resource.description == resource_data.description
        
        # Test GET_ALL (Requirement 2.6)
        all_resources = await repository.get_all()
        assert len(all_resources) == 1
        assert all_resources[0].id == resource_id
        
        # Test SEARCH (Requirement 2.6)
        search_results = await repository.search(resource_data.name[:5] if len(resource_data.name) >= 5 else resource_data.name)
        assert len(search_results) >= 1
        assert any(r.id == resource_id for r in search_results)
        
        # Test UPDATE (Requirement 2.4)
        update_data = ResourceUpdate(
            name=resource_data.name + "_updated",
            description="Updated description"
        )
        updated_resource = await repository.update(resource_id, update_data)
        assert updated_resource is not None
        assert updated_resource.id == resource_id
        assert updated_resource.name == update_data.name
        assert updated_resource.description == update_data.description
        
        # Verify update persisted
        retrieved_after_update = await repository.get_by_id(resource_id)
        assert retrieved_after_update.name == update_data.name
        assert retrieved_after_update.description == update_data.description
        
        # Test DELETE (Requirement 2.5)
        delete_result = await repository.delete(resource_id, cascade=False)
        assert delete_result is True
        
        # Verify deletion
        deleted_resource = await repository.get_by_id(resource_id)
        assert deleted_resource is None
        
        # Verify get_all returns empty list
        all_resources_after_delete = await repository.get_all()
        assert len(all_resources_after_delete) == 0
    
    await engine.dispose()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=50)
@given(resource_data=resource_create_strategy())
async def test_sqlalchemy_repository_interface_compliance(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (SQLAlchemy baseline)
    Validates: Requirement 2.1
    
    For any valid resource data, the SQLAlchemy repository should implement
    the BaseResourceRepository interface correctly without exposing
    backend-specific details.
    """
    # Create in-memory database for this test
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        repository = SQLAlchemyResourceRepository(session)
        
        # Verify repository implements the interface
        from app.repositories.base_resource_repository import BaseResourceRepository
        assert isinstance(repository, BaseResourceRepository)
        
        # Verify all interface methods are callable
        assert callable(repository.get_all)
        assert callable(repository.get_by_id)
        assert callable(repository.create)
        assert callable(repository.update)
        assert callable(repository.delete)
        assert callable(repository.search)
        
        # Test that operations work through the interface
        created = await repository.create(resource_data)
        assert created is not None
        
        retrieved = await repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
    
    await engine.dispose()
