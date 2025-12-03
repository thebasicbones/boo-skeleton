"""Property-based tests for CRUD round-trip consistency across backends

Feature: mongodb-integration, Property 5: CRUD round-trip consistency
Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3

This test verifies that creating a resource and then immediately retrieving it
returns a resource with identical field values (except for system-generated timestamps)
for both SQLAlchemy and MongoDB backends.
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
from datetime import datetime, timezone


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


# Strategy for generating ResourceCreate objects
@st.composite
def resource_create_strategy(draw):
    """
    Generate valid ResourceCreate data.
    
    Note: Dependencies are set to empty list because we're testing CRUD round-trip
    for individual resources. Testing with actual dependencies would require
    creating those dependency resources first, which is tested separately.
    """
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    # Use empty dependencies for round-trip tests
    # Testing with non-existent dependency IDs would violate referential integrity
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


@pytest.fixture
async def sqlalchemy_repository():
    """Create a SQLAlchemy repository with in-memory database"""
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
        yield repository
    
    await engine.dispose()


@pytest.fixture
async def mongodb_repository():
    """Create a MongoDB repository with test database"""
    if not is_mongodb_available():
        pytest.skip("MongoDB is not available for testing")
    
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = "fastapi_crud_test_roundtrip"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]
    
    # Create indexes
    await db.resources.create_index("name")
    await db.resources.create_index("dependencies")
    
    repository = MongoDBResourceRepository(db)
    
    yield repository
    
    # Cleanup: drop test database
    await client.drop_database(test_db_name)
    client.close()


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(resource_data=resource_create_strategy())
async def test_sqlalchemy_crud_roundtrip_consistency(resource_data):
    """
    Feature: mongodb-integration, Property 5: CRUD round-trip consistency
    Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3
    
    For any valid resource data, creating a resource in SQLAlchemy backend
    and then immediately retrieving it should return a resource with identical
    field values (except for system-generated timestamps).
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
        
        # CREATE: Create the resource (Requirement 2.2)
        created_resource_obj = await repository.create(resource_data)
        created_resource = resource_to_dict(created_resource_obj)
        
        # Verify resource was created with required fields (Requirement 3.1)
        assert created_resource is not None
        assert 'id' in created_resource
        assert 'name' in created_resource
        assert 'description' in created_resource
        assert 'dependencies' in created_resource
        assert 'created_at' in created_resource
        assert 'updated_at' in created_resource
        
        # Verify ID was generated (Requirement 3.2)
        assert created_resource['id'] is not None
        assert isinstance(created_resource['id'], str)
        assert len(created_resource['id']) > 0
        
        # READ: Retrieve the resource by ID (Requirement 2.3)
        retrieved_resource_obj = await repository.get_by_id(created_resource['id'])
        retrieved_resource = resource_to_dict(retrieved_resource_obj)
        
        # Verify resource was retrieved
        assert retrieved_resource is not None
        
        # ROUND-TRIP CONSISTENCY: Verify field values match (Requirement 3.3)
        # ID should be identical
        assert retrieved_resource['id'] == created_resource['id']
        
        # Name should be identical (after normalization)
        assert retrieved_resource['name'] == created_resource['name']
        
        # Description should be identical
        assert retrieved_resource['description'] == created_resource['description']
        
        # Dependencies should be identical (same IDs in same order)
        assert retrieved_resource['dependencies'] == created_resource['dependencies']
        
        # Timestamps should exist and be reasonable
        assert retrieved_resource['created_at'] is not None
        assert retrieved_resource['updated_at'] is not None
        assert isinstance(retrieved_resource['created_at'], datetime)
        assert isinstance(retrieved_resource['updated_at'], datetime)
        
        # Timestamps should match between created and retrieved
        assert retrieved_resource['created_at'] == created_resource['created_at']
        assert retrieved_resource['updated_at'] == created_resource['updated_at']
    
    await engine.dispose()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(resource_data=resource_create_strategy())
