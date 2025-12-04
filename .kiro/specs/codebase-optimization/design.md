# Design Document: Codebase Optimization

## Overview

This design document outlines the architectural simplifications for the FastAPI CRUD backend. The optimization focuses on reducing code complexity while maintaining 100% functional compatibility with the existing system. The refactoring will consolidate the service layer, simplify the exception hierarchy, reduce schema duplication, and streamline validation logic.

The key principle is **consolidation without feature loss** - every optimization must preserve existing behavior, pass all tests, and maintain support for both SQLAlchemy and MongoDB backends.

## Architecture

### Current Architecture
```
┌─────────────────┐
│   API Routes    │
├─────────────────┤
│ ResourceService │
│ TopoSortService │ ← Two separate services
├─────────────────┤
│  Repository     │ ← Abstraction layer
│   (Abstract)    │    with conversions
├─────────────────┤
│ SQLAlchemy/Mongo│
└─────────────────┘
```

### Optimized Architecture
```
┌─────────────────┐
│   API Routes    │
├─────────────────┤
│ ResourceService │ ← Single service with
│ (with DB ops)   │    direct DB access
├─────────────────┤
│ SQLAlchemy/Mongo│ ← Direct database access
└─────────────────┘
```

## Components and Interfaces

### 1. Simplified Database Access (Repository Pattern Removed)

**Current State**: Three-layer abstraction
- Repository abstract base class (`BaseResourceRepository`)
- Two repository implementations (`SQLAlchemyResourceRepository`, `MongoDBResourceRepository`)
- Service layer that calls repository methods
- MongoDB repository has `_document_to_dict` and `_dict_to_document` conversion overhead

**Optimized State**: Direct database access in service layer

**Changes**:
1. Remove `BaseResourceRepository` abstract class
2. Remove `SQLAlchemyResourceRepository` class
3. Remove `MongoDBResourceRepository` class
4. Move database operations directly into `ResourceService`
5. Use backend-specific logic only where necessary (e.g., SQLAlchemy uses ORM objects, MongoDB uses dicts)
6. Eliminate conversion methods (`_document_to_dict`, `_dict_to_document`)

**Implementation Approach**:
```python
class ResourceService:
    def __init__(self, db: AsyncSession | AsyncIOMotorDatabase):
        self.db = db
        self.is_mongodb = isinstance(db, AsyncIOMotorDatabase)
        if self.is_mongodb:
            self.collection = db.resources
    
    async def get_all(self) -> list:
        if self.is_mongodb:
            # Direct MongoDB operations
            cursor = self.collection.find({})
            documents = await cursor.to_list(length=None)
            return documents  # Return dicts directly
        else:
            # Direct SQLAlchemy operations
            result = await self.db.execute(
                select(Resource).options(selectinload(Resource.dependencies))
            )
            return list(result.scalars().all())  # Return ORM objects directly
```

**Benefits**:
- Eliminates 3 classes (~600 lines of code)
- Removes conversion overhead in MongoDB operations
- Clearer code flow - no jumping between layers
- Easier to understand - database operations are visible in service
- Still maintains support for both backends
- Service layer already has helper methods to handle dict vs object differences

**Rationale**: With only 2 backends and the service layer already handling both dict and object formats via helper methods (`_get_resource_id`, `_get_resource_name`, etc.), the repository abstraction adds complexity without significant benefit. Direct database access in the service layer is simpler and more maintainable.

### 2. Unified Service Layer

**Current State**: Two separate service classes
- `ResourceService` - Business logic for CRUD operations
- `TopologicalSortService` - Topological sorting and cycle detection

**Optimized State**: Single `ResourceService` class with integrated topological sorting

**Changes**:
1. Move all methods from `TopologicalSortService` into `ResourceService` as private methods:
   - `_topological_sort(resources)` - Sort resources using Kahn's algorithm
   - `_validate_no_cycles(resources, new_id, new_deps)` - Validate no circular dependencies
   - `_find_cycle(graph, in_degree)` - Find cycle path for error reporting
   - `_has_cycle(resources)` - Check if cycle exists

