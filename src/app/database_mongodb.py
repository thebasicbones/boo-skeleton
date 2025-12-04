"""MongoDB database connection and client management"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.exceptions import DatabaseError
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Get MongoDB configuration from settings
settings = get_settings()
MONGODB_URL = settings.get_database_url()
MONGODB_DATABASE = settings.mongodb_database or "fastapi_crud"
MONGODB_TIMEOUT = settings.mongodb_timeout

# Global MongoDB client instance
_mongodb_client: AsyncIOMotorClient | None = None


def get_mongodb_client() -> AsyncIOMotorClient:
    """
    Get MongoDB client instance.

    Returns:
        AsyncIOMotorClient: The MongoDB client instance

    Raises:
        DatabaseError: If client is not initialized
    """
    global _mongodb_client

    if _mongodb_client is None:
        raise DatabaseError(
            "MongoDB client not initialized. Call init_mongodb() first.",
            error_type="connection",
            details="Client instance is None",
        )

    return _mongodb_client


async def get_mongodb_db() -> AsyncIOMotorDatabase:
    """
    Dependency function to get MongoDB database instance.

    Yields:
        AsyncIOMotorDatabase: The MongoDB database instance

    Raises:
        DatabaseError: If connection fails
    """
    try:
        client = get_mongodb_client()
        db = client[MONGODB_DATABASE]
        yield db
    except Exception as e:
        logger.error(f"Failed to get MongoDB database: {e}")
        raise DatabaseError(
            f"Failed to access MongoDB database: {MONGODB_DATABASE}",
            error_type="connection",
            details=str(e)
        )


async def init_mongodb() -> None:
    """
    Initialize MongoDB connection and create indexes.

    This function:
    1. Creates the MongoDB client with configured timeout
    2. Verifies the connection by pinging the server
    3. Creates necessary indexes on the resources collection

    Raises:
        DatabaseError: If connection fails or server is unreachable
    """
    global _mongodb_client

    try:
        logger.info(f"Initializing MongoDB connection to {MONGODB_URL}")

        # Create MongoDB client with timeout configuration
        _mongodb_client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=MONGODB_TIMEOUT,
            connectTimeoutMS=MONGODB_TIMEOUT,
        )

        # Verify connection by pinging the server
        await _mongodb_client.admin.command("ping")
        logger.info("MongoDB connection established successfully")

        # Get database instance
        db = _mongodb_client[MONGODB_DATABASE]

        # Create indexes on resources collection
        logger.info("Creating MongoDB indexes...")
        resources_collection = db.resources

        # Index on name for search queries
        await resources_collection.create_index("name")
        logger.info("Created index on 'name' field")

        # Index on dependencies for relationship queries
        await resources_collection.create_index("dependencies")
        logger.info("Created index on 'dependencies' field")

        logger.info("MongoDB initialization complete")

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Failed to connect to MongoDB at {MONGODB_URL}: {str(e)}"
        logger.error(error_msg)
        raise DatabaseError(
            error_msg,
            error_type="connection",
            details=f"Connection timeout: {MONGODB_TIMEOUT}ms"
        )
    except Exception as e:
        error_msg = f"Unexpected error during MongoDB initialization: {str(e)}"
        logger.error(error_msg)
        raise DatabaseError(error_msg, error_type="general", details=str(e))


async def close_mongodb() -> None:
    """
    Close MongoDB connection gracefully.

    This function closes the MongoDB client connection and cleans up resources.
    It's safe to call even if the client is not initialized.
    """
    global _mongodb_client

    if _mongodb_client is not None:
        try:
            logger.info("Closing MongoDB connection...")
            _mongodb_client.close()
            _mongodb_client = None
            logger.info("MongoDB connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
            # Don't raise exception during shutdown
    else:
        logger.debug("MongoDB client already closed or not initialized")
