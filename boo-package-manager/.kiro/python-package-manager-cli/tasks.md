# Implementation Plan

- [x] 1. Set up project structure and core infrastructure
  - Create CLI project directory structure with proper Python package layout
  - Set up pyproject.toml with dependencies (click/typer, httpx, rich, pydantic, hypothesis, pytest)
  - Configure development tools (black, ruff, mypy, pytest)
  - Create basic CLI entry point with version and help commands
  - _Requirements: 15.1_

- [ ] 2. Implement backend API client
- [ ] 2.1 Create BackendClient class with httpx
  - Implement async HTTP client with base URL configuration
  - Add authentication header support for API keys
  - Implement connection pooling and timeout handling
  - _Requirements: 9.1, 9.2_

- [ ] 2.2 Implement CRUD operations for resources
  - Add create_resource() method (POST /api/resources)
  - Add get_resource() method (GET /api/resources/{id})
  - Add list_resources() method (GET /api/resources)
  - Add update_resource() method (PUT /api/resources/{id})
  - Add delete_resource() method with cascade support (DELETE /api/resources/{id})
  - _Requirements: 1.1, 2.1, 5.1, 7.1_

- [ ] 2.3 Implement search functionality
  - Add search_resources() method (GET /api/search?q=)
  - Handle empty query (returns all resources in topological order)
  - Parse and return topologically sorted results
  - _Requirements: 6.1, 6.5_

- [ ]* 2.4 Write property test for backend client
  - **Property 1: Installation order follows topological sort**
  - **Validates: Requirements 1.4**

- [ ]* 2.5 Add error handling for backend client
  - Handle network errors (connection refused, timeout)
  - Handle HTTP errors (404, 422, 500)
  - Parse CircularDependencyError from backend responses
  - Implement retry logic with exponential backoff
  - _Requirements: 4.2, 9.4_

- [ ] 3. Implement PyPI client
- [ ] 3.1 Create PyPIClient class
  - Implement async HTTP client for PyPI JSON API
  - Add get_package_metadata() method
  - Add get_latest_version() method
  - Add search_packages() method
  - _Requirements: 1.1, 5.2, 6.1, 7.1_

- [ ]* 3.2 Write unit tests for PyPI client
  - Test metadata fetching with mocked responses
  - Test version parsing
  - Test search result parsing
  - _Requirements: 1.1, 5.2_

- [ ] 3.3 Add caching for PyPI metadata
  - Implement local SQLite cache for package metadata
  - Add cache expiration logic (24 hours)
  - Add cache invalidation on explicit refresh
  - _Requirements: 9.4_

- [ ] 4. Implement pip wrapper
- [ ] 4.1 Create PipWrapper class
  - Implement install() method using subprocess
  - Implement uninstall() method using subprocess
  - Implement list_installed() method (parse pip list output)
  - Implement get_package_info() method (parse pip show output)
  - _Requirements: 1.1, 2.1, 5.1_

- [ ] 4.2 Add output parsing for pip commands
  - Parse pip install output for progress tracking
  - Parse pip list output to JSON format
  - Parse pip show output to structured data
  - Handle pip error messages
  - _Requirements: 1.5, 2.5_

- [ ]* 4.3 Write unit tests for pip wrapper
  - Test subprocess command construction
  - Test output parsing with sample pip outputs
  - Test error handling for pip failures
  - _Requirements: 1.1, 1.5_

- [ ] 5. Implement configuration management
- [ ] 5.1 Create Config class with Pydantic
  - Define configuration schema (backend_url, api_key, cache_dir, etc.)
  - Implement config file loading from ~/.boo/config.toml
  - Add environment variable support
  - Add default values
  - _Requirements: 14.1, 14.4_

- [ ] 5.2 Implement config commands
  - Implement `boo config set <key> <value>` command
  - Implement `boo config get <key>` command
  - Implement `boo config list` command
  - Add validation for config values
  - _Requirements: 14.1, 14.2, 14.3, 14.5_

- [ ]* 5.3 Write property test for config round-trip
  - **Property 47: Config round-trip**
  - **Validates: Requirements 14.1, 14.2**

