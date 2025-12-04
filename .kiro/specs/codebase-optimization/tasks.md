# Implementation Plan

- [x] 1. Phase 1: Consolidate schema validation with base class
  - Create `ResourceBase` schema class with shared validators for name, description, and dependencies
  - Update `ResourceCreate` to inherit from `ResourceBase` and remove duplicate validators
  - Update `ResourceUpdate` to inherit from `ResourceBase` and remove duplicate validators
  - Verify schema validation behavior is unchanged
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 1.1 Run existing tests to verify schema validation unchanged
  - Execute all existing unit tests for schemas
  - Execute all existing property tests
  - Verify no regressions in validation behavior
  - _Requirements: 6.1, 6.2_

<!-- - [ ] 2. Phase 2: Consolidate service layer by integrating topological sort
  - Move `topological_sort()` method from `TopologicalSortService` to `ResourceService` as `_topological_sort()`
  - Move `validate_no_cycles()` method from `TopologicalSortService` to `ResourceService` as `_validate_no_cycles()`
  - Move `_find_cycle()` helper method to `ResourceService`
  - Move `has_cycle()` method to `ResourceService` as `_has_cycle()`
  - Update `ResourceService.__init__()` to remove `self.topo_service` initialization
  - Update all method calls from `self.topo_service.method()` to `self._method()`
  - Delete `app/services/topological_sort_service.py` file
  - Update imports in files that reference `TopologicalSortService`
  - _Requirements: 2.1, 2.2, 2.3, 2.4_ -->

- [ ]* 2.1 Write property test for topological sort preservation
  - **Property 2: Topological Sort Preservation**
  - **Validates: Requirements 2.4**
  - Generate random DAGs and verify sort correctness
  - Generate graphs with cycles and verify CircularDependencyError is raised
  - Test edge cases: empty graphs, single nodes, disconnected components
  - Run minimum 100 iterations

- [ ]* 2.2 Run existing tests to verify service consolidation unchanged
  - Execute all existing unit tests for services
  - Execute all existing property tests
  - Verify topological sorting behavior is unchanged
  - _Requirements: 6.1, 6.2_

- [x] 3. Phase 3: Consolidate dependency validation logic
  - Create `_validate_and_check_cycles()` private method in `ResourceService`
  - Implement logic to validate dependencies exist and check for circular dependencies
  - Update `create_resource()` to use `_validate_and_check_cycles()` instead of inline validation
  - Update `update_resource()` to use `_validate_and_check_cycles()` instead of inline validation
  - Remove duplicate validation code from both methods
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 3.1 Run existing tests to verify validation consolidation unchanged
  - Execute all existing unit tests for resource service
  - Execute all existing property tests
  - Verify dependency validation behavior is unchanged
  - _Requirements: 6.1, 6.2_

- [x] 4. Phase 4: Simplify exception hierarchy
  - Update `DatabaseError` class to accept `error_type` parameter ("connection", "timeout", "duplicate", "general")
  - Update `DatabaseError.__init__()` to store `error_type` and `details`
  - Rename `ResourceNotFoundError` to `NotFoundError` in `app/exceptions.py`
  - Remove `DatabaseConnectionError` class definition
  - Remove `DatabaseTimeoutError` class definition
  - Remove `DuplicateResourceError` class definition
  - _Requirements: 3.1, 3.2_

- [ ] 5. Update repository implementations to use consolidated exceptions
  - Update `MongoDBResourceRepository` to raise `DatabaseError(msg, error_type="connection")` instead of `DatabaseConnectionError`
  - Update `MongoDBResourceRepository` to raise `DatabaseError(msg, error_type="timeout")` instead of `DatabaseTimeoutError`
  - Update `MongoDBResourceRepository` to raise `DatabaseError(msg, error_type="duplicate")` instead of `DuplicateResourceError`
  - Update `SQLAlchemyResourceRepository` if it uses any of the removed exceptions
  - Update imports to remove references to deleted exception classes
  - _Requirements: 3.2_

- [ ] 6. Update service layer to use consolidated exceptions
  - Update `ResourceService` to raise `NotFoundError` instead of `ResourceNotFoundError`
  - Update all imports to use `NotFoundError`
  - Verify all exception handling logic is correct
  - _Requirements: 3.2, 3.3_

