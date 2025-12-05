"""Tests for backend API client."""

import pytest
from boo.api.client import BackendClient
from boo.config import Config


def test_backend_client_initialization() -> None:
    """Test BackendClient initialization."""
    client = BackendClient()
    assert client.base_url == "http://localhost:8000"
    assert client.timeout == 30.0


def test_backend_client_with_custom_url() -> None:
    """Test BackendClient with custom URL."""
    client = BackendClient(base_url="http://example.com:9000")
    assert client.base_url == "http://example.com:9000"


def test_backend_client_with_api_key() -> None:
    """Test BackendClient with API key."""
    client = BackendClient(api_key="test-key")
    assert "Authorization" in client.client.headers
    assert client.client.headers["Authorization"] == "Bearer test-key"


def test_backend_client_strips_trailing_slash() -> None:
    """Test that trailing slash is removed from base URL."""
    client = BackendClient(base_url="http://localhost:8000/")
    assert client.base_url == "http://localhost:8000"


@pytest.mark.asyncio
async def test_backend_client_context_manager() -> None:
    """Test BackendClient as async context manager."""
    async with BackendClient() as client:
        assert client is not None
        assert client.client is not None


def test_config_defaults() -> None:
    """Test configuration defaults."""
    config = Config()
    assert config.backend_url == "http://localhost:8000"
    assert config.timeout == 30.0
    assert config.color_output is True
    assert config.auto_sync is True