- [ ] 6. Implement UI layer with Rich
- [ ] 6.1 Create UI class with Rich console
  - Implement print_success(), print_error(), print_warning() methods
  - Implement print_table() for formatted tables
  - Implement print_tree() for hierarchical trees
  - Implement progress_bar() for long operations
  - _Requirements: 3.1, 3.2, 5.1, 15.1_

- [ ]* 6.2 Write unit tests for UI formatting
  - Test table formatting with sample data
  - Test tree formatting with sample dependency graphs
  - Test color output (with and without color support)
  - _Requirements: 3.2, 5.1_

- [ ] 7. Implement install command
- [ ] 7.1 Create install command handler
  - Parse package name and optional version specifier
  - Fetch package metadata from PyPI
  - Create Resource in backend
  - Handle backend validation errors (circular dependencies)
  - _Requirements: 1.1, 1.2_

- [ ] 7.2 Implement installation logic
  - Get topological order from backend
  - Install packages in order using pip wrapper
  - Display progress for each package
  - Handle installation failures with rollback
  - _Requirements: 1.4, 1.5_

- [ ] 7.3 Add requirements file support
  - Parse requirements.txt file
  - Create Resources for all packages
  - Install in topological order
  - _Requirements: 1.3_

- [ ]* 7.4 Write property test for installation order
  - **Property 1: Installation order follows topological sort**
  - **Validates: Requirements 1.4**

- [ ]* 7.5 Write property test for installation rollback
  - **Property 3: Installation rollback on failure**
  - **Validates: Requirements 1.5**

- [ ] 8. Implement uninstall command
- [ ] 8.1 Create uninstall command handler
  - Parse package name and cascade flag
  - Find Resource in backend by name
  - Query backend for dependent packages
  - Display warning if dependents exist
  - _Requirements: 2.1, 2.2_

- [ ] 8.2 Implement uninstallation logic
  - Call backend delete with cascade flag
  - Uninstall package using pip wrapper
  - Display confirmation message
  - Handle non-existent packages
  - _Requirements: 2.3, 2.4, 2.5_

- [ ]* 8.3 Write property test for cascade delete
  - **Property 5: Cascade delete completeness**
  - **Validates: Requirements 2.3**

- [ ]* 8.4 Write property test for uninstall cleanup
  - **Property 6: Uninstall cleanup**
  - **Validates: Requirements 2.4**

- [ ] 9. Implement list command
- [ ] 9.1 Create list command handler
  - Fetch all Resources from backend
  - Display in table format with name, version, description
  - Support --format json option
  - Support --filter pattern option
  - _Requirements: 5.1, 5.3, 5.5_

- [ ] 9.2 Add outdated package detection
  - Fetch latest versions from PyPI for all packages
  - Compare with backend Resource versions
  - Display outdated packages with both versions
  - _Requirements: 5.2, 5.4_

- [ ]* 9.3 Write property test for list completeness
  - **Property 14: List completeness**
  - **Validates: Requirements 5.1**

- [ ]* 9.4 Write property test for JSON output
  - **Property 16: JSON output validity**
  - **Validates: Requirements 5.3**

- [ ] 10. Implement tree command
- [ ] 10.1 Create tree command handler
  - Fetch all Resources from backend
  - Build hierarchical tree structure from dependencies
  - Display using Rich tree visualization
  - Support --depth option for limiting tree depth
  - _Requirements: 3.1, 3.2, 3.4_

- [ ] 10.2 Add package-specific tree
  - Support `boo tree <package>` for single package
  - Recursively fetch dependencies
  - Build subtree
  - _Requirements: 3.3_

- [ ] 10.3 Handle circular dependencies in tree display
  - Detect cycles from backend CircularDependencyError
  - Mark circular dependencies in tree with special indicator
  - _Requirements: 3.5_

- [ ]* 10.4 Write property test for tree structure
  - **Property 8: Tree structure correctness**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 10.5 Write property test for depth limiting
  - **Property 10: Depth limiting**
  - **Validates: Requirements 3.4**

- [ ] 11. Implement search command
- [ ] 11.1 Create search command handler
  - Call backend search endpoint with query
  - Display results in table format
  - Support --limit option
  - Handle empty results
  - _Requirements: 6.1, 6.3, 6.4_

- [ ] 11.2 Verify topological ordering
  - Ensure results maintain backend's topological order
  - Display dependencies for each result
  - _Requirements: 6.2, 6.5_

