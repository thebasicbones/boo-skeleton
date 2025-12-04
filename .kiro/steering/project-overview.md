---
inclusion: always
---

# FastAPI CRUD Backend - Project Overview

## Project Description

This is a RESTful API backend built with FastAPI that provides CRUD operations with topological sorting capabilities for managing resources with dependencies. The system supports both SQLite and MongoDB as database backends.

## Core Features

- RESTful API with FastAPI framework
- Topological sorting for dependency management
- Dual database backend support (SQLite and MongoDB)
- Resource dependency tracking and validation
- Circular dependency detection
- Cascade delete functionality
- Comprehensive test suite with property-based testing

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with ASGI
- **Databases**: SQLite (SQLAlchemy) and MongoDB (Motor)
- **Validation**: Pydantic 2.5.0
- **Testing**: Pytest, Hypothesis (property-based testing)
- **Documentation**: Sphinx with RTD theme
- **Code Quality**: Black, Ruff, MyPy, pre-commit hooks

## Architecture Pattern

The project follows a **layered architecture**:

1. **Routers** (`app/routers/`) - API endpoints and request handling
2. **Services** (`app/services/`) - Business logic and orchestration
3. **Repositories** (`app/repositories/`) - Data access layer with abstract interfaces
4. **Models** (`app/models/`) - Database models (SQLAlchemy)
5. **Schemas** (`app/schemas.py`) - Pydantic models for validation

## Key Design Principles

- **Repository Pattern**: Abstract data access to support multiple database backends
- **Dependency Injection**: FastAPI's dependency system for database sessions
- **Type Safety**: Full type hints with MyPy validation
- **Separation of Concerns**: Clear boundaries between layers
- **Error Handling**: Custom exceptions with consistent error responses
- **Testing**: Property-based testing for comprehensive coverage

## Database Backends

### SQLite (Default)
- File-based database using SQLAlchemy ORM
- Ideal for development and small deployments
- Connection: `sqlite+aiosqlite:///./app.db`

### MongoDB
- Document-based NoSQL database using Motor (async driver)
- Recommended for production and scalability
- Connection: `mongodb://localhost:27017` or MongoDB Atlas

## Environment Configuration

Configuration is managed through `.env` files and Pydantic Settings:
- `DATABASE_TYPE`: `sqlite` or `mongodb`
- `DATABASE_URL`: Connection string
- `MONGODB_DATABASE`: Database name (for MongoDB)
- `ENVIRONMENT`: `development`, `staging`, or `production`

## Current Version

Version 1.0.0 - See VERSION file and CHANGELOG.md for details
