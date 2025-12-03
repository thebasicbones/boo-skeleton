"""Property-based tests for backend abstraction transparency across both backends

Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

This test verifies that repository operations produce identical results
regardless of whether SQLite or MongoDB is the configured backend.
"""
import pytest
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.sqlalchemy_resource import Base
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.schemas import ResourceCreate, ResourceUpdate
from datetime import datetime


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
    """Generate valid ResourceCreate data"""
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=[]  # No dependencies for baseline test
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


def round_to_milliseconds(dt):
    """Round datetime to millisecond precision for MongoDB comparison"""
    if dt is None:
        return None
    return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline due to variable database operation timing
)
@given(resource_data=resource_create_strategy())
async def test_backend_abstraction_create_operation(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
    Validates: Requirements 2.1, 2.2
    
    For any valid resource data, the CREATE operation should produce identical
    results regardless of whether SQLite or MongoDB is the configured backend.
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
    test_db_name = f"fastapi_crud_test_abstraction_{os.getpid()}"
    
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
            mongodb_created = mongodb_created_obj  # Already a dict
            
            # Verify both backends return resources with same structure
            assert set(sqlalchemy_created.keys()) == set(mongodb_created.keys())
            
            # Verify both backends preserve input data correctly
            assert sqlalchemy_created['name'] == resource_data.name
            assert mongodb_created['name'] == resource_data.name
            
            assert sqlalchemy_created['description'] == resource_data.description
            assert mongodb_created['description'] == resource_data.description
            
            assert sqlalchemy_created['dependencies'] == resource_data.dependencies
            assert mongodb_created['dependencies'] == resource_data.dependencies
            
            # Verify both backends generate IDs
            assert sqlalchemy_created['id'] is not None
            assert mongodb_created['id'] is not None
            assert isinstance(sqlalchemy_created['id'], str)
            assert isinstance(mongodb_created['id'], str)
            
            # Verify both backends generate timestamps
            assert sqlalchemy_created['created_at'] is not None
            assert mongodb_created['created_at'] is not None
            assert sqlalchemy_created['updated_at'] is not None
            assert mongodb_created['updated_at'] is not None
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline due to variable database operation timing
)
@given(resource_data=resource_create_strategy())
async def test_backend_abstraction_read_operation(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
    Validates: Requirements 2.1, 2.3
    
    For any valid resource data, the READ operation (get_by_id) should produce
    identical results regardless of whether SQLite or MongoDB is the configured backend.
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
    test_db_name = f"fastapi_crud_test_read_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # Create resources in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(resource_data)
            mongodb_created_obj = await mongodb_repo.create(resource_data)
            
            sqlalchemy_created = resource_to_dict(sqlalchemy_created_obj)
            mongodb_created = mongodb_created_obj
            
            # Read from both backends
            sqlalchemy_retrieved_obj = await sqlalchemy_repo.get_by_id(sqlalchemy_created['id'])
            mongodb_retrieved_obj = await mongodb_repo.get_by_id(mongodb_created['id'])
            
            sqlalchemy_retrieved = resource_to_dict(sqlalchemy_retrieved_obj)
            mongodb_retrieved = mongodb_retrieved_obj
            
            # Verify both backends return resources with same structure
            assert set(sqlalchemy_retrieved.keys()) == set(mongodb_retrieved.keys())
            
            # Verify both backends return correct data
            assert sqlalchemy_retrieved['id'] == sqlalchemy_created['id']
            assert mongodb_retrieved['id'] == mongodb_created['id']
            
            assert sqlalchemy_retrieved['name'] == resource_data.name
            assert mongodb_retrieved['name'] == resource_data.name
            
            assert sqlalchemy_retrieved['description'] == resource_data.description
            assert mongodb_retrieved['description'] == resource_data.description
            
            assert sqlalchemy_retrieved['dependencies'] == resource_data.dependencies
            assert mongodb_retrieved['dependencies'] == resource_data.dependencies
            
            # Test get_by_id with non-existent ID
            non_existent_id = "00000000-0000-0000-0000-000000000000"
            sqlalchemy_not_found = await sqlalchemy_repo.get_by_id(non_existent_id)
            mongodb_not_found = await mongodb_repo.get_by_id(non_existent_id)
            
            # Both backends should return None for non-existent resources
            assert sqlalchemy_not_found is None
            assert mongodb_not_found is None
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline due to variable database operation timing
)
@given(resource_data=resource_create_strategy())
async def test_backend_abstraction_update_operation(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
    Validates: Requirements 2.1, 2.4
    
    For any valid resource data, the UPDATE operation should produce identical
    results regardless of whether SQLite or MongoDB is the configured backend.
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
    test_db_name = f"fastapi_crud_test_update_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # Create resources in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(resource_data)
            mongodb_created_obj = await mongodb_repo.create(resource_data)
            
            sqlalchemy_created = resource_to_dict(sqlalchemy_created_obj)
            mongodb_created = mongodb_created_obj
            
            # Update resources in both backends
            update_data = ResourceUpdate(
                name=resource_data.name + "_updated",
                description="Updated description"
            )
            
            sqlalchemy_updated_obj = await sqlalchemy_repo.update(sqlalchemy_created['id'], update_data)
            mongodb_updated_obj = await mongodb_repo.update(mongodb_created['id'], update_data)
            
            sqlalchemy_updated = resource_to_dict(sqlalchemy_updated_obj)
            mongodb_updated = mongodb_updated_obj
            
            # Verify both backends return resources with same structure
            assert set(sqlalchemy_updated.keys()) == set(mongodb_updated.keys())
            
            # Verify both backends applied the update correctly
            assert sqlalchemy_updated['name'] == update_data.name
            assert mongodb_updated['name'] == update_data.name
            
            assert sqlalchemy_updated['description'] == update_data.description
            assert mongodb_updated['description'] == update_data.description
            
            # Verify IDs didn't change
            assert sqlalchemy_updated['id'] == sqlalchemy_created['id']
            assert mongodb_updated['id'] == mongodb_created['id']
            
            # Verify updated_at changed (should be later than created_at)
            assert sqlalchemy_updated['updated_at'] >= sqlalchemy_updated['created_at']
            assert mongodb_updated['updated_at'] >= mongodb_updated['created_at']
            
            # Test update with non-existent ID
            non_existent_id = "00000000-0000-0000-0000-000000000000"
            sqlalchemy_not_found = await sqlalchemy_repo.update(non_existent_id, update_data)
            mongodb_not_found = await mongodb_repo.update(non_existent_id, update_data)
            
            # Both backends should return None for non-existent resources
            assert sqlalchemy_not_found is None
            assert mongodb_not_found is None
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline due to variable database operation timing
)
@given(resource_data=resource_create_strategy())
async def test_backend_abstraction_delete_operation(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
    Validates: Requirements 2.1, 2.5
    
    For any valid resource data, the DELETE operation should produce identical
    results regardless of whether SQLite or MongoDB is the configured backend.
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
    test_db_name = f"fastapi_crud_test_delete_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # Create resources in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(resource_data)
            mongodb_created_obj = await mongodb_repo.create(resource_data)
            
            sqlalchemy_created = resource_to_dict(sqlalchemy_created_obj)
            mongodb_created = mongodb_created_obj
            
            # Delete resources in both backends
            sqlalchemy_delete_result = await sqlalchemy_repo.delete(sqlalchemy_created['id'], cascade=False)
            mongodb_delete_result = await mongodb_repo.delete(mongodb_created['id'], cascade=False)
            
            # Both backends should return True for successful deletion
            assert sqlalchemy_delete_result is True
            assert mongodb_delete_result is True
            
            # Verify resources are deleted in both backends
            sqlalchemy_after_delete = await sqlalchemy_repo.get_by_id(sqlalchemy_created['id'])
            mongodb_after_delete = await mongodb_repo.get_by_id(mongodb_created['id'])
            
            assert sqlalchemy_after_delete is None
            assert mongodb_after_delete is None
            
            # Test delete with non-existent ID
            non_existent_id = "00000000-0000-0000-0000-000000000000"
            sqlalchemy_not_found = await sqlalchemy_repo.delete(non_existent_id, cascade=False)
            mongodb_not_found = await mongodb_repo.delete(non_existent_id, cascade=False)
            
            # Both backends should return False for non-existent resources
            assert sqlalchemy_not_found is False
            assert mongodb_not_found is False
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline due to variable database operation timing
)
@given(resource_data=resource_create_strategy())
async def test_backend_abstraction_list_operation(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
    Validates: Requirements 2.1, 2.6
    
    For any valid resource data, the LIST operation (get_all) should produce
    identical results regardless of whether SQLite or MongoDB is the configured backend.
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
    test_db_name = f"fastapi_crud_test_list_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # Initially, both backends should return empty lists
            sqlalchemy_initial = await sqlalchemy_repo.get_all()
            mongodb_initial = await mongodb_repo.get_all()
            
            assert len(sqlalchemy_initial) == 0
            assert len(mongodb_initial) == 0
            
            # Create resources in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(resource_data)
            mongodb_created_obj = await mongodb_repo.create(resource_data)
            
            # Get all resources from both backends
            sqlalchemy_all = await sqlalchemy_repo.get_all()
            mongodb_all = await mongodb_repo.get_all()
            
            # Both backends should return exactly one resource
            assert len(sqlalchemy_all) == 1
            assert len(mongodb_all) == 1
            
            # Convert to dicts for comparison
            sqlalchemy_resource = resource_to_dict(sqlalchemy_all[0])
            mongodb_resource = mongodb_all[0]
            
            # Verify both backends return resources with same structure
            assert set(sqlalchemy_resource.keys()) == set(mongodb_resource.keys())
            
            # Verify both backends return correct data
            assert sqlalchemy_resource['name'] == resource_data.name
            assert mongodb_resource['name'] == resource_data.name
            
            assert sqlalchemy_resource['description'] == resource_data.description
            assert mongodb_resource['description'] == resource_data.description
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline due to variable database operation timing
)
@given(resource_data=resource_create_strategy())
async def test_backend_abstraction_search_operation(resource_data):
    """
    Feature: mongodb-integration, Property 4: Backend abstraction transparency (both backends)
    Validates: Requirements 2.1, 2.6
    
    For any valid resource data, the SEARCH operation should produce identical
    results regardless of whether SQLite or MongoDB is the configured backend.
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
    test_db_name = f"fastapi_crud_test_search_{os.getpid()}"
    
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[test_db_name]
    
    try:
        await mongo_db.resources.create_index("name")
        await mongo_db.resources.create_index("dependencies")
        
        # Test both backends
        async with async_session() as session:
            sqlalchemy_repo = SQLAlchemyResourceRepository(session)
            mongodb_repo = MongoDBResourceRepository(mongo_db)
            
            # Create resources in both backends
            sqlalchemy_created_obj = await sqlalchemy_repo.create(resource_data)
            mongodb_created_obj = await mongodb_repo.create(resource_data)
            
            # Search for resources in both backends using the name
            search_query = resource_data.name[:5] if len(resource_data.name) >= 5 else resource_data.name
            
            sqlalchemy_search_results = await sqlalchemy_repo.search(search_query)
            mongodb_search_results = await mongodb_repo.search(search_query)
            
            # Both backends should find the resource
            assert len(sqlalchemy_search_results) >= 1
            assert len(mongodb_search_results) >= 1
            
            # Convert to dicts for comparison
            sqlalchemy_found = [resource_to_dict(r) for r in sqlalchemy_search_results]
            mongodb_found = mongodb_search_results
            
            # Verify both backends found resources with matching names
            sqlalchemy_names = [r['name'] for r in sqlalchemy_found]
            mongodb_names = [r['name'] for r in mongodb_found]
            
            assert resource_data.name in sqlalchemy_names
            assert resource_data.name in mongodb_names
            
            # Test search with non-matching query
            non_matching_query = "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
            sqlalchemy_no_results = await sqlalchemy_repo.search(non_matching_query)
            mongodb_no_results = await mongodb_repo.search(non_matching_query)
            
            # Both backends should return empty lists
            assert len(sqlalchemy_no_results) == 0
            assert len(mongodb_no_results) == 0
    
    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()
