# Quick Reference Guide

A cheat sheet for common development tasks and commands.

## Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate              # macOS/Linux
venv\Scripts\activate                 # Windows

# Deactivate virtual environment
deactivate

# Install dependencies
pip install -r requirements.txt       # Production
pip install -r requirements-dev.txt   # Development

# Install pre-commit hooks
pre-commit install
```

## Running the Application

```bash
# Start development server
python main.py

# Start with specific environment
ENVIRONMENT=development python main.py
ENVIRONMENT=staging python main.py
ENVIRONMENT=production python main.py

# Start with custom port
API_PORT=8001 python main.py

# Start with Uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start with Gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Code Quality

### Formatting

```bash
# Format all files
black .

# Check formatting without changes
black --check .

# Format specific file/directory
black app/services/
black app/services/resource_service.py

# Show what would be changed
black --diff .
```

### Linting

```bash
# Lint all files
ruff check .

# Lint with auto-fix
ruff check --fix .

# Lint specific directory
ruff check app/

# Show all errors (not just first)
ruff check --show-source .

# Lint with statistics
ruff check --statistics .
```

### Type Checking

```bash
# Type check application
mypy app/

# Type check with verbose output
mypy --verbose app/

# Type check specific file
mypy app/services/resource_service.py

# Type check and show error codes
mypy --show-error-codes app/

# Type check with coverage report
mypy --html-report mypy-report app/
```

### Pre-commit Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run all hooks on staged files
pre-commit run

# Run specific hook
pre-commit run black
pre-commit run ruff
pre-commit run mypy
pre-commit run trailing-whitespace

# Update hooks to latest versions
pre-commit autoupdate

# Reinstall hooks
pre-commit uninstall
pre-commit install

# Skip hooks for one commit (not recommended)
git commit --no-verify -m "message"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with extra verbose output
pytest -vv

# Run specific test file
pytest tests/test_resource_service.py

# Run specific test function
pytest tests/test_resource_service.py::test_create_resource

# Run tests matching pattern
pytest -k "crud"
pytest -k "property"
pytest -k "not mongodb"

# Run tests with markers
pytest -m "not slow"
pytest -m "property"

# Run in parallel (faster)
pytest -n auto  # requires pytest-xdist

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Coverage

```bash
# Run tests with coverage
pytest --cov=app

# Coverage with HTML report
pytest --cov=app --cov-report=html

# Coverage with XML report (for CI)
pytest --cov=app --cov-report=xml

# Coverage with terminal report
pytest --cov=app --cov-report=term

# Coverage showing missing lines
pytest --cov=app --cov-report=term-missing

# Coverage with minimum threshold
pytest --cov=app --cov-fail-under=80

# View HTML coverage report
open htmlcov/index.html              # macOS
xdg-open htmlcov/index.html          # Linux
start htmlcov/index.html             # Windows
```

### Test Debugging

```bash
# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error
pytest --pdbcls=IPython.terminal.debugger:Pdb

# Clear test cache
pytest --cache-clear

# Show available fixtures
pytest --fixtures

# Show test collection without running
pytest --collect-only
```

## Documentation

### Building Documentation

```bash
# Build HTML documentation
cd docs
make html

# Build with clean slate
make clean
make html

# Build PDF documentation
make latexpdf

# Build with verbose output
sphinx-build -v source build/html

# Build and watch for changes
sphinx-autobuild source build/html

# Check for broken links
make linkcheck
```

### Viewing Documentation

```bash
# Open HTML documentation
open build/html/index.html           # macOS
xdg-open build/html/index.html       # Linux
start build/html/index.html          # Windows

# Serve documentation locally
cd build/html
python -m http.server 8080
# Visit http://localhost:8080
```

## Dependency Management

### Adding Dependencies

```bash
# Add production dependency
echo "new-package" >> requirements.in
pip-compile requirements.in
pip install -r requirements.txt

# Add development dependency
echo "new-dev-package" >> requirements-dev.in
pip-compile requirements-dev.in
pip install -r requirements-dev.txt
```

### Updating Dependencies

