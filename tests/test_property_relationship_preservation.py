"""Property-based tests for relationship preservation across backends

Feature: mongodb-integration, Property 8: Relationship preservation
Validates: Requirements 3.4

This test verifies that resources with dependencies maintain the same
dependency IDs when stored and retrieved from either backend.
"""
import pytest
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.sqlalchemy_resource import Base
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.schemas import ResourceCreate


def resource_to_dict(resource):
    """
    Convert a Resource object (SQLAlchemy ORM) or dict to a standardized dict format.
    
    This helper ensures consistent comparison between SQLAlchemy and MongoDB results.
    """
    if isinstance(resource, dict):
        return resource
    
    # Convert SQLAlchemy Resource object to dict
    return {
        'id': resource.id,
        'name': resource.name,
        'description': resource.description,
        'dependencies': [dep.id for dep in resource.dependencies] if hasattr(resource, 'dependencies') and resource.dependencies else [],
        'created_at': resource.created_at,
        'updated_at': resource.updated_at
    }


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


# Strategy for generating ResourceCreate objects with dependencies
@st.composite
def resource_with_dependencies_strategy(draw, dependency_ids):
    """
    Generate valid ResourceCreate data with dependencies.
    
    Args:
        dependency_ids: List of valid dependency IDs to choose from
    
    Returns:
        ResourceCreate object with dependencies
    """
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    
    # Generate a list of dependencies (0 to min(5, len(dependency_ids)))
    max_deps = min(5, len(dependency_ids))
    if max_deps > 0:
        num_deps = draw(st.integers(min_value=0, max_value=max_deps))
        if num_deps > 0:
            dependencies = draw(st.lists(
                st.sampled_from(dependency_ids),
                min_size=num_deps,
                max_size=num_deps,
                unique=True
            ))
        else:
            dependencies = []
    else:
        dependencies = []
    
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=dependencies
    )


