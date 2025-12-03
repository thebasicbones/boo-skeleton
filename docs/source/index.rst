FastAPI CRUD Backend Documentation
===================================

Welcome to the FastAPI CRUD Backend documentation. This project provides a RESTful API
for managing resources with dependency tracking and topological sorting capabilities.

Features
--------

* **Dual Database Support**: Works with both SQLite (via SQLAlchemy) and MongoDB
* **Dependency Management**: Track dependencies between resources with circular dependency detection
* **Topological Sorting**: Automatically order resources based on their dependencies
* **RESTful API**: Full CRUD operations with FastAPI
* **Type Safety**: Comprehensive type hints and Pydantic validation
* **Async/Await**: Fully asynchronous database operations

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Clone the repository
   git clone <repository-url>
   cd fastapi-crud-backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate

   # Install dependencies
   pip install -r requirements.txt

   # Copy environment file
   cp .env.example .env

Running the Application
~~~~~~~~~~~~~~~~~~~~~~~

**With SQLite (default):**

.. code-block:: bash

   python main.py

**With MongoDB:**

.. code-block:: bash

   # Start MongoDB server
   python start_mongodb_server.py

   # In another terminal, run the application
   python main.py

The API will be available at http://localhost:8000

API Documentation
~~~~~~~~~~~~~~~~~

Once the application is running, you can access:

* **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
* **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/routers
   api/services
   api/repositories
   api/schemas
   api/exceptions

.. toctree::
   :maxdepth: 2
   :caption: Additional Information

   architecture
   testing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