```bash
# Update all production dependencies
pip-compile --upgrade requirements.in

# Update all development dependencies
pip-compile --upgrade requirements-dev.in

# Update specific package
pip-compile --upgrade-package fastapi requirements.in

# Install updated dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Sync environment with requirements
pip-sync requirements.txt requirements-dev.txt
```

### Security Scanning

```bash
# Check for vulnerabilities
safety check

# Check requirements file
safety check -r requirements.txt

# Full report with details
safety check --full-report

# Check and output JSON
safety check --json

# Ignore specific vulnerabilities
safety check --ignore 12345
```

## Database Operations

### SQLite

```bash
# Initialize database
python scripts/init_db.py

# View database
sqlite3 app.db
# In SQLite shell:
.tables                              # List tables
.schema resources                    # Show table schema
SELECT * FROM resources;             # Query data
.quit                                # Exit

# Backup database
cp app.db app.db.backup

# Remove database
rm app.db
```

### MongoDB

```bash
# Start MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod            # Linux
docker start mongodb                   # Docker

# Stop MongoDB
brew services stop mongodb-community   # macOS
sudo systemctl stop mongod             # Linux
docker stop mongodb                    # Docker

# Connect to MongoDB
mongosh
mongosh mongodb://localhost:27017

# MongoDB shell commands
show dbs                               # List databases
use fastapi_crud                       # Switch database
show collections                       # List collections
db.resources.find()                    # Query documents
db.resources.countDocuments()          # Count documents
db.resources.deleteMany({})            # Delete all documents
exit                                   # Exit shell

# Backup MongoDB
mongodump --db fastapi_crud --out backup/

# Restore MongoDB
mongorestore --db fastapi_crud backup/fastapi_crud/

# Export to JSON
mongoexport --db fastapi_crud --collection resources --out resources.json

# Import from JSON
mongoimport --db fastapi_crud --collection resources --file resources.json
```

### Migration

```bash
# Migrate SQLite to MongoDB
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing

# Export SQLite data
python scripts/migrate_sqlite_to_mongodb.py \
  --export-only \
  --output backup.json

# Import to MongoDB
python scripts/migrate_sqlite_to_mongodb.py \
  --import-only \
  --input backup.json \
  --clear-existing
```

## Git Workflows

### Feature Development

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/my-feature

# Update from main
git checkout main
git pull origin main
git checkout feature/my-feature
git rebase main

# Squash commits
git rebase -i HEAD~3
```

### Commit Message Format

```bash
# Format: <type>: <description>

# Types:
feat: new feature
fix: bug fix
docs: documentation changes
test: test additions/changes
refactor: code refactoring
style: formatting changes
chore: maintenance tasks
ci: CI/CD changes
perf: performance improvements
deps: dependency updates

# Examples:
git commit -m "feat: add cascade delete functionality"
git commit -m "fix: resolve circular dependency detection"
git commit -m "docs: update API documentation"
git commit -m "test: add property tests for CRUD operations"
```

### Release Process

```bash
# Update version
echo "1.1.0" > VERSION

# Update changelog
# Edit CHANGELOG.md

# Commit version bump
git add VERSION CHANGELOG.md
git commit -m "chore: release version 1.1.0"

# Create tag
git tag -a v1.1.0 -m "Release version 1.1.0"

# Push changes and tag
git push origin main
git push origin v1.1.0
```

## API Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/

# Create resource
curl -X POST http://localhost:8000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "Testing", "dependencies": []}'

# List resources
curl http://localhost:8000/api/resources

# Get specific resource
curl http://localhost:8000/api/resources/{id}

# Update resource
curl -X PUT http://localhost:8000/api/resources/{id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated", "description": "Updated description"}'

# Delete resource
curl -X DELETE http://localhost:8000/api/resources/{id}

# Delete with cascade
curl -X DELETE "http://localhost:8000/api/resources/{id}?cascade=true"

# Search resources
curl "http://localhost:8000/api/search?q=test"
```

### Using HTTPie

```bash
# Install HTTPie
pip install httpie

# Health check
http GET http://localhost:8000/health

# Create resource
http POST http://localhost:8000/api/resources \
  name="Test" \
  description="Testing" \
  dependencies:='[]'

# List resources
http GET http://localhost:8000/api/resources

# Update resource
http PUT http://localhost:8000/api/resources/{id} \
  name="Updated" \
  description="Updated description"

# Delete resource
http DELETE http://localhost:8000/api/resources/{id}
```