# Check if MongoDB is available
def is_mongodb_available():
    """Check if MongoDB is available for testing"""
    import socket
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    
    # Parse host and port from URL
    if "://" in mongodb_url:
        host_port = mongodb_url.split("://")[1].split("/")[0]
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 27017
    else:
        host = "localhost"
        port = 27017
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    num_dependencies=st.integers(min_value=0, max_value=5),
    seed=st.integers(min_value=0, max_value=1000000)
)
async def test_sqlalchemy_relationship_preservation(num_dependencies, seed):
    """
    Feature: mongodb-integration, Property 8: Relationship preservation
    Validates: Requirements 3.4
    
    For any resource with dependencies, storing the resource in SQLAlchemy backend
    and then retrieving it should return the resource with the same dependency IDs
    in the dependencies array.
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
        
        # CREATE DEPENDENCY RESOURCES: Create resources that will be dependencies
        dependency_ids = []
        for i in range(num_dependencies):
            dep_data = ResourceCreate(
                name=f"Dependency_{seed}_{i}",
                description=f"Dependency resource {i}",
                dependencies=[]
            )
            dep_resource_obj = await repository.create(dep_data)
            dep_resource = resource_to_dict(dep_resource_obj)
            dependency_ids.append(dep_resource['id'])
        
        # CREATE RESOURCE WITH DEPENDENCIES
        resource_data = ResourceCreate(
            name=f"Resource_with_deps_{seed}",
            description="Resource with dependencies",
            dependencies=dependency_ids
        )
        
        created_resource_obj = await repository.create(resource_data)
        created_resource = resource_to_dict(created_resource_obj)
        
        # Verify resource was created with dependencies
        assert created_resource is not None
        assert 'dependencies' in created_resource
        
        # Store the original dependency IDs for comparison
        original_dependencies = sorted(created_resource['dependencies'])
        
        # RETRIEVE: Retrieve the resource by ID (Requirement 3.4)
        retrieved_resource_obj = await repository.get_by_id(created_resource['id'])
        retrieved_resource = resource_to_dict(retrieved_resource_obj)
        
        # Verify resource was retrieved
        assert retrieved_resource is not None
        
        # RELATIONSHIP PRESERVATION: Verify dependency IDs are preserved
        retrieved_dependencies = sorted(retrieved_resource['dependencies'])
        
        # The dependencies array should contain the same IDs
        assert len(retrieved_dependencies) == len(original_dependencies), \
            f"Expected {len(original_dependencies)} dependencies, got {len(retrieved_dependencies)}"
        
        assert retrieved_dependencies == original_dependencies, \
            f"Dependency IDs not preserved. Expected {original_dependencies}, got {retrieved_dependencies}"
        
        # Verify each dependency ID is in the original list
        for dep_id in retrieved_dependencies:
            assert dep_id in dependency_ids, \
                f"Dependency ID {dep_id} not in original dependency list"
    
    await engine.dispose()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    num_dependencies=st.integers(min_value=0, max_value=5),
    seed=st.integers(min_value=0, max_value=1000000)
)
async def test_mongodb_relationship_preservation(num_dependencies, seed):
    """
    Feature: mongodb-integration, Property 8: Relationship preservation
    Validates: Requirements 3.4
    
    For any resource with dependencies, storing the resource in MongoDB backend
    and then retrieving it should return the resource with the same dependency IDs
    in the dependencies array.
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_relationship_{os.getpid()}"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]
    
    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")
        
        repository = MongoDBResourceRepository(db)
        
        # CREATE DEPENDENCY RESOURCES: Create resources that will be dependencies
        dependency_ids = []
        for i in range(num_dependencies):
            dep_data = ResourceCreate(
                name=f"Dependency_{seed}_{i}",
                description=f"Dependency resource {i}",
                dependencies=[]
            )
            dep_resource = await repository.create(dep_data)
            dependency_ids.append(dep_resource['id'])
        
        # CREATE RESOURCE WITH DEPENDENCIES
        resource_data = ResourceCreate(
            name=f"Resource_with_deps_{seed}",
            description="Resource with dependencies",
            dependencies=dependency_ids
        )
        
        created_resource = await repository.create(resource_data)
        
        # Verify resource was created with dependencies
        assert created_resource is not None
        assert 'dependencies' in created_resource
        
        # Store the original dependency IDs for comparison
        original_dependencies = sorted(created_resource['dependencies'])
        
        # RETRIEVE: Retrieve the resource by ID (Requirement 3.4)
        retrieved_resource = await repository.get_by_id(created_resource['id'])
        
        # Verify resource was retrieved
        assert retrieved_resource is not None
        
        # RELATIONSHIP PRESERVATION: Verify dependency IDs are preserved
        retrieved_dependencies = sorted(retrieved_resource['dependencies'])
        
        # The dependencies array should contain the same IDs
        assert len(retrieved_dependencies) == len(original_dependencies), \
            f"Expected {len(original_dependencies)} dependencies, got {len(retrieved_dependencies)}"
        
        assert retrieved_dependencies == original_dependencies, \
            f"Dependency IDs not preserved. Expected {original_dependencies}, got {retrieved_dependencies}"
        
        # Verify each dependency ID is in the original list
        for dep_id in retrieved_dependencies:
            assert dep_id in dependency_ids, \
                f"Dependency ID {dep_id} not in original dependency list"
        
    finally:
        # Cleanup: drop test database
        await client.drop_database(test_db_name)
        client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    num_dependencies=st.integers(min_value=0, max_value=5),
    seed=st.integers(min_value=0, max_value=1000000)
)
async def test_backend_equivalence_relationship_preservation(num_dependencies, seed):
    """
    Feature: mongodb-integration, Property 8: Relationship preservation
    Validates: Requirements 3.4
    
    For any resource with dependencies, the relationship preservation behavior
    should be equivalent between SQLAlchemy and MongoDB backends. Both should:
    - Store dependency IDs correctly
    - Retrieve resources with the same dependency IDs
    - Preserve the dependency relationships
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Setup SQLAlchemy
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
    
    # Setup MongoDB
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_relationship_equiv_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # CREATE DEPENDENCY RESOURCES in both backends
            sqlalchemy_dep_ids = []
            mongodb_dep_ids = []
            
            for i in range(num_dependencies):
                dep_data = ResourceCreate(
                    name=f"Dependency_{seed}_{i}",
                    description=f"Dependency resource {i}",
                    dependencies=[]
                )
                
                # Create in SQLAlchemy
                sqlalchemy_dep_obj = await sqlalchemy_repo.create(dep_data)
                sqlalchemy_dep = resource_to_dict(sqlalchemy_dep_obj)
                sqlalchemy_dep_ids.append(sqlalchemy_dep['id'])
                
                # Create in MongoDB
                mongodb_dep = await mongodb_repo.create(dep_data)
                mongodb_dep_ids.append(mongodb_dep['id'])
            
            # CREATE RESOURCES WITH DEPENDENCIES in both backends
            sqlalchemy_resource_data = ResourceCreate(
                name=f"SQLAlchemy_Resource_{seed}",
                description="Resource with dependencies",
                dependencies=sqlalchemy_dep_ids
            )
            
            mongodb_resource_data = ResourceCreate(
                name=f"MongoDB_Resource_{seed}",
                description="Resource with dependencies",
                dependencies=mongodb_dep_ids
            )
            
            # Create in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(sqlalchemy_resource_data)
            mongodb_created = await mongodb_repo.create(mongodb_resource_data)
            
            sqlalchemy_created = resource_to_dict(sqlalchemy_created_obj)
            
            # Retrieve from both backends
            sqlalchemy_retrieved_obj = await sqlalchemy_repo.get_by_id(sqlalchemy_created['id'])
            mongodb_retrieved = await mongodb_repo.get_by_id(mongodb_created['id'])
            
            sqlalchemy_retrieved = resource_to_dict(sqlalchemy_retrieved_obj)
            
            # Verify both backends preserve dependencies
            sqlalchemy_deps = sorted(sqlalchemy_retrieved['dependencies'])
            mongodb_deps = sorted(mongodb_retrieved['dependencies'])
            
            # Both should have the same number of dependencies
            assert len(sqlalchemy_deps) == num_dependencies, \
                f"SQLAlchemy: Expected {num_dependencies} dependencies, got {len(sqlalchemy_deps)}"
            assert len(mongodb_deps) == num_dependencies, \
                f"MongoDB: Expected {num_dependencies} dependencies, got {len(mongodb_deps)}"
            
            # Both should preserve the original dependency IDs
            assert sqlalchemy_deps == sorted(sqlalchemy_dep_ids), \
                "SQLAlchemy did not preserve dependency IDs"
            assert mongodb_deps == sorted(mongodb_dep_ids), \
                "MongoDB did not preserve dependency IDs"
            
            # Verify both backends have equivalent behavior (same structure)
            assert len(sqlalchemy_deps) == len(mongodb_deps), \
                "Both backends should preserve the same number of dependencies"
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()
