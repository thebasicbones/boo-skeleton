"""Tests for TopologicalSortService"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.topological_sort_service import CircularDependencyError, TopologicalSortService


class TestTopologicalSort:
    """Test Kahn's algorithm implementation"""

    def test_empty_list(self):
        """Test sorting empty resource list"""
        result = TopologicalSortService.topological_sort([])
        assert result == []

    def test_single_resource_no_dependencies(self):
        """Test single resource with no dependencies"""
        resources = [{"id": "A", "dependencies": []}]
        result = TopologicalSortService.topological_sort(resources)
        assert len(result) == 1
        assert result[0]["id"] == "A"

    def test_linear_dependency_chain(self):
        """Test linear dependency chain: A -> B -> C"""
        resources = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": ["C"]},
            {"id": "C", "dependencies": []},
        ]
        result = TopologicalSortService.topological_sort(resources)
        ids = [r["id"] for r in result]

        # C should come before B, B should come before A
        assert ids.index("C") < ids.index("B")
        assert ids.index("B") < ids.index("A")

    def test_multiple_independent_resources(self):
        """Test multiple resources with no dependencies"""
        resources = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": []},
            {"id": "C", "dependencies": []},
        ]
        result = TopologicalSortService.topological_sort(resources)
        assert len(result) == 3
        ids = {r["id"] for r in result}
        assert ids == {"A", "B", "C"}

    def test_diamond_dependency(self):
        """Test diamond dependency: A depends on B and C, both depend on D"""
        resources = [
            {"id": "A", "dependencies": ["B", "C"]},
            {"id": "B", "dependencies": ["D"]},
            {"id": "C", "dependencies": ["D"]},
            {"id": "D", "dependencies": []},
        ]
        result = TopologicalSortService.topological_sort(resources)
        ids = [r["id"] for r in result]

        # D should come first
        assert ids[0] == "D"
        # B and C should come before A
        assert ids.index("B") < ids.index("A")
        assert ids.index("C") < ids.index("A")

    def test_complex_dag(self):
        """Test complex DAG with multiple dependency paths"""
        resources = [
            {"id": "A", "dependencies": ["B", "C"]},
            {"id": "B", "dependencies": ["D"]},
            {"id": "C", "dependencies": ["D", "E"]},
            {"id": "D", "dependencies": ["F"]},
            {"id": "E", "dependencies": []},
            {"id": "F", "dependencies": []},
        ]
        result = TopologicalSortService.topological_sort(resources)
        ids = [r["id"] for r in result]

        # Verify all dependency constraints
        assert ids.index("B") < ids.index("A")
        assert ids.index("C") < ids.index("A")
        assert ids.index("D") < ids.index("B")
        assert ids.index("D") < ids.index("C")
        assert ids.index("E") < ids.index("C")
        assert ids.index("F") < ids.index("D")

    def test_nonexistent_dependency_ignored(self):
        """Test that dependencies to non-existent resources are ignored"""
        resources = [
            {"id": "A", "dependencies": ["B", "Z"]},  # Z doesn't exist
            {"id": "B", "dependencies": []},
        ]
        result = TopologicalSortService.topological_sort(resources)
        ids = [r["id"] for r in result]

        # Should still work, ignoring the non-existent dependency
        assert ids.index("B") < ids.index("A")


