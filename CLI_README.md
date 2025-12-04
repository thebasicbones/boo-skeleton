# FastAPI CRUD CLI

A powerful command-line scaffolding tool for generating production-ready FastAPI CRUD backend projects with support for multiple database backends (SQLite, MongoDB, PostgreSQL).

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

✨ **Interactive CLI** - Beautiful, user-friendly prompts with colors and formatting  
🗄️ **Multiple Databases** - Support for SQLite, MongoDB, and PostgreSQL  
🎨 **Rich Terminal UI** - Colorful output with progress indicators and tables  
📦 **Complete Projects** - Generates fully functional FastAPI applications  
🔧 **Customizable** - Configure project metadata, dependencies, and optional features  
✅ **Production Ready** - Includes tests, documentation, and best practices  
🚀 **Automated Setup** - Automatically creates virtual environment and installs dependencies  
⚙️ **Environment Configuration** - Collects and saves all environment variables to .env  

## Installation

Install via pip:

```bash
pip install fastapi-crud-cli
```

Verify installation:

```bash
fastapi-crud --version
```

## Quick Start

Create a new FastAPI project in 3 simple steps:

### 1. Run the create command

```bash
fastapi-crud create
```

### 2. Answer the interactive prompts

The CLI will guide you through configuration:

- **Project name**: Choose a name for your project
- **Database type**: Select SQLite, MongoDB, or PostgreSQL
- **Database configuration**: Provide connection details
- **Environment settings**: Configure environment type, API host/port, CORS, etc.
- **Project metadata**: Author name, email, description
- **Optional features**: Examples, development tools, static files

### 3. Start your new project

```bash
cd my-fastapi-project
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

Your API is now running at `http://localhost:8000`! 🎉

**Note:** The CLI automatically:
- ✓ Creates a virtual environment
- ✓ Installs all dependencies
- ✓ Configures your `.env` file with the settings you provided

## What's New: Automated Setup

The `fastapi-crud create` command now handles the complete project setup automatically:

### Automatic Virtual Environment Creation

No need to manually create a virtual environment. The CLI creates it for you in the project directory.

### Automatic Dependency Installation

All required dependencies from `requirements.txt` are automatically installed in the virtual environment.

### Environment Variable Collection

The CLI now prompts for all necessary environment variables and saves them directly to your `.env` file:

- **Environment Type**: Development, Staging, or Production
- **API Host**: Server host address (default: 0.0.0.0)
- **API Port**: Server port (default: 8000)
- **Debug Mode**: Enable/disable debug mode
- **CORS Origins**: Allowed CORS origins for your API
- **Database Settings**: All database-specific configuration

### What This Means For You

Instead of following 6 manual steps after generation, you can now:

1. Run `fastapi-crud create`
2. Answer the prompts
3. Navigate to your project: `cd my-project`
4. Activate the environment: `source venv/bin/activate`
5. Start coding: `python main.py`

## Usage

### Create a New Project

```bash
fastapi-crud create
```

This launches an interactive wizard that guides you through project configuration.

### List Available Database Options

```bash
fastapi-crud list
```

Displays a formatted table of supported database backends with descriptions.

### Get Database Information

```bash
fastapi-crud info mongodb
fastapi-crud info sqlite
fastapi-crud info postgresql
```

Shows detailed information about a specific database backend including requirements and features.

### Display Version

```bash
fastapi-crud --version
```

### Show Help

```bash
fastapi-crud --help
fastapi-crud create --help
```

## Generated Project Structure

The CLI generates a complete, production-ready project:

```
my-fastapi-project/
├── app/
│   ├── __init__.py
│   ├── models/              # Database models
│   ├── repositories/        # Data access layer
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── database_factory.py  # Database backend selection
│   ├── database_*.py        # Database connections
│   ├── exceptions.py        # Custom exceptions
│   ├── error_handlers.py    # Error handling
│   └── schemas.py           # Pydantic models
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   └── test_*.py            # Test suite
├── venv/                    # Virtual environment (auto-created)
├── static/                  # Frontend files (optional)
├── scripts/                 # Utility scripts (optional)
├── .env                     # Environment variables (auto-configured)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata
├── README.md                # Project documentation
└── main.py                  # Application entry point
```

## Database Support

### SQLite (Default)

Perfect for development and small deployments:

```bash
# During project creation, select: SQLite
# No additional configuration needed
```

**Features:**
- Zero configuration
- File-based database
- Ideal for development
- No separate server required

### MongoDB

Recommended for production and scalability:

```bash
# During project creation, select: MongoDB
# Provide connection URL and database name
```

**Features:**
- NoSQL document database
- Horizontal scalability
- Flexible schema
- Cloud-ready (MongoDB Atlas)

**Connection Examples:**
- Local: `mongodb://localhost:27017`
- Atlas: `mongodb+srv://user:pass@cluster.mongodb.net/`

### PostgreSQL

Enterprise-grade relational database:

```bash
# During project creation, select: PostgreSQL
# Provide host, port, database, username, password
```

**Features:**
- ACID compliance
- Advanced SQL features
- Strong data integrity
- Production-proven

## Environment Configuration

The CLI now collects all environment variables during project creation:

### Application Settings