async def test_mongodb_crud_roundtrip_consistency(resource_data):
    """
    Feature: mongodb-integration, Property 5: CRUD round-trip consistency
    Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3
    
    For any valid resource data, creating a resource in MongoDB backend
    and then immediately retrieving it should return a resource with identical
    field values (except for system-generated timestamps).
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_roundtrip_{os.getpid()}"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]
    
    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")
        
        repository = MongoDBResourceRepository(db)
        
        # CREATE: Create the resource (Requirement 2.2)
        created_resource = await repository.create(resource_data)
        
        # Verify resource was created with required fields (Requirement 3.1)
        assert created_resource is not None
        assert 'id' in created_resource
        assert 'name' in created_resource
        assert 'description' in created_resource
        assert 'dependencies' in created_resource
        assert 'created_at' in created_resource
        assert 'updated_at' in created_resource
        
        # Verify ID was generated (Requirement 3.2)
        assert created_resource['id'] is not None
        assert isinstance(created_resource['id'], str)
        assert len(created_resource['id']) > 0
        
        # READ: Retrieve the resource by ID (Requirement 2.3)
        retrieved_resource = await repository.get_by_id(created_resource['id'])
        
        # Verify resource was retrieved
        assert retrieved_resource is not None
        
        # ROUND-TRIP CONSISTENCY: Verify field values match (Requirement 3.3)
        # ID should be identical
        assert retrieved_resource['id'] == created_resource['id']
        
        # Name should be identical
        assert retrieved_resource['name'] == created_resource['name']
        
        # Description should be identical
        assert retrieved_resource['description'] == created_resource['description']
        
        # Dependencies should be identical (same IDs in same order)
        assert retrieved_resource['dependencies'] == created_resource['dependencies']
        
        # Timestamps should exist and be reasonable
        assert retrieved_resource['created_at'] is not None
        assert retrieved_resource['updated_at'] is not None
        assert isinstance(retrieved_resource['created_at'], datetime)
        assert isinstance(retrieved_resource['updated_at'], datetime)
        
        # Timestamps should match between created and retrieved
        # Note: MongoDB stores datetimes with millisecond precision (not microsecond)
        # So we need to compare timestamps rounded to milliseconds
        def round_to_milliseconds(dt):
            """Round datetime to millisecond precision"""
            return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)
        
        assert round_to_milliseconds(retrieved_resource['created_at']) == round_to_milliseconds(created_resource['created_at'])
        assert round_to_milliseconds(retrieved_resource['updated_at']) == round_to_milliseconds(created_resource['updated_at'])
        
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
@given(resource_data=resource_create_strategy())
async def test_backend_equivalence_crud_roundtrip(resource_data):
    """
    Feature: mongodb-integration, Property 5: CRUD round-trip consistency
    Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3
    
    For any valid resource data, the CRUD round-trip behavior should be
    equivalent between SQLAlchemy and MongoDB backends. Both should:
    - Create resources with the same field structure
    - Retrieve resources with identical field values
    - Preserve all data through the round-trip
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
    test_db_name = f"fastapi_crud_test_equiv_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # Create in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(resource_data)
            mongodb_created_obj = await mongodb_repo.create(resource_data)
            
            sqlalchemy_created = resource_to_dict(sqlalchemy_created_obj)
            mongodb_created = resource_to_dict(mongodb_created_obj)
            
            # Retrieve from both backends
            sqlalchemy_retrieved_obj = await sqlalchemy_repo.get_by_id(sqlalchemy_created['id'])
            mongodb_retrieved_obj = await mongodb_repo.get_by_id(mongodb_created['id'])
            
            sqlalchemy_retrieved = resource_to_dict(sqlalchemy_retrieved_obj)
            mongodb_retrieved = resource_to_dict(mongodb_retrieved_obj)
            
            # Verify both backends have same field structure
            assert set(sqlalchemy_created.keys()) == set(mongodb_created.keys())
            assert set(sqlalchemy_retrieved.keys()) == set(mongodb_retrieved.keys())
            
            # Verify both backends preserve data correctly (ignoring IDs and timestamps)
            assert sqlalchemy_created['name'] == mongodb_created['name']
            assert sqlalchemy_created['description'] == mongodb_created['description']
            assert sqlalchemy_created['dependencies'] == mongodb_created['dependencies']
            
            assert sqlalchemy_retrieved['name'] == mongodb_retrieved['name']
            assert sqlalchemy_retrieved['description'] == mongodb_retrieved['description']
            assert sqlalchemy_retrieved['dependencies'] == mongodb_retrieved['dependencies']
            
            # Verify round-trip consistency for both backends
            assert sqlalchemy_retrieved['name'] == sqlalchemy_created['name']
            assert mongodb_retrieved['name'] == mongodb_created['name']
            
            assert sqlalchemy_retrieved['description'] == sqlalchemy_created['description']
            assert mongodb_retrieved['description'] == mongodb_created['description']
            
            assert sqlalchemy_retrieved['dependencies'] == sqlalchemy_created['dependencies']
            assert mongodb_retrieved['dependencies'] == mongodb_created['dependencies']
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()
