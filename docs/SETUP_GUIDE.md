# Developer Setup Guide

This guide will walk you through setting up the FastAPI CRUD Backend development environment from scratch.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10, 3.11, or 3.12** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads/)
- **MongoDB** (optional, for MongoDB backend) - [Installation Guide](../MONGODB_SETUP.md)

### Verify Prerequisites

```bash
# Check Python version (should be 3.10+)
python --version
# or
python3 --version

# Check Git
git --version

# Check MongoDB (optional)
mongosh --version
```

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fastapi-crud-backend.git

# Navigate to the project directory
cd fastapi-crud-backend
```

## Step 2: Create Virtual Environment

A virtual environment isolates project dependencies from your system Python.

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

**Tip:** To deactivate the virtual environment later, simply run `deactivate`.

## Step 3: Install Dependencies

### Production Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt
```

This installs:
- FastAPI - Web framework
- Uvicorn - ASGI server
- SQLAlchemy - ORM for SQLite
- Motor/PyMongo - MongoDB drivers
- Pydantic - Data validation
- And more...

### Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

This installs:
- pytest - Testing framework
- Hypothesis - Property-based testing
- Black - Code formatter
- Ruff - Linter
- MyPy - Type checker
- pre-commit - Git hooks
- pytest-cov - Coverage reporting
- Sphinx - Documentation generator
- And more...

### Verify Installation

```bash
# Check installed packages
pip list

# Verify key packages
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import pytest; print(f'pytest: {pytest.__version__}')"
```

## Step 4: Configure Environment

### Create Environment File

```bash
# Copy example environment file
cp .env.example .env
```

### Edit Environment File

Open `.env` in your editor and configure:

```bash
# Database Configuration
DATABASE_TYPE=sqlite  # or mongodb
DATABASE_URL=sqlite:///./app.db  # or mongodb://localhost:27017

# For MongoDB (if using)
MONGODB_DATABASE=fastapi_crud
# MONGODB_USERNAME=your_username
# MONGODB_PASSWORD=your_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=development
```

### Environment Options

**SQLite (Default - Recommended for Development):**
```bash
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./app.db
```

**MongoDB (Recommended for Production):**
```bash
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud
```

## Step 5: Install Pre-commit Hooks

Pre-commit hooks automatically check your code before each commit.

```bash
# Install pre-commit hooks
pre-commit install

# Verify installation
pre-commit run --all-files
```

This will:
- Format code with Black
- Lint code with Ruff
- Type check with MyPy
- Check for common issues

**First run may take a few minutes** as it downloads and installs hook environments.

## Step 6: Verify Setup

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

**Expected output:**
```
================================ test session starts =================================
platform darwin -- Python 3.11.x, pytest-7.x.x, pluggy-1.x.x
collected 50 items

tests/test_api_endpoints.py ................                                   [ 32%]
tests/test_resource_service.py ........                                        [ 48%]
tests/test_property_crud_roundtrip.py ....                                     [ 56%]
...

================================ 50 passed in 5.23s ==================================
```

### Start the Application

```bash
# Start development server
python main.py
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Test the API

Open your browser or use curl:

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
start http://localhost:8000/docs  # Windows

# Create a test resource
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Resource", "description": "Testing setup", "dependencies": []}'

# List resources
curl http://localhost:8000/api/resources
```

## Step 7: Build Documentation (Optional)

```bash
# Navigate to docs directory
cd docs

# Build HTML documentation
make html

# View documentation
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux
start build/html/index.html  # Windows

# Return to project root
cd ..
```

## Step 8: Configure Your IDE

### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

Install recommended extensions:
- Python
- Pylance
- Black Formatter
- Ruff

### PyCharm

1. **Set Python Interpreter:**
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Existing Environment
   - Select `venv/bin/python`

2. **Configure Black:**
   - File → Settings → Tools → Black
   - Enable "On code reformat"
   - Enable "On save"

3. **Configure Ruff:**
   - File → Settings → Tools → External Tools
   - Add Ruff as external tool

4. **Enable Type Checking:**
   - File → Settings → Editor → Inspections
   - Enable "Type checker" inspections

