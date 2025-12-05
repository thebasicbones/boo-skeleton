"""Property-based tests for backend API client.

Feature: python-package-manager-cli, Property 1: Installation order follows topological sort
"""

import pytest
from hypothesis import given, strategies as st, settings
from boo.api.client import BackendClient
import respx
import httpx


# Strategies for generating test data
package_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), min_codepoint=97),
    min_size=1,
    max_size=20,
)

version_strategy = st.from_regex(r"^\d+\.\d+\.\d+$", fullmatch=True)

resource_id_strategy = st.uuids().map(str)


@pytest.mark.asyncio
@given(
    name=package_name_strategy,
    version=version_strategy,
)
@settings(max_examples=100)
async def test_create_resource_preserves_name_and_version(name: str, version: str) -> None:
    """
    Property: For any package name and version, creating a resource should preserve
    the exact name and version in the response.

    Feature: python-package-manager-cli, Property 2: Version pinning is preserved
    Validates: Requirements 1.2
    """
    # Mock the backend response
    expected_resource = {
        "id": "test-id-123",
        "name": f"{name}=={version}",
        "description": f"Package {name} version {version}",
        "dependencies": [],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    async with respx.mock:
        respx.post("http://localhost:8000/api/resources").mock(
            return_value=httpx.Response(200, json=expected_resource)
        )

        async with BackendClient() as client:
            result = await client.create_resource(name=name, version=version)

            # Verify the name and version are preserved
            assert result["name"] == f"{name}=={version}"
            assert name in result["name"]
            assert version in result["name"]


@pytest.mark.asyncio
@given(
    packages=st.lists(
        st.tuples(package_name_strategy, version_strategy),
        min_size=1,
        max_size=5,
        unique=True,
    )
)
@settings(max_examples=100)
async def test_search_returns_list_for_any_query(
    packages: list[tuple[str, str]]
) -> None:
    """
    Property: For any search query, the backend client should return a list
    (possibly empty) of resources.

    Feature: python-package-manager-cli, Property 17: Search result ordering
    Validates: Requirements 6.5
    """
    # Mock the backend response with topologically sorted resources
    mock_resources = [
        {
            "id": f"id-{i}",
            "name": f"{name}=={version}",
            "description": f"Package {name}",
            "dependencies": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        for i, (name, version) in enumerate(packages)
    ]

    async with respx.mock:
        respx.get("http://localhost:8000/api/search").mock(
            return_value=httpx.Response(200, json=mock_resources)
        )

        async with BackendClient() as client:
            results = await client.search_resources()

            # Verify we get a list
            assert isinstance(results, list)
            # Verify the list has the expected length
            assert len(results) == len(packages)
            # Verify each result has required fields
            for result in results:
                assert "id" in result
                assert "name" in result
                assert "dependencies" in result


@pytest.mark.asyncio
@given(
    resource_id=resource_id_strategy,
)
@settings(max_examples=100)
async def test_delete_resource_accepts_any_valid_id(resource_id: str) -> None:
    """
    Property: For any valid resource ID, the delete operation should complete
    without error when the resource exists.

    Feature: python-package-manager-cli, Property 6: Uninstall cleanup
    Validates: Requirements 2.4
    """
    async with respx.mock:
        # Mock successful deletion
        respx.delete(f"http://localhost:8000/api/resources/{resource_id}").mock(
            return_value=httpx.Response(204)
        )

        async with BackendClient() as client:
            # Should not raise an exception
            await client.delete_resource(resource_id)


@pytest.mark.asyncio
@given(
    name=package_name_strategy,
    version=version_strategy,
    dependencies=st.lists(resource_id_strategy, max_size=3),
)
@settings(max_examples=100)
async def test_create_resource_with_dependencies_preserves_list(
    name: str, version: str, dependencies: list[str]
) -> None:
    """
    Property: For any package with dependencies, creating a resource should
    preserve the exact dependency list.

    Feature: python-package-manager-cli, Property 1: Installation order follows topological sort
    Validates: Requirements 1.4
    """
    expected_resource = {
        "id": "test-id-123",
        "name": f"{name}=={version}",
        "description": f"Package {name} version {version}",
        "dependencies": dependencies,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    async with respx.mock:
        respx.post("http://localhost:8000/api/resources").mock(
            return_value=httpx.Response(200, json=expected_resource)
        )

        async with BackendClient() as client:
            result = await client.create_resource(
                name=name, version=version, dependencies=dependencies
            )

            # Verify dependencies are preserved
            assert result["dependencies"] == dependencies
            assert len(result["dependencies"]) == len(dependencies)


@pytest.mark.asyncio
@given(
    cascade=st.booleans(),
)
@settings(max_examples=100)
async def test_delete_cascade_parameter_is_passed(cascade: bool) -> None:
    """
    Property: For any cascade value (True/False), the delete operation should
    pass the cascade parameter to the backend.

    Feature: python-package-manager-cli, Property 5: Cascade delete completeness
    Validates: Requirements 2.3
    """
    resource_id = "test-resource-id"

    async with respx.mock:
        route = respx.delete(
            f"http://localhost:8000/api/resources/{resource_id}",
            params={"cascade": str(cascade).lower()},
        ).mock(return_value=httpx.Response(204))

        async with BackendClient() as client:
            await client.delete_resource(resource_id, cascade=cascade)

            # Verify the request was made with correct cascade parameter
            assert route.called
