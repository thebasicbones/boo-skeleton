# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create directory structure for FastAPI application (app/, static/, tests/)
  - Set up virtual environment and install dependencies (FastAPI, SQLAlchemy, Uvicorn, Pytest, Hypothesis)
  - Create requirements.txt with all dependencies
  - Initialize Git repository with .gitignore
  - _Requirements: All_

- [x] 2. Implement database models and schema
  - Create SQLAlchemy models for Resource and ResourceDependency
  - Define database schema with proper foreign keys and indexes
  - Set up database connection and session management
  - Create database initialization script
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_

- [x] 3. Implement Pydantic schemas for validation
  - Create ResourceCreate schema with validation rules
  - Create ResourceUpdate schema
  - Create ResourceResponse schema
  - Create ErrorResponse schema for consistent error formatting
  - _Requirements: 1.2, 6.1, 6.2, 7.4_

- [x] 4. Implement topological sort service
  - Create TopologicalSortService class
  - Implement Kahn's algorithm for topological sorting
  - Implement circular dependency detection with cycle path identification
  - Add validation method to check for cycles before create/update
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 4.1 Write property test for topological sort
  - **Property 9: Topological sort ordering**
  - **Validates: Requirements 5.1**
  - Generate random DAGs and verify dependencies always appear before dependents

- [x] 5. Implement resource repository layer
  - Create ResourceRepository class with database operations
  - Implement get_all() to retrieve all resources with dependencies
  - Implement get_by_id() for single resource retrieval
  - Implement create() for inserting new resources
  - Implement update() for modifying resources
  - Implement delete() with cascade option
  - Implement search() for filtering resources
  - _Requirements: 1.1, 2.1, 2.3, 3.1, 4.1, 5.1_

- [x] 5.1 Write property test for CRUD round-trips
  - **Property 1: Resource creation round-trip**
  - **Validates: Requirements 1.1, 2.1**
  - Generate random valid resources, create and retrieve, verify equivalence

- [x] 5.2 Write property test for cascade delete
  - **Property 12: Cascade delete removes dependents**
  - **Validates: Requirements 11.2**
  - Generate dependency graphs, test cascade delete removes all dependents

- [x] 5.3 Write property test for non-cascade delete
  - **Property 13: Non-cascade delete preserves dependents**
  - **Validates: Requirements 11.3**
  - Generate dependency graphs, test non-cascade delete preserves dependents

- [x] 6. Implement resource service layer
  - Create ResourceService class with business logic
  - Implement create_resource() with circular dependency validation
  - Implement get_resource() and get_all_resources()
  - Implement update_resource() with dependency validation
  - Implement delete_resource() with cascade logic
  - Implement search_resources() with topological sort integration
  - _Requirements: 1.1, 1.2, 2.1, 2.3, 3.1, 4.1, 5.1_

- [x] 6.1 Write property test for invalid data rejection
  - **Property 2: Invalid data rejection**
  - **Validates: Requirements 1.2, 6.1, 6.2, 6.3**
  - Generate invalid resource data, verify all rejected with HTTP 422

- [x] 6.2 Write property test for update persistence
  - **Property 5: Update persistence**
  - **Validates: Requirements 3.1**
  - Generate random updates, verify persistence through retrieval

- [x] 7. Implement API endpoints
  - Create FastAPI router for resource endpoints
  - Implement POST /api/resources (create)
  - Implement GET /api/resources (list all)
  - Implement GET /api/resources/{id} (get single)
  - Implement PUT /api/resources/{id} (update)
  - Implement DELETE /api/resources/{id} (delete with cascade query param)
  - Implement GET /api/search (search with topological sort)
  - Add CORS middleware for frontend access
  - _Requirements: 1.1, 1.4, 2.1, 2.4, 3.1, 3.4, 4.1, 4.3, 5.1, 5.5_

- [x] 7.1 Write property test for HTTP status codes
  - **Property 3: Successful creation returns 201**
  - **Property 6: Successful update returns 200**
  - **Property 8: Successful delete returns 204**
  - **Property 10: Successful search returns 200**
  - **Validates: Requirements 1.4, 3.4, 4.3, 5.5**
  - Verify correct status codes for all successful operations

- [x] 7.2 Write property test for error response consistency
  - **Property 11: Consistent error format**
  - **Validates: Requirements 7.4**
  - Generate various error conditions, verify consistent response format

- [x] 8. Implement error handling
  - Create custom exception classes (ResourceNotFound, ValidationError, CircularDependencyError)
  - Implement global exception handlers for FastAPI
  - Add error logging with appropriate detail levels
  - Ensure consistent error response format across all endpoints
  - _Requirements: 2.2, 3.2, 4.2, 6.3, 7.1, 7.2, 7.3, 7.4_

- [x] 9. Create main application entry point
  - Create main.py with FastAPI app initialization
  - Configure database on startup
  - Register routers and middleware
  - Add OpenAPI documentation configuration
  - Create startup script for running the server
  - _Requirements: All backend requirements_

