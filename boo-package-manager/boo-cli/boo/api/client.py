"""Backend API client for communicating with boo-package-manager."""

import asyncio
import logging as std_logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import httpx

from boo.exceptions import (
    BackendError,
    CircularDependencyError,
    NetworkError,
    NotFoundError,
)

logger = std_logging.getLogger(__name__)

T = TypeVar("T")


class BackendClient:
    """Client for communicating with boo-package-manager backend."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the backend client.

        Args:
            base_url: Base URL of the backend API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Set up headers
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Create async client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def __aenter__(self) -> "BackendClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """
        Check if the backend is reachable.

        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"Backend health check failed: {e}")
            return False

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Handle HTTP error responses.

        Args:
            response: HTTP response object

        Raises:
            BackendError: For backend-specific errors
            NotFoundError: For 404 errors
            CircularDependencyError: For circular dependency errors
            httpx.HTTPStatusError: For other HTTP errors
        """
        if response.status_code >= 400:
            try:
                error_detail = response.json()
                error_type = error_detail.get("error", "Unknown")
                message = error_detail.get("message", "Unknown error")
                details = error_detail.get("details", {})

                logger.error(f"Backend error ({error_type}): {message}")

                # Handle specific error types
                if response.status_code == 404:
                    raise NotFoundError(message, details)
                elif error_type == "CircularDependencyError":
                    cycle_path = details.get("cycle", "").split(" → ")
                    raise CircularDependencyError(message, cycle_path)
                else:
                    raise BackendError(message, response.status_code, details)

            except (NotFoundError, CircularDependencyError, BackendError):
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Fallback for non-JSON responses
                logger.error(f"Backend error: {response.text}")
                raise BackendError(
                    f"Backend returned error: {response.text}",
                    response.status_code,
                )

    async def _retry_request(
        self,
        func: Callable[..., Any],
        *args: Any,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> Any:
        """
        Retry a request with exponential backoff.

        Args:
            func: Async function to retry
            *args: Positional arguments for func
            max_retries: Maximum number of retry attempts
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            NetworkError: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")

        # All retries failed
        raise NetworkError(
            f"Failed to connect to backend after {max_retries} attempts",
            {"last_error": str(last_exception)},
        )

    # CRUD Operations

    async def create_resource(
        self,
        name: str,
        version: str,
        dependencies: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new package resource in the backend.

        Args:
            name: Package name
            version: Package version
            dependencies: List of dependency package IDs
            description: Optional package description

        Returns:
            Created resource data

        Raises:
            NetworkError: If connection fails after retries
            BackendError: If the backend returns an error
            CircularDependencyError: If circular dependency is detected
        """
        payload = {
            "name": f"{name}=={version}",
            "description": description or f"Package {name} version {version}",
            "dependencies": dependencies or [],
        }

        logger.info(f"Creating resource: {name}=={version}")

        async def _make_request() -> httpx.Response:
            return await self.client.post("/api/resources", json=payload)

        response = await self._retry_request(_make_request)
        self._handle_error(response)
        return response.json()

    async def get_resource(self, resource_id: str) -> dict[str, Any]:
        """
        Get a package resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Resource data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        logger.info(f"Getting resource: {resource_id}")
        response = await self.client.get(f"/api/resources/{resource_id}")
        self._handle_error(response)
        return response.json()

    async def list_resources(self) -> list[dict[str, Any]]:
        """
        List all package resources.

        Returns:
            List of resource data

        Raises:
            NetworkError: If connection fails after retries
            BackendError: If the backend returns an error
        """
        logger.info("Listing all resources")

        async def _make_request() -> httpx.Response:
            return await self.client.get("/api/resources")

        response = await self._retry_request(_make_request)
        self._handle_error(response)
        return response.json()

    async def update_resource(
        self,
        resource_id: str,
        name: Optional[str] = None,
        version: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update a package resource.

        Args:
            resource_id: Resource ID
            name: Optional new package name
            version: Optional new package version
            dependencies: Optional new list of dependency package IDs
            description: Optional new package description

        Returns:
            Updated resource data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        payload: dict[str, Any] = {}

        if name and version:
            payload["name"] = f"{name}=={version}"
        elif name:
            payload["name"] = name

        if description is not None:
            payload["description"] = description

        if dependencies is not None:
            payload["dependencies"] = dependencies

        logger.info(f"Updating resource: {resource_id}")
        response = await self.client.put(f"/api/resources/{resource_id}", json=payload)
        self._handle_error(response)
        return response.json()

    async def delete_resource(
        self, resource_id: str, cascade: bool = False
    ) -> None:
        """
        Delete a package resource.

        Args:
            resource_id: Resource ID
            cascade: If True, also delete dependent resources

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        params = {"cascade": str(cascade).lower()}
        logger.info(f"Deleting resource: {resource_id} (cascade={cascade})")
        response = await self.client.delete(f"/api/resources/{resource_id}", params=params)
        self._handle_error(response)

    # Search Operations

    async def search_resources(self, query: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Search for package resources.

        The backend returns results in topological order (dependencies before dependents).
        An empty query returns all resources in topological order.

        Args:
            query: Search query (optional). If None or empty, returns all resources.

        Returns:
            List of resource data in topological order

        Raises:
            NetworkError: If connection fails after retries
            BackendError: If the backend returns an error
        """
        params = {}
        if query:
            params["q"] = query

        logger.info(f"Searching resources: {query or '(all)'}")

        async def _make_request() -> httpx.Response:
            return await self.client.get("/api/search", params=params)

        response = await self._retry_request(_make_request)
        self._handle_error(response)
        return response.json()