- [ ]* 11.3 Write property test for search ordering
  - **Property 17: Search result ordering**
  - **Validates: Requirements 6.5**

- [ ] 12. Implement check command
- [ ] 12.1 Create check command handler
  - Fetch all Resources from backend
  - Attempt to validate dependency graph
  - Display success message if no conflicts
  - Display circular dependency errors with cycle path
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 12.2 Handle conflict detection
  - Parse CircularDependencyError from backend
  - Display cycle path clearly
  - Suggest resolution if possible
  - _Requirements: 4.3_

- [ ]* 12.3 Write property test for validation
  - **Property 12: Validation completeness**
  - **Validates: Requirements 4.1**

- [ ] 13. Implement update command
- [ ] 13.1 Create update command handler
  - Fetch latest version from PyPI
  - Update Resource in backend
  - Handle validation errors
  - Display old and new versions
  - _Requirements: 7.1, 7.4_

- [ ] 13.2 Add bulk update support
  - Implement `boo update --all` to update all packages
  - Iterate through all Resources
  - Update each one
  - _Requirements: 7.2_

- [ ] 13.3 Add dry-run mode
  - Implement `--dry-run` flag
  - Fetch latest versions but don't update backend
  - Display what would be updated
  - _Requirements: 7.5_

- [ ]* 13.4 Write property test for update conflict prevention
  - **Property 22: Update conflict prevention**
  - **Validates: Requirements 7.3**

- [ ]* 13.5 Write property test for dry-run safety
  - **Property 23: Dry-run safety**
  - **Validates: Requirements 7.5**

- [ ] 14. Implement lock file functionality
- [ ] 14.1 Create LockFile class
  - Define lock file format with Pydantic
  - Implement generate() method to create lock file
  - Include all packages with exact versions
  - Include transitive dependencies
  - Include package hashes
  - _Requirements: 8.1, 8.2, 8.5_

- [ ] 14.2 Implement lock command
  - Create `boo lock` command
  - Generate lock file from current environment
  - Save to boo.lock file
  - _Requirements: 8.1_

- [ ] 14.3 Add locked installation support
  - Implement `--locked` flag for install command
  - Read lock file
  - Install exact versions from lock file
  - Warn if lock file is outdated
  - _Requirements: 8.3, 8.4_

- [ ]* 14.4 Write property test for lock file round-trip
  - **Property 25: Lock file round-trip**
  - **Validates: Requirements 8.3**

- [ ]* 14.5 Write property test for lock file completeness
  - **Property 24: Lock file completeness**
  - **Validates: Requirements 8.1, 8.2**

- [ ] 15. Implement sync command
- [ ] 15.1 Create sync command handler
  - Compare local packages with backend Resources
  - Create Resources for new local packages
  - Update Resources for changed packages
  - Display summary of changes
  - _Requirements: 9.1, 9.2, 9.5_

- [ ] 15.2 Add pull sync support
  - Implement `--pull` flag
  - Fetch all Resources from backend
  - Install missing packages locally
  - _Requirements: 9.3_

- [ ] 15.3 Implement offline caching
  - Cache operations when backend is unavailable
  - Store in local SQLite database
  - Retry when backend becomes available
  - _Requirements: 9.4_

- [ ]* 15.4 Write property test for sync correctness
  - **Property 27: Sync operation correctness**
  - **Validates: Requirements 9.1, 9.2**

- [ ]* 15.5 Write property test for offline caching
  - **Property 29: Offline operation caching**
  - **Validates: Requirements 9.4**

- [ ] 16. Implement graph command
- [ ] 16.1 Create graph command handler
  - Fetch all Resources from backend
  - Build graph structure from dependencies
  - Support ASCII art output format
  - Support DOT format output
  - Support JSON format output
  - _Requirements: 10.1, 10.2_

- [ ] 16.2 Add image generation support
  - Implement `--output` flag for image files
  - Use graphviz to generate PNG/SVG
  - _Requirements: 10.3_

- [ ] 16.3 Handle circular dependencies in graph
  - Highlight cycles in different color
  - Use backend's CircularDependencyError
  - _Requirements: 10.4_

- [ ] 16.4 Add package-specific subgraph
  - Support `boo graph <package>` for single package
  - Fetch transitive dependencies
  - Build subgraph
  - _Requirements: 10.5_

