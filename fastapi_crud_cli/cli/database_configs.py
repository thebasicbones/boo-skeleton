"""
Database configuration module for FastAPI CRUD CLI.

This module defines database-specific configurations including dependencies,
environment variables, and prompts for each supported database backend.
"""

from abc import ABC, abstractmethod
from typing import Any


class DatabaseConfig(ABC):
    """
    Abstract base class for database configurations.
    
    Each database backend (SQLite, MongoDB, PostgreSQL) implements this interface
    to provide database-specific configuration, dependencies, and prompts.
    """
    
    def __init__(self):
        """Initialize database configuration."""
        self.name: str = ""
        self.description: str = ""
        self.dependencies: list[str] = []
        self.env_variables: dict[str, str] = {}
    
    @abstractmethod
    def get_prompts(self) -> list[dict[str, Any]]:
        """
        Return list of prompts for this database.
        
        Returns:
            List of prompt dictionaries with keys:
                - name: Variable name for the prompt
                - message: Prompt message to display
                - default: Default value
                - type: Input type (optional)
        """
        pass
    
    @abstractmethod
    def generate_env_content(self, user_config: dict[str, Any]) -> str:
        """
        Generate .env file content for this database.
        
        Args:
            user_config: User-provided configuration values
            
        Returns:
            String content for .env file with database-specific variables
        """
        pass


class SQLiteConfig(DatabaseConfig):
    """Configuration for SQLite database backend."""
    
    def __init__(self):
        """Initialize SQLite configuration."""
        super().__init__()
        self.name = "SQLite"
        self.description = "Lightweight file-based SQL database (ideal for development)"
        self.dependencies = [
            "sqlalchemy>=2.0.0",
            "aiosqlite>=0.19.0",
        ]
        self.env_variables = {
            "DATABASE_TYPE": "sqlite",
            "DATABASE_URL": "sqlite+aiosqlite:///./app.db",
        }
    
    def get_prompts(self) -> list[dict[str, Any]]:
        """
        Return prompts for SQLite configuration.
        
        SQLite requires minimal configuration - just the database file path.
        
        Returns:
            List containing database file path prompt
        """
        return [
            {
                "name": "database_file",
                "message": "Database file path",
                "default": "./app.db",
                "type": "text",
            }
        ]
    
    def generate_env_content(self, user_config: dict[str, Any]) -> str:
        """
        Generate .env file content for SQLite.
        
        Args:
            user_config: Dictionary containing 'database_file' key
            
        Returns:
            Environment variable content for SQLite configuration
        """
        database_file = user_config.get("database_file", "./app.db")
        
        return f"""# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///{database_file}

# Application Settings
ENVIRONMENT=development
"""


class MongoDBConfig(DatabaseConfig):
    """Configuration for MongoDB database backend."""
    
    def __init__(self):
        """Initialize MongoDB configuration."""
        super().__init__()
        self.name = "MongoDB"
        self.description = "NoSQL document database (recommended for production)"
        self.dependencies = [
            "pymongo>=4.0.0",
            "motor>=3.0.0",
        ]
        self.env_variables = {
            "DATABASE_TYPE": "mongodb",
            "DATABASE_URL": "mongodb://localhost:27017",
            "MONGODB_DATABASE": "fastapi_crud",
        }
    
    def get_prompts(self) -> list[dict[str, Any]]:
        """
        Return prompts for MongoDB configuration.
        
        MongoDB requires connection URL and database name.
        
        Returns:
            List containing MongoDB connection URL and database name prompts
        """
        return [
            {
                "name": "mongodb_url",
                "message": "MongoDB connection URL",
                "default": "mongodb://localhost:27017",
                "type": "text",
            },
            {
                "name": "database_name",
                "message": "Database name",
                "default": "fastapi_crud",
                "type": "text",
            },
        ]
    
    def generate_env_content(self, user_config: dict[str, Any]) -> str:
        """
        Generate .env file content for MongoDB.
        
        Args:
            user_config: Dictionary containing 'mongodb_url' and 'database_name' keys
            
        Returns:
            Environment variable content for MongoDB configuration
        """
        mongodb_url = user_config.get("mongodb_url", "mongodb://localhost:27017")
        database_name = user_config.get("database_name", "fastapi_crud")
        
        return f"""# Database Configuration
DATABASE_TYPE=mongodb
DATABASE_URL={mongodb_url}
MONGODB_DATABASE={database_name}

# Application Settings
ENVIRONMENT=development
"""


