"""
Multi-environment configuration system using Pydantic Settings.

This module provides type-safe, validated configuration management
for development, staging, and production environments.
"""

import logging
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment-specific configuration.

    This class uses Pydantic Settings to load and validate configuration
    from environment variables and .env files. It supports multiple
    environments (development, staging, production) with appropriate
    defaults and validation rules.
    """

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment (development, staging, or production)",
    )

    # Database Configuration
    database_type: Literal["sqlite", "mongodb"] = Field(
        default="sqlite", description="Database backend type"
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./app.db",
        description="Database connection URL",
    )
    mongodb_database: str | None = Field(
        default=None, description="MongoDB database name (required for MongoDB)"
    )
    mongodb_timeout: int = Field(
        default=5000, description="MongoDB connection timeout in milliseconds"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port", ge=1, le=65535)
    api_reload: bool = Field(default=False, description="Enable auto-reload for development")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Application Metadata
    app_title: str = Field(default="FastAPI CRUD Backend", description="Application title")
    app_version: str = Field(default="1.0.0", description="Application version")

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Security Configuration
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for security features",
    )
    allowed_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env files
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is a valid logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {', '.join(valid_levels)}")
        return v_upper

    @field_validator("database_type")
    @classmethod
    def validate_database_type(cls, v: str) -> str:
        """Validate database type."""
        return v.lower()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        return v.lower()

    def __init__(self, **kwargs):
        """Initialize settings and perform post-validation checks."""
        super().__init__(**kwargs)

        # Validate MongoDB-specific requirements
        if self.database_type == "mongodb" and not self.mongodb_database:
            raise ValueError("mongodb_database is required when database_type is 'mongodb'")

        # Warn about insecure configurations in production
        if self.environment == "production":
            if self.secret_key == "dev-secret-key-change-in-production":
                logger.warning(
                    "Using default secret key in production! "
                    "Set SECRET_KEY environment variable."
                )
            if self.debug:
                logger.warning("Debug mode is enabled in production!")
            if "*" in self.allowed_origins:
                logger.warning(
                    "CORS is configured to allow all origins in production! " "This is insecure."
                )

    def get_database_url(self) -> str:
        """
        Get the appropriate database URL based on database type.

        Returns:
            str: Database connection URL
        """
        return self.database_url


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function implements a singleton pattern to ensure settings
    are loaded only once during application startup.

    Returns:
        Settings: Application settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(f"Settings loaded for environment: {_settings.environment}")
    return _settings
