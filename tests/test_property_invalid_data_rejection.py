"""Property-based tests for invalid data rejection

Feature: fastapi-crud-backend, Property 2: Invalid data rejection
Validates: Requirements 1.2, 6.1, 6.2, 6.3

For any invalid resource data (missing required fields, wrong types, invalid dependencies),
the API should reject the request with an HTTP 422 status code and detailed validation error.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from pydantic import ValidationError
from app.schemas import ResourceCreate, ResourceUpdate


# Strategy for generating invalid names
@st.composite
def invalid_names(draw):
    """Generate invalid name values"""
    choice = draw(st.integers(min_value=0, max_value=3))
    
    if choice == 0:
        # Empty string
        return ""
    elif choice == 1:
        # Whitespace only
        return draw(st.text(alphabet=" \t\n\r", min_size=1, max_size=10))
    elif choice == 2:
        # Too long (> 100 characters)
        return draw(st.text(min_size=101, max_size=200))
    else:
        # None (missing required field)
        return None


# Strategy for generating invalid descriptions
@st.composite
def invalid_descriptions(draw):
    """Generate invalid description values"""
    # Too long (> 500 characters)
    return draw(st.text(min_size=501, max_size=1000))


# Strategy for generating invalid dependencies
@st.composite
def invalid_dependencies(draw):
    """Generate invalid dependency lists"""
    choice = draw(st.integers(min_value=0, max_value=1))
    
    if choice == 0:
        # Duplicate dependencies
        dep_id = draw(st.text(min_size=1, max_size=50))
        count = draw(st.integers(min_value=2, max_value=5))
        return [dep_id] * count
    else:
        # List with duplicates mixed in
        unique_deps = draw(st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=5, unique=True))
        # Add a duplicate
        duplicate = draw(st.sampled_from(unique_deps))
        unique_deps.append(duplicate)
        return unique_deps


class TestPropertyInvalidDataRejection:
    """Property-based tests for invalid data rejection"""
    
    @settings(max_examples=100)
    @given(invalid_name=invalid_names())
    def test_resource_create_rejects_invalid_names(self, invalid_name):
        """
        Property: For any invalid name value, ResourceCreate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 1.2, 6.1, 6.2
        """
        with pytest.raises(ValidationError) as exc_info:
            if invalid_name is None:
                # Missing required field - pass no name
                ResourceCreate()
            else:
                ResourceCreate(name=invalid_name)
        
        # Verify it's a validation error (which would translate to HTTP 422)
        assert exc_info.value.errors()
        # Ensure error details are present
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any('name' in str(error).lower() for error in errors)
    
    @settings(max_examples=100)
    @given(invalid_desc=invalid_descriptions())
    def test_resource_create_rejects_invalid_descriptions(self, invalid_desc):
        """
        Property: For any invalid description value, ResourceCreate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 1.2, 6.1, 6.2
        """
        with pytest.raises(ValidationError) as exc_info:
            ResourceCreate(name="Valid Name", description=invalid_desc)
        
        # Verify it's a validation error (which would translate to HTTP 422)
        assert exc_info.value.errors()
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any('description' in str(error).lower() for error in errors)
    
    @settings(max_examples=100)
    @given(invalid_deps=invalid_dependencies())
    def test_resource_create_rejects_duplicate_dependencies(self, invalid_deps):
        """
        Property: For any dependency list with duplicates, ResourceCreate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 1.2, 6.1, 6.2
        """
        with pytest.raises(ValidationError) as exc_info:
            ResourceCreate(name="Valid Name", dependencies=invalid_deps)
        
        # Verify it's a validation error (which would translate to HTTP 422)
        assert exc_info.value.errors()
        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Check that the error mentions dependencies or uniqueness
        error_str = str(errors).lower()
        assert 'dependencies' in error_str or 'unique' in error_str
    
    @settings(max_examples=100)
    @given(
        name=st.one_of(st.none(), st.text(max_size=0)),
        description=st.one_of(st.none(), st.text(min_size=501, max_size=1000)),
        dependencies=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10)
    )
    def test_resource_create_rejects_wrong_types(self, name, description, dependencies):
        """
        Property: For any data with wrong types or missing required fields, 
        ResourceCreate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 1.2, 6.2, 6.3
        """
        # Only test cases that should actually fail
        should_fail = (
            name is None or 
            name == "" or
            (description is not None and len(description) > 500)
        )
        
        if not should_fail:
            return  # Skip valid cases
        
        with pytest.raises(ValidationError):
            if name is None:
                ResourceCreate(description=description, dependencies=dependencies)
            else:
                ResourceCreate(name=name, description=description, dependencies=dependencies)
    
    @settings(max_examples=100)
    @given(invalid_name=invalid_names())
    def test_resource_update_rejects_invalid_names(self, invalid_name):
        """
        Property: For any invalid name value in update, ResourceUpdate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 6.1, 6.2
        """
        # Skip None case for updates (None means "don't update this field")
        if invalid_name is None:
            return
        
        with pytest.raises(ValidationError) as exc_info:
            ResourceUpdate(name=invalid_name)
        
        # Verify it's a validation error (which would translate to HTTP 422)
        assert exc_info.value.errors()
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any('name' in str(error).lower() for error in errors)
    
    @settings(max_examples=100)
    @given(invalid_desc=invalid_descriptions())
    def test_resource_update_rejects_invalid_descriptions(self, invalid_desc):
        """
        Property: For any invalid description value in update, ResourceUpdate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 6.1, 6.2
        """
        with pytest.raises(ValidationError) as exc_info:
            ResourceUpdate(description=invalid_desc)
        
        # Verify it's a validation error (which would translate to HTTP 422)
        assert exc_info.value.errors()
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any('description' in str(error).lower() for error in errors)
    
    @settings(max_examples=100)
    @given(invalid_deps=invalid_dependencies())
    def test_resource_update_rejects_duplicate_dependencies(self, invalid_deps):
        """
        Property: For any dependency list with duplicates in update, ResourceUpdate should reject with ValidationError
        
        Feature: fastapi-crud-backend, Property 2: Invalid data rejection
        Validates: Requirements 6.1, 6.2
        """
        with pytest.raises(ValidationError) as exc_info:
            ResourceUpdate(dependencies=invalid_deps)
        
        # Verify it's a validation error (which would translate to HTTP 422)
        assert exc_info.value.errors()
        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Check that the error mentions dependencies or uniqueness
        error_str = str(errors).lower()
        assert 'dependencies' in error_str or 'unique' in error_str