## Common Setup Issues

### Issue: Python version mismatch

**Problem:** `python --version` shows Python 2.x or wrong version

**Solution:**
```bash
# Use python3 explicitly
python3 --version
python3 -m venv venv

# Or create alias in ~/.bashrc or ~/.zshrc
alias python=python3
```

### Issue: pip install fails

**Problem:** Permission errors or package conflicts

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # You should see (venv) in prompt

# Upgrade pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Try installing again
pip install -r requirements.txt
```

### Issue: Pre-commit hooks fail

**Problem:** Hooks fail on first run

**Solution:**
```bash
# This is normal on first run - hooks are being installed
# Let them complete, then run again
pre-commit run --all-files

# If specific hook fails, run it individually
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

### Issue: MongoDB connection fails

**Problem:** Can't connect to MongoDB

**Solution:**
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# Start MongoDB
# macOS:
brew services start mongodb-community

# Linux:
sudo systemctl start mongod

# Docker:
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Or use SQLite instead (no MongoDB needed)
# Edit .env:
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./app.db
```

### Issue: Tests fail

**Problem:** Tests fail on first run

**Solution:**
```bash
# Clear test cache
pytest --cache-clear

# Remove test databases
rm -f test.db app.db

# Ensure MongoDB is running (if using MongoDB tests)
mongosh --eval "db.version()"

# Run tests again
pytest -v
```

### Issue: Port already in use

**Problem:** "Address already in use" error

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
# Edit .env:
API_PORT=8001
```

## Next Steps

Now that your environment is set up:

1. **Read the documentation:**
   - [README.md](../README.md) - Project overview
   - [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
   - [API Documentation](http://localhost:8000/docs) - Interactive API docs

2. **Explore the codebase:**
   - `app/` - Application code
   - `tests/` - Test suite
   - `docs/` - Documentation

3. **Try making changes:**
   - Create a feature branch: `git checkout -b feature/my-feature`
   - Make changes to the code
   - Run tests: `pytest`
   - Commit: `git commit -m "feat: my feature"` (hooks run automatically)

4. **Learn the development workflow:**
   - Read [CONTRIBUTING.md](../CONTRIBUTING.md)
   - Review [docs/RELEASE_PROCESS.md](RELEASE_PROCESS.md)
   - Check out example PRs in the repository

## Development Workflow Summary

```bash
# Daily workflow
source venv/bin/activate  # Activate environment
git checkout -b feature/my-feature  # Create feature branch
# ... make changes ...
pytest  # Run tests
git add .  # Stage changes
git commit -m "feat: description"  # Commit (hooks run automatically)
git push origin feature/my-feature  # Push to remote
# ... create pull request on GitHub ...
```

## Getting Help

If you encounter issues:

1. Check [Troubleshooting](../README.md#troubleshooting) section
2. Review [CONTRIBUTING.md](../CONTRIBUTING.md) troubleshooting
3. Search existing GitHub issues
4. Ask in project discussions
5. Create a new issue with:
   - Python version
   - Operating system
   - Steps to reproduce
   - Error messages
   - What you've tried

## Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [MongoDB Documentation](https://docs.mongodb.com/)

## Quick Reference Card

```bash
# Environment
source venv/bin/activate          # Activate venv
deactivate                        # Deactivate venv

# Running
python main.py                    # Start server
python main.py --reload           # Start with auto-reload

# Testing
pytest                            # Run all tests
pytest -v                         # Verbose output
pytest --cov=app                  # With coverage
pytest -k "test_name"             # Run specific test

# Code Quality
black .                           # Format code
ruff check .                      # Lint code
ruff check --fix .                # Lint and fix
mypy app/                         # Type check
pre-commit run --all-files        # Run all hooks

# Documentation
cd docs && make html              # Build docs
open docs/build/html/index.html   # View docs

# Dependencies
pip install -r requirements.txt   # Install deps
pip-compile requirements.in       # Update deps
safety check                      # Security scan

# Git
git checkout -b feature/name      # New branch
git add .                         # Stage changes
git commit -m "type: message"     # Commit
git push origin feature/name      # Push branch
```

Happy coding! 🚀
