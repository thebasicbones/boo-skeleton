"""Tests for Pydantic schemas"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    ErrorResponse,
    ResourceCreate,
    ResourceList,
    ResourceResponse,
    ResourceUpdate,
)


class TestResourceCreate:
    """Tests for ResourceCreate schema"""

    def test_valid_resource_create(self):
        """Test creating a valid resource"""
        data = {
            "name": "Test Resource",
            "description": "A test resource",
            "dependencies": ["dep1", "dep2"],
        }
        resource = ResourceCreate(**data)
        assert resource.name == "Test Resource"
        assert resource.description == "A test resource"
        assert resource.dependencies == ["dep1", "dep2"]

    def test_resource_create_minimal(self):
        """Test creating resource with only required fields"""
        resource = ResourceCreate(name="Minimal Resource")
        assert resource.name == "Minimal Resource"
        assert resource.description is None
        assert resource.dependencies == []

    def test_name_whitespace_stripped(self):
        """Test that name whitespace is stripped"""
        resource = ResourceCreate(name="  Spaced Name  ")
        assert resource.name == "Spaced Name"

    def test_empty_name_rejected(self):
        """Test that empty or whitespace-only names are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ResourceCreate(name="   ")
        assert "Name cannot be empty" in str(exc_info.value)

    def test_name_too_long_rejected(self):
        """Test that names exceeding max length are rejected"""
        with pytest.raises(ValidationError):
            ResourceCreate(name="x" * 101)

    def test_description_too_long_rejected(self):
        """Test that descriptions exceeding max length are rejected"""
        with pytest.raises(ValidationError):
            ResourceCreate(name="Test", description="x" * 501)

    def test_duplicate_dependencies_rejected(self):
        """Test that duplicate dependencies are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ResourceCreate(name="Test", dependencies=["dep1", "dep1"])
        assert "Dependencies must be unique" in str(exc_info.value)

    def test_description_whitespace_stripped(self):
        """Test that description whitespace is stripped"""
        resource = ResourceCreate(name="Test", description="  Description  ")
        assert resource.description == "Description"

    def test_empty_description_becomes_none(self):
        """Test that empty description becomes None"""
        resource = ResourceCreate(name="Test", description="   ")
        assert resource.description is None


class TestResourceUpdate:
    """Tests for ResourceUpdate schema"""

    def test_valid_resource_update(self):
        """Test updating with valid data"""
        data = {
            "name": "Updated Name",
            "description": "Updated description",
            "dependencies": ["new-dep"],
        }
        update = ResourceUpdate(**data)
        assert update.name == "Updated Name"
        assert update.description == "Updated description"
        assert update.dependencies == ["new-dep"]

    def test_partial_update(self):
        """Test partial updates with only some fields"""
        update = ResourceUpdate(name="Only Name")
        assert update.name == "Only Name"
        assert update.description is None
        assert update.dependencies is None

    def test_empty_update(self):
        """Test update with no fields"""
        update = ResourceUpdate()
        assert update.name is None
        assert update.description is None
        assert update.dependencies is None

    def test_name_whitespace_stripped(self):
        """Test that name whitespace is stripped"""
        update = ResourceUpdate(name="  Spaced  ")
        assert update.name == "Spaced"

    def test_empty_name_rejected(self):
        """Test that empty or whitespace-only names are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ResourceUpdate(name="   ")
        assert "Name cannot be empty" in str(exc_info.value)

    def test_duplicate_dependencies_rejected(self):
        """Test that duplicate dependencies are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ResourceUpdate(dependencies=["dep1", "dep1"])
        assert "Dependencies must be unique" in str(exc_info.value)


class TestResourceResponse:
    """Tests for ResourceResponse schema"""

    def test_valid_resource_response(self):
        """Test creating a valid response"""
        now = datetime.now(UTC)
        data = {
            "id": "test-id",
            "name": "Test Resource",
            "description": "A test",
            "dependencies": ["dep1"],
            "created_at": now,
            "updated_at": now,
        }
        response = ResourceResponse(**data)
        assert response.id == "test-id"
        assert response.name == "Test Resource"
        assert response.description == "A test"
        assert response.dependencies == ["dep1"]
        assert response.created_at == now
        assert response.updated_at == now

    def test_response_without_description(self):
        """Test response without optional description"""
        now = datetime.now(UTC)
        response = ResourceResponse(id="test-id", name="Test", created_at=now, updated_at=now)
        assert response.description is None
        assert response.dependencies == []


class TestResourceList:
    """Tests for ResourceList schema"""

    def test_valid_resource_list(self):
        """Test creating a valid resource list"""
        now = datetime.now(UTC)
        resources = [ResourceResponse(id="id1", name="Resource 1", created_at=now, updated_at=now)]
        resource_list = ResourceList(resources=resources, total=1, topologically_sorted=True)
        assert len(resource_list.resources) == 1
        assert resource_list.total == 1
        assert resource_list.topologically_sorted is True

    def test_empty_resource_list(self):
        """Test empty resource list"""
        resource_list = ResourceList(resources=[], total=0)
        assert len(resource_list.resources) == 0
        assert resource_list.total == 0
        assert resource_list.topologically_sorted is False


class TestErrorResponse:
    """Tests for ErrorResponse schema"""

    def test_valid_error_response(self):
        """Test creating a valid error response"""
        error = ErrorResponse(
            error="ValidationError",
            message="Invalid data",
            details={"field": "name", "issue": "too short"},
        )
        assert error.error == "ValidationError"
        assert error.message == "Invalid data"
        assert error.details == {"field": "name", "issue": "too short"}

    def test_error_without_details(self):
        """Test error response without details"""
        error = ErrorResponse(error="NotFoundError", message="Resource not found")
        assert error.error == "NotFoundError"
        assert error.message == "Resource not found"
        assert error.details is None

    def test_error_with_complex_details(self):
        """Test error with complex details structure"""
        error = ErrorResponse(
            error="CircularDependencyError",
            message="Cycle detected",
            details={"cycle": ["A", "B", "C", "A"], "affected_resources": ["id1", "id2", "id3"]},
        )
        assert "cycle" in error.details
        assert "affected_resources" in error.details