2. Remove `TopologicalSortService` class entirely

3. Update `ResourceService.__init__()` to remove `self.topo_service` initialization

4. Update all internal calls from `self.topo_service.method()` to `self._method()`

**Benefits**:
- One less class to maintain
- Clearer code flow (no jumping between services)
- Topological sorting is clearly a utility for resource operations, not a standalone service

### 3. Simplified Exception Hierarchy

**Current State**: 7 exception classes
```python
ResourceNotFoundError
ValidationError
CircularDependencyError
DatabaseError (base)
├── DatabaseConnectionError
├── DatabaseTimeoutError
└── DuplicateResourceError
```

**Optimized State**: 4 exception classes
```python
NotFoundError (renamed from ResourceNotFoundError)
ValidationError
CircularDependencyError
DatabaseError (consolidated)
```

**Changes**:

1. **Rename** `ResourceNotFoundError` → `NotFoundError`
   - More generic, can be used for any "not found" scenario
   - Keep same constructor signature: `NotFoundError(resource_id: str)`

2. **Consolidate** database exceptions into single `DatabaseError` class:
   ```python
   class DatabaseError(Exception):
       """Database operation error with optional context"""
       
       def __init__(
           self, 
           message: str, 
           error_type: str = "general",
           details: str | None = None
       ):
           self.message = message
           self.error_type = error_type  # "connection", "timeout", "duplicate", "general"
           self.details = details
           super().__init__(message)
   ```

3. **Remove** these classes:
   - `DatabaseConnectionError` → Use `DatabaseError(msg, error_type="connection")`
   - `DatabaseTimeoutError` → Use `DatabaseError(msg, error_type="timeout")`
   - `DuplicateResourceError` → Use `DatabaseError(msg, error_type="duplicate")`

4. **Update error handlers** to map based on `error_type`:
   - `error_type="connection"` → HTTP 503
   - `error_type="timeout"` → HTTP 503
   - `error_type="duplicate"` → HTTP 409
   - `error_type="general"` → HTTP 500

**Benefits**:
- Fewer exception classes to maintain
- Consistent error handling pattern
- Same HTTP status code mappings
- Easier to add new error types without new classes

### 4. Consolidated Schema Validation

**Current State**: Duplicate validators in `ResourceCreate` and `ResourceUpdate`

**Optimized State**: Shared base class with inherited validators

**Changes**:

1. Create `ResourceBase` schema with shared validators:
   ```python
   class ResourceBase(BaseModel):
       """Base schema with shared validation logic"""
       
       @field_validator("name")
       @classmethod
       def validate_name(cls, v: str | None) -> str | None:
           """Validate name is not empty or whitespace"""
           if v is not None:
               if not v.strip():
                   raise ValueError("Name cannot be empty or whitespace only")
               return v.strip()
           return v
       
       @field_validator("description")
       @classmethod
       def validate_description(cls, v: str | None) -> str | None:
           """Strip whitespace from description"""
           if v is not None:
               stripped = v.strip()
               return stripped if stripped else None
           return v
       
       @field_validator("dependencies")
       @classmethod
       def validate_dependencies(cls, v: list[str] | None) -> list[str] | None:
           """Validate dependencies are unique"""
           if v is not None and len(v) != len(set(v)):
               raise ValueError("Dependencies must be unique")
           return v
   ```

2. Update `ResourceCreate` to inherit from `ResourceBase`:
   ```python
   class ResourceCreate(ResourceBase):
       """Schema for creating a new resource"""
       name: str = Field(...)
       description: str | None = Field(None, max_length=500)
       dependencies: list[str] = Field(default_factory=list)
       # Validators inherited from ResourceBase
   ```

3. Update `ResourceUpdate` to inherit from `ResourceBase`:
   ```python
   class ResourceUpdate(ResourceBase):
       """Schema for updating an existing resource"""
       name: str | None = Field(None, min_length=1, max_length=100)
       description: str | None = Field(None, max_length=500)
       dependencies: list[str] | None = Field(None)
       # Validators inherited from ResourceBase
   ```

