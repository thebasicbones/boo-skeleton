---
inclusion: manual
---

# API Design Guidelines

## RESTful Principles

This API follows REST conventions for resource management:

- **Resources** are nouns (not verbs)
- **HTTP methods** indicate actions (GET, POST, PUT, DELETE)
- **Status codes** communicate results
- **URLs** are hierarchical and predictable

## URL Structure

### Resource Endpoints

```
GET    /api/resources           # List all resources
POST   /api/resources           # Create new resource
GET    /api/resources/{id}      # Get specific resource
PUT    /api/resources/{id}      # Update resource
DELETE /api/resources/{id}      # Delete resource
```

### Search and Filter

```
GET    /api/search?q=query      # Search resources
GET    /api/resources?tag=api   # Filter by tag (future)
```

### Naming Conventions

- Use **plural nouns** for collections: `/resources` not `/resource`
- Use **kebab-case** for multi-word resources: `/api/user-profiles`
- Keep URLs **lowercase**
- Avoid verbs in URLs: `/api/resources` not `/api/get-resources`

## HTTP Methods

### GET - Retrieve Resources

```python
@router.get("/resources")
async def list_resources() -> list[ResourceResponse]:
    """List all resources."""
    pass

@router.get("/resources/{id}")
async def get_resource(id: str) -> ResourceResponse:
    """Get a specific resource."""
    pass
```

**Characteristics:**
- Idempotent (multiple calls produce same result)
- Safe (no side effects)
- Cacheable
- Returns 200 OK or 404 Not Found

### POST - Create Resources

```python
@router.post("/resources", status_code=201)
async def create_resource(data: ResourceCreate) -> ResourceResponse:
    """Create a new resource."""
    pass
```

**Characteristics:**
- Not idempotent (creates new resource each time)
- Returns 201 Created with Location header
- Returns created resource in response body

### PUT - Update Resources

```python
@router.put("/resources/{id}")
async def update_resource(
    id: str,
    data: ResourceUpdate
) -> ResourceResponse:
    """Update an existing resource."""
    pass
```

**Characteristics:**
- Idempotent (multiple identical calls produce same result)
- Full resource update
- Returns 200 OK or 404 Not Found

### DELETE - Remove Resources

```python
@router.delete("/resources/{id}", status_code=204)
async def delete_resource(id: str) -> None:
    """Delete a resource."""
    pass
```

**Characteristics:**
- Idempotent
- Returns 204 No Content
- No response body

## HTTP Status Codes

### Success Codes (2xx)

- **200 OK** - Successful GET, PUT
- **201 Created** - Successful POST
- **204 No Content** - Successful DELETE

### Client Error Codes (4xx)

- **400 Bad Request** - Malformed request
- **404 Not Found** - Resource doesn't exist
- **422 Unprocessable Entity** - Validation error

### Server Error Codes (5xx)

- **500 Internal Server Error** - Unexpected server error

## Request/Response Format

### Request Body (POST/PUT)

```json
{
  "name": "Frontend Service",
  "description": "React-based frontend",
  "dependencies": ["backend-id", "auth-id"]
}
```

### Response Body

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Frontend Service",
  "description": "React-based frontend",
  "dependencies": ["backend-id", "auth-id"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
  "error": "NotFoundError",
  "message": "Resource not found",
  "details": {
    "resource_id": "invalid-id"
  }
}
```

## Validation

### Input Validation

Use Pydantic schemas for automatic validation:

```python
class ResourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    dependencies: list[str] = Field(default_factory=list)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
```

### Validation Errors

Return 422 with detailed error information:

```json
{
  "error": "ValidationError",
  "message": "Invalid resource data",
  "details": {
    "name": ["Name cannot be empty or whitespace only"],
    "dependencies": ["Dependencies must be unique"]
  }
}
```

## Query Parameters

### Pagination (Future Enhancement)

```python
@router.get("/resources")
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> list[ResourceResponse]:
    pass
```

### Filtering

```python
@router.get("/resources")
async def list_resources(
    tag: str | None = Query(None),
    name: str | None = Query(None)
) -> list[ResourceResponse]:
    pass
```

### Sorting

```python
@router.get("/resources")
async def list_resources(
    sort_by: str = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc")
) -> list[ResourceResponse]:
    pass
```

## API Versioning

### URL Versioning (Current)

```
/api/v1/resources
/api/v2/resources
```

### Header Versioning (Alternative)

```
GET /api/resources
Accept: application/vnd.api+json; version=1
```

## Documentation

### OpenAPI/Swagger

FastAPI automatically generates OpenAPI documentation:

```python
app = FastAPI(
    title="FastAPI CRUD Backend",
    description="RESTful API with topological sorting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

### Endpoint Documentation

```python
@router.post("/resources", status_code=201)
async def create_resource(
    data: ResourceCreate,
    service: ResourceService = Depends(get_resource_service)
) -> ResourceResponse:
    """
    Create a new resource with dependencies.
    
    - **name**: Resource name (required, 1-100 characters)
    - **description**: Optional description (max 500 characters)
    - **dependencies**: List of resource IDs this resource depends on
    
    Returns the created resource with generated ID and timestamps.
    
    Raises:
    - **422**: Validation error or circular dependency detected
    - **500**: Database error
    """
    return await service.create_resource(data)
```

## Best Practices

### 1. Use Appropriate Status Codes

```python
# Good
@router.post("/resources", status_code=201)
async def create_resource(data: ResourceCreate):
    pass

# Bad
@router.post("/resources")  # Defaults to 200, should be 201
async def create_resource(data: ResourceCreate):
    pass
```

### 2. Return Created Resources

```python
# Good - return the created resource
@router.post("/resources", status_code=201)
async def create_resource(data: ResourceCreate) -> ResourceResponse:
    resource = await service.create_resource(data)
    return resource

# Bad - return nothing
@router.post("/resources", status_code=201)
async def create_resource(data: ResourceCreate) -> None:
    await service.create_resource(data)
```

### 3. Use Dependency Injection

```python
# Good
@router.get("/resources")
async def list_resources(
    service: ResourceService = Depends(get_resource_service)
) -> list[ResourceResponse]:
    return await service.get_all_resources()

# Bad - create service inside endpoint
@router.get("/resources")
async def list_resources() -> list[ResourceResponse]:
    service = ResourceService()  # Don't do this
    return await service.get_all_resources()
```

### 4. Validate Input

```python
# Good - use Pydantic for validation
@router.post("/resources")
async def create_resource(data: ResourceCreate):
    pass

# Bad - manual validation
@router.post("/resources")
async def create_resource(data: dict):
    if "name" not in data:
        raise HTTPException(400, "Name required")
    # ... more manual validation
```

### 5. Handle Errors Consistently

```python
# Good - use exception handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "NotFoundError", "message": str(exc)}
    )

# Bad - handle in each endpoint
@router.get("/resources/{id}")
async def get_resource(id: str):
    try:
        return await service.get_resource(id)
    except NotFoundError:
        return JSONResponse(status_code=404, content={"error": "Not found"})
```
