"""Property-based tests for MongoDB connection lifecycle

Feature: mongodb-integration, Property 1: Backend initialization from configuration (MongoDB)
Validates: Requirements 1.2

This test verifies that the MongoDB backend can be successfully initialized
from valid configuration and establishes a working connection.
"""
import os

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.exceptions import DatabaseConnectionError


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


# Skip tests if MongoDB is not available
pytestmark = pytest.mark.skipif(
    not is_mongodb_available(), reason="MongoDB is not available for testing"
)


# Strategy for generating valid MongoDB configuration
@st.composite
def valid_mongodb_config_strategy(draw):
    """
    Generate valid MongoDB configuration.

    For testing purposes, we'll use the actual MongoDB instance
    configured in the environment, as we need a real connection
    to verify the initialization works correctly.
    """
    # Use environment variables or defaults
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")

    # Ensure URL has proper mongodb:// prefix
    if not mongodb_url.startswith("mongodb://") and not mongodb_url.startswith("mongodb+srv://"):
        mongodb_url = f"mongodb://{mongodb_url}"

    mongodb_database = os.getenv("MONGODB_DATABASE", "fastapi_crud_test")
    mongodb_timeout = draw(st.integers(min_value=1000, max_value=10000))

    return {"url": mongodb_url, "database": mongodb_database, "timeout": mongodb_timeout}


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=1000,  # Allow more time for MongoDB initialization
)
@given(config=valid_mongodb_config_strategy())
async def test_mongodb_initialization_from_configuration(config, monkeypatch):
    """
    Feature: mongodb-integration, Property 1: Backend initialization from configuration (MongoDB)
    Validates: Requirement 1.2

    For any valid MongoDB configuration, when the application initializes,
    the application should successfully establish a connection to MongoDB
    and be ready to handle requests.

    This property verifies:
    1. Connection can be established with valid configuration
    2. The client is accessible after initialization
    3. The connection can be verified (ping succeeds)
    4. Indexes are created successfully
    5. Connection can be closed gracefully
    """
    # Set environment variables for this test
    monkeypatch.setenv("DATABASE_URL", config["url"])
    monkeypatch.setenv("MONGODB_DATABASE", config["database"])
    monkeypatch.setenv("MONGODB_TIMEOUT", str(config["timeout"]))

    # Force reload of module-level variables
    import importlib

    import app.database_mongodb

    importlib.reload(app.database_mongodb)

    try:
        # Test initialization
        await app.database_mongodb.init_mongodb()

        # Verify client is accessible
        client = app.database_mongodb.get_mongodb_client()
        assert client is not None, "MongoDB client should be initialized"

        # Verify connection works by pinging
        ping_result = await client.admin.command("ping")
        assert ping_result.get("ok") == 1.0, "MongoDB ping should succeed"

        # Verify database is accessible
        db = client[config["database"]]
        assert db is not None, "Database should be accessible"

        # Verify indexes were created on resources collection
        resources_collection = db.resources
        indexes = await resources_collection.list_indexes().to_list(length=None)
        index_names = [idx["name"] for idx in indexes]

        # Should have at least _id_ (default), name, and dependencies indexes
        assert "_id_" in index_names, "Default _id index should exist"
        assert "name_1" in index_names, "Name index should be created"
        assert "dependencies_1" in index_names, "Dependencies index should be created"

    finally:
        # Clean up: close connection
        await app.database_mongodb.close_mongodb()

        # Verify connection is closed
        # After closing, attempting to get client should raise an error
        with pytest.raises(DatabaseConnectionError):
            app.database_mongodb.get_mongodb_client()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(config=valid_mongodb_config_strategy())
async def test_mongodb_connection_ready_after_init(config, monkeypatch):
    """
    Feature: mongodb-integration, Property 1: Backend initialization from configuration (MongoDB)
    Validates: Requirement 1.2

    For any valid MongoDB configuration, after initialization completes,
    the application should be ready to handle database requests immediately.

    This verifies that the connection is not just established but actually
    usable for database operations.
    """
    # Set environment variables for this test
    monkeypatch.setenv("DATABASE_URL", config["url"])
    monkeypatch.setenv("MONGODB_DATABASE", config["database"])
    monkeypatch.setenv("MONGODB_TIMEOUT", str(config["timeout"]))

    # Force reload of module-level variables
    import importlib

    import app.database_mongodb

    importlib.reload(app.database_mongodb)

    try:
        # Initialize MongoDB
        await app.database_mongodb.init_mongodb()

        # Get client and database
        client = app.database_mongodb.get_mongodb_client()
        db = client[config["database"]]

        # Perform a simple database operation to verify readiness
        # Insert a test document
        test_collection = db.test_connection
        test_doc = {"test": "connection_ready", "value": 42}
        insert_result = await test_collection.insert_one(test_doc)
        assert insert_result.inserted_id is not None, "Should be able to insert document"

        # Retrieve the document
        retrieved_doc = await test_collection.find_one({"_id": insert_result.inserted_id})
        assert retrieved_doc is not None, "Should be able to retrieve document"
        assert retrieved_doc["test"] == "connection_ready"
        assert retrieved_doc["value"] == 42

        # Clean up test document
        await test_collection.delete_one({"_id": insert_result.inserted_id})

    finally:
        # Clean up: close connection
        await app.database_mongodb.close_mongodb()


@pytest.mark.property
@pytest.mark.asyncio
async def test_mongodb_graceful_shutdown(monkeypatch):
    """
    Feature: mongodb-integration, Property 1: Backend initialization from configuration (MongoDB)
    Validates: Requirement 1.2

    The MongoDB connection should close gracefully without errors,
    and multiple close calls should be safe (idempotent).
    """
    # Use default configuration
    mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")

    # Ensure URL has proper mongodb:// prefix
    if not mongodb_url.startswith("mongodb://") and not mongodb_url.startswith("mongodb+srv://"):
        mongodb_url = f"mongodb://{mongodb_url}"

    mongodb_database = os.getenv("MONGODB_DATABASE", "fastapi_crud_test")

    # Set environment variables
    monkeypatch.setenv("DATABASE_URL", mongodb_url)
    monkeypatch.setenv("MONGODB_DATABASE", mongodb_database)

    # Force reload to ensure clean state
    import importlib

    import app.database_mongodb

    importlib.reload(app.database_mongodb)

    # Initialize
    await app.database_mongodb.init_mongodb()

    # Verify client exists
    client = app.database_mongodb.get_mongodb_client()
    assert client is not None

    # Close connection
    await app.database_mongodb.close_mongodb()

    # Verify client is None after close
    with pytest.raises(DatabaseConnectionError):
        app.database_mongodb.get_mongodb_client()

    # Calling close again should be safe (idempotent)
    await app.database_mongodb.close_mongodb()  # Should not raise exception