- [ ] 7. Update error handlers for consolidated exceptions
  - Update `resource_not_found_handler` to handle `NotFoundError` instead of `ResourceNotFoundError`
  - Update `database_connection_error_handler` to handle `DatabaseError` with `error_type="connection"` → HTTP 503
  - Update `database_timeout_error_handler` to handle `DatabaseError` with `error_type="timeout"` → HTTP 503
  - Update `duplicate_resource_error_handler` to handle `DatabaseError` with `error_type="duplicate"` → HTTP 409
  - Add handler for `DatabaseError` with `error_type="general"` → HTTP 500
  - Consolidate handlers into single `database_error_handler` that checks `error_type`
  - Remove individual handler functions for deleted exception types
  - Update error response format to maintain backward compatibility
  - _Requirements: 3.3, 3.4_

- [ ]* 7.1 Write property test for error response consistency
  - **Property 3: Error Response Consistency**
  - **Validates: Requirements 3.3, 3.4, 6.4**
  - Test NotFoundError → 404 with correct format
  - Test ValidationError → 422 with correct format
  - Test CircularDependencyError → 422 with cycle path
  - Test DatabaseError variants → correct status codes (503, 409, 500)
  - Verify error response structure matches expected format
  - Run minimum 100 iterations

- [ ]* 7.2 Run existing tests to verify error handling unchanged
  - Execute all existing unit tests for error handlers
  - Execute all existing property tests
  - Verify error responses match expected format
  - _Requirements: 6.1, 6.2_

- [x] 8. Update database factory and other imports
  - Update `app/database_factory.py` imports to use consolidated exceptions
  - Update `app/database_mongodb.py` imports to use consolidated exceptions
  - Update `app/database_sqlalchemy.py` imports if needed
  - Search codebase for any remaining references to deleted exception classes
  - Update all imports and exception handling
  - _Requirements: 3.2, 3.3_

- [ ] 9. Phase 5: Remove repository pattern and move database operations to service layer
  - Add `is_mongodb` flag to `ResourceService.__init__()` to detect backend type
  - Add `self.collection = db.resources` for MongoDB backend
  - Move `get_all()` logic from repositories directly into `ResourceService`
  - Move `get_by_id()` logic from repositories directly into `ResourceService`
  - Move `create()` logic from repositories directly into `ResourceService`
  - Move `update()` logic from repositories directly into `ResourceService`
  - Move `delete()` logic from repositories directly into `ResourceService`
  - Move `_get_all_dependents()` helper method into `ResourceService`
  - Move `search()` logic from repositories directly into `ResourceService`
  - Update all service methods to call database operations directly instead of `self.repository.method()`
  - Remove `self.repository = get_repository(db)` from `ResourceService.__init__()`
  - Delete `app/repositories/base_resource_repository.py`
  - Delete `app/repositories/mongodb_resource_repository.py`
  - Delete `app/repositories/sqlalchemy_resource_repository.py`
  - Update `app/database_factory.py` to remove `get_repository()` function
  - Update imports throughout codebase to remove repository references
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 9.1 Write property test for backend consistency
  - **Property 1: Backend Consistency**
  - **Validates: Requirements 6.1, 6.4, 7.3, 7.5**
  - Generate random resources with various dependency structures
  - Execute CRUD operations against both SQLAlchemy and MongoDB backends
  - Compare responses for equivalence
  - Verify error conditions produce same exceptions
  - Run minimum 100 iterations

- [ ]* 9.2 Run existing tests to verify repository removal unchanged
  - Execute all existing unit tests
  - Execute all existing property tests
  - Verify all database operations work correctly
  - Verify both backends function properly
  - _Requirements: 7.1, 7.2_

- [ ] 10. Final checkpoint - Verify all tests pass
  - Ensure all tests pass, ask the user if questions arise
  - Run complete test suite including unit tests and property tests
  - Verify no regressions in functionality
  - Verify code coverage maintained or improved
  - Confirm both SQLAlchemy and MongoDB backends work correctly
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