**Benefits**:
- Single source of truth for validation logic
- Changes to validation rules only need to be made once
- Clearer inheritance hierarchy

### 5. Consolidated Dependency Validation

**Current State**: Duplicate validation logic in `create_resource()` and `update_resource()`

Both methods contain nearly identical code for:
1. Validating dependencies exist
2. Building resource graph
3. Checking for circular dependencies

**Optimized State**: Single private method for all dependency validation

**Changes**:

1. Create new private method `_validate_and_check_cycles()`:
   ```python
   async def _validate_and_check_cycles(
       self,
       resource_id: str,
       dependencies: list[str]
   ) -> None:
       """
       Validate dependencies exist and check for circular dependencies.
       
       Args:
           resource_id: ID of resource being created/updated
           dependencies: List of dependency IDs
           
       Raises:
           ValidationError: If dependencies don't exist or would create cycle
       """
       # Validate all dependency IDs exist
       if dependencies:
           await self._validate_dependencies_exist(dependencies)
       
       # Get all existing resources
       existing_resources = await self.repository.get_all()
       
       # Convert to dict format for validation
       resource_dicts = [
           {
               "id": self._get_resource_id(r),
               "dependencies": self._get_resource_dependencies(r)
           }
           for r in existing_resources
       ]
       
       # Validate no cycles would be created
       try:
           self._validate_no_cycles(resource_dicts, resource_id, dependencies)
       except CircularDependencyError as e:
           raise ValidationError(
               "Cannot create/update resource: would create circular dependency",
               {"cycle": str(e)}
           )
   ```

2. Update `create_resource()` to use new method:
   ```python
   async def create_resource(self, data: ResourceCreate) -> ResourceResponse:
       # Validate dependencies and check cycles
       temp_id = "temp_new_resource_id"
       await self._validate_and_check_cycles(temp_id, data.dependencies)
       
       # Create the resource
       resource = await self.repository.create(data)
       return self._resource_to_response(resource)
   ```

3. Update `update_resource()` to use new method:
   ```python
   async def update_resource(
       self, 
       resource_id: str, 
       data: ResourceUpdate
   ) -> ResourceResponse:
       # Check if resource exists
       existing = await self.repository.get_by_id(resource_id)
       if not existing:
           raise NotFoundError(resource_id)
       
       # Validate dependencies if being updated
       if data.dependencies is not None:
           await self._validate_and_check_cycles(resource_id, data.dependencies)
       
       # Update the resource
       updated = await self.repository.update(resource_id, data)
       return self._resource_to_response(updated)
   ```

**Benefits**:
- Single location for dependency validation logic
- Easier to maintain and test
- Consistent behavior between create and update
- Reduced code duplication (~30 lines eliminated)

## Data Models

No changes to data models. The existing SQLAlchemy `Resource` model and MongoDB document structure remain unchanged.

## Corr
ectness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

Before defining the correctness properties, I analyzed the testable acceptance criteria for redundancy:

**Identified Redundancies:**
- Property 7.3 (API responses identical) and Property 7.4 (error responses identical) can be combined into a single comprehensive property about response preservation
- Property 6.1 (direct database operations) is validated by Property 7.3 (response preservation) - if responses are identical, database operations work correctly
- Properties 7.1 and 7.2 (existing tests pass) are meta-properties that will be verified by running the test suite, not new properties to implement

**Consolidated Properties:**
After removing redundancies, we have 3 core properties that provide unique validation value:

1. Backend consistency (validates identical behavior across SQLAlchemy and MongoDB)
2. Topological sort preservation (validates algorithm correctness is maintained)
3. Error handling preservation (validates HTTP responses for error conditions)

### Property 1: Backend Consistency

*For any* valid CRUD operation (create, read, update, delete, search) with any valid input data, executing the operation against SQLAlchemy backend and MongoDB backend should produce equivalent results (same data, same status codes, same error conditions).

**Validates: Requirements 6.1, 6.4, 7.3, 7.5**

