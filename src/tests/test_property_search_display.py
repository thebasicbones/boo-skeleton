"""Property-based tests for frontend search display with topological order

Feature: fastapi-crud-backend, Property 22: Search displays topological order
Validates: Requirements 12.1

This module tests that the frontend search functionality displays results
in topological order, where dependencies always appear before dependents.
"""

import os

import pytest
from httpx import AsyncClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from motor.motor_asyncio import AsyncIOMotorClient

from app.database_factory import get_db
from app.database_sqlalchemy import AsyncSessionLocal, drop_sqlalchemy_db, init_sqlalchemy_db
from main import app
from tests.strategies import valid_description_strategy, valid_name_strategy


@pytest.fixture(params=["sqlite", "mongodb"])
async def search_test_client(request, mongodb_available):
    """Create a test client for search display testing"""
    backend = request.param

    if backend == "sqlite":
        # Setup SQLite
        await drop_sqlalchemy_db()
        await init_sqlalchemy_db()

        async def override_get_db():
            async with AsyncSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

        app.dependency_overrides.clear()
        await drop_sqlalchemy_db()

    elif backend == "mongodb":
        if not mongodb_available:
            pytest.skip("MongoDB is not available for testing")

        # Setup MongoDB
        mongodb_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
        test_db_name = f"fastapi_crud_test_search_{os.getpid()}"

        client_instance = AsyncIOMotorClient(mongodb_url)
        db = client_instance[test_db_name]

        # Create indexes
        await db.resources.create_index("name")
        await db.resources.create_index("dependencies")

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

        app.dependency_overrides.clear()

        # Cleanup
        await client_instance.drop_database(test_db_name)
        client_instance.close()


def verify_topological_order(resources: list[dict], dependency_map: dict[str, list[str]]) -> bool:
    """
    Verify that resources are in topological order.

    For each resource, all of its dependencies must appear before it in the list.

    Args:
        resources: List of resource dictionaries in the order returned by search
        dependency_map: Map of resource ID to list of dependency IDs

    Returns:
        bool: True if the order is valid topological order
    """
    # Build a position map: resource_id -> position in list
    position_map = {resource["id"]: idx for idx, resource in enumerate(resources)}

    # For each resource, verify all dependencies appear before it
    for resource in resources:
        resource_id = resource["id"]
        resource_position = position_map[resource_id]

        # Get dependencies for this resource
        dependencies = dependency_map.get(resource_id, [])

        # Check each dependency appears before this resource
        for dep_id in dependencies:
            if dep_id in position_map:
                dep_position = position_map[dep_id]
                if dep_position >= resource_position:
                    # Dependency appears after dependent - invalid topological order
                    return False

    return True