- **ENVIRONMENT**: `development`, `staging`, or `production`
- **DEBUG**: Enable/disable debug mode
- **API_HOST**: Server host address
- **API_PORT**: Server port number
- **CORS_ORIGINS**: Comma-separated list of allowed origins

### Database Settings

**SQLite:**
- `DATABASE_TYPE=sqlite`
- `DATABASE_URL=sqlite+aiosqlite:///./app.db`

**MongoDB:**
- `DATABASE_TYPE=mongodb`
- `MONGODB_URL=mongodb://localhost:27017`
- `MONGODB_DATABASE=your_database_name`

**PostgreSQL:**
- `DATABASE_TYPE=postgresql`
- `DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname`

All these settings are automatically saved to your `.env` file based on your responses during project creation.

## Generated Project Features

Every generated project includes:

### Core Features

- ✅ RESTful API with FastAPI
- ✅ CRUD operations for resources
- ✅ Topological sorting for dependencies
- ✅ Automatic API documentation (Swagger/ReDoc)
- ✅ Pydantic validation
- ✅ Custom error handling
- ✅ Environment-based configuration

### Architecture

- 🏗️ Layered architecture (Routers → Services → Repositories)
- 🔌 Repository pattern for database abstraction
- 💉 Dependency injection
- 🎯 Type hints throughout
- 📦 Modular design

### Testing (Optional)

- 🧪 Pytest test suite
- 🔄 Property-based testing with Hypothesis
- 📊 Code coverage reporting
- 🎭 Test fixtures and utilities

### Development Tools (Optional)

- 🎨 Black code formatter
- 🔍 Ruff linter
- 📝 MyPy type checker
- 🪝 Pre-commit hooks
- 📚 Comprehensive documentation

## Example: Creating a MongoDB Project

```bash
$ fastapi-crud create

🚀 FastAPI CRUD Project Generator

❯ Project name: my-api-project
❯ Database type: MongoDB
❯ MongoDB connection URL: mongodb://localhost:27017
❯ Database name: my_api_db

Environment Configuration
❯ Select environment: development
❯ API host: 0.0.0.0
❯ API port: 8000
❯ CORS allowed origins: http://localhost:3000,http://localhost:8000

❯ Author name: John Doe
❯ Author email: john@example.com
❯ Project description: My awesome API
❯ Include example scripts? Yes
❯ Include development tools? Yes
❯ Include static files? Yes

📋 Configuration Summary:
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting           ┃ Value                        ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Project Name      │ my-api-project               │
│ Database          │ MongoDB                      │
│ Environment       │ development                  │
│ Author            │ John Doe                     │
│ Dev Tools         │ Yes                          │
└───────────────────┴──────────────────────────────┘

❯ Generate project with this configuration? Yes

⋯ Creating project structure...
⋯ Generating source files...
⋯ Creating configuration files...
✓ Project 'my-api-project' created successfully!

⋯ Setting up virtual environment...
✓ Virtual environment created
⋯ Installing dependencies (this may take a moment)...
✓ Dependencies installed successfully

Next Steps:

1. Navigate to your project:
   cd my-api-project

2. Activate the virtual environment:
   source venv/bin/activate

3. Review your environment configuration:
   cat .env

4. Run the development server:
   python main.py

5. Visit the API documentation:
   http://localhost:8000/docs

✓ Virtual environment created
✓ Dependencies installed
✓ Environment variables configured

Happy coding! 🚀
```

## Requirements

- Python 3.10 or higher
- pip (Python package installer)

## Dependencies

The CLI tool uses:

- **Click** - Command-line interface framework
- **Rich** - Terminal formatting and colors
- **Jinja2** - Template rendering engine
- **Pydantic** - Data validation
- **Questionary** - Interactive prompts

Generated projects include:

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Database drivers** - SQLAlchemy, Motor, or asyncpg (based on selection)

## Troubleshooting

### Command not found after installation

```bash
# Ensure pip install location is in PATH
python -m pip install --user fastapi-crud-cli

# Or use pipx for isolated installation
pipx install fastapi-crud-cli
```

### Virtual environment creation fails

If automatic virtual environment creation fails, you can create it manually:

```bash
cd my-project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependency installation fails

If automatic dependency installation fails, install manually:

```bash
cd my-project
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Permission errors during generation

```bash
# Ensure you have write permissions in the target directory
# Or run from a directory where you have write access
cd ~/projects
fastapi-crud create
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Links

- **Documentation**: [GitHub README](https://github.com/yourusername/fastapi-crud-cli#readme)
- **Source Code**: [GitHub Repository](https://github.com/yourusername/fastapi-crud-cli)
- **Issue Tracker**: [GitHub Issues](https://github.com/yourusername/fastapi-crud-cli/issues)
- **Changelog**: [CHANGELOG.md](https://github.com/yourusername/fastapi-crud-cli/blob/main/CHANGELOG.md)

## Support

If you encounter any issues or have questions:

1. Check the [documentation](https://github.com/yourusername/fastapi-crud-cli#readme)
2. Search [existing issues](https://github.com/yourusername/fastapi-crud-cli/issues)
3. Create a [new issue](https://github.com/yourusername/fastapi-crud-cli/issues/new)

## Acknowledgments

Built with ❤️ using FastAPI, Click, and Rich.

---

**Happy coding!** 🚀
