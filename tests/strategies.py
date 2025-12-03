"""Hypothesis strategies for generating test data

This module provides custom Hypothesis strategies for generating valid
resource data for property-based testing. These strategies ensure that
generated data conforms to the application's validation rules.
"""
from hypothesis import strategies as st
from app.schemas import ResourceCreate, ResourceUpdate
import uuid


@st.composite
def valid_name_strategy(draw):
    """
    Generate valid resource names (1-100 characters, non-empty after strip).
    
    This strategy generates names that:
    - Are between 1 and 100 characters long
    - Are not just whitespace
    - Exclude control characters that could cause issues
    
    Args:
        draw: Hypothesis draw function
    
    Returns:
        str: A valid resource name
    """
    # Generate text excluding control characters
    name = draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
        min_size=1,
        max_size=100
    ))
    
    # If the name is only whitespace, generate a non-whitespace name
    if not name.strip():
        name = draw(st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                blacklist_characters=' \t\n\r'
            ),
            min_size=1,
            max_size=100
        ))
    
    return name


@st.composite
def valid_description_strategy(draw):
    """
    Generate valid resource descriptions (optional, max 500 characters).
    
    This strategy generates descriptions that:
    - Can be None (optional field)
    - Are at most 500 characters long
    - Exclude control characters
    
    Args:
        draw: Hypothesis draw function
    
    Returns:
        Optional[str]: A valid resource description or None
    """
    return draw(st.one_of(
        st.none(),
        st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            max_size=500
        )
    ))


@st.composite
def resource_id_strategy(draw):
    """
    Generate valid resource IDs (UUIDs as strings).
    
    This strategy generates valid UUID strings that can be used as
    resource identifiers or dependency references.
    
    Args:
        draw: Hypothesis draw function
    
    Returns:
        str: A valid UUID string
    """
    return str(draw(st.uuids()))


@st.composite
def dependency_list_strategy(draw, min_size=0, max_size=5):
    """
    Generate valid dependency lists (unique resource IDs).
    
    This strategy generates lists of unique resource IDs that can be
    used as dependencies. The list is guaranteed to contain no duplicates.
    
    Args:
        draw: Hypothesis draw function
        min_size: Minimum number of dependencies (default: 0)
        max_size: Maximum number of dependencies (default: 5)
    
    Returns:
        List[str]: A list of unique resource ID strings
    """
    # Generate a set to ensure uniqueness, then convert to list
    num_deps = draw(st.integers(min_value=min_size, max_value=max_size))
    if num_deps == 0:
        return []
    
    # Generate unique UUIDs
    deps = []
    for _ in range(num_deps):
        deps.append(str(uuid.uuid4()))
    
    return deps


@st.composite
def resource_create_strategy(draw, with_dependencies=False):
    """
    Generate valid ResourceCreate data.
    
    This strategy generates ResourceCreate objects that satisfy all
    validation rules:
    - Name is 1-100 characters, non-empty after strip
    - Description is optional, max 500 characters
    - Dependencies are unique resource IDs
    
    Args:
        draw: Hypothesis draw function
        with_dependencies: If True, may include dependencies (default: False)
    
    Returns:
        ResourceCreate: A valid ResourceCreate object
    """
    name = draw(valid_name_strategy())
    description = draw(valid_description_strategy())
    
    # Only include dependencies if explicitly requested
    # This is because testing with dependencies requires those resources to exist
    if with_dependencies:
        dependencies = draw(dependency_list_strategy(min_size=0, max_size=5))
    else:
        dependencies = []
    
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=dependencies
    )


