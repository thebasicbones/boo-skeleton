"""Configuration management for boo CLI."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Config(BaseSettings):
    """CLI configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="BOO_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Backend settings
    backend_url: str = Field(
        default="http://localhost:8000",
        description="URL of the boo-package-manager backend",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for backend authentication",
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )

    # Cache settings
    cache_dir: Path = Field(
        default=Path.home() / ".boo" / "cache",
        description="Directory for local cache",
    )

    # UI settings
    color_output: bool = Field(
        default=True,
        description="Enable colored output",
    )
    default_format: str = Field(
        default="table",
        description="Default output format (table, json, tree)",
    )

    # Sync settings
    auto_sync: bool = Field(
        default=True,
        description="Automatically sync with backend",
    )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment/files."""
    global _config
    _config = Config()
    return _config
