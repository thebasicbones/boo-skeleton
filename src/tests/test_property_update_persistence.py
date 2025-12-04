"""Property-based tests for update persistence across backends

Feature: mongodb-integration, Property 6: Update persistence
Validates: Requirements 2.4, 3.3

This test verifies that updating a resource and then retrieving it
returns the resource with the updated values applied for both
SQLAlchemy and MongoDB backends.
"""
import os
from datetime import datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.sqlalchemy_resource import Base
from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.schemas import ResourceCreate, ResourceUpdate


def resource_to_dict(resource):
    """
    Convert a Resource object (SQLAlchemy ORM) or dict to a standardized dict format.

    This helper ensures consistent comparison between SQLAlchemy and MongoDB results.
    """
    if isinstance(resource, dict):
        return resource

    # Convert SQLAlchemy Resource object to dict
    return {
        "id": resource.id,
        "name": resource.name,
        "description": resource.description,
        "dependencies": [dep.id for dep in resource.dependencies]
        if hasattr(resource, "dependencies") and resource.dependencies
        else [],
        "created_at": resource.created_at,
        "updated_at": resource.updated_at,
    }


# Strategy for generating valid resource names
@st.composite
def valid_name_strategy(draw):
    """Generate valid resource names (1-100 characters, non-empty after strip)"""
    name = draw(
        st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1, max_size=100)
    )
    if not name.strip():
        name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), blacklist_characters=" \t\n\r"
                ),
                min_size=1,
                max_size=100,
            )
        )
    return name


# Strategy for generating ResourceCreate objects
@st.composite
def resource_create_strategy(draw):
    """
    Generate valid ResourceCreate data.

    Note: Dependencies are set to empty list because we're testing update
    persistence for individual resources without complex dependency chains.
    """
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    dependencies = []
    return ResourceCreate(name=name, description=description, dependencies=dependencies)


# Strategy for generating ResourceUpdate objects
@st.composite
def resource_update_strategy(draw):
    """
    Generate valid ResourceUpdate data.

    This strategy generates partial updates where any combination of fields
    can be updated (name, description, dependencies).
    """
    # Generate at least one field to update
    update_name = draw(st.booleans())
    update_description = draw(st.booleans())
    update_dependencies = draw(st.booleans())

    # Ensure at least one field is being updated
    if not (update_name or update_description or update_dependencies):
        update_name = True

    name = draw(valid_name_strategy()) if update_name else None
    description = draw(st.one_of(st.none(), st.text(max_size=500))) if update_description else None
    dependencies = [] if update_dependencies else None

    return ResourceUpdate(name=name, description=description, dependencies=dependencies)


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
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(initial_data=resource_create_strategy(), update_data=resource_update_strategy())
async def test_sqlalchemy_update_persistence(initial_data, update_data):
    """
    Feature: mongodb-integration, Property 6: Update persistence
    Validates: Requirements 2.4, 3.3

    For any existing resource and any valid update data, updating the resource
    in SQLAlchemy backend and then retrieving it should return the resource
    with the updated values applied.
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

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        repository = SQLAlchemyResourceRepository(session)

        # CREATE: Create the initial resource
        created_resource_obj = await repository.create(initial_data)
        created_resource = resource_to_dict(created_resource_obj)
        resource_id = created_resource["id"]

        # Store original values for comparison
        original_name = created_resource["name"]
        original_description = created_resource["description"]
        original_dependencies = created_resource["dependencies"]
        original_created_at = created_resource["created_at"]

        # UPDATE: Update the resource (Requirement 2.4)
        updated_resource_obj = await repository.update(resource_id, update_data)
        updated_resource = resource_to_dict(updated_resource_obj)

        # Verify update succeeded
        assert updated_resource is not None
        assert updated_resource["id"] == resource_id

        # RETRIEVE: Retrieve the resource again to verify persistence (Requirement 3.3)
        retrieved_resource_obj = await repository.get_by_id(resource_id)
        retrieved_resource = resource_to_dict(retrieved_resource_obj)

        # Verify resource was retrieved
        assert retrieved_resource is not None
        assert retrieved_resource["id"] == resource_id

        # UPDATE PERSISTENCE: Verify updated values are persisted
        # Check name update
        if update_data.name is not None:
            assert retrieved_resource["name"] == update_data.name
            assert updated_resource["name"] == update_data.name
        else:
            assert retrieved_resource["name"] == original_name

        # Check description update
        if update_data.description is not None:
            assert retrieved_resource["description"] == update_data.description
            assert updated_resource["description"] == update_data.description
        else:
            assert retrieved_resource["description"] == original_description

        # Check dependencies update
        if update_data.dependencies is not None:
            assert retrieved_resource["dependencies"] == update_data.dependencies
            assert updated_resource["dependencies"] == update_data.dependencies
        else:
            assert retrieved_resource["dependencies"] == original_dependencies

        # Verify created_at timestamp is unchanged
        assert retrieved_resource["created_at"] == original_created_at

        # Verify updated_at timestamp was updated
        assert retrieved_resource["updated_at"] >= original_created_at
        assert isinstance(retrieved_resource["updated_at"], datetime)

    await engine.dispose()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(initial_data=resource_create_strategy(), update_data=resource_update_strategy())
async def test_mongodb_update_persistence(initial_data, update_data):
    """
    Feature: mongodb-integration, Property 6: Update persistence
    Validates: Requirements 2.4, 3.3

    For any existing resource and any valid update data, updating the resource
    in MongoDB backend and then retrieving it should return the resource
    with the updated values applied.
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_update_{os.getpid()}"

    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]

    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")

        repository = MongoDBResourceRepository(db)

        # CREATE: Create the initial resource
        created_resource = await repository.create(initial_data)
        resource_id = created_resource["id"]

        # Store original values for comparison
        original_name = created_resource["name"]
        original_description = created_resource["description"]
        original_dependencies = created_resource["dependencies"]
        original_created_at = created_resource["created_at"]

        # UPDATE: Update the resource (Requirement 2.4)
        updated_resource = await repository.update(resource_id, update_data)

        # Verify update succeeded
        assert updated_resource is not None
        assert updated_resource["id"] == resource_id

        # RETRIEVE: Retrieve the resource again to verify persistence (Requirement 3.3)
        retrieved_resource = await repository.get_by_id(resource_id)

        # Verify resource was retrieved
        assert retrieved_resource is not None
        assert retrieved_resource["id"] == resource_id

        # UPDATE PERSISTENCE: Verify updated values are persisted
        # Check name update
        if update_data.name is not None:
            assert retrieved_resource["name"] == update_data.name
            assert updated_resource["name"] == update_data.name
        else:
            assert retrieved_resource["name"] == original_name

        # Check description update
        if update_data.description is not None:
            assert retrieved_resource["description"] == update_data.description
            assert updated_resource["description"] == update_data.description
        else:
            assert retrieved_resource["description"] == original_description

        # Check dependencies update
        if update_data.dependencies is not None:
            assert retrieved_resource["dependencies"] == update_data.dependencies
            assert updated_resource["dependencies"] == update_data.dependencies
        else:
            assert retrieved_resource["dependencies"] == original_dependencies

        # Verify created_at timestamp is unchanged
        # Note: MongoDB stores datetimes with millisecond precision
        def round_to_milliseconds(dt):
            """Round datetime to millisecond precision"""
            return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)

        assert round_to_milliseconds(retrieved_resource["created_at"]) == round_to_milliseconds(
            original_created_at
        )

        # Verify updated_at timestamp was updated
        assert retrieved_resource["updated_at"] >= original_created_at
        assert isinstance(retrieved_resource["updated_at"], datetime)

    finally:
        # Cleanup: drop test database
        await client.drop_database(test_db_name)
        client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(initial_data=resource_create_strategy(), update_data=resource_update_strategy())
