"""Database factory for backend selection and initialization"""
import logging
from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DatabaseConnectionError
from app.repositories.base_resource_repository import BaseResourceRepository
from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Supported database types
DATABASE_TYPE_SQLITE = "sqlite"
DATABASE_TYPE_MONGODB = "mongodb"


def get_database_type() -> str:
    """
    Get the configured database backend type from settings.

    Returns:
        str: Database type ("sqlite" or "mongodb")

    Raises:
        DatabaseConnectionError: If DATABASE_TYPE is invalid
    """
    settings = get_settings()
    db_type = settings.database_type.lower()

    if db_type not in [DATABASE_TYPE_SQLITE, DATABASE_TYPE_MONGODB]:
        raise DatabaseConnectionError(
            f"Invalid DATABASE_TYPE: {db_type}. Must be 'sqlite' or 'mongodb'",
            details=f"Configured value: {db_type}",
        )

    logger.info(f"Database type configured as: {db_type}")
    return db_type


async def get_db() -> AsyncGenerator[AsyncSession | AsyncIOMotorDatabase, None]:
    """
    Dependency function that returns the appropriate database session/client
    based on the configured backend.

    This function is used as a FastAPI dependency to inject the database
    connection into route handlers.

    Yields:
        Union[AsyncSession, AsyncIOMotorDatabase]: Database session for SQLite
            or database instance for MongoDB

    Raises:
        DatabaseConnectionError: If database type is invalid or connection fails
    """
    db_type = get_database_type()

    if db_type == DATABASE_TYPE_SQLITE:
        # Import here to avoid circular imports
        from app.database_sqlalchemy import get_sqlalchemy_db

        async for session in get_sqlalchemy_db():
            yield session

    elif db_type == DATABASE_TYPE_MONGODB:
        # Import here to avoid circular imports
        from app.database_mongodb import get_mongodb_db

        async for db in get_mongodb_db():
            yield db

    else:
        raise DatabaseConnectionError(
            f"Unsupported database type: {db_type}",
            details="This should not happen if get_database_type() validation works",
        )


def get_repository(db: AsyncSession | AsyncIOMotorDatabase) -> BaseResourceRepository:
    """
    Factory function that instantiates the correct repository class
    based on the database connection type.

    Args:
        db: Database session (AsyncSession) or database instance (AsyncIOMotorDatabase)

    Returns:
        BaseResourceRepository: Appropriate repository implementation

    Raises:
        DatabaseConnectionError: If database type cannot be determined
    """
    # Determine database type based on the connection object type
    if isinstance(db, AsyncSession):
        logger.debug("Creating SQLAlchemy repository")
        return SQLAlchemyResourceRepository(db)

    elif isinstance(db, AsyncIOMotorDatabase):
        logger.debug("Creating MongoDB repository")
        return MongoDBResourceRepository(db)

    else:
        raise DatabaseConnectionError(
            f"Unknown database connection type: {type(db).__name__}",
            details=f"Expected AsyncSession or AsyncIOMotorDatabase, got {type(db)}",
        )


async def init_database() -> None:
    """
    Initialize the configured database backend.

    This function:
    - Reads the DATABASE_TYPE environment variable
    - Initializes the appropriate database backend
    - Creates tables/indexes as needed

    Raises:
        DatabaseConnectionError: If initialization fails
    """
    db_type = get_database_type()

    logger.info(f"Initializing {db_type} database...")

    try:
        if db_type == DATABASE_TYPE_SQLITE:
            from app.database_sqlalchemy import init_sqlalchemy_db

            await init_sqlalchemy_db()
            logger.info("SQLite database initialized successfully")

        elif db_type == DATABASE_TYPE_MONGODB:
            from app.database_mongodb import init_mongodb

            await init_mongodb()
            logger.info("MongoDB database initialized successfully")

        else:
            raise DatabaseConnectionError(
                f"Cannot initialize unsupported database type: {db_type}",
                details="This should not happen if get_database_type() validation works",
            )

    except DatabaseConnectionError:
        # Re-raise database connection errors as-is
        raise

    except Exception as e:
        logger.error(f"Failed to initialize {db_type} database: {e}", exc_info=True)
        raise DatabaseConnectionError(
            f"Database initialization failed for {db_type}", details=str(e)
        )


async def close_database() -> None:
    """
    Close connections for the configured database backend gracefully.

    This function:
    - Reads the DATABASE_TYPE environment variable
    - Closes connections for the appropriate database backend
    - Cleans up resources

    Note: This function does not raise exceptions during shutdown to avoid
    masking other shutdown errors.
    """
    try:
        db_type = get_database_type()
        logger.info(f"Closing {db_type} database connections...")

        if db_type == DATABASE_TYPE_SQLITE:
            # SQLAlchemy connections are managed per-request and don't need
            # explicit global cleanup, but we could dispose the engine if needed
            from app.database_sqlalchemy import engine

            await engine.dispose()
            logger.info("SQLite database connections closed")

        elif db_type == DATABASE_TYPE_MONGODB:
            from app.database_mongodb import close_mongodb

            await close_mongodb()
            logger.info("MongoDB database connections closed")

        else:
            logger.warning(f"Unknown database type during shutdown: {db_type}")

    except Exception as e:
        # Log but don't raise during shutdown
        logger.error(f"Error closing database connections: {e}", exc_info=True)
