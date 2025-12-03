"""Tests for database factory module"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_factory import (
    DATABASE_TYPE_MONGODB,
    DATABASE_TYPE_SQLITE,
    close_database,
    get_database_type,
    get_repository,
    init_database,
)
from app.exceptions import DatabaseConnectionError
from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository


class TestGetDatabaseType:
    """Tests for get_database_type function"""

    def test_get_database_type_sqlite_default(self):
        """Test that sqlite is returned as default when DATABASE_TYPE is not set"""
        with patch.dict(os.environ, {}, clear=True):
            assert get_database_type() == DATABASE_TYPE_SQLITE

    def test_get_database_type_sqlite_explicit(self):
        """Test that sqlite is returned when explicitly configured"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            assert get_database_type() == DATABASE_TYPE_SQLITE

    def test_get_database_type_mongodb(self):
        """Test that mongodb is returned when configured"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "mongodb"}):
            assert get_database_type() == DATABASE_TYPE_MONGODB

    def test_get_database_type_case_insensitive(self):
        """Test that database type is case-insensitive"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "MONGODB"}):
            assert get_database_type() == DATABASE_TYPE_MONGODB

        with patch.dict(os.environ, {"DATABASE_TYPE": "SQLite"}):
            assert get_database_type() == DATABASE_TYPE_SQLITE

    def test_get_database_type_invalid(self):
        """Test that invalid database type raises error"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgres"}):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                get_database_type()

            assert "Invalid DATABASE_TYPE" in str(exc_info.value)


class TestGetRepository:
    """Tests for get_repository factory function"""

    def test_get_repository_sqlalchemy(self):
        """Test that SQLAlchemy repository is created for AsyncSession"""
        mock_session = MagicMock(spec=AsyncSession)

        repository = get_repository(mock_session)

        assert isinstance(repository, SQLAlchemyResourceRepository)
        assert repository.db is mock_session

    def test_get_repository_mongodb(self):
        """Test that MongoDB repository is created for AsyncIOMotorDatabase"""
        mock_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_db.resources = MagicMock()  # Add resources collection mock

        repository = get_repository(mock_db)

        assert isinstance(repository, MongoDBResourceRepository)
        assert repository.db is mock_db

    def test_get_repository_invalid_type(self):
        """Test that invalid database connection type raises error"""
        invalid_db = "not a database connection"

        with pytest.raises(DatabaseConnectionError) as exc_info:
            get_repository(invalid_db)

        assert "Unknown database connection type" in str(exc_info.value)


class TestInitDatabase:
    """Tests for init_database function"""

    @pytest.mark.asyncio
    async def test_init_database_sqlite(self):
        """Test that SQLite database is initialized correctly"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            with patch(
                "app.database_sqlalchemy.init_sqlalchemy_db", new_callable=AsyncMock
            ) as mock_init:
                await init_database()
                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_database_mongodb(self):
        """Test that MongoDB database is initialized correctly"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "mongodb"}):
            with patch("app.database_mongodb.init_mongodb", new_callable=AsyncMock) as mock_init:
                await init_database()
                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_database_error_handling(self):
        """Test that initialization errors are properly wrapped"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            with patch(
                "app.database_sqlalchemy.init_sqlalchemy_db", new_callable=AsyncMock
            ) as mock_init:
                mock_init.side_effect = Exception("Connection failed")

                with pytest.raises(DatabaseConnectionError) as exc_info:
                    await init_database()

                assert "Database initialization failed" in str(exc_info.value)


class TestCloseDatabase:
    """Tests for close_database function"""

    @pytest.mark.asyncio
    async def test_close_database_sqlite(self):
        """Test that SQLite database connections are closed correctly"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            with patch("app.database_sqlalchemy.engine") as mock_engine:
                mock_engine.dispose = AsyncMock()
                await close_database()
                mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database_mongodb(self):
        """Test that MongoDB database connections are closed correctly"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "mongodb"}):
            with patch("app.database_mongodb.close_mongodb", new_callable=AsyncMock) as mock_close:
                await close_database()
                mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database_error_handling(self):
        """Test that close errors are logged but not raised"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "mongodb"}):
            with patch("app.database_mongodb.close_mongodb", new_callable=AsyncMock) as mock_close:
                mock_close.side_effect = Exception("Close failed")

                # Should not raise exception
                await close_database()