- [x] 10. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise

- [ ] 11. Create frontend HTML structure
  - Create index.html with semantic HTML5 structure
  - Add header section with title
  - Add search bar section
  - Add resource list/grid container
  - Add create/edit modal form structure
  - Add delete confirmation modal
  - Link CSS and JavaScript files
  - _Requirements: 8.1, 9.1, 10.1, 11.1, 12.1, 13.1_

- [ ] 12. Implement frontend CSS styling
  - Create styles.css with clean, minimal design
  - Style header and search bar
  - Style resource cards/list items
  - Style forms and modals
  - Add dependency visualization styles (arrows, indentation, or badges)
  - Add loading state animations
  - Add responsive layout rules
  - Add visual feedback for interactions (hover, focus, active states)
  - _Requirements: 8.2, 13.1, 13.2_

- [ ] 13. Implement frontend API client
  - Create app.js with API base URL configuration
  - Implement fetchResources() to get all resources
  - Implement fetchResource(id) to get single resource
  - Implement createResource(data) for POST requests
  - Implement updateResource(id, data) for PUT requests
  - Implement deleteResource(id, cascade) for DELETE requests
  - Implement searchResources(query) for search endpoint
  - Add error handling for network failures
  - _Requirements: 8.1, 9.1, 10.2, 11.2, 11.3, 12.1_

- [ ] 14. Implement resource display functionality
  - Create renderResources() function to display resource list
  - Implement dependency visualization (show dependency names/arrows)
  - Add empty state message when no resources exist
  - Display all resource attributes (id, name, description, dependencies)
  - Add loading state indicator
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 13.3_

- [ ]* 14.1 Write property test for resource display
  - **Property 14: Resource display completeness**
  - **Validates: Requirements 8.4**
  - Generate random resources, verify all attributes displayed

- [ ] 15. Implement create resource functionality
  - Add event listener for create form submission
  - Implement form validation before submission
  - Call createResource() API function
  - Display newly created resource in list
  - Show error messages for validation failures
  - Clear form after successful creation
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 15.1 Write property test for create form submission
  - **Property 15: Create form submission**
  - **Property 16: Dependency inclusion in create**
  - **Validates: Requirements 9.1, 9.2, 9.4**
  - Generate random form data, verify API calls and UI updates

- [ ] 16. Implement update resource functionality
  - Add event listener for edit button clicks
  - Populate edit form with current resource data
  - Implement form submission for updates
  - Call updateResource() API function
  - Update displayed resource with new data
  - Show error messages for failures
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ]* 16.1 Write property test for update functionality
  - **Property 18: Edit form population**
  - **Property 19: Update form submission**
  - **Property 20: Dependency modification in update**
  - **Validates: Requirements 10.1, 10.2, 10.3**
  - Generate random resources and updates, verify form population and submission

- [ ] 17. Implement delete resource functionality
  - Add event listener for delete button clicks
  - Show confirmation modal with cascade option
  - Implement cascade checkbox in confirmation dialog
  - Call deleteResource() with cascade parameter
  - Remove deleted resource from display
  - Show error messages for failures
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 17.1 Write property test for delete functionality
  - **Property 21: Delete removes from UI**
  - **Validates: Requirements 11.5**
  - Generate random resources, delete them, verify UI removal

- [ ] 18. Implement search functionality
  - Add event listener for search input
  - Implement debounced search to avoid excessive API calls
  - Call searchResources() API function
  - Display results in topological order
  - Show visual indicators for dependency order (numbering, indentation)
  - Handle empty search (show all resources sorted)
  - Display error message for circular dependencies
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 18.1 Write property test for search display
  - **Property 22: Search displays topological order**
  - **Validates: Requirements 12.1**
  - Generate random search queries, verify topological order in results

- [ ] 19. Implement error display functionality
  - Create showError() function for displaying error messages
  - Add error message container to HTML
  - Style error messages (toast/alert style)
  - Implement auto-dismiss for error messages
  - Display validation errors inline on forms when possible
  - _Requirements: 9.3, 10.4, 11.4, 12.3_

- [ ]* 19.1 Write property test for error display
  - **Property 17: Error message display**
  - **Validates: Requirements 9.3**
  - Generate random API errors, verify display in UI

- [ ] 20. Add frontend initialization and event setup
  - Create init() function to set up event listeners
  - Load initial resources on page load
  - Set up form event handlers
  - Initialize search functionality
  - Add keyboard shortcuts (Enter to submit, Escape to close modals)
  - _Requirements: 8.1, 13.4_

- [ ] 21. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise

- [ ] 22. Create documentation
  - Create README.md with project overview
  - Document API endpoints with examples
  - Document how to run the application
  - Document how to run tests
  - Add example usage scenarios
  - _Requirements: All_
