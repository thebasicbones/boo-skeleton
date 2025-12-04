---
inclusion: always
---

# Development Workflow

## Getting Started

### Initial Setup

1. **Clone and Navigate**
   ```bash
   cd fastapi-crud-backend
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Daily Development Workflow

### 1. Start Development Session

```bash
# Activate virtual environment
source venv/bin/activate

# Pull latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt
```

### 2. Start Development Server

```bash
# Option 1: Using the startup script
./run.sh

# Option 2: Using Python directly
python main.py

# Option 3: Using Uvicorn with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Make Changes

Follow the architecture patterns:
- Add/modify schemas in `app/schemas.py`
- Update repository interfaces in `app/repositories/base.py`
- Implement in both SQLite and MongoDB repositories
- Add business logic in services
- Create/update API endpoints in routers

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_resource_service.py -v

# Run tests matching pattern
pytest -k "crud" -v

# Run only property tests
pytest tests/test_property_*.py -v
```

### 5. Check Code Quality

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or run individually:
black .                    # Format code
ruff check . --fix        # Lint and auto-fix
mypy app/                 # Type check
```

### 6. Commit Changes

```bash
# Stage changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "feat: add new feature"

# If hooks fail, fix issues and commit again
```

## Testing Workflow

### Running Tests

```bash
# Quick test run
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report

# Run specific test categories
pytest tests/test_api_endpoints.py -v        # API tests
pytest tests/test_resource_service.py -v     # Service tests
pytest tests/test_property_*.py -v           # Property tests
```

### Writing Tests

#### Unit Test Example
```python
# tests/test_resource_service.py
async def test_create_resource_with_valid_data():
    """Test creating a resource with valid data."""
    data = ResourceCreate(
        name="Test Resource",
        description="Test description",
        dependencies=[]
    )
    result = await service.create_resource(data)
    assert result.name == "Test Resource"
```

#### Property Test Example
```python
# tests/test_property_crud_roundtrip.py
from hypothesis import given
from tests.strategies import resource_strategy

@given(resource_data=resource_strategy())
async def test_resource_creation_roundtrip(resource_data):
    """Property: Created resources can be retrieved with same data."""
    created = await service.create_resource(resource_data)
    retrieved = await service.get_resource(created.id)
    assert created.name == retrieved.name
```

### Test-Driven Development (TDD)

1. **Write failing test** - Define expected behavior
2. **Run test** - Verify it fails
3. **Implement feature** - Write minimal code to pass
4. **Run test** - Verify it passes
5. **Refactor** - Improve code while keeping tests green

## Database Workflow

### SQLite (Default)

```bash
# Database file is created automatically
# Location: ./app.db

# View database
sqlite3 app.db
.tables
.schema resources
SELECT * FROM resources;
.quit
```

### MongoDB

```bash
# Start MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Or start local MongoDB (macOS)
brew services start mongodb-community

# Connect with mongosh
mongosh
use fastapi_crud
db.resources.find()
exit
```

### Switching Databases

Edit `.env`:
```bash
# For SQLite
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./app.db

# For MongoDB
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud
```

Restart the application after changing database type.

### Migration Between Databases

```bash
# Export SQLite to JSON
python scripts/migrate_sqlite_to_mongodb.py \
  --export-only \
  --output backup.json

# Import JSON to MongoDB
python scripts/migrate_sqlite_to_mongodb.py \
  --import-only \
  --input backup.json \
  --clear-existing
```

## Debugging

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Debug Tests

```bash
# Run tests with debugger on failure
pytest --pdb

# Run tests with print output
pytest -s

# Run specific test with verbose output
pytest tests/test_resource_service.py::test_create_resource -vv -s
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# In code
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

View logs:
```bash
# Console output (stdout)
# File output: app.log
tail -f app.log
```

## Git Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/add-new-endpoint

# Make changes and commit
git add .
git commit -m "feat: add new endpoint"

# Push to remote
git push origin feature/add-new-endpoint

# Create pull request on GitHub
```

### Commit Message Convention

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat: add cascade delete functionality"
git commit -m "fix: resolve circular dependency detection bug"
git commit -m "docs: update API documentation"
git commit -m "test: add property tests for update operations"
```

## Code Review Checklist

Before submitting a pull request:

- [ ] All tests pass (`pytest`)
- [ ] Code coverage maintained or improved
- [ ] Pre-commit hooks pass
- [ ] Type hints added for new functions
- [ ] Docstrings added for public functions
- [ ] Error handling implemented
- [ ] Logging added for important operations
- [ ] API documentation updated (if applicable)
- [ ] README updated (if applicable)
- [ ] No sensitive data in commits

## Troubleshooting

### Common Issues

**Issue: Pre-commit hooks fail**
```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

**Issue: Tests fail with database errors**
```bash
# Clear test database
rm -f test_app.db

# Restart MongoDB
docker restart mongodb

# Check database connection
python -c "from config.settings import get_settings; print(get_settings().database_url)"
```

**Issue: Import errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check virtual environment
which python
python --version
```

**Issue: Port already in use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

## Performance Profiling

### Profile API Endpoints

```python
import cProfile
import pstats

# Profile a function
profiler = cProfile.Profile()
profiler.enable()
# ... code to profile
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Monitor Database Queries

```python
# Enable SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Documentation

### Update API Documentation

API documentation is auto-generated from:
- Docstrings in router functions
- Pydantic schema examples
- FastAPI metadata

View at: http://localhost:8000/docs

### Update README

When adding features:
1. Update feature list
2. Add usage examples
3. Update API endpoint documentation
4. Add troubleshooting tips if needed

### Generate Sphinx Documentation

```bash
cd docs
make html
open build/html/index.html
```