class PostgreSQLConfig(DatabaseConfig):
    """Configuration for PostgreSQL database backend."""
    
    def __init__(self):
        """Initialize PostgreSQL configuration."""
        super().__init__()
        self.name = "PostgreSQL"
        self.description = "Advanced open-source relational database"
        self.dependencies = [
            "sqlalchemy>=2.0.0",
            "asyncpg>=0.29.0",
            "psycopg2-binary>=2.9.0",
        ]
        self.env_variables = {
            "DATABASE_TYPE": "postgresql",
            "DATABASE_URL": "postgresql+asyncpg://user:password@localhost:5432/dbname",
        }
    
    def get_prompts(self) -> list[dict[str, Any]]:
        """
        Return prompts for PostgreSQL configuration.
        
        PostgreSQL requires host, port, database name, username, and password.
        
        Returns:
            List containing PostgreSQL connection parameter prompts
        """
        return [
            {
                "name": "host",
                "message": "PostgreSQL host",
                "default": "localhost",
                "type": "text",
            },
            {
                "name": "port",
                "message": "PostgreSQL port",
                "default": "5432",
                "type": "text",
            },
            {
                "name": "database_name",
                "message": "Database name",
                "default": "fastapi_crud",
                "type": "text",
            },
            {
                "name": "username",
                "message": "Database username",
                "default": "postgres",
                "type": "text",
            },
            {
                "name": "password",
                "message": "Database password",
                "default": "",
                "type": "password",
            },
        ]
    
    def generate_env_content(self, user_config: dict[str, Any]) -> str:
        """
        Generate .env file content for PostgreSQL.
        
        Args:
            user_config: Dictionary containing PostgreSQL connection parameters
            
        Returns:
            Environment variable content for PostgreSQL configuration
        """
        host = user_config.get("host", "localhost")
        port = user_config.get("port", "5432")
        database_name = user_config.get("database_name", "fastapi_crud")
        username = user_config.get("username", "postgres")
        password = user_config.get("password", "")
        
        # Build connection URL
        database_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database_name}"
        
        return f"""# Database Configuration
DATABASE_TYPE=postgresql
DATABASE_URL={database_url}

# Application Settings
ENVIRONMENT=development
"""


# Registry of all available database configurations
DATABASE_CONFIGS: dict[str, DatabaseConfig] = {
    "sqlite": SQLiteConfig(),
    "mongodb": MongoDBConfig(),
    "postgresql": PostgreSQLConfig(),
}


def get_database_config(database_type: str) -> DatabaseConfig:
    """
    Get database configuration by type.
    
    Args:
        database_type: Database type identifier (sqlite, mongodb, postgresql)
        
    Returns:
        DatabaseConfig instance for the specified database type
        
    Raises:
        ValueError: If database type is not supported
    """
    if database_type not in DATABASE_CONFIGS:
        available = ", ".join(DATABASE_CONFIGS.keys())
        raise ValueError(
            f"Unsupported database type: {database_type}. "
            f"Available options: {available}"
        )
    
    return DATABASE_CONFIGS[database_type]


def get_available_databases() -> list[tuple[str, str]]:
    """
    Get list of available database types with descriptions.
    
    Returns:
        List of tuples containing (database_type, description)
    """
    return [
        (db_type, config.description)
        for db_type, config in DATABASE_CONFIGS.items()
    ]
