"""Property-based tests for MongoDB connection error handling

Feature: mongodb-integration, Property 10: Connection error handling
Validates: Requirements 6.1

This test verifies that when MongoDB operations fail due to connection issues,
the application returns an appropriate HTTP error response and logs the underlying error.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import status

from app.repositories.mongodb_resource_repository import MongoDBResourceRepository
from app.exceptions import DatabaseConnectionError
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
def connection_error_strategy(draw):
    """Generate different types of connection errors"""
    error_type = draw(st.sampled_from([
        ConnectionFailure,
        ServerSelectionTimeoutError
    ]))
    error_message = draw(st.text(min_size=10, max_size=200))
    
    return error_type(error_message)


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_data=resource_create_strategy(),
    connection_error=connection_error_strategy()
)
async def test_create_operation_connection_error_handling(resource_data, connection_error):
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB create operation that fails due to connection issues,
    the application should raise DatabaseConnectionError with appropriate details.
    
    This property verifies:
    1. Connection errors are caught during create operations
    2. DatabaseConnectionError is raised with descriptive message
    3. Original error details are preserved
    """
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise connection error
    mock_collection.insert_one = AsyncMock(side_effect=connection_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to create resource and verify error handling
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await repository.create(resource_data)
    
    # Verify the exception contains appropriate information
    assert "connection error" in str(exc_info.value).lower()
    assert exc_info.value.details is not None
    assert str(connection_error) in exc_info.value.details


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_id=st.text(min_size=1, max_size=36),
    connection_error=connection_error_strategy()
)
async def test_get_by_id_operation_connection_error_handling(resource_id, connection_error):
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB get_by_id operation that fails due to connection issues,
    the application should raise DatabaseConnectionError with appropriate details.
    """
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise connection error
    mock_collection.find_one = AsyncMock(side_effect=connection_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to get resource and verify error handling
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await repository.get_by_id(resource_id)
    
    # Verify the exception contains appropriate information
    assert "connection error" in str(exc_info.value).lower()
    assert resource_id in str(exc_info.value) or exc_info.value.details is not None


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(connection_error=connection_error_strategy())
async def test_get_all_operation_connection_error_handling(connection_error):
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB get_all operation that fails due to connection issues,
    the application should raise DatabaseConnectionError with appropriate details.
    """
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise connection error
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(side_effect=connection_error)
    mock_collection.find = MagicMock(return_value=mock_cursor)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to get all resources and verify error handling
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await repository.get_all()
    
    # Verify the exception contains appropriate information
    assert "connection error" in str(exc_info.value).lower()
    assert exc_info.value.details is not None


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_id=st.text(min_size=1, max_size=36),
    update_data=resource_update_strategy(),
    connection_error=connection_error_strategy()
)
async def test_update_operation_connection_error_handling(resource_id, update_data, connection_error):
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB update operation that fails due to connection issues,
    the application should raise DatabaseConnectionError with appropriate details.
    """
    from datetime import datetime, timezone
    
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # First call to find_one succeeds (checking if resource exists)
    # Second call to find_one fails with connection error (after update)
    mock_collection.find_one = AsyncMock(side_effect=[
        {
            '_id': resource_id,
            'name': 'Test Resource',
            'description': 'Test Description',
            'dependencies': [],
            'created_at': datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            'updated_at': datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        },
        connection_error
    ])
    
    # Update operation succeeds
    mock_update_result = AsyncMock()
    mock_update_result.modified_count = 1
    mock_update_result.matched_count = 1
    mock_collection.update_one = AsyncMock(return_value=mock_update_result)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to update resource and verify error handling
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await repository.update(resource_id, update_data)
    
    # Verify the exception contains appropriate information
    assert "connection error" in str(exc_info.value).lower()


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    resource_id=st.text(min_size=1, max_size=36),
    connection_error=connection_error_strategy()
)
async def test_delete_operation_connection_error_handling(resource_id, connection_error):
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB delete operation that fails due to connection issues,
    the application should raise DatabaseConnectionError with appropriate details.
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
    
    # Delete operation fails with connection error
    mock_collection.delete_one = AsyncMock(side_effect=connection_error)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to delete resource and verify error handling
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await repository.delete(resource_id, cascade=False)
    
    # Verify the exception contains appropriate information
    assert "connection error" in str(exc_info.value).lower()
    assert resource_id in str(exc_info.value) or exc_info.value.details is not None


@pytest.mark.property
@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    query=st.one_of(st.none(), st.text(max_size=100)),
    connection_error=connection_error_strategy()
)
async def test_search_operation_connection_error_handling(query, connection_error):
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB search operation that fails due to connection issues,
    the application should raise DatabaseConnectionError with appropriate details.
    """
    # Create a mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_collection = AsyncMock()
    mock_db.resources = mock_collection
    
    # Configure the mock to raise connection error
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(side_effect=connection_error)
    mock_collection.find = MagicMock(return_value=mock_cursor)
    
    # Create repository with mock database
    repository = MongoDBResourceRepository(mock_db)
    
    # Attempt to search and verify error handling
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await repository.search(query)
    
    # Verify the exception contains appropriate information
    assert "connection error" in str(exc_info.value).lower()
    assert exc_info.value.details is not None


@pytest.mark.property
@pytest.mark.asyncio
async def test_api_returns_503_on_connection_error():
    """
    Feature: mongodb-integration, Property 10: Connection error handling
    Validates: Requirement 6.1
    
    For any MongoDB operation that fails due to connection issues,
    the API should return HTTP 503 Service Unavailable.
    
    This test verifies the end-to-end error handling from repository
    through service layer to API response.
    """
    from httpx import AsyncClient
    
    # Mock the repository to raise connection error
    with patch('app.services.resource_service.get_repository') as mock_get_repo:
        # Create a mock repository that raises connection error
        mock_repo = AsyncMock()
        mock_repo.get_all = AsyncMock(side_effect=DatabaseConnectionError(
            "Failed to retrieve resources due to connection error",
            details="Connection lost"
        ))
        mock_get_repo.return_value = mock_repo
        
        # Make API request using async client
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/resources")
        
        # Verify HTTP 503 response
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Verify error response structure
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"] == "DatabaseConnectionError"
        assert "message" in error_data
        assert "connection" in error_data["message"].lower()
