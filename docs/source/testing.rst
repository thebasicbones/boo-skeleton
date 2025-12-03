Testing
=======

This document describes the testing strategy and how to run tests.

Test Structure
--------------

The test suite is organized in the ``tests/`` directory:

.. code-block:: text

   tests/
   ├── conftest.py                    # Pytest fixtures and configuration
   ├── strategies.py                  # Hypothesis strategies for property tests
   ├── test_api_endpoints.py          # API endpoint integration tests
   ├── test_database_factory.py       # Database factory tests
   ├── test_database_models.py        # Database model tests
   ├── test_resource_repository.py    # Repository unit tests
   ├── test_resource_service.py       # Service unit tests
   ├── test_schemas.py                # Schema validation tests
   ├── test_topological_sort_service.py  # Topological sort tests
   └── test_property_*.py             # Property-based tests

Test Types
----------

Unit Tests
~~~~~~~~~~

Unit tests verify individual components in isolation:

* **Repository tests**: Database operations
* **Service tests**: Business logic
* **Schema tests**: Validation rules
* **Topological sort tests**: Dependency ordering

Integration Tests
~~~~~~~~~~~~~~~~~

Integration tests verify components working together:

* **API endpoint tests**: Full request/response cycle
* **Database factory tests**: Repository creation

Property-Based Tests
~~~~~~~~~~~~~~~~~~~~

Property-based tests use Hypothesis to verify properties across many generated inputs:

* **CRUD roundtrip**: Create, read, update operations preserve data
* **Cascade delete**: Deleting with cascade removes all dependents
* **Topological ordering**: Search results maintain dependency order
* **Validation**: Invalid data is properly rejected
* **Error handling**: Errors produce consistent responses

Running Tests
-------------

Run All Tests
~~~~~~~~~~~~~

.. code-block:: bash

   pytest

Run with Coverage
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest --cov=app --cov-report=html --cov-report=term

This generates:

* Terminal coverage report
* HTML coverage report in ``htmlcov/``
* XML coverage report for CI/CD

Run Specific Test File
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/test_resource_service.py

Run Specific Test
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/test_resource_service.py::test_create_resource

Run Property Tests Only
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/test_property_*.py

Run with Verbose Output
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest -v

Test Configuration
------------------

Pytest Configuration
~~~~~~~~~~~~~~~~~~~~

Configuration is in ``pytest.ini``:

.. code-block:: ini

   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts =
       -v
       --strict-markers
       --tb=short
       --cov=app
       --cov-report=term-missing
       --cov-report=html

Coverage Configuration
~~~~~~~~~~~~~~~~~~~~~~

Configuration is in ``.coveragerc``:

.. code-block:: ini

   [run]
   source = app
   omit =
       */tests/*
       */venv/*
       */__pycache__/*

   [report]
   precision = 2
   show_missing = True

Test Fixtures
-------------

Common fixtures are defined in ``tests/conftest.py``:

Database Fixtures
~~~~~~~~~~~~~~~~~

* ``sqlite_db`` - SQLite database session
* ``mongodb_db`` - MongoDB database instance
* ``db`` - Parametrized fixture for both databases

Service Fixtures
~~~~~~~~~~~~~~~~

* ``resource_service`` - ResourceService instance
* ``topo_service`` - TopologicalSortService instance

Data Fixtures
~~~~~~~~~~~~~

* ``sample_resource`` - Sample resource data
* ``sample_resources`` - Multiple sample resources

Writing Tests
-------------

Unit Test Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def test_create_resource(resource_service):
       """Test creating a resource."""
       data = ResourceCreate(
           name="Test Resource",
           description="Test description",
           dependencies=[]
       )

       result = await resource_service.create_resource(data)

       assert result.name == "Test Resource"
       assert result.description == "Test description"
       assert result.dependencies == []

Property Test Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hypothesis import given
   from tests.strategies import resource_create_strategy

   @given(resource_create_strategy())
   async def test_create_roundtrip(resource_service, resource_data):
       """Property: Created resources can be retrieved."""
       created = await resource_service.create_resource(resource_data)
       retrieved = await resource_service.get_resource(created.id)

       assert retrieved.name == created.name
       assert retrieved.description == created.description

Best Practices
--------------

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Test names should describe what they verify
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Reuse common setup code
5. **Test Edge Cases**: Include boundary conditions
6. **Property Tests**: Use Hypothesis for comprehensive coverage
7. **Async Tests**: Use ``async def`` for async code
8. **Mock Sparingly**: Prefer real implementations when possible

Continuous Integration
----------------------

Tests run automatically on:

* Every push to any branch
* Every pull request
* Multiple Python versions (3.10, 3.11, 3.12)

CI configuration is in ``.github/workflows/ci.yml``.

Coverage Requirements
---------------------

* Minimum coverage: 80%
* Coverage reports uploaded to Codecov
* Pull requests show coverage diff
* Failing coverage fails the build
