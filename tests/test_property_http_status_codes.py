"""Property-based tests for HTTP status codes

Feature: fastapi-crud-backend, Property 3: Successful creation returns 201
Feature: fastapi-crud-backend, Property 6: Successful update returns 200
Feature: fastapi-crud-backend, Property 8: Successful delete returns 204
Feature: fastapi-crud-backend, Property 10: Successful search returns 200
Validates: Requirements 1.4, 3.4, 4.3, 5.5
"""
import pytest
from hypothesis import given, strategies as st, settings
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from app.database import init_db, drop_db, get_db, AsyncSessionLocal


# Strategy for generating valid resource names (1-100 characters, not just whitespace)
@st.composite
def valid_name_strategy(draw):
    """Generate valid resource names"""
    name = draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
        min_size=1,
        max_size=100
    ))
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


# Strategy for generating valid resource descriptions (0-500 characters or None)
description_strategy = st.one_of(
    st.none(),
    st.text(max_size=500)
)


# Strategy for generating valid resource data
@st.composite
def resource_data_strategy(draw):
    """Generate valid resource data for API requests"""
    name = draw(valid_name_strategy())
    description = draw(description_strategy)
    
    return {
        "name": name,
        "description": description,
        "dependencies": []
    }


# Strategy for generating valid update data
@st.composite
def update_data_strategy(draw):
    """Generate valid update data for API requests"""
    # At least one field should be present
    include_name = draw(st.booleans())
    include_description = draw(st.booleans())
    
    # Ensure at least one field is included
    if not include_name and not include_description:
        include_name = True
    
    data = {}
    if include_name:
        data["name"] = draw(valid_name_strategy())
    if include_description:
        # Only include description if we're actually setting it to a value
        # (not None, which would be omitted from the update)
        desc = draw(st.text(max_size=500))
        data["description"] = desc
    
    return data


@pytest.fixture
async def test_db():
    """Create a test database session"""
    await drop_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        yield session
    
    await drop_db()


@pytest.fixture
async def client(test_db):
    """Create a test client with database dependency override"""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(resource_data=resource_data_strategy())
async def test_successful_creation_returns_201(resource_data):
    """
    Feature: fastapi-crud-backend, Property 3: Successful creation returns 201
    Validates: Requirements 1.4
    
    For any valid resource creation request, the API should return 
    HTTP 201 status code with the created resource.
    """
    # Setup database
    await drop_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create resource
            response = await client.post("/api/resources", json=resource_data)
            
            # Verify status code is 201
            assert response.status_code == 201, \
                f"Expected status code 201 for successful creation, got {response.status_code}"
            
            # Verify response contains the created resource
            data = response.json()
            assert "id" in data
            assert data["name"] == resource_data["name"].strip()
        
        app.dependency_overrides.clear()
    
    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(
    create_data=resource_data_strategy(),
    update_data=update_data_strategy()
)
async def test_successful_update_returns_200(create_data, update_data):
    """
    Feature: fastapi-crud-backend, Property 6: Successful update returns 200
    Validates: Requirements 3.4
    
    For any valid resource update request, the API should return 
    HTTP 200 status code with the updated resource.
    """
    # Setup database
    await drop_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a resource first
            create_response = await client.post("/api/resources", json=create_data)
            assert create_response.status_code == 201
            resource_id = create_response.json()["id"]
            
            # Update the resource
            response = await client.put(f"/api/resources/{resource_id}", json=update_data)
            
            # Verify status code is 200
            assert response.status_code == 200, \
                f"Expected status code 200 for successful update, got {response.status_code}"
            
            # Verify response contains the updated resource
            data = response.json()
            assert data["id"] == resource_id
            
            # Verify updated fields
            if "name" in update_data:
                assert data["name"] == update_data["name"].strip()
            if "description" in update_data:
                # The API strips whitespace and converts empty strings to None
                # If the stripped description is empty, the field is not updated (keeps original)
                stripped_desc = update_data["description"].strip() if update_data["description"] else ""
                if stripped_desc:
                    # Non-empty description should be updated
                    assert data["description"] == stripped_desc
                # If empty, the original description is preserved (we don't check it here)
        
        app.dependency_overrides.clear()
    
    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(resource_data=resource_data_strategy())
async def test_successful_delete_returns_204(resource_data):
    """
    Feature: fastapi-crud-backend, Property 8: Successful delete returns 204
    Validates: Requirements 4.3
    
    For any successful delete operation, the API should return 
    HTTP 204 status code.
    """
    # Setup database
    await drop_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a resource first
            create_response = await client.post("/api/resources", json=resource_data)
            assert create_response.status_code == 201
            resource_id = create_response.json()["id"]
            
            # Delete the resource
            response = await client.delete(f"/api/resources/{resource_id}")
            
            # Verify status code is 204
            assert response.status_code == 204, \
                f"Expected status code 204 for successful delete, got {response.status_code}"
            
            # Verify no content is returned
            assert response.content == b''
        
        app.dependency_overrides.clear()
    
    await drop_db()


@pytest.mark.property
@pytest.mark.asyncio
@settings(max_examples=100)
@given(search_query=st.one_of(
    st.none(), 
    st.text(
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
        max_size=50
    )
))
async def test_successful_search_returns_200(search_query):
    """
    Feature: fastapi-crud-backend, Property 10: Successful search returns 200
    Validates: Requirements 5.5
    
    For any valid search request, the API should return 
    HTTP 200 status code with topologically sorted results.
    """
    # Setup database
    await drop_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a few resources for searching
            await client.post("/api/resources", json={"name": "Resource A", "dependencies": []})
            await client.post("/api/resources", json={"name": "Resource B", "dependencies": []})
            
            # Perform search
            if search_query is None:
                response = await client.get("/api/search")
            else:
                response = await client.get("/api/search", params={"q": search_query})
            
            # Verify status code is 200
            assert response.status_code == 200, \
                f"Expected status code 200 for successful search, got {response.status_code}"
            
            # Verify response is a list
            data = response.json()
            assert isinstance(data, list)
        
        app.dependency_overrides.clear()
    
    await drop_db()