## Environment Variables

### Common Variables

```bash
# Database
export DATABASE_TYPE=sqlite
export DATABASE_URL=sqlite:///./app.db
export MONGODB_DATABASE=fastapi_crud

# API
export API_HOST=0.0.0.0
export API_PORT=8000
export DEBUG=true

# Logging
export LOG_LEVEL=DEBUG

# Environment
export ENVIRONMENT=development

# Testing
export MONGODB_DATABASE=test_db
```

### Loading Environment Files

```bash
# Load from specific file
export $(cat .env.development | xargs)

# Load with dotenv
python -c "from dotenv import load_dotenv; load_dotenv('.env.development')"

# Use in command
env $(cat .env.development | xargs) python main.py
```

## CI/CD

### GitHub Actions

```bash
# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# Watch current run
gh run watch

# Re-run failed jobs
gh run rerun <run-id>

# Download artifacts
gh run download <run-id>
```

### Local CI Testing

```bash
# Install act
brew install act  # macOS
# or download from https://github.com/nektos/act

# List workflows
act -l

# Run CI workflow
act -j test

# Run lint workflow
act -j lint

# Run with secrets
act -j test -s GITHUB_TOKEN=<token>

# Dry run
act -n
```

## Troubleshooting

### Clear Caches

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clear pytest cache
pytest --cache-clear
rm -rf .pytest_cache

# Clear mypy cache
rm -rf .mypy_cache

# Clear coverage data
rm -f .coverage
rm -rf htmlcov

# Clear all caches
make clean  # if Makefile exists
```

### Reset Environment

```bash
# Deactivate and remove venv
deactivate
rm -rf venv

# Recreate venv
python3 -m venv venv
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Reinstall pre-commit hooks
pre-commit uninstall
pre-commit install
```

### Check System Status

```bash
# Python version
python --version

# Pip version
pip --version

# Installed packages
pip list

# Package dependencies
pip show fastapi

# Check for conflicts
pip check

# Virtual environment location
which python

# Environment variables
env | grep -i python
env | grep -i database

# Port usage
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Process list
ps aux | grep python
ps aux | grep mongod
```

## Performance

### Profiling

```bash
# Profile application
python -m cProfile -o profile.stats main.py

# View profile results
python -m pstats profile.stats
# In pstats shell:
sort cumulative
stats 20

# Profile with line_profiler
pip install line_profiler
kernprof -l -v script.py

# Memory profiling
pip install memory_profiler
python -m memory_profiler script.py
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost:8000

# Run headless
locust -f tests/load_test.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 1m \
  --headless
```

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Project aliases
alias venv-activate='source venv/bin/activate'
alias venv-deactivate='deactivate'

# Testing aliases
alias test='pytest'
alias test-cov='pytest --cov=app --cov-report=html'
alias test-fast='pytest -x'

# Code quality aliases
alias format='black . && ruff check --fix .'
alias lint='ruff check .'
alias typecheck='mypy app/'
alias quality='black . && ruff check --fix . && mypy app/'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph --decorate'

# Application aliases
alias run='python main.py'
alias run-dev='ENVIRONMENT=development python main.py'
alias run-test='ENVIRONMENT=test python main.py'
```

## Keyboard Shortcuts

### Terminal

- `Ctrl+C` - Stop running process
- `Ctrl+Z` - Suspend process
- `Ctrl+D` - Exit shell/EOF
- `Ctrl+L` - Clear screen
- `Ctrl+R` - Search command history
- `Ctrl+A` - Move to line start
- `Ctrl+E` - Move to line end

### Pytest

- `Ctrl+C` - Stop test run
- `q` - Quit on failure (with `-x`)

### Python Debugger (pdb)

- `n` - Next line
- `s` - Step into
- `c` - Continue
- `l` - List code
- `p <var>` - Print variable
- `q` - Quit debugger

## Additional Resources

- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [RELEASE_PROCESS.md](RELEASE_PROCESS.md) - Release procedures
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