async def test_backend_equivalence_update_persistence(initial_data, update_data):
    """
    Feature: mongodb-integration, Property 6: Update persistence
    Validates: Requirements 2.4, 3.3

    For any existing resource and any valid update data, the update persistence
    behavior should be equivalent between SQLAlchemy and MongoDB backends.
    Both should persist the updated values correctly.
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

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Setup MongoDB
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_update_equiv_{os.getpid()}"

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
            sqlalchemy_created_obj = await sqlalchemy_repo.create(initial_data)
            mongodb_created_obj = await mongodb_repo.create(initial_data)

            sqlalchemy_created = resource_to_dict(sqlalchemy_created_obj)
            mongodb_created = resource_to_dict(mongodb_created_obj)

            sqlalchemy_id = sqlalchemy_created["id"]
            mongodb_id = mongodb_created["id"]

            # Update in both backends
            sqlalchemy_updated_obj = await sqlalchemy_repo.update(sqlalchemy_id, update_data)
            mongodb_updated_obj = await mongodb_repo.update(mongodb_id, update_data)

            resource_to_dict(sqlalchemy_updated_obj)
            resource_to_dict(mongodb_updated_obj)

            # Retrieve from both backends
            sqlalchemy_retrieved_obj = await sqlalchemy_repo.get_by_id(sqlalchemy_id)
            mongodb_retrieved_obj = await mongodb_repo.get_by_id(mongodb_id)

            sqlalchemy_retrieved = resource_to_dict(sqlalchemy_retrieved_obj)
            mongodb_retrieved = resource_to_dict(mongodb_retrieved_obj)

            # Verify both backends applied the same updates
            if update_data.name is not None:
                assert sqlalchemy_retrieved["name"] == update_data.name
                assert mongodb_retrieved["name"] == update_data.name
                assert sqlalchemy_retrieved["name"] == mongodb_retrieved["name"]

            if update_data.description is not None:
                assert sqlalchemy_retrieved["description"] == update_data.description
                assert mongodb_retrieved["description"] == update_data.description
                assert sqlalchemy_retrieved["description"] == mongodb_retrieved["description"]

            if update_data.dependencies is not None:
                assert sqlalchemy_retrieved["dependencies"] == update_data.dependencies
                assert mongodb_retrieved["dependencies"] == update_data.dependencies
                assert sqlalchemy_retrieved["dependencies"] == mongodb_retrieved["dependencies"]

            # Verify both backends preserve created_at
            assert sqlalchemy_retrieved["created_at"] == sqlalchemy_created["created_at"]

            # MongoDB comparison needs millisecond rounding
            def round_to_milliseconds(dt):
                return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)

            assert round_to_milliseconds(mongodb_retrieved["created_at"]) == round_to_milliseconds(
                mongodb_created["created_at"]
            )

            # Verify both backends updated updated_at
            assert sqlalchemy_retrieved["updated_at"] >= sqlalchemy_created["created_at"]
            assert mongodb_retrieved["updated_at"] >= mongodb_created["created_at"]

    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()