**Rationale**: This property ensures that removing the repository pattern and moving database operations directly into the service layer doesn't introduce backend-specific bugs. By testing operations against both backends with the same inputs, we verify that both database implementations maintain consistent behavior despite having different internal implementations (ORM objects vs dicts).

**Testing Approach**: 
- Generate random resources with various dependency structures
- Execute create, read, update, delete, and search operations against both backends
- Compare responses for equivalence (accounting for backend-specific ID formats)
- Verify error conditions produce same exceptions

### Property 2: Topological Sort Preservation

*For any* set of resources with dependencies, the topological sort algorithm should produce a valid ordering where all dependencies appear before their dependents, and circular dependencies should be detected and reported.

**Validates: Requirements 2.4**

**Rationale**: Moving topological sort methods from `TopologicalSortService` into `ResourceService` must not break the algorithm. This property verifies that Kahn's algorithm still works correctly and cycle detection remains functional.

**Testing Approach**:
- Generate random directed acyclic graphs (DAGs) of resources
- Verify sorted output has all dependencies before dependents
- Generate graphs with cycles and verify `CircularDependencyError` is raised
- Test edge cases: empty graphs, single nodes, disconnected components

### Property 3: Error Response Consistency

*For any* error condition (not found, validation error, circular dependency, database error), the HTTP response (status code, error format, error message structure) should be identical before and after the optimization.

**Validates: Requirements 3.3, 3.4, 7.4**

**Rationale**: Consolidating exceptions from 7 to 4 classes must not change the API contract. Clients should receive the same error responses. This property ensures backward compatibility of error handling.

**Testing Approach**:
- Test NotFoundError → 404 with correct error format
- Test ValidationError → 422 with correct error format
- Test CircularDependencyError → 422 with cycle path in details
- Test DatabaseError with error_type="connection" → 503
- Test DatabaseError with error_type="timeout" → 503
- Test DatabaseError with error_type="duplicate" → 409
- Test DatabaseError with error_type="general" → 500

## Error Handling

### Exception Mapping

The optimized exception hierarchy maps to HTTP status codes as follows:

| Exception | HTTP Status | Use Case |
|-----------|-------------|----------|
| `NotFoundError` | 404 | Resource not found by ID |
| `ValidationError` | 422 | Invalid input data, circular dependencies |
| `CircularDependencyError` | 422 | Circular dependency detected |
| `DatabaseError` (connection) | 503 | Database connection failed |
| `DatabaseError` (timeout) | 503 | Database operation timed out |
| `DatabaseError` (duplicate) | 409 | Duplicate resource ID |
| `DatabaseError` (general) | 500 | Other database errors |

### Error Response Format

All errors return consistent JSON format:
```json
{
  "error": "ErrorType",
  "message": "Human-readable description",
  "details": {
    "additional": "context"
  }
}
```

### Backward Compatibility

The consolidation maintains backward compatibility by:
1. Preserving all HTTP status code mappings
2. Maintaining the same error response structure
3. Including the same details in error responses
4. Using the same error type names in responses

## Testing Strategy

### Unit Testing

Unit tests will verify:
1. **Service layer refactoring**:
   - Topological sort methods work correctly when moved to `ResourceService`
   - Dependency validation consolidation produces same results
   - Private method calls work correctly

2. **Exception consolidation**:
   - `DatabaseError` with different `error_type` values
   - Error handlers map to correct HTTP status codes
   - Error response format matches expected structure

3. **Schema validation**:
   - Inherited validators work correctly
   - `ResourceBase` validators apply to both `ResourceCreate` and `ResourceUpdate`
   - Validation error messages are preserved

### Property-Based Testing

Property-based tests will verify the three correctness properties defined above:

1. **Property 1: Backend Consistency**
   - Generate random resources and operations
   - Execute against both SQLAlchemy and MongoDB
   - Verify equivalent results
   - **Tag**: `Feature: codebase-optimization, Property 1: Backend Consistency`
   - **Minimum iterations**: 100

2. **Property 2: Topological Sort Preservation**
   - Generate random DAGs and graphs with cycles
   - Verify sort correctness and cycle detection
   - **Tag**: `Feature: codebase-optimization, Property 2: Topological Sort Preservation`
   - **Minimum iterations**: 100

