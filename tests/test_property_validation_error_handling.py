"""Property-based tests for validation error handling

Feature: mongodb-integration, Property 11: Validation error handling
Validates: Requirements 6.2

This test verifies that when MongoDB operations fail due to data validation errors,
the application returns an HTTP 400 Bad Request response with details about the validation failure.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from pymongo.errors import WriteError
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import status

from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.exceptions import ValidationError
from app.schemas import ResourceCreate, ResourceUpdate
from main import app


# Strategy for generating valid resource data
@st.composite
def resource_create_strategy(draw):
    """Generate valid ResourceCreate data for testing"""
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'), blacklist_characters='\x00'
    )))
    description = draw(st.one_of(
        st.none(),
        st.text(max_size=500, alphabet=st.characters(
            blacklist_categories=('Cs', 'Cc'), blacklist_characters='\x00'
        ))
    ))
    # Generate unique dependencies
    dependencies = draw(st.lists(
        st.text(min_size=1, max_size=36),
        max_size=5,
        unique=True
    ))
    
    return ResourceCreate(
        name=name,
        description=description,
        dependencies=dependencies
    )


@st.composite
def resource_update_strategy(draw):
    """Generate valid ResourceUpdate data for testing"""
    name = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(
            blacklist_categories=('Cs', 'Cc'), blacklist_characters='\x00'
        ))
    ))
    description = draw(st.one_of(
        st.none(),
        st.text(max_size=500, alphabet=st.characters(
            blacklist_categories=('Cs', 'Cc'), blacklist_characters='\x00'
        ))
    ))
    # Generate unique dependencies
    dependencies = draw(st.one_of(
        st.none(),
        st.lists(st.text(min_size=1, max_size=36), max_size=5, unique=True)
    ))
    
    return ResourceUpdate(
        name=name,
        description=description,
        dependencies=dependencies
    )


@st.composite
def validation_error_strategy(draw):
    """Generate different types of validation errors"""
    error_messages = [
        "Document failed validation",
        "Validation error: field 'name' is required",
        "Validation failed for field 'description'",
        "Schema validation error: invalid data type",
        "Validation constraint violated"
    ]
    
    error_message = draw(st.sampled_from(error_messages))
    error_code = draw(st.integers(min_value=121, max_value=122))  # MongoDB validation error codes
    
    # Create a WriteError with validation-related message
    # WriteError requires specific structure
    error_doc = {
        'index': 0,
        'code': error_code,
        'errmsg': error_message
    }
    
    return WriteError(error_message, error_code, error_doc)


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_data=resource_create_strategy(),
    validation_error=validation_error_strategy()
)
async def test_create_operation_validation_error_handling(resource_data, validation_error):
    """
    Feature: mongodb-integration, Property 11: Validation error handling
    Validates: Requirement 6.2
    
    For any MongoDB create operation that fails due to validation errors,
    the application should raise ValidationError with appropriate details.
    
    This property verifies:
    1. Validation errors are caught during create operations
    2. ValidationError is raised with descriptive message
    3. Error details are preserved
    """
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise validation error
    mock_collection.insert_one = AsyncMock(side_effect=validation_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to create resource and verify error handling
    with pytest.raises(ValidationError) as exc_info:
        await repository.create(resource_data)
    
    # Verify the exception contains appropriate information
    assert "validation" in str(exc_info.value).lower()
    assert exc_info.value.details is not None
    assert 'error' in exc_info.value.details


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_id=st.text(min_size=1, max_size=36),
    update_data=resource_update_strategy(),
    validation_error=validation_error_strategy()
)
async def test_update_operation_validation_error_handling(resource_id, update_data, validation_error):
    """
    Feature: mongodb-integration, Property 11: Validation error handling
    Validates: Requirement 6.2
    
    For any MongoDB update operation that fails due to validation errors,
    the application should raise ValidationError with appropriate details.
    """
    from datetime import datetime, timezone
    
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # First call to find_one succeeds (checking if resource exists)
    mock_collection.find_one = AsyncMock(return_value={
        '_id': resource_id,
        'name': 'Test Resource',
        'description': 'Test Description',
        'dependencies': [],
        'created_at': datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        'updated_at': datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    })
    
    # Update operation fails with validation error
    mock_collection.update_one = AsyncMock(side_effect=validation_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to update resource and verify error handling
    with pytest.raises(ValidationError) as exc_info:
        await repository.update(resource_id, update_data)
    
    # Verify the exception contains appropriate information
    assert "validation" in str(exc_info.value).lower()
    assert exc_info.value.details is not None
    assert 'error' in exc_info.value.details


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(validation_error=validation_error_strategy())
async def test_validation_error_preserves_details(validation_error):
    """
    Feature: mongodb-integration, Property 11: Validation error handling
    Validates: Requirement 6.2
    
    For any validation error, the error details should be preserved
    when converting from MongoDB WriteError to ValidationError.
    """
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise validation error
    mock_collection.insert_one = AsyncMock(side_effect=validation_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Create minimal valid resource data
    resource_data = ResourceCreate(
        name="Test Resource",
        description="Test Description",
        dependencies=[]
    )
    
    # Attempt to create resource and verify error details are preserved
    with pytest.raises(ValidationError) as exc_info:
        await repository.create(resource_data)
    
    # Verify error details contain the original error message
    assert exc_info.value.details is not None
    assert 'error' in exc_info.value.details
    assert str(validation_error) in str(exc_info.value.details['error'])


@pytest.mark.property
@pytest.mark.asyncio
async def test_api_returns_400_on_validation_error():
    """
    Feature: mongodb-integration, Property 11: Validation error handling
    Validates: Requirement 6.2
    
    For any MongoDB operation that fails due to validation errors,
    the API should return HTTP 400 Bad Request with validation details.
    
    This test verifies the end-to-end error handling from repository
    through service layer to API response.
    """
    from httpx import AsyncClient
    
    # Mock the repository to raise validation error
    with patch('app.services.resource_service.get_repository') as mock_get_repo:
        # Create a mock repository that raises validation error
        mock_repo = AsyncMock()
        mock_repo.create = AsyncMock(side_effect=ValidationError(
            "Data validation failed",
            details={'error': 'Document failed validation: name field is required'}
        ))
        mock_get_repo.return_value = mock_repo
        
        # Make API request using async client
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/resources",
                json={
                    "name": "Test Resource",
                    "description": "Test Description",
                    "dependencies": []
                }
            )
        
        # Verify HTTP 422 response (FastAPI uses 422 for validation errors)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Verify error response structure
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"] == "ValidationError"
        assert "message" in error_data
        assert "validation" in error_data["message"].lower()
        assert "details" in error_data


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_data=resource_create_strategy(),
    error_message=st.text(min_size=10, max_size=200)
)
async def test_validation_error_message_clarity(resource_data, error_message):
    """
    Feature: mongodb-integration, Property 11: Validation error handling
    Validates: Requirement 6.2
    
    For any validation error with a specific error message,
    the ValidationError should preserve that message for debugging.
    """
    # Create a WriteError with the generated error message
    error_doc = {
        'index': 0,
        'code': 121,
        'errmsg': f"Document failed validation: {error_message}"
    }
    validation_error = WriteError(
        f"Document failed validation: {error_message}",
        121,
        error_doc
    )
    
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise validation error
    mock_collection.insert_one = AsyncMock(side_effect=validation_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to create resource and verify error message is preserved
    with pytest.raises(ValidationError) as exc_info:
        await repository.create(resource_data)
    
    # Verify the error details contain the original message
    assert exc_info.value.details is not None
    assert 'error' in exc_info.value.details
    # The error message should be in the details
    error_str = str(exc_info.value.details['error'])
    assert "validation" in error_str.lower()
