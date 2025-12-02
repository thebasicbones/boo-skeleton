"""Property-based tests for CRUD round-trips

Feature: fastapi-crud-backend, Property 1: Resource creation round-trip
Validates: Requirements 1.1, 2.1
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.resource import Base, Resource
from app.repositories.resource_repository import ResourceRepository
from app.schemas import ResourceCreate


# Strategy for generating valid resource names (1-100 characters, not just whitespace)
@st.composite
def valid_name_strategy(draw):
    """Generate valid resource names"""
    # Generate a non-empty string with at least one non-whitespace character
    name = draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
        min_size=1,
        max_size=100
    ))
    # Ensure it's not just whitespace
    if not name.strip():
        # If it's all whitespace, replace with a valid name
        name = draw(st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                blacklist_characters=' \t\n\r'
            ),
            min_size=1,
            max_size=100
        ))
    return name


# Strategy for generating valid resource descriptions (0-500 characters or None)
description_strategy = st.one_of(
    st.none(),
    st.text(max_size=500)
)


# Strategy for generating ResourceCreate objects without dependencies
@st.composite
def resource_create_strategy(draw):
    """Generate valid ResourceCreate objects without dependencies"""
    name = draw(valid_name_strategy())
    description = draw(description_strategy)
    
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=[]
    )


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


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(resource_data=resource_create_strategy())
async def test_resource_creation_roundtrip(resource_data):
    """
    Feature: fastapi-crud-backend, Property 1: Resource creation round-trip
    Validates: Requirements 1.1, 2.1
    
    For any valid resource data, creating a resource via POST and then 
    retrieving it via GET should return equivalent resource data with 
    a unique identifier assigned.
    """
    # Create in-memory database for this test
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        # Enable foreign key constraints for SQLite
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        repository = ResourceRepository(session)
        
        # Create the resource
        created_resource = await repository.create(resource_data)
        
        # Verify the resource was created with an ID
        assert created_resource.id is not None
        assert isinstance(created_resource.id, str)
        assert len(created_resource.id) > 0
        
        # Retrieve the resource by ID
        retrieved_resource = await repository.get_by_id(created_resource.id)
        
        # Verify the resource was retrieved
        assert retrieved_resource is not None
        
        # Verify equivalence of data
        assert retrieved_resource.id == created_resource.id
        assert retrieved_resource.name == resource_data.name.strip()
        
        # Handle description comparison (None vs empty string)
        expected_description = resource_data.description.strip() if resource_data.description and resource_data.description.strip() else None
        assert retrieved_resource.description == expected_description
        
        # Verify dependencies are empty (as per our strategy)
        assert retrieved_resource.dependencies == []
        
        # Verify timestamps exist
        assert retrieved_resource.created_at is not None
        assert retrieved_resource.updated_at is not None
    
    await engine.dispose()