3. **Property 3: Error Response Consistency**
   - Generate various error conditions
   - Verify HTTP status codes and response format
   - **Tag**: `Feature: codebase-optimization, Property 3: Error Response Consistency`
   - **Minimum iterations**: 100

### Integration Testing

Integration tests will verify:
1. All existing API endpoints work correctly
2. Both database backends function properly
3. Error handling works end-to-end
4. No regressions in existing functionality

### Test Execution Strategy

1. **Before refactoring**: Run full test suite to establish baseline (all tests should pass)
2. **During refactoring**: Run tests after each major change
3. **After refactoring**: Run full test suite to verify no regressions
4. **Property tests**: Run with minimum 100 iterations to catch edge cases

### Success Criteria

The optimization is successful when:
- All existing unit tests pass without modification
- All existing property-based tests pass without modification
- All three new correctness properties pass
- Code coverage remains at or above current levels
- No functional regressions detected

## Implementation Notes

### Migration Path

The refactoring should be done in this order to minimize risk:

1. **Phase 1: Schema consolidation** (lowest risk)
   - Create `ResourceBase` with shared validators
   - Update `ResourceCreate` and `ResourceUpdate` to inherit
   - Run tests to verify validation behavior unchanged

2. **Phase 2: Dependency validation consolidation** (low risk)
   - Create `_validate_and_check_cycles()` method
   - Update `create_resource()` and `update_resource()` to use it
   - Run tests to verify validation behavior unchanged

3. **Phase 3: Exception consolidation** (medium risk)
   - Update `DatabaseError` class with `error_type` parameter
   - Update all code raising database exceptions to use new format
   - Update error handlers to check `error_type`
   - Rename `ResourceNotFoundError` to `NotFoundError`
   - Run tests to verify error handling unchanged

4. **Phase 4: Remove repository pattern** (highest risk)
   - Move database operations from repositories directly into `ResourceService`
   - Add `is_mongodb` flag to determine backend type
   - Implement backend-specific logic inline where needed
   - Remove `BaseResourceRepository`, `SQLAlchemyResourceRepository`, `MongoDBResourceRepository`
   - Update `database_factory.py` to remove `get_repository()` function
   - Run tests to verify all operations work correctly

5. **Phase 5: Service consolidation** (medium risk)
   - Move topological sort methods into `ResourceService`
   - Update method calls from `self.topo_service.method()` to `self._method()`
   - Remove `TopologicalSortService` class
   - Run tests to verify sorting behavior unchanged

### Rollback Strategy

Each phase should be committed separately so rollback is possible:
- If Phase 1 fails: Revert schema changes
- If Phase 2 fails: Revert validation consolidation
- If Phase 3 fails: Revert exception changes
- If Phase 4 fails: Revert repository removal (most critical)
- If Phase 5 fails: Revert service consolidation

### Code Review Checklist

- [ ] All existing tests pass
- [ ] New property tests pass with 100+ iterations
- [ ] No new dependencies added
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Both SQLAlchemy and MongoDB backends tested
- [ ] Error responses match expected format
- [ ] No breaking changes to API contract

## Conclusion

This optimization reduces architectural complexity while maintaining 100% functional compatibility. The consolidation eliminates:
- 3 repository classes (BaseResourceRepository, SQLAlchemyResourceRepository, MongoDBResourceRepository) - ~600 lines
- 1 service class (TopologicalSortService) - ~150 lines
- 3 exception classes (DatabaseConnectionError, DatabaseTimeoutError, DuplicateResourceError) - ~30 lines
- ~50 lines of duplicate validation code
- ~30 lines of duplicate validator code
- MongoDB conversion overhead (_document_to_dict, _dict_to_document)

**Total reduction**: ~860 lines of code eliminated

The result is a more maintainable codebase with:
- Clearer code flow (no jumping between layers)
- Simpler architecture (2 layers instead of 3)
- Better performance (no conversion overhead)
- Easier debugging (database operations visible in service)
- No loss of functionality or test coverage
