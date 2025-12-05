"""Property-based tests for delete completeness across backends

Feature: mongodb-integration, Property 7: Delete completeness
Validates: Requirements 2.5

This test verifies that deleting a resource from either backend
results in subsequent retrieval attempts returning not found.
"""

import os

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.sqlalchemy_resource import Base
from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
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
        "id": resource.id,
        "name": resource.name,
        "description": resource.description,
        "dependencies": (
            [dep.id for dep in resource.dependencies]
            if hasattr(resource, "dependencies") and resource.dependencies
            else []
        ),
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

    Note: Dependencies are set to empty list because we're testing delete
    completeness for individual resources without complex dependency chains.
    """
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    dependencies = []
    return ResourceCreate(name=name, description=description, dependencies=dependencies)


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
@given(resource_data=resource_create_strategy())
async def test_sqlalchemy_delete_completeness(resource_data):
    """
    Feature: mongodb-integration, Property 7: Delete completeness
    Validates: Requirements 2.5

    For any existing resource, deleting the resource from SQLAlchemy backend
    should result in subsequent retrieval attempts returning not found.
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

        # CREATE: Create the resource
        created_resource_obj = await repository.create(resource_data)
        created_resource = resource_to_dict(created_resource_obj)
        resource_id = created_resource["id"]

        # Verify resource exists before deletion
        existing_resource_obj = await repository.get_by_id(resource_id)
        existing_resource = resource_to_dict(existing_resource_obj)
        assert existing_resource is not None
        assert existing_resource["id"] == resource_id

        # DELETE: Delete the resource (Requirement 2.5)
        delete_result = await repository.delete(resource_id, cascade=False)
        assert delete_result is True

        # VERIFY DELETE COMPLETENESS: Subsequent retrieval should return None
        deleted_resource = await repository.get_by_id(resource_id)
        assert (
            deleted_resource is None
        ), f"Resource {resource_id} should not be found after deletion but was retrieved"

    await engine.dispose()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy())
async def test_mongodb_delete_completeness(resource_data):
    """
    Feature: mongodb-integration, Property 7: Delete completeness
    Validates: Requirements 2.5

    For any existing resource, deleting the resource from MongoDB backend
    should result in subsequent retrieval attempts returning not found.
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_delete_{os.getpid()}"

    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]

    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")

        repository = MongoDBResourceRepository(db)

        # CREATE: Create the resource
        created_resource = await repository.create(resource_data)
        resource_id = created_resource["id"]

        # Verify resource exists before deletion
        existing_resource = await repository.get_by_id(resource_id)
        assert existing_resource is not None
        assert existing_resource["id"] == resource_id

        # DELETE: Delete the resource (Requirement 2.5)
        delete_result = await repository.delete(resource_id, cascade=False)
        assert delete_result is True

        # VERIFY DELETE COMPLETENESS: Subsequent retrieval should return None
        deleted_resource = await repository.get_by_id(resource_id)
        assert (
            deleted_resource is None
        ), f"Resource {resource_id} should not be found after deletion but was retrieved"

    finally:
        # Cleanup: drop test database
        await client.drop_database(test_db_name)
        client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy())
async def test_backend_equivalence_delete_completeness(resource_data):
    """
    Feature: mongodb-integration, Property 7: Delete completeness
    Validates: Requirements 2.5

    For any existing resource, the delete completeness behavior should be
    equivalent between SQLAlchemy and MongoDB backends. Both should:
    - Successfully delete the resource
    - Return None on subsequent retrieval attempts
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
    test_db_name = f"fastapi_crud_test_delete_equiv_{os.getpid()}"

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

            sqlalchemy_id = sqlalchemy_created["id"]
            mongodb_id = mongodb_created["id"]

            # Verify both resources exist before deletion
            sqlalchemy_existing_obj = await sqlalchemy_repo.get_by_id(sqlalchemy_id)
            mongodb_existing_obj = await mongodb_repo.get_by_id(mongodb_id)

            sqlalchemy_existing = resource_to_dict(sqlalchemy_existing_obj)
            mongodb_existing = resource_to_dict(mongodb_existing_obj)

            assert sqlalchemy_existing is not None
            assert mongodb_existing is not None

            # Delete from both backends
            sqlalchemy_delete_result = await sqlalchemy_repo.delete(sqlalchemy_id, cascade=False)
            mongodb_delete_result = await mongodb_repo.delete(mongodb_id, cascade=False)

            # Verify both backends report successful deletion
            assert sqlalchemy_delete_result is True
            assert mongodb_delete_result is True

            # Verify both backends return None on subsequent retrieval
            sqlalchemy_deleted = await sqlalchemy_repo.get_by_id(sqlalchemy_id)
            mongodb_deleted = await mongodb_repo.get_by_id(mongodb_id)

            assert (
                sqlalchemy_deleted is None
            ), "SQLAlchemy backend should return None for deleted resource"
            assert (
                mongodb_deleted is None
            ), "MongoDB backend should return None for deleted resource"

            # Verify both backends behave equivalently
            assert (sqlalchemy_deleted is None) == (
                mongodb_deleted is None
            ), "Both backends should have equivalent delete completeness behavior"

    finally:
        await engine.dispose()
        await mongo_client.drop_database(test_db_name)
        mongo_client.close()