- [ ]* 16.5 Write property test for graph structure
  - **Property 31: Graph structure correctness**
  - **Validates: Requirements 10.1**

- [ ] 17. Implement audit command
- [ ] 17.1 Create audit command handler
  - Fetch all installed packages
  - Query vulnerability database (e.g., PyPI Advisory Database)
  - Display vulnerabilities with severity levels
  - _Requirements: 11.1, 11.2_

- [ ] 17.2 Add auto-fix support
  - Implement `--fix` flag
  - Attempt to upgrade vulnerable packages
  - Display success/failure for each fix
  - _Requirements: 11.3_

- [ ] 17.3 Handle unfixable vulnerabilities
  - Detect when no safe version exists
  - Suggest manual remediation steps
  - _Requirements: 11.5_

- [ ]* 17.4 Write property test for audit completeness
  - **Property 35: Audit completeness**
  - **Validates: Requirements 11.1**

- [ ] 18. Implement virtual environment management
- [ ] 18.1 Create env command group
  - Implement `boo env create <name>` command
  - Implement `boo env list` command
  - Implement `boo env delete <name>` command
  - Implement `boo env activate <name>` command (display instructions)
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [ ] 18.2 Add environment tracking
  - Store managed environments in config
  - Detect active environment
  - Display active environment in command output
  - _Requirements: 12.5_

- [ ]* 18.3 Write property test for environment management
  - **Property 39: Environment creation**
  - **Property 41: Environment deletion**
  - **Validates: Requirements 12.1, 12.4**

- [ ] 19. Implement export command
- [ ] 19.1 Create export command handler
  - Fetch all installed packages
  - Generate requirements.txt format by default
  - Support `--format poetry` for pyproject.toml
  - Support `--format conda` for environment.yml
  - _Requirements: 13.1, 13.2, 13.3_

- [ ] 19.2 Add dependency filtering
  - Include only top-level dependencies by default
  - Support `--all` flag to include transitive dependencies
  - _Requirements: 13.4, 13.5_

- [ ]* 19.3 Write property test for export completeness
  - **Property 43: Export completeness**
  - **Validates: Requirements 13.1**

- [ ]* 19.4 Write property test for export format validity
  - **Property 44: Export format validity**
  - **Validates: Requirements 13.2, 13.3**

- [ ] 20. Implement help system
- [ ] 20.1 Add comprehensive help text
  - Implement `boo --help` with command list
  - Add detailed help for each command with `boo <command> --help`
  - Include usage examples in help text
  - _Requirements: 15.1, 15.2, 15.3_

- [ ] 20.2 Add command suggestions
  - Implement fuzzy matching for invalid commands
  - Suggest similar valid commands
  - _Requirements: 15.4_

- [ ] 20.3 Add docs command
  - Implement `boo docs` command
  - Open online documentation in web browser
  - _Requirements: 15.5_

- [ ] 21. Integration testing and polish
- [ ] 21.1 Write integration tests
  - Test full install flow (CLI → backend → pip)
  - Test uninstall with cascade
  - Test sync operations
  - Test offline mode
  - _Requirements: All_

- [ ]* 21.2 Write remaining property tests
  - Implement all 52 correctness properties
  - Ensure 100+ iterations per property test
  - Tag each test with property number
  - _Requirements: All_

- [ ] 21.3 Add error handling polish
  - Improve error messages for common failures
  - Add helpful suggestions for errors
  - Test error recovery scenarios
  - _Requirements: All_

- [ ] 21.4 Performance optimization
  - Add parallel PyPI requests where possible
  - Optimize cache usage
  - Profile slow operations
  - _Requirements: All_

- [ ] 22. Documentation and packaging
- [ ] 22.1 Write user documentation
  - Create README with installation instructions
  - Add usage examples for all commands
  - Document configuration options
  - _Requirements: 15.1_

- [ ] 22.2 Write developer documentation
  - Document architecture and design decisions
  - Add contribution guidelines
  - Document testing strategy
  - _Requirements: All_

- [ ] 22.3 Package for distribution
  - Configure pyproject.toml for PyPI
  - Add entry point for `boo` command
  - Test installation from package
  - _Requirements: All_

- [ ] 23. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