@st.composite
def resource_update_strategy(draw, include_name=True, include_description=True, include_dependencies=False):
    """
    Generate valid ResourceUpdate data.
    
    This strategy generates ResourceUpdate objects with optional fields.
    At least one field will be set to ensure the update is meaningful.
    
    Args:
        draw: Hypothesis draw function
        include_name: If True, may include name field (default: True)
        include_description: If True, may include description field (default: True)
        include_dependencies: If True, may include dependencies field (default: False)
    
    Returns:
        ResourceUpdate: A valid ResourceUpdate object
    """
    # Generate optional fields
    name = None
    description = None
    dependencies = None
    
    if include_name:
        name = draw(st.one_of(st.none(), valid_name_strategy()))
    
    if include_description:
        description = draw(st.one_of(st.none(), valid_description_strategy()))
    
    if include_dependencies:
        dependencies = draw(st.one_of(
            st.none(),
            dependency_list_strategy(min_size=0, max_size=5)
        ))
    
    # Ensure at least one field is set
    if name is None and description is None and dependencies is None:
        # Pick a random field to set
        field_choice = draw(st.integers(min_value=0, max_value=2))
        if field_choice == 0 and include_name:
            name = draw(valid_name_strategy())
        elif field_choice == 1 and include_description:
            description = draw(valid_description_strategy())
        elif include_dependencies:
            dependencies = draw(dependency_list_strategy(min_size=0, max_size=5))
        else:
            # Fallback to name if other options not available
            name = draw(valid_name_strategy())
    
    return ResourceUpdate(
        name=name,
        description=description,
        dependencies=dependencies
    )


@st.composite
def resource_create_with_existing_dependencies_strategy(draw, existing_ids):
    """
    Generate ResourceCreate data with dependencies from existing resources.
    
    This strategy is useful for testing relationship preservation and
    cascade operations where dependencies must reference actual resources.
    
    Args:
        draw: Hypothesis draw function
        existing_ids: List of existing resource IDs to choose from
    
    Returns:
        ResourceCreate: A valid ResourceCreate object with valid dependencies
    """
    name = draw(valid_name_strategy())
    description = draw(valid_description_strategy())
    
    # Select a subset of existing IDs as dependencies
    if existing_ids:
        num_deps = draw(st.integers(min_value=0, max_value=min(len(existing_ids), 5)))
        if num_deps > 0:
            dependencies = draw(st.lists(
                st.sampled_from(existing_ids),
                min_size=num_deps,
                max_size=num_deps,
                unique=True
            ))
        else:
            dependencies = []
    else:
        dependencies = []
    
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=dependencies
    )


@st.composite
def invalid_name_strategy(draw):
    """
    Generate invalid resource names for testing validation.
    
    This strategy generates names that should be rejected:
    - Empty strings
    - Whitespace-only strings
    - Strings exceeding 100 characters
    
    Args:
        draw: Hypothesis draw function
    
    Returns:
        str: An invalid resource name
    """
    return draw(st.one_of(
        # Empty string
        st.just(""),
        # Whitespace only
        st.text(alphabet=" \t\n\r", min_size=1, max_size=10),
        # Too long
        st.text(min_size=101, max_size=200)
    ))


@st.composite
def invalid_description_strategy(draw):
    """
    Generate invalid resource descriptions for testing validation.
    
    This strategy generates descriptions that should be rejected:
    - Strings exceeding 500 characters
    
    Args:
        draw: Hypothesis draw function
    
    Returns:
        str: An invalid resource description
    """
    return draw(st.text(min_size=501, max_size=1000))


@st.composite
def invalid_dependencies_strategy(draw):
    """
    Generate invalid dependency lists for testing validation.
    
    This strategy generates dependency lists that should be rejected:
    - Lists with duplicate IDs
    - Lists with invalid UUID formats
    
    Args:
        draw: Hypothesis draw function
    
    Returns:
        List[str]: An invalid dependency list
    """
    return draw(st.one_of(
        # Duplicate IDs
        st.lists(st.just("duplicate-id"), min_size=2, max_size=5),
        # Invalid UUID formats
        st.lists(st.text(alphabet="xyz", min_size=5, max_size=10), min_size=1, max_size=3)
    ))


# Convenience strategies for common test scenarios

# Strategy for creating a single resource without dependencies
simple_resource_strategy = resource_create_strategy(with_dependencies=False)

# Strategy for creating a resource that may have dependencies
resource_with_deps_strategy = resource_create_strategy(with_dependencies=True)

# Strategy for partial updates (only name)
name_only_update_strategy = resource_update_strategy(
    include_name=True,
    include_description=False,
    include_dependencies=False
)

# Strategy for partial updates (only description)
description_only_update_strategy = resource_update_strategy(
    include_name=False,
    include_description=True,
    include_dependencies=False
)

# Strategy for full updates (all fields)
full_update_strategy = resource_update_strategy(
    include_name=True,
    include_description=True,
    include_dependencies=True
)
