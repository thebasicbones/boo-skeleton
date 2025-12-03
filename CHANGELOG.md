# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- VERSION file for semantic versioning
- CHANGELOG.md for tracking project changes
- Pull request template with changelog reminder

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [1.0.0] - 2024-12-04

### Added
- Comprehensive DevOps tooling infrastructure
- Pre-commit hooks for automated code quality checks (Black, Ruff, MyPy)
- GitHub Actions CI/CD workflows for testing and linting
- Code coverage reporting with Codecov integration
- Sphinx documentation system with Read the Docs theme
- Multi-environment configuration support (development, staging, production)
- Dependency management with pip-tools and Dependabot
- MongoDB integration as alternative database backend
- Dual database backend support (SQLite and MongoDB)
- Database factory pattern for backend abstraction
- MongoDB migration script with validation
- Comprehensive property-based testing with Hypothesis
- API documentation with FastAPI's built-in Swagger/ReDoc
- Developer documentation (CONTRIBUTING.md, testing guides)
- Status badges in README for CI/CD and coverage

### Changed
- Improved error handling with custom exception classes
- Enhanced API error responses with consistent format
- Updated test suite with 100+ property-based tests
- Refactored database layer for backend abstraction
- Improved documentation structure and completeness

## [0.2.0] - 2024-11-15

### Added
- MongoDB backend implementation
- MongoDB connection lifecycle management
- MongoDB repository implementation
- Migration script for SQLite to MongoDB
- MongoDB-specific property-based tests
- MongoDB setup documentation
- Docker Compose configuration for MongoDB

### Changed
- Database abstraction layer to support multiple backends
- Configuration system to support MongoDB settings
- Test suite to support both SQLite and MongoDB

### Fixed
- Connection handling for MongoDB
- Async operations in MongoDB repository
- Test isolation for MongoDB tests

## [0.1.0] - 2024-10-01

### Added
- Initial FastAPI CRUD backend implementation
- RESTful API endpoints for resource management
- Topological sorting for dependency management
- SQLite database backend with SQLAlchemy
- Resource creation, retrieval, update, and deletion
- Cascade delete functionality
- Circular dependency detection
- Search functionality with topological ordering
- Basic test suite with pytest
- API documentation with Swagger/ReDoc
- Health check endpoint
- Static web interface for resource management
- Error handling and custom exceptions
- Repository pattern for data access
- Service layer for business logic
- Pydantic schemas for data validation

### Security
- Input validation for all API endpoints
- SQL injection prevention through SQLAlchemy ORM
- Dependency validation to prevent circular references

[Unreleased]: https://github.com/yourusername/fastapi-crud-backend/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/fastapi-crud-backend/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/yourusername/fastapi-crud-backend/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/fastapi-crud-backend/releases/tag/v0.1.0
