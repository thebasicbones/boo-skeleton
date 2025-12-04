"""Property-based tests for schema field completeness in MongoDB

Feature: mongodb-integration, Property 9: Schema field completeness
Validates: Requirements 3.1

This test verifies that resources stored in MongoDB contain all required fields
(id, name, description, dependencies, created_at, updated_at) with appropriate
data types.
"""
import os
from datetime import datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from motor.motor_asyncio import AsyncIOMotorClient

from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.schemas import ResourceCreate


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

    Note: Dependencies are set to empty list or a list of valid UUIDs
    to test schema completeness without requiring actual dependency resources.
    """
    name = draw(valid_name_strategy())
    description = draw(st.one_of(st.none(), st.text(max_size=500)))
    # Generate 0-3 random UUID strings as dependencies
    num_deps = draw(st.integers(min_value=0, max_value=3))
    dependencies = [str(draw(st.uuids())) for _ in range(num_deps)]

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
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy())
async def test_mongodb_schema_field_completeness(resource_data):
    """
    Feature: mongodb-integration, Property 9: Schema field completeness
    Validates: Requirements 3.1

    For any resource stored in MongoDB, the MongoDB document should contain
    all required fields (id, name, description, dependencies, created_at, updated_at)
    with appropriate data types.
    """
    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_schema_{os.getpid()}"

    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]

    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")

        repository = MongoDBResourceRepository(db)

        # CREATE: Create the resource
        created_resource = await repository.create(resource_data)

        # FIELD COMPLETENESS: Verify all required fields are present
        required_fields = ["id", "name", "description", "dependencies", "created_at", "updated_at"]

        for field in required_fields:
            assert (
                field in created_resource
            ), f"Required field '{field}' is missing from MongoDB document"

        # FIELD TYPE VALIDATION: Verify appropriate data types

        # 1. ID field should be a non-empty string
        assert isinstance(
            created_resource["id"], str
        ), f"Field 'id' should be string, got {type(created_resource['id'])}"
        assert len(created_resource["id"]) > 0, "Field 'id' should not be empty"

        # 2. Name field should be a non-empty string
        assert isinstance(
            created_resource["name"], str
        ), f"Field 'name' should be string, got {type(created_resource['name'])}"
        assert len(created_resource["name"]) > 0, "Field 'name' should not be empty"

        # 3. Description field should be string or None
        assert created_resource["description"] is None or isinstance(
            created_resource["description"], str
        ), f"Field 'description' should be string or None, got {type(created_resource['description'])}"

        # 4. Dependencies field should be a list
        assert isinstance(
            created_resource["dependencies"], list
        ), f"Field 'dependencies' should be list, got {type(created_resource['dependencies'])}"

        # All dependency items should be strings
        for dep in created_resource["dependencies"]:
            assert isinstance(dep, str), f"Dependency item should be string, got {type(dep)}"

        # 5. Created_at field should be a datetime object
        assert isinstance(
            created_resource["created_at"], datetime
        ), f"Field 'created_at' should be datetime, got {type(created_resource['created_at'])}"

        # Created_at should be timezone-aware (UTC)
        assert (
            created_resource["created_at"].tzinfo is not None
        ), "Field 'created_at' should be timezone-aware"

        # 6. Updated_at field should be a datetime object
        assert isinstance(
            created_resource["updated_at"], datetime
        ), f"Field 'updated_at' should be datetime, got {type(created_resource['updated_at'])}"

        # Updated_at should be timezone-aware (UTC)
        assert (
            created_resource["updated_at"].tzinfo is not None
        ), "Field 'updated_at' should be timezone-aware"

        # VERIFY DOCUMENT IN DATABASE: Check the actual MongoDB document
        # This ensures the repository layer is correctly storing data
        raw_document = await db.resources.find_one({"_id": created_resource["id"]})

        assert raw_document is not None, "Resource should exist in MongoDB"

        # Verify MongoDB document has all required fields (using MongoDB field names)
        mongodb_required_fields = [
            "_id",
            "name",
            "description",
            "dependencies",
            "created_at",
            "updated_at",
        ]

        for field in mongodb_required_fields:
            assert (
                field in raw_document
            ), f"Required field '{field}' is missing from raw MongoDB document"

        # Verify MongoDB document field types
        assert isinstance(
            raw_document["_id"], str
        ), f"MongoDB field '_id' should be string, got {type(raw_document['_id'])}"

        assert isinstance(
            raw_document["name"], str
        ), f"MongoDB field 'name' should be string, got {type(raw_document['name'])}"

        assert raw_document["description"] is None or isinstance(
            raw_document["description"], str
        ), f"MongoDB field 'description' should be string or None, got {type(raw_document['description'])}"

        assert isinstance(
            raw_document["dependencies"], list
        ), f"MongoDB field 'dependencies' should be list, got {type(raw_document['dependencies'])}"

        assert isinstance(
            raw_document["created_at"], datetime
        ), f"MongoDB field 'created_at' should be datetime, got {type(raw_document['created_at'])}"

        assert isinstance(
            raw_document["updated_at"], datetime
        ), f"MongoDB field 'updated_at' should be datetime, got {type(raw_document['updated_at'])}"

        # VERIFY DATA CONSISTENCY: Ensure repository layer correctly maps fields
        assert created_resource["id"] == raw_document["_id"], "Repository should map '_id' to 'id'"

        assert (
            created_resource["name"] == raw_document["name"]
        ), "Name field should be consistent between repository and MongoDB"

        assert (
            created_resource["description"] == raw_document["description"]
        ), "Description field should be consistent between repository and MongoDB"

        assert (
            created_resource["dependencies"] == raw_document["dependencies"]
        ), "Dependencies field should be consistent between repository and MongoDB"

    finally:
        # Cleanup: drop test database
        await client.drop_database(test_db_name)
        client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy())
async def test_mongodb_schema_field_completeness_after_update(resource_data):
    """
    Feature: mongodb-integration, Property 9: Schema field completeness
    Validates: Requirements 3.1

    For any resource stored in MongoDB and then updated, the MongoDB document
    should still contain all required fields with appropriate data types.
    This verifies that updates don't accidentally remove required fields.
    """
    from app.schemas import ResourceUpdate

    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_schema_update_{os.getpid()}"

    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]

    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")

        repository = MongoDBResourceRepository(db)

        # CREATE: Create the resource
        created_resource = await repository.create(resource_data)

        # UPDATE: Update the resource with partial data
        update_data = ResourceUpdate(name="Updated Name", description="Updated Description")

        updated_resource = await repository.update(created_resource["id"], update_data)

        # FIELD COMPLETENESS: Verify all required fields are still present after update
        required_fields = ["id", "name", "description", "dependencies", "created_at", "updated_at"]

        for field in required_fields:
            assert (
                field in updated_resource
            ), f"Required field '{field}' is missing from MongoDB document after update"

        # FIELD TYPE VALIDATION: Verify appropriate data types after update
        assert isinstance(
            updated_resource["id"], str
        ), f"Field 'id' should be string after update, got {type(updated_resource['id'])}"

        assert isinstance(
            updated_resource["name"], str
        ), f"Field 'name' should be string after update, got {type(updated_resource['name'])}"

        assert updated_resource["description"] is None or isinstance(
            updated_resource["description"], str
        ), f"Field 'description' should be string or None after update, got {type(updated_resource['description'])}"

        assert isinstance(
            updated_resource["dependencies"], list
        ), f"Field 'dependencies' should be list after update, got {type(updated_resource['dependencies'])}"

        assert isinstance(
            updated_resource["created_at"], datetime
        ), f"Field 'created_at' should be datetime after update, got {type(updated_resource['created_at'])}"

        assert isinstance(
            updated_resource["updated_at"], datetime
        ), f"Field 'updated_at' should be datetime after update, got {type(updated_resource['updated_at'])}"

        # VERIFY FIELDS NOT UPDATED ARE PRESERVED
        assert updated_resource["id"] == created_resource["id"], "ID should not change after update"

        assert (
            updated_resource["dependencies"] == created_resource["dependencies"]
        ), "Dependencies should be preserved when not updated"

        # MongoDB stores datetimes with millisecond precision (not microsecond)
        # So we need to compare timestamps rounded to milliseconds
        def round_to_milliseconds(dt):
            """Round datetime to millisecond precision"""
            return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)

        assert round_to_milliseconds(updated_resource["created_at"]) == round_to_milliseconds(
            created_resource["created_at"]
        ), "Created_at should not change after update"

        # VERIFY UPDATED FIELDS CHANGED
        assert updated_resource["name"] == "Updated Name", "Name should be updated"

        assert (
            updated_resource["description"] == "Updated Description"
        ), "Description should be updated"

        # Updated_at should be different (later) than created_at
        assert (
            updated_resource["updated_at"] >= created_resource["updated_at"]
        ), "Updated_at should be updated to a later time"

    finally:
        # Cleanup: drop test database
        await client.drop_database(test_db_name)
        client.close()


@pytest.mark.property
@pytest.mark.asyncio
@pytest.mark.skipif(not is_mongodb_available(), reason="MongoDB not available")
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(resource_data=resource_create_strategy())
async def test_mongodb_schema_field_completeness_after_retrieval(resource_data):
    """
    Feature: mongodb-integration, Property 9: Schema field completeness
    Validates: Requirements 3.1

    For any resource stored in MongoDB and then retrieved by ID or through
    get_all/search operations, the returned resource should contain all
    required fields with appropriate data types.
    """
    # Use test database
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    test_db_name = f"fastapi_crud_test_schema_retrieval_{os.getpid()}"

    client = AsyncIOMotorClient(mongodb_url)
    db = client[test_db_name]

    try:
        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")

        repository = MongoDBResourceRepository(db)

        # CREATE: Create the resource
        created_resource = await repository.create(resource_data)

        # TEST 1: Retrieve by ID
        retrieved_by_id = await repository.get_by_id(created_resource["id"])

        required_fields = ["id", "name", "description", "dependencies", "created_at", "updated_at"]

        for field in required_fields:
            assert (
                field in retrieved_by_id
            ), f"Required field '{field}' is missing from resource retrieved by ID"

        # Verify types for get_by_id
        assert isinstance(retrieved_by_id["id"], str)
        assert isinstance(retrieved_by_id["name"], str)
        assert retrieved_by_id["description"] is None or isinstance(
            retrieved_by_id["description"], str
        )
        assert isinstance(retrieved_by_id["dependencies"], list)
        assert isinstance(retrieved_by_id["created_at"], datetime)
        assert isinstance(retrieved_by_id["updated_at"], datetime)

        # TEST 2: Retrieve through get_all
        all_resources = await repository.get_all()

        assert len(all_resources) > 0, "get_all should return at least the created resource"

        # Find our resource in the list
        our_resource = next((r for r in all_resources if r["id"] == created_resource["id"]), None)
        assert our_resource is not None, "Created resource should be in get_all results"

        for field in required_fields:
            assert (
                field in our_resource
            ), f"Required field '{field}' is missing from resource retrieved via get_all"

        # Verify types for get_all
        assert isinstance(our_resource["id"], str)
        assert isinstance(our_resource["name"], str)
        assert our_resource["description"] is None or isinstance(our_resource["description"], str)
        assert isinstance(our_resource["dependencies"], list)
        assert isinstance(our_resource["created_at"], datetime)
        assert isinstance(our_resource["updated_at"], datetime)

        # TEST 3: Retrieve through search
        # Use a safe search term (alphanumeric only) to avoid regex issues
        import re

        safe_search_term = re.sub(r"[^a-zA-Z0-9]", "", created_resource["name"])[:5]
        if safe_search_term:  # Only search if we have a valid term
            search_results = await repository.search(safe_search_term)
        else:
            # If no safe characters, just get all resources
            search_results = await repository.get_all()

        # Find our resource in search results (it should be there if name matches)
        our_search_result = next(
            (r for r in search_results if r["id"] == created_resource["id"]), None
        )

        if our_search_result:  # Only check if found (search might not always return it)
            for field in required_fields:
                assert (
                    field in our_search_result
                ), f"Required field '{field}' is missing from resource retrieved via search"

            # Verify types for search
            assert isinstance(our_search_result["id"], str)
            assert isinstance(our_search_result["name"], str)
            assert our_search_result["description"] is None or isinstance(
                our_search_result["description"], str
            )
            assert isinstance(our_search_result["dependencies"], list)
            assert isinstance(our_search_result["created_at"], datetime)
            assert isinstance(our_search_result["updated_at"], datetime)

    finally:
        # Cleanup: drop test database
        await client.drop_database(test_db_name)
        client.close()
