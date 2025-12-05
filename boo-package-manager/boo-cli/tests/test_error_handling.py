"""Tests for error handling in backend client."""

import pytest
import httpx
import respx
from boo.api.client import BackendClient
from boo.exceptions import (
    NetworkError,
    BackendError,
    CircularDependencyError,
    NotFoundError,
)


@pytest.mark.asyncio
async def test_handle_404_error() -> None:
    """Test that 404 errors are properly handled."""
    async with respx.mock:
        respx.get("http://localhost:8000/api/resources/nonexistent").mock(
            return_value=httpx.Response(
                404,
                json={
                    "error": "NotFoundError",
                    "message": "Resource not found",
                    "details": {"resource_id": "nonexistent"},
                },
            )
        )

        async with BackendClient() as client:
            with pytest.raises(NotFoundError) as exc_info:
                await client.get_resource("nonexistent")

            assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_handle_circular_dependency_error() -> None:
    """Test that circular dependency errors are properly parsed."""
    async with respx.mock:
        respx.post("http://localhost:8000/api/resources").mock(
            return_value=httpx.Response(
                422,
                json={
                    "error": "CircularDependencyError",
                    "message": "Circular dependency detected",
                    "details": {"cycle": "A → B → C → A"},
                },
            )
        )

        async with BackendClient() as client:
            with pytest.raises(CircularDependencyError) as exc_info:
                await client.create_resource("test", "1.0.0", dependencies=["dep1"])

            assert exc_info.value.cycle_path == ["A", "B", "C", "A"]


@pytest.mark.asyncio
async def test_handle_generic_backend_error() -> None:
    """Test that generic backend errors are properly handled."""
    async with respx.mock:
        respx.get("http://localhost:8000/api/resources").mock(
            return_value=httpx.Response(
                500,
                json={
                    "error": "InternalServerError",
                    "message": "Database connection failed",
                    "details": {},
                },
            )
        )

        async with BackendClient() as client:
            with pytest.raises(BackendError) as exc_info:
                await client.list_resources()

            assert exc_info.value.status_code == 500
            assert "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_retry_on_connection_error() -> None:
    """Test that connection errors trigger retry logic."""
    attempt_count = 0

    async def mock_request(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise httpx.ConnectError("Connection refused")
        return httpx.Response(200, json=[])

    async with respx.mock:
        respx.get("http://localhost:8000/api/resources").mock(side_effect=mock_request)

        async with BackendClient() as client:
            # Should succeed on second attempt
            result = await client.list_resources()
            assert result == []
            assert attempt_count == 2


@pytest.mark.asyncio
async def test_network_error_after_max_retries() -> None:
    """Test that NetworkError is raised after max retries."""

    async def mock_request(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    async with respx.mock:
        respx.get("http://localhost:8000/api/resources").mock(side_effect=mock_request)

        async with BackendClient() as client:
            with pytest.raises(NetworkError) as exc_info:
                await client.list_resources()

            assert "after 3 attempts" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_error_triggers_retry() -> None:
    """Test that timeout errors trigger retry logic."""
    attempt_count = 0

    async def mock_request(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise httpx.TimeoutException("Request timeout")
        return httpx.Response(200, json=[])

    async with respx.mock:
        respx.get("http://localhost:8000/api/resources").mock(side_effect=mock_request)

        async with BackendClient() as client:
            result = await client.list_resources()
            assert result == []
            assert attempt_count == 2
