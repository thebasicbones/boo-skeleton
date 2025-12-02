"""Property-based tests for update persistence

Feature: fastapi-crud-backend, Property 5: Update persistence
Validates: Requirements 3.1

For any existing resource and valid update data, updating the resource via PUT 
and then retrieving it should return the updated data.
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.sqlalchemy_resource import Base, Resource
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.schemas import ResourceCreate, ResourceUpdate


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


# Strategy for generating ResourceUpdate objects
@st.composite
def resource_update_strategy(draw):
    """Generate valid ResourceUpdate objects without dependencies"""
    # Randomly decide which fields to update (at least one)
    update_name = draw(st.booleans())
    update_description = draw(st.booleans())
    
    # Ensure at least one field is updated
    if not update_name and not update_description:
        update_name = True
    
    name = draw(valid_name_strategy()) if update_name else None
    description = draw(description_strategy) if update_description else None
    
    return ResourceUpdate(
        name=name,
        description=description,
        dependencies=None  # Not testing dependency updates in this property
    )


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(
    initial_data=resource_create_strategy(),
    update_data=resource_update_strategy()
)
async def test_update_persistence(initial_data, update_data):
    """
    Feature: fastapi-crud-backend, Property 5: Update persistence
    Validates: Requirements 3.1
    
    For any existing resource and valid update data, updating the resource 
    via PUT and then retrieving it should return the updated data.
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
        repository = SQLAlchemyResourceRepository(session)
        
        # Create the initial resource
        created_resource = await repository.create(initial_data)
        resource_id = created_resource.id
        
        # Verify the resource was created
        assert resource_id is not None
        
        # Update the resource
        updated_resource = await repository.update(resource_id, update_data)
        
        # Verify the update succeeded
        assert updated_resource is not None
        assert updated_resource.id == resource_id
        
        # Retrieve the resource again to verify persistence
        retrieved_resource = await repository.get_by_id(resource_id)
        
        # Verify the resource was retrieved
        assert retrieved_resource is not None
        assert retrieved_resource.id == resource_id
        
        # Verify the updated fields persisted correctly
        if update_data.name is not None:
            # Name was updated
            expected_name = update_data.name.strip()
            assert retrieved_resource.name == expected_name
            assert updated_resource.name == expected_name
        else:
            # Name was not updated, should remain the same
            expected_name = initial_data.name.strip()
            assert retrieved_resource.name == expected_name
        
        if update_data.description is not None:
            # Description was updated
            expected_description = update_data.description.strip() if update_data.description and update_data.description.strip() else None
            assert retrieved_resource.description == expected_description
            assert updated_resource.description == expected_description
        else:
            # Description was not updated, should remain the same
            expected_description = initial_data.description.strip() if initial_data.description and initial_data.description.strip() else None
            assert retrieved_resource.description == expected_description
        
        # Verify dependencies remain unchanged (empty in this test)
        assert retrieved_resource.dependencies == []
        
        # Verify timestamps
        assert retrieved_resource.created_at is not None
        assert retrieved_resource.updated_at is not None
        # Updated timestamp should be >= created timestamp
        assert retrieved_resource.updated_at >= retrieved_resource.created_at
    
    await engine.dispose()
