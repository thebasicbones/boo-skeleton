"""SQLAlchemy database connection and session management"""
import os

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.sqlalchemy_resource import Base

# Database URL - use SQLite by default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# Create async engine
# For SQLite, we use StaticPool to ensure the same connection is reused
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=False,  # Set to True for SQL query logging
)

# Enable foreign key constraints for SQLite
if "sqlite" in DATABASE_URL:

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def get_sqlalchemy_db():
    """Dependency function to get SQLAlchemy database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_sqlalchemy_db():
    """Initialize SQLAlchemy database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_sqlalchemy_db():
    """Drop all SQLAlchemy tables - useful for testing"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
