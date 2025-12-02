"""Property-based tests for cascade delete functionality

Feature: fastapi-crud-backend, Property 12: Cascade delete removes dependents
Validates: Requirements 11.2
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.sqlalchemy_resource import Base, Resource
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.schemas import ResourceCreate


# Strategy for generating valid resource names
@st.composite
def valid_name_strategy(draw):
    """Generate valid resource names"""
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


# Strategy for generating dependency graphs (DAGs)
@st.composite
def dependency_graph_strategy(draw):
    """
    Generate a random dependency graph (DAG).
    
    Returns a list of ResourceCreate objects where later resources
    can depend on earlier resources (ensuring no cycles).
    """
    # Generate 2-10 resources
    num_resources = draw(st.integers(min_value=2, max_value=10))
    
    resources = []
    for i in range(num_resources):
        name = draw(valid_name_strategy())
        description = draw(st.one_of(st.none(), st.text(max_size=100)))
        
        # Can only depend on resources created before this one (ensures DAG)
        # Randomly select 0-3 dependencies from earlier resources
        if i > 0:
            max_deps = min(3, i)
            num_deps = draw(st.integers(min_value=0, max_value=max_deps))
            # We'll store indices for now, will convert to IDs after creation
            dependency_indices = draw(st.lists(
                st.integers(min_value=0, max_value=i-1),
                min_size=num_deps,
                max_size=num_deps,
                unique=True
            ))
        else:
            dependency_indices = []
        
        resources.append({
            'name': name,
            'description': description,
            'dependency_indices': dependency_indices
        })
    
    return resources


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(graph_data=dependency_graph_strategy())
async def test_cascade_delete_removes_all_dependents(graph_data):
    """
    Feature: fastapi-crud-backend, Property 12: Cascade delete removes dependents
    Validates: Requirements 11.2
    
    For any resource with downstream dependencies, deleting with cascade=true 
    should remove the resource and all resources that depend on it 
    (directly or transitively).
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
        
        # Create all resources and track their IDs
        created_resources = []
        resource_ids = []
        
        for resource_data in graph_data:
            # Convert dependency indices to actual IDs
            dependency_ids = [
                resource_ids[idx] 
                for idx in resource_data['dependency_indices']
            ]
            
            resource_create = ResourceCreate(
                name=resource_data['name'],
                description=resource_data['description'],
                dependencies=dependency_ids
            )
            
            created = await repository.create(resource_create)
            created_resources.append(created)
            resource_ids.append(created.id)
        
        # Find a resource that has at least one dependent
        # (a resource that other resources depend on)
        target_resource_id = None
        expected_deleted_ids = set()
        
        for i, resource_id in enumerate(resource_ids):
            # Check if any later resources depend on this one
            dependents = []
            for j, other_data in enumerate(graph_data):
                if i in other_data['dependency_indices']:
                    dependents.append(j)
            
            if dependents:
                # Found a resource with dependents
                target_resource_id = resource_id
                
                # Calculate all transitive dependents
                expected_deleted_ids.add(target_resource_id)
                to_process = dependents[:]
                processed = set()
                
                while to_process:
                    dep_idx = to_process.pop(0)
                    if dep_idx in processed:
                        continue
                    processed.add(dep_idx)
                    expected_deleted_ids.add(resource_ids[dep_idx])
                    
                    # Find dependents of this dependent
                    for k, other_data in enumerate(graph_data):
                        if dep_idx in other_data['dependency_indices']:
                            if k not in processed:
                                to_process.append(k)
                
                break
        
        # If no resource has dependents, skip this test case
        assume(target_resource_id is not None)
        assume(len(expected_deleted_ids) > 1)  # At least the target + 1 dependent
        
        # Perform cascade delete
        delete_result = await repository.delete(target_resource_id, cascade=True)
        assert delete_result is True
        
        # Verify all expected resources were deleted
        for resource_id in expected_deleted_ids:
            deleted_resource = await repository.get_by_id(resource_id)
            assert deleted_resource is None, \
                f"Resource {resource_id} should have been deleted but still exists"
        
        # Verify resources NOT in the dependent chain still exist
        for resource_id in resource_ids:
            if resource_id not in expected_deleted_ids:
                remaining_resource = await repository.get_by_id(resource_id)
                assert remaining_resource is not None, \
                    f"Resource {resource_id} should still exist but was deleted"
    
    await engine.dispose()