class TestCircularDependencyDetection:
    """Test circular dependency detection"""

    def test_direct_cycle_two_nodes(self):
        """Test direct cycle: A -> B -> A"""
        resources = [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": ["A"]}]

        with pytest.raises(CircularDependencyError) as exc_info:
            TopologicalSortService.topological_sort(resources)

        # Verify cycle path is identified
        assert "A" in str(exc_info.value)
        assert "B" in str(exc_info.value)

    def test_self_dependency(self):
        """Test self-dependency: A -> A"""
        resources = [{"id": "A", "dependencies": ["A"]}]

        with pytest.raises(CircularDependencyError) as exc_info:
            TopologicalSortService.topological_sort(resources)

        assert "A" in str(exc_info.value)

    def test_indirect_cycle_three_nodes(self):
        """Test indirect cycle: A -> B -> C -> A"""
        resources = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": ["C"]},
            {"id": "C", "dependencies": ["A"]},
        ]

        with pytest.raises(CircularDependencyError) as exc_info:
            TopologicalSortService.topological_sort(resources)

        # All three nodes should be in the cycle
        error_msg = str(exc_info.value)
        assert "A" in error_msg
        assert "B" in error_msg
        assert "C" in error_msg

    def test_cycle_in_larger_graph(self):
        """Test cycle detection in a larger graph with some valid paths"""
        resources = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": ["C"]},
            {"id": "C", "dependencies": ["D"]},
            {"id": "D", "dependencies": ["B"]},  # Cycle: B -> C -> D -> B
            {"id": "E", "dependencies": []},  # Independent node
        ]

        with pytest.raises(CircularDependencyError):
            TopologicalSortService.topological_sort(resources)

    def test_has_cycle_returns_true(self):
        """Test has_cycle method returns True for cyclic graph"""
        resources = [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": ["A"]}]

        assert TopologicalSortService.has_cycle(resources) is True

    def test_has_cycle_returns_false(self):
        """Test has_cycle method returns False for acyclic graph"""
        resources = [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": []}]

        assert TopologicalSortService.has_cycle(resources) is False


class TestValidateNoCycles:
    """Test validation method for create/update operations"""

    def test_validate_new_resource_no_cycle(self):
        """Test validation passes when adding resource creates no cycle"""
        existing = [{"id": "A", "dependencies": []}, {"id": "B", "dependencies": ["A"]}]

        # Adding C that depends on B should be fine
        TopologicalSortService.validate_no_cycles(existing, "C", ["B"])

    def test_validate_new_resource_creates_cycle(self):
        """Test validation fails when adding resource creates cycle"""
        existing = [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": []}]

        # Adding dependency from B to A would create cycle
        with pytest.raises(CircularDependencyError):
            TopologicalSortService.validate_no_cycles(existing, "B", ["A"])

    def test_validate_update_resource_no_cycle(self):
        """Test validation passes when updating resource creates no cycle"""
        existing = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": []},
            {"id": "C", "dependencies": []},
        ]

        # Updating C to depend on A should be fine
        TopologicalSortService.validate_no_cycles(existing, "C", ["A"])

    def test_validate_update_resource_creates_cycle(self):
        """Test validation fails when updating resource creates cycle"""
        existing = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": ["C"]},
            {"id": "C", "dependencies": []},
        ]

        # Updating C to depend on A would create cycle: A -> B -> C -> A
        with pytest.raises(CircularDependencyError):
            TopologicalSortService.validate_no_cycles(existing, "C", ["A"])

    def test_validate_self_dependency(self):
        """Test validation fails for self-dependency"""
        existing = [{"id": "A", "dependencies": []}]

        # A depending on itself should fail
        with pytest.raises(CircularDependencyError):
            TopologicalSortService.validate_no_cycles(existing, "A", ["A"])

    def test_validate_new_resource_with_no_dependencies(self):
        """Test validation passes for new resource with no dependencies"""
        existing = [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": []}]

        # Adding C with no dependencies should always be fine
        TopologicalSortService.validate_no_cycles(existing, "C", [])

    def test_validate_complex_cycle_prevention(self):
        """Test validation prevents complex multi-node cycles"""
        existing = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": ["C"]},
            {"id": "C", "dependencies": ["D"]},
            {"id": "D", "dependencies": []},
        ]

        # Updating D to depend on A would create a 4-node cycle
        with pytest.raises(CircularDependencyError):
            TopologicalSortService.validate_no_cycles(existing, "D", ["A"])


# Property-Based Tests


def generate_dag(
    num_nodes: int, edge_probability: float = 0.3
) -> tuple[list[dict], dict[str, set[str]]]:
    """
    Generate a random Directed Acyclic Graph (DAG).

    Returns:
        Tuple of (resources list, adjacency dict for verification)
    """
    if num_nodes == 0:
        return [], {}

    # Create nodes with IDs
    node_ids = [f"node_{i}" for i in range(num_nodes)]

    # Build adjacency list ensuring no cycles (only add edges from lower to higher indices)
    adjacency = {node_id: set() for node_id in node_ids}

    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            # Randomly add edge from node_j to node_i (j depends on i)
            # This ensures acyclicity since j > i
            if edge_probability > 0 and (hash((i, j)) % 100) / 100.0 < edge_probability:
                adjacency[node_ids[j]].add(node_ids[i])

    # Convert to resource format
    resources = [{"id": node_id, "dependencies": list(adjacency[node_id])} for node_id in node_ids]

    return resources, adjacency


@st.composite
def dag_strategy(draw):
    """Hypothesis strategy for generating random DAGs"""
    num_nodes = draw(st.integers(min_value=0, max_value=20))
    edge_prob = draw(st.floats(min_value=0.0, max_value=0.5))

    resources, adjacency = generate_dag(num_nodes, edge_prob)
    return resources, adjacency


class TestTopologicalSortProperties:
    """Property-based tests for topological sort"""

    # Feature: fastapi-crud-backend, Property 9: Topological sort ordering
    # Validates: Requirements 5.1
    @settings(max_examples=100)
    @given(dag_strategy())
    def test_property_topological_sort_ordering(self, dag_data):
        """
        Property: For any set of resources with dependency relationships forming a DAG,
        the search endpoint should return results where all dependencies appear before their dependents.

        This test generates random DAGs and verifies that in the sorted output,
        every resource appears after all of its dependencies.
        """
        resources, adjacency = dag_data

        # Skip empty graphs
        if not resources:
            result = TopologicalSortService.topological_sort(resources)
            assert result == []
            return

        # Perform topological sort
        result = TopologicalSortService.topological_sort(resources)

        # Verify all resources are in the result
        assert len(result) == len(resources)
        result_ids = {r["id"] for r in result}
        original_ids = {r["id"] for r in resources}
        assert result_ids == original_ids

        # Create position map for efficient lookup
        position = {r["id"]: idx for idx, r in enumerate(result)}

        # Verify the core property: all dependencies appear before dependents
        for resource in result:
            resource_id = resource["id"]
            resource_position = position[resource_id]

            # Check each dependency
            for dep_id in resource.get("dependencies", []):
                # Only check dependencies that exist in the resource set
                if dep_id in position:
                    dep_position = position[dep_id]
                    # Dependency must appear before the resource that depends on it
                    assert (
                        dep_position < resource_position
                    ), f"Dependency violation: {dep_id} (pos {dep_position}) should appear before {resource_id} (pos {resource_position})"
