# Implementation Plan: FastAPI CRUD CLI Scaffolding Tool

- [x] 1. Set up package structure and core dependencies
  - Create package directory structure (fastapi_crud_cli/, cli/, templates/, utils/)
  - Create pyproject.toml with package metadata and dependencies
  - Create MANIFEST.in to include template files in distribution
  - Set up entry point for fastapi-crud command
  - Create __version__.py for version management
  - _Requirements: 1.1, 1.2, 9.1, 9.2, 9.3_

- [ ]* 1.1 Write property test for template file accessibility
  - **Property 6: Template file accessibility**
  - **Validates: Requirements 9.5**

- [x] 2. Implement validation module
  - Create validators.py with ProjectValidator class
  - Implement validate_project_name() method with regex validation
  - Implement validate_directory_available() for conflict detection
  - Implement validate_mongodb_url() for MongoDB connection string validation
  - Implement validate_postgres_config() for PostgreSQL parameter validation
  - Implement validate_email() for basic email format validation
  - _Requirements: 2.3, 8.1, 8.2, 8.3_

- [ ]* 2.1 Write property test for project name validation
  - **Property 1: Project name validation**
  - **Validates: Requirements 2.3**

- [ ]* 2.2 Write property test for invalid database parameter rejection
  - **Property 5: Invalid database parameter rejection**
  - **Validates: Requirements 8.2**

- [ ]* 2.3 Write unit tests for validation edge cases
  - Test empty strings, very long names, special characters
  - Test directory conflict scenarios
  - Test various invalid database URL formats
  - _Requirements: 2.3, 8.1, 8.2_

- [x] 3. Implement database configuration module
  - Create database_configs.py with DatabaseConfig base class
  - Implement SQLiteConfig with dependencies and env variables
  - Implement MongoDBConfig with connection prompts
  - Implement PostgreSQLConfig with host/port/credentials prompts
  - Create DATABASE_CONFIGS registry dictionary
  - Implement get_prompts() and generate_env_content() methods for each config
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 3.1 Write property test for database configuration consistency
  - **Property 3: Database configuration consistency**
  - **Validates: Requirements 4.4, 4.5**

- [x] 4. Implement output formatter module
  - Create output.py with OutputFormatter class
  - Implement display_welcome() with Rich banner
  - Implement display_progress() with spinner
  - Implement display_success() with green checkmarks
  - Implement display_error() with red error symbols
  - Implement display_summary_table() for configuration display
  - Implement display_file_tree() for generated files
  - Implement display_next_steps() with post-generation instructions
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 7.3, 7.5_

- [x] 5. Implement interactive prompts module
  - Create prompts.py with ProjectPrompts class
  - Implement prompt_project_name() with validation
  - Implement prompt_database_type() with SQLite/MongoDB/PostgreSQL options
  - Implement prompt_database_config() that delegates to database-specific prompts
  - Implement prompt_project_metadata() for author/description
  - Implement prompt_optional_features() for examples/dev tools
  - Implement confirm_generation() with summary display
  - _Requirements: 2.1, 2.2, 2.4, 6.1, 6.2, 6.3, 6.4, 7.1, 8.4_

- [x] 6. Create template files
  - Create templates/project/ directory structure
  - Create Jinja2 templates for all Python source files (app/, config/, tests/)
  - Create templates for configuration files (.env.j2, .gitignore.j2, pyproject.toml.j2)
  - Create README.md.j2 template with database-specific sections
  - Create requirements.txt.j2 with conditional dependencies
  - Create database-specific configuration YAML files
  - Add template variables for project_name, database_type, author info, etc.
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 6.5_

- [ ] 7. Implement template engine module
  - Create template_engine.py with TemplateEngine class
  - Initialize Jinja2 Environment with FileSystemLoader
  - Implement render_file() for single template rendering
  - Implement get_template_context() to build context from ProjectConfig
  - Implement render_project() to process all templates
  - Add logic for conditional template inclusion based on user options
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 7.1 Write unit tests for template rendering
  - Test template variable substitution
  - Test conditional template inclusion
  - Test handling of missing variables
  - _Requirements: 5.2_

- [ ] 8. Implement file generator module
  - Create generator.py with ProjectGenerator class
  - Implement generate_project() as main orchestration method
  - Implement create_directory_structure() for folder creation
  - Implement generate_source_files() using template engine
  - Implement generate_config_files() for .env, pyproject.toml, etc.
  - Implement generate_documentation() for README
  - Implement copy_static_assets() for optional static files
  - Add progress feedback using OutputFormatter
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.2_

- [ ]* 8.1 Write property test for project structure completeness
  - **Property 2: Project structure completeness**
  - **Validates: Requirements 5.1, 5.3, 5.4, 5.5**

- [ ]* 8.2 Write property test for development tools inclusion
  - **Property 4: Development tools inclusion**
  - **Validates: Requirements 6.5**

- [ ]* 8.3 Write unit tests for file generation
  - Test directory creation with various configurations
  - Test file writing with different content types
  - Test handling of existing directories
  - _Requirements: 5.1, 8.1_

- [x] 9. Implement CLI list command
  - Create list command in main.py
  - Display formatted table of database options using Rich
  - Include descriptions for SQLite, MongoDB, PostgreSQL
  - _Requirements: 10.1_

- [ ] 10. Implement CLI info command
  - Create info command in main.py with database_type argument
  - Implement logic to fetch database configuration details
  - Display requirements, features, and dependencies
  - Handle missing database type argument
  - Handle invalid database type with suggestions
  - _Requirements: 10.2, 10.4, 10.5_

- [ ]* 10.1 Write property test for database info command completeness
  - **Property 7: Database info command completeness**
  - **Validates: Requirements 10.2**

- [ ]* 10.2 Write property test for invalid database type suggestion
  - **Property 8: Invalid database type suggestion**
  - **Validates: Requirements 10.5**

- [x] 11. Implement CLI create command
  - Create create command in main.py
  - Wire together ProjectPrompts to collect user input
  - Wire together ProjectValidator to validate inputs
  - Build ProjectConfig from validated inputs
  - Call ProjectGenerator to create project
  - Display welcome message, progress, and success/error messages
  - Handle cancellation gracefully without creating files
  - _Requirements: 2.1, 2.5, 7.1, 7.2, 7.3, 7.4, 8.4, 8.5_

- [ ]* 11.1 Write integration tests for create command
  - Test end-to-end project generation with various configurations
  - Test cancellation at confirmation prompt
  - Test error handling for invalid inputs
  - Use Click's CliRunner for testing
  - _Requirements: 2.5, 8.5_

- [ ] 12. Implement CLI main entry point
  - Create main.py with cli() group function
  - Register create, list, and info commands
  - Add --version option to display version
  - Add --help option with comprehensive usage information
  - Initialize Rich Console for all output
  - _Requirements: 1.2, 1.3, 1.4_

- [ ]* 12.1 Write unit tests for CLI commands
  - Test --version displays correct version
  - Test --help displays all commands
  - Test command registration and routing
  - _Requirements: 1.3, 1.4_

- [ ] 13. Create package distribution files
  - Finalize pyproject.toml with all metadata (name, version, description, author, classifiers)
  - Create/update MANIFEST.in to include all template files
  - Create setup.py if needed for backward compatibility
  - Ensure console_scripts entry point is properly configured
  - Create comprehensive README.md with installation and usage instructions
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 13.1 Write installation tests
  - Test package installation in clean virtual environment
  - Test fastapi-crud command is available globally
  - Test command works from any directory
  - _Requirements: 1.1, 1.2, 9.3_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
