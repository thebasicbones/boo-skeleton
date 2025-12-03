# Implementation Plan: MongoDB Integration

- [x] 1. Set up MongoDB dependencies and configuration infrastructure
  - Add Motor and PyMongo to `requirements.txt`
  - Create environment variable configuration for `DATABASE_TYPE`, `MONGODB_DATABASE`, and MongoDB-specific settings
  - Update `.env.example` with MongoDB configuration examples
  - _Requirements: 1.1, 1.2_

- [x] 2. Create abstract repository interface
  - Create `app/repositories/base_resource_repository.py` with `BaseResourceRepository` abstract base class
  - Define abstract methods: `get_all()`, `get_by_id()`, `create()`, `update()`, `delete()`, `search()`
  - Add type hints and docstrings for all interface methods
  - _Requirements: 2.1_

- [x] 3. Refactor existing SQLAlchemy code for multi-backend support
- [x] 3.1 Rename and refactor SQLAlchemy-specific files
  - Rename `app/database.py` to `app/database_sqlalchemy.py`
  - Rename `app/models/resource.py` to `app/models/sqlalchemy_resource.py`
  - Rename `app/repositories/resource_repository.py` to `app/repositories/sqlalchemy_resource_repository.py`
  - Update `ResourceRepository` class name to `SQLAlchemyResourceRepository`
  - Make `SQLAlchemyResourceRepository` inherit from `BaseResourceRepository`
  - Update all imports throughout the codebase to use new file names
  - _Requirements: 2.1_

- [x] 3.2 Write property test for SQLAlchemy repository operations
  - **Property 4: Backend abstraction transparency (SQLAlchemy baseline)**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 4. Implement MongoDB connection management
- [x] 4.1 Create MongoDB database connection module
  - Create `app/database_mongodb.py` with Motor client initialization
  - Implement `get_mongodb_client()` function to return AsyncIOMotorClient
  - Implement `get_mongodb_db()` function to return database instance
  - Implement `init_mongodb()` function to create indexes
  - Implement `close_mongodb()` function for graceful shutdown
  - Handle connection errors with descriptive error messages
  - _Requirements: 1.2, 1.4, 1.5_

- [x] 4.2 Write property test for MongoDB connection lifecycle
  - **Property 1: Backend initialization from configuration (MongoDB)**
  - **Validates: Requirements 1.2**

- [ ]* 4.3 Write property test for invalid configuration handling
  - **Property 2: Invalid configuration rejection**
  - **Validates: Requirements 1.4**

- [ ]* 4.4 Write property test for graceful shutdown
  - **Property 3: Graceful connection cleanup**
  - **Validates: Requirements 1.5**

- [x] 5. Implement MongoDB repository
- [x] 5.1 Create MongoDB resource repository
  - Create `app/repositories/mongodb_resource_repository.py` with `MongoDBResourceRepository` class
  - Implement `__init__()` to accept Motor database instance
  - Implement helper methods for document-to-model and model-to-document conversion
  - Ensure UUID generation for `_id` field
  - Ensure proper datetime handling (UTC timestamps)
  - _Requirements: 2.1, 3.1, 3.2, 3.3_

- [x] 5.2 Implement MongoDB repository CRUD operations
  - Implement `create()` method with dependency handling
  - Implement `get_by_id()` method
  - Implement `get_all()` method
  - Implement `update()` method with partial updates and dependency handling
  - Implement `delete()` method with cascade support (recursive dependent deletion)
  - Implement `search()` method with name/description text search
  - Handle MongoDB-specific errors and translate to custom exceptions
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 3.4, 6.1, 6.2_

- [x] 5.3 Create MongoDB indexes
  - Create index on `name` field for search performance
  - Create index on `dependencies` array for relationship queries
  - Implement index creation in `init_mongodb()` function
  - _Requirements: 2.6_

- [x] 5.4 Write property test for CRUD round-trip consistency
  - **Property 5: CRUD round-trip consistency**
  - **Validates: Requirements 2.2, 2.3, 3.1, 3.2, 3.3**

- [x] 5.5 Write property test for update persistence
  - **Property 6: Update persistence**
  - **Validates: Requirements 2.4, 3.3**

- [x] 5.6 Write property test for delete completeness
  - **Property 7: Delete completeness**
  - **Validates: Requirements 2.5**