@st.composite
def dag_structure_strategy(draw):
    """
    Generate a valid DAG (Directed Acyclic Graph) structure for testing.

    This strategy creates a set of resources with dependency relationships
    that form a valid DAG (no cycles).

    Returns:
        List of tuples: (name, description, dependencies_indices)
        where dependencies_indices are indices of resources this one depends on
    """
    # Generate 3-10 resources
    num_resources = draw(st.integers(min_value=3, max_value=10))

    resources = []
    for i in range(num_resources):
        name = draw(valid_name_strategy())
        description = draw(valid_description_strategy())

        # A resource can only depend on resources created before it
        # This ensures we create a DAG (no cycles)
        if i == 0:
            # First resource has no dependencies
            dependencies = []
        else:
            # Can depend on any previous resource
            max_deps = min(i, 3)  # Limit to 3 dependencies max
            num_deps = draw(st.integers(min_value=0, max_value=max_deps))

            if num_deps > 0:
                # Select unique indices from previous resources
                dependencies = draw(
                    st.lists(
                        st.integers(min_value=0, max_value=i - 1),
                        min_size=num_deps,
                        max_size=num_deps,
                        unique=True,
                    )
                )
            else:
                dependencies = []

        resources.append((name, description, dependencies))

    return resources


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    dag_structure=dag_structure_strategy(),
    search_query=st.one_of(
        st.just(""),
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),  # Exclude control characters
                blacklist_characters="\x00",  # Explicitly exclude null bytes
            ),
            max_size=20,
        ),
    ),
)
async def test_property_search_displays_topological_order(
    search_test_client: AsyncClient, dag_structure, search_query: str
):
    """
    Feature: fastapi-crud-backend, Property 22: Search displays topological order

    For any search query, the frontend should display results in topological
    order where all dependencies appear before their dependents.

    This test:
    1. Creates a DAG of resources with dependency relationships
    2. Performs a search (with or without query)
    3. Verifies the results are in valid topological order
    4. Verifies dependencies always appear before dependents

    Validates: Requirements 12.1
    """
    # Create resources based on the DAG structure
    created_resources = []
    dependency_map = {}  # resource_id -> list of dependency IDs

    for name, description, dep_indices in dag_structure:
        # Map dependency indices to actual resource IDs
        dependency_ids = [created_resources[idx]["id"] for idx in dep_indices]

        # Create the resource
        response = await search_test_client.post(
            "/api/resources",
            json={"name": name, "description": description, "dependencies": dependency_ids},
        )

        assert response.status_code == 201, f"Failed to create resource: {response.text}"

        created_resource = response.json()
        created_resources.append(created_resource)
        dependency_map[created_resource["id"]] = dependency_ids

    # Perform search with the query
    search_response = await search_test_client.get(
        "/api/search", params={"q": search_query} if search_query else {}
    )

    assert (
        search_response.status_code == 200
    ), f"Search failed with status {search_response.status_code}: {search_response.text}"

    search_results = search_response.json()

    # If search query is provided, results might be filtered
    # But they should still be in topological order
    assert isinstance(search_results, list), "Search results should be a list"

    # If we have results, verify topological order
    if len(search_results) > 0:
        # Verify topological order property
        is_valid_order = verify_topological_order(search_results, dependency_map)

        assert is_valid_order, (
            "Search results are not in valid topological order. "
            "Dependencies must appear before dependents."
        )

        # Additional verification: for each resource in results,
        # if its dependencies are also in results, they must appear before it
        result_ids = {r["id"] for r in search_results}

        for resource in search_results:
            resource_id = resource["id"]
            dependencies = dependency_map.get(resource_id, [])

            # For dependencies that are in the results, verify they appear before
            for dep_id in dependencies:
                if dep_id in result_ids:
                    # Find positions
                    dep_position = next(
                        i for i, r in enumerate(search_results) if r["id"] == dep_id
                    )
                    resource_position = next(
                        i for i, r in enumerate(search_results) if r["id"] == resource_id
                    )

                    assert (
                        dep_position < resource_position
                    ), f"Dependency {dep_id} must appear before dependent {resource_id}"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_search_empty_query_returns_all_in_topological_order(
    search_test_client: AsyncClient,
):
    """
    Feature: fastapi-crud-backend, Property 22: Search displays topological order

    When the search query is empty, all resources should be returned in
    topological order.

    Validates: Requirements 12.1, 12.4
    """
    # Create a simple dependency chain: A -> B -> C
    # (C depends on B, B depends on A)

    # Create A (no dependencies)
    response_a = await search_test_client.post(
        "/api/resources",
        json={"name": "Resource A", "description": "First resource", "dependencies": []},
    )
    assert response_a.status_code == 201
    resource_a = response_a.json()

    # Create B (depends on A)
    response_b = await search_test_client.post(
        "/api/resources",
        json={
            "name": "Resource B",
            "description": "Second resource",
            "dependencies": [resource_a["id"]],
        },
    )
    assert response_b.status_code == 201
    resource_b = response_b.json()

    # Create C (depends on B)
    response_c = await search_test_client.post(
        "/api/resources",
        json={
            "name": "Resource C",
            "description": "Third resource",
            "dependencies": [resource_b["id"]],
        },
    )
    assert response_c.status_code == 201
    resource_c = response_c.json()

    # Search with empty query
    search_response = await search_test_client.get("/api/search")
    assert search_response.status_code == 200

    results = search_response.json()

    # Should return all 3 resources
    assert len(results) >= 3, "Should return at least the 3 created resources"

    # Find positions of our resources
    positions = {}
    for idx, resource in enumerate(results):
        if resource["id"] == resource_a["id"]:
            positions["A"] = idx
        elif resource["id"] == resource_b["id"]:
            positions["B"] = idx
        elif resource["id"] == resource_c["id"]:
            positions["C"] = idx

    # Verify all three are present
    assert "A" in positions, "Resource A not found in results"
    assert "B" in positions, "Resource B not found in results"
    assert "C" in positions, "Resource C not found in results"

    # Verify topological order: A before B before C
    assert positions["A"] < positions["B"], "Resource A should appear before B (B depends on A)"
    assert positions["B"] < positions["C"], "Resource B should appear before C (C depends on B)"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_search_with_query_maintains_topological_order(
    search_test_client: AsyncClient,
):
    """
    Feature: fastapi-crud-backend, Property 22: Search displays topological order

    When a search query is provided, the filtered results should still
    maintain topological order.

    Validates: Requirements 12.1, 12.2
    """
    # Create resources with a common search term
    # A (contains "test") -> B (contains "test") -> C (no "test")

    # Create A
    response_a = await search_test_client.post(
        "/api/resources",
        json={
            "name": "Test Resource Alpha",
            "description": "First test resource",
            "dependencies": [],
        },
    )
    assert response_a.status_code == 201
    resource_a = response_a.json()

    # Create B (depends on A)
    response_b = await search_test_client.post(
        "/api/resources",
        json={
            "name": "Test Resource Beta",
            "description": "Second test resource",
            "dependencies": [resource_a["id"]],
        },
    )
    assert response_b.status_code == 201
    resource_b = response_b.json()

    # Create C (depends on B, but doesn't contain "test")
    response_c = await search_test_client.post(
        "/api/resources",
        json={
            "name": "Resource Gamma",
            "description": "Third resource",
            "dependencies": [resource_b["id"]],
        },
    )
    assert response_c.status_code == 201
    response_c.json()

    # Search for "test"
    search_response = await search_test_client.get("/api/search", params={"q": "test"})
    assert search_response.status_code == 200

    results = search_response.json()

    # Should return resources containing "test" (A and B)
    result_ids = [r["id"] for r in results]

    # Both A and B should be in results
    assert resource_a["id"] in result_ids, "Resource A should match search"
    assert resource_b["id"] in result_ids, "Resource B should match search"

    # Find positions
    pos_a = result_ids.index(resource_a["id"])
    pos_b = result_ids.index(resource_b["id"])

    # Verify topological order: A before B
    assert pos_a < pos_b, "Resource A should appear before B in search results (B depends on A)"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_search_complex_dag_topological_order(search_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 22: Search displays topological order

    Test a more complex DAG structure to ensure topological ordering works
    for non-linear dependency graphs.

    Structure:
        A   B
        |  /|
        | / |
        |/  |
        C   D
         \\ /
          E

    Valid topological orders include: A,B,C,D,E or B,A,D,C,E etc.
    But dependencies must always come before dependents.

    Validates: Requirements 12.1
    """
    # Create A and B (no dependencies)
    response_a = await search_test_client.post(
        "/api/resources", json={"name": "A", "description": "Node A", "dependencies": []}
    )
    assert response_a.status_code == 201
    resource_a = response_a.json()

    response_b = await search_test_client.post(
        "/api/resources", json={"name": "B", "description": "Node B", "dependencies": []}
    )
    assert response_b.status_code == 201
    resource_b = response_b.json()

    # Create C (depends on A and B)
    response_c = await search_test_client.post(
        "/api/resources",
        json={
            "name": "C",
            "description": "Node C",
            "dependencies": [resource_a["id"], resource_b["id"]],
        },
    )
    assert response_c.status_code == 201
    resource_c = response_c.json()

    # Create D (depends on A and B)
    response_d = await search_test_client.post(
        "/api/resources",
        json={
            "name": "D",
            "description": "Node D",
            "dependencies": [resource_a["id"], resource_b["id"]],
        },
    )
    assert response_d.status_code == 201
    resource_d = response_d.json()

    # Create E (depends on C and D)
    response_e = await search_test_client.post(
        "/api/resources",
        json={
            "name": "E",
            "description": "Node E",
            "dependencies": [resource_c["id"], resource_d["id"]],
        },
    )
    assert response_e.status_code == 201
    resource_e = response_e.json()

    # Search with empty query to get all
    search_response = await search_test_client.get("/api/search")
    assert search_response.status_code == 200

    results = search_response.json()

    # Build position map
    positions = {}
    for idx, resource in enumerate(results):
        if resource["id"] == resource_a["id"]:
            positions["A"] = idx
        elif resource["id"] == resource_b["id"]:
            positions["B"] = idx
        elif resource["id"] == resource_c["id"]:
            positions["C"] = idx
        elif resource["id"] == resource_d["id"]:
            positions["D"] = idx
        elif resource["id"] == resource_e["id"]:
            positions["E"] = idx

    # Verify all are present
    assert all(
        node in positions for node in ["A", "B", "C", "D", "E"]
    ), "All nodes should be in results"

    # Verify topological constraints
    # A and B must come before C
    assert positions["A"] < positions["C"], "A must come before C"
    assert positions["B"] < positions["C"], "B must come before C"

    # A and B must come before D
    assert positions["A"] < positions["D"], "A must come before D"
    assert positions["B"] < positions["D"], "B must come before D"

    # C and D must come before E
    assert positions["C"] < positions["E"], "C must come before E"
    assert positions["D"] < positions["E"], "D must come before E"


@pytest.mark.asyncio
@pytest.mark.property
async def test_property_search_no_dependencies_consistent_order(search_test_client: AsyncClient):
    """
    Feature: fastapi-crud-backend, Property 22: Search displays topological order

    When resources have no dependencies, they should still be returned in
    a consistent order.

    Validates: Requirements 12.1, 5.4
    """
    # Create multiple resources with no dependencies
    created_ids = []
    for i in range(5):
        response = await search_test_client.post(
            "/api/resources",
            json={
                "name": f"Independent Resource {i}",
                "description": f"Resource {i} with no dependencies",
                "dependencies": [],
            },
        )
        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    # Search multiple times and verify consistent order
    search_response_1 = await search_test_client.get("/api/search")
    assert search_response_1.status_code == 200
    results_1 = search_response_1.json()

    search_response_2 = await search_test_client.get("/api/search")
    assert search_response_2.status_code == 200
    results_2 = search_response_2.json()

    # Extract our created resource IDs from both results
    ids_1 = [r["id"] for r in results_1 if r["id"] in created_ids]
    ids_2 = [r["id"] for r in results_2 if r["id"] in created_ids]

    # Order should be consistent
    assert ids_1 == ids_2, "Resources with no dependencies should appear in consistent order"
