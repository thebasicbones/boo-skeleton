Architecture
============

This document describes the architecture and design patterns used in the FastAPI CRUD Backend.

Overview
--------

The application follows a layered architecture pattern with clear separation of concerns:

.. code-block:: text

   ┌─────────────────────────────────────┐
   │         API Layer (Routers)         │
   │    FastAPI endpoints & validation   │
   └─────────────────────────────────────┘
                    │
                    ▼
   ┌─────────────────────────────────────┐
   │      Service Layer (Services)       │
   │   Business logic & orchestration    │
   └─────────────────────────────────────┘
                    │
                    ▼
   ┌─────────────────────────────────────┐
   │   Repository Layer (Repositories)   │
   │    Database abstraction & queries   │
   └─────────────────────────────────────┘
                    │
                    ▼
   ┌─────────────────────────────────────┐
   │         Database Layer              │
   │    SQLite (SQLAlchemy) / MongoDB    │
   └─────────────────────────────────────┘

Layers
------

API Layer (Routers)
~~~~~~~~~~~~~~~~~~~

The API layer handles HTTP requests and responses using FastAPI. It is responsible for:

* Request validation using Pydantic schemas
* Response serialization
* HTTP status codes and error responses
* OpenAPI documentation generation

**Key files:**

* ``app/routers/resources.py`` - Resource CRUD endpoints

Service Layer
~~~~~~~~~~~~~

The service layer contains business logic and orchestrates operations between routers and repositories. It is responsible for:

* Dependency validation and circular dependency detection
* Topological sorting of resources
* Cross-cutting concerns like logging
* Coordinating multiple repository operations

**Key files:**

* ``app/services/resource_service.py`` - Resource business logic
* ``app/services/topological_sort_service.py`` - Dependency ordering

Repository Layer
~~~~~~~~~~~~~~~~

The repository layer provides database abstraction, allowing the application to work with different database backends. It is responsible for:

* Database queries and operations
* Data transformation between database and application formats
* Connection management
* Transaction handling

**Key files:**

* ``app/repositories/base_resource_repository.py`` - Abstract interface
* ``app/repositories/sqlalchemy_resource_repository.py`` - SQLite implementation
* ``app/repositories/mongodb_resource_repository.py`` - MongoDB implementation

Design Patterns
---------------

Repository Pattern
~~~~~~~~~~~~~~~~~~

The repository pattern abstracts database operations behind a common interface. This allows:

* Switching between SQLite and MongoDB without changing business logic
* Easy testing with mock repositories
* Consistent API across different storage backends

Factory Pattern
~~~~~~~~~~~~~~~

The database factory (``app/database_factory.py``) creates the appropriate repository based on configuration:

.. code-block:: python

   def get_repository(db):
       if isinstance(db, AsyncSession):
           return SQLAlchemyResourceRepository(db)
       else:
           return MongoDBResourceRepository(db)

Dependency Injection
~~~~~~~~~~~~~~~~~~~~

FastAPI's dependency injection system is used throughout:

.. code-block:: python

   @router.get("/resources")
   async def list_resources(
       db: AsyncSession | AsyncIOMotorDatabase = Depends(get_db)
   ):
       service = ResourceService(db)
       return await service.get_all_resources()

Data Flow
---------

Create Resource Example
~~~~~~~~~~~~~~~~~~~~~~~

1. Client sends POST request to ``/api/resources``
2. FastAPI validates request body against ``ResourceCreate`` schema
3. Router calls ``ResourceService.create_resource()``
4. Service validates dependencies and checks for circular dependencies
5. Service calls repository's ``create()`` method
6. Repository inserts data into database
7. Repository returns created resource
8. Service converts to ``ResourceResponse`` schema
9. Router returns response with 201 status code

Search with Topological Sort
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Client sends GET request to ``/api/search?q=frontend``
2. Router calls ``ResourceService.search_resources()``
3. Service calls repository's ``search()`` method
4. Repository queries database for matching resources
5. Service calls ``TopologicalSortService.topological_sort()``
6. Topological sort orders resources by dependencies
7. Service converts to list of ``ResourceResponse`` schemas
8. Router returns ordered results

Error Handling
--------------

The application uses custom exceptions for different error scenarios:

* ``ResourceNotFoundError`` - Resource doesn't exist (404)
* ``ValidationError`` - Invalid data or circular dependency (422)
* ``CircularDependencyError`` - Circular dependency detected (422)
* ``DatabaseConnectionError`` - Database connection failed (500)
* ``DatabaseTimeoutError`` - Database operation timed out (500)

These exceptions are caught by error handlers in ``app/error_handlers.py`` and converted to appropriate HTTP responses.

Database Backends
-----------------

SQLite (SQLAlchemy)
~~~~~~~~~~~~~~~~~~~

* Uses SQLAlchemy ORM with async support
* Stores data in ``app.db`` file
* Many-to-many relationship for dependencies
* Automatic cascade delete support

MongoDB
~~~~~~~

* Uses Motor (async MongoDB driver)
* Stores data in ``resources`` collection
* Dependencies stored as array of IDs
* Manual cascade delete implementation

Both backends provide identical functionality through the repository interface.