- [x] 5.7 Write property test for relationship preservation
  - **Property 8: Relationship preservation**
  - **Validates: Requirements 3.4**

- [x] 5.8 Write property test for schema field completeness
  - **Property 9: Schema field completeness**
  - **Validates: Requirements 3.1**

- [ ] 6. Create database factory for backend selection
- [x] 6.1 Implement database factory
  - Create `app/database_factory.py` with `DatabaseFactory` class
  - Implement `get_database_type()` to read `DATABASE_TYPE` environment variable
  - Implement `get_db()` dependency function that returns appropriate session/client based on configuration
  - Implement `get_repository()` function that instantiates the correct repository class
  - Implement `init_database()` function that initializes the configured backend
  - Implement `close_database()` function that closes connections for the configured backend
  - _Requirements: 1.1, 1.2, 1.3, 2.1_

- [x] 6.2 Write property test for backend abstraction transparency
  - **Property 4: Backend abstraction transparency (both backends)**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 7. Update service layer to use database factory
  - Update `app/services/resource_service.py` to use `get_repository()` from database factory
  - Ensure `ResourceService` works with both repository implementations
  - Verify no backend-specific code in service layer
  - _Requirements: 2.1_

- [x] 8. Update API layer to use database factory
  - Update `main.py` to use `init_database()` and `close_database()` from factory
  - Update routers to use `get_db()` dependency from factory
  - Ensure startup and shutdown events handle both backends
  - _Requirements: 1.2, 1.3, 1.5_

- [ ] 9. Implement MongoDB-specific error handling
- [ ] 9.1 Extend exception hierarchy
  - Add `DatabaseConnectionError`, `DatabaseTimeoutError`, `DuplicateResourceError` to `app/exceptions.py`
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 9.2 Update error handlers
  - Update `app/error_handlers.py` to handle new database exception types
  - Map `DatabaseConnectionError` and `DatabaseTimeoutError` to HTTP 503
  - Map validation errors to HTTP 400
  - Map `DuplicateResourceError` to HTTP 409
  - Ensure error responses include descriptive messages
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 9.3 Write property test for connection error handling
  - **Property 10: Connection error handling**
  - **Validates: Requirements 6.1**

- [ ]* 9.4 Write property test for validation error handling
  - **Property 11: Validation error handling**
  - **Validates: Requirements 6.2**

- [ ] 10. Create test infrastructure for dual-backend testing
- [ ] 10.1 Create parameterized test fixtures
  - Create `tests/conftest.py` fixtures for both SQLite and MongoDB backends
  - Implement `db_backend` fixture parameterized with "sqlite" and "mongodb"
  - Implement setup and teardown for MongoDB test database
  - Ensure test isolation (clean database state between tests)
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 10.2 Create Hypothesis strategies for resource data
  - Create `tests/strategies.py` with custom Hypothesis strategies
  - Implement `resource_create_strategy()` for generating valid ResourceCreate data
  - Implement `resource_update_strategy()` for generating valid ResourceUpdate data
  - Implement `resource_id_strategy()` for generating valid UUIDs
  - _Requirements: 4.4_

- [ ] 11. Update existing tests to support both backends
  - Update existing unit tests to use parameterized `db_backend` fixture
  - Ensure all existing tests pass with both SQLite and MongoDB
  - Update test assertions to be backend-agnostic
  - _Requirements: 4.1, 4.4_

- [ ] 12. Create migration script
  - Create `scripts/migrate_sqlite_to_mongodb.py`
  - Implement SQLite data export to JSON
  - Implement MongoDB data import from JSON
  - Add validation to verify data integrity after migration
  - Add command-line interface with progress reporting
  - _Requirements: 5.3_

- [ ] 13. Update documentation
  - Update `README.md` with MongoDB setup instructions
  - Document all MongoDB-specific environment variables
  - Provide example connection strings for local and cloud deployments
  - Document migration process from SQLite to MongoDB
  - Add troubleshooting section for common MongoDB issues
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 14. Checkpoint - Ensure all tests pass
  - Run full test suite with both SQLite and MongoDB backends
  - Verify all property-based tests pass with 100+ iterations
  - Verify all unit tests pass
  - Verify all integration tests pass
  - Ensure all tests pass, ask the user if questions arise.
