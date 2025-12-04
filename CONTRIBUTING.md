# Contributing to FastAPI CRUD Backend

Thank you for your interest in contributing to this project! This guide will help you get started with development and understand our workflows.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Testing](#testing)
- [Dependency Management](#dependency-management)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)
- [Getting Help](#getting-help)

## Development Setup

### Prerequisites

- Python 3.10, 3.11, or 3.12
- Git
- MongoDB (for integration tests)

### Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fastapi-crud-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Copy the environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

## Code Quality Standards

We use several tools to maintain code quality:

### Code Formatting

We use **Black** for code formatting with a line length of 100 characters:

```bash
# Format all Python files
black .

# Check formatting without making changes
black --check .
```

### Linting

We use **Ruff** for fast linting:

```bash
# Run linter
ruff check .

# Run linter with auto-fix
ruff check --fix .
```

### Type Checking

We use **MyPy** for static type checking:

```bash
# Run type checker
mypy app/
```

### Pre-commit Hooks

Pre-commit hooks automatically run these checks before each commit. If any check fails, the commit will be blocked until you fix the issues.

To run all pre-commit hooks manually:

```bash
pre-commit run --all-files
```

## Testing

### Running Tests

Run the full test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html --cov-report=xml
```

View coverage report:

```bash
# Open htmlcov/index.html in your browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Writing Tests

- Write unit tests for all new functionality
- Write property-based tests for universal properties using Hypothesis
- Ensure tests are deterministic and don't depend on external services
- Aim for high code coverage (>80%)

## Dependency Management

We use a structured approach to dependency management with pip-tools and automated updates via Dependabot.

### Dependency Files

- **requirements.in**: Unpinned production dependencies
- **requirements.txt**: Pinned production dependencies (generated)
- **requirements-dev.in**: Unpinned development dependencies
- **requirements-dev.txt**: Pinned development dependencies (generated)

### Adding New Dependencies

#### Production Dependencies

1. Add the package to `requirements.in` (without version pin):
   ```
   # requirements.in
   new-package
   ```

2. Compile the requirements file:
   ```bash
   pip-compile requirements.in
   ```

3. Install the new dependency:
   ```bash
   pip install -r requirements.txt
   ```

4. Commit both `requirements.in` and `requirements.txt`:
   ```bash
   git add requirements.in requirements.txt
   git commit -m "deps: add new-package"
   ```

#### Development Dependencies

1. Add the package to `requirements-dev.in` (without version pin):
   ```
   # requirements-dev.in
   new-dev-package
   ```

2. Compile the requirements file:
   ```bash
   pip-compile requirements-dev.in
   ```

3. Install the new dependency:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Commit both `requirements-dev.in` and `requirements-dev.txt`:
   ```bash
   git add requirements-dev.in requirements-dev.txt
   git commit -m "deps: add new-dev-package"
   ```

### Updating Dependencies

#### Update All Dependencies

To update all dependencies to their latest compatible versions:

```bash
# Update production dependencies
pip-compile --upgrade requirements.in

# Update development dependencies
pip-compile --upgrade requirements-dev.in

# Install updated dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests to ensure compatibility
pytest
```

#### Update Specific Dependency

To update a specific package:

```bash
# Update a specific production dependency
pip-compile --upgrade-package package-name requirements.in

# Update a specific development dependency
pip-compile --upgrade-package package-name requirements-dev.in
```

### Security Scanning

We use **safety** to check for known security vulnerabilities:

```bash
# Check for vulnerabilities in installed packages
safety check

# Check requirements file
safety check -r requirements.txt
```

Run security checks regularly and address any vulnerabilities promptly.

### Automated Dependency Updates

We use **Dependabot** to automatically create pull requests for dependency updates:

- Dependabot runs weekly on Mondays at 9:00 AM
- It creates PRs for outdated dependencies
- Patch updates are grouped together to reduce PR noise
- Major version updates for core dependencies (FastAPI, SQLAlchemy, Pydantic) are ignored by default

#### Reviewing Dependabot PRs

1. Check the PR description for changelog and breaking changes
2. Review the CI test results
3. If tests pass and changes look safe, approve and merge
4. If tests fail, investigate the failure and update code if needed
5. For major version updates, review migration guides and test thoroughly

### Dependency Update Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Dependency Update Flow                    │
└─────────────────────────────────────────────────────────────┘

1. Add dependency to .in file (unpinned)
   ↓
2. Run pip-compile to generate .txt file (pinned)
   ↓
3. Install from .txt file
   ↓
4. Run tests to verify compatibility
   ↓
5. Commit both .in and .txt files
   ↓
6. Dependabot monitors for updates weekly
   ↓
7. Review and merge Dependabot PRs
```

## Documentation

### Building Documentation

We use Sphinx for documentation:

```bash
cd docs
make html
```

View the documentation:

```bash
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux
start build/html/index.html  # Windows
```

### Writing Documentation

- Add docstrings to all public functions, classes, and modules
- Use Google-style docstrings
- Update relevant .rst files in `docs/source/` when adding new features
- Include code examples where appropriate

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**:
   ```bash
   # Format code
   black .

   # Run linter
   ruff check --fix .

   # Run type checker
   mypy app/

   # Run tests
   pytest --cov=app
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `deps:` for dependency updates
   - `ci:` for CI/CD changes

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure all CI checks pass
   - Request review from maintainers

7. **Address review feedback**:
   - Make requested changes
   - Push additional commits
   - Re-request review when ready

8. **Merge**:
   - Once approved, a maintainer will merge your PR
   - Delete your feature branch after merging

## Code Review Guidelines

When reviewing pull requests:

- Check that code follows style guidelines
- Verify tests are comprehensive and passing
- Ensure documentation is updated
- Look for potential bugs or edge cases
- Provide constructive feedback
- Approve when satisfied with the changes

## Release Process

We follow semantic versioning and maintain a detailed changelog for all releases.

### Semantic Versioning

Version numbers follow the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incompatible API changes or breaking changes
- **MINOR**: New functionality in a backwards-compatible manner
- **PATCH**: Backwards-compatible bug fixes

Examples:
- `1.0.0` → `1.0.1`: Bug fix (patch)
- `1.0.1` → `1.1.0`: New feature (minor)
- `1.1.0` → `2.0.0`: Breaking change (major)

### Changelog Management

All changes must be documented in `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format.

#### During Development

When making changes, add entries to the `[Unreleased]` section under the appropriate category:

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

Example:

```markdown
## [Unreleased]

### Added
- New endpoint for batch resource creation
- Support for resource tagging

### Fixed
- Circular dependency detection for complex graphs
- Memory leak in topological sort algorithm
```

#### Creating a Release

1. **Prepare the release**:
   ```bash
   # Ensure you're on the main branch and up to date
   git checkout main
   git pull origin main
   ```

2. **Update VERSION file**:
   ```bash
   # Edit VERSION file with new version number
   echo "1.1.0" > VERSION
   ```

3. **Update CHANGELOG.md**:
   - Move all `[Unreleased]` entries to a new version section
   - Add the release date
   - Update comparison links at the bottom

   Example:
   ```markdown
   ## [Unreleased]

   ### Added

   ### Changed

   ## [1.1.0] - 2024-12-15

   ### Added
   - New endpoint for batch resource creation
   - Support for resource tagging

   ### Fixed
   - Circular dependency detection for complex graphs
   ```

4. **Commit version changes**:
   ```bash
   git add VERSION CHANGELOG.md
   git commit -m "chore: release version 1.1.0"
   ```

5. **Create and push tag**:
   ```bash
   # Create annotated tag
   git tag -a v1.1.0 -m "Release version 1.1.0"

   # Push commit and tag
   git push origin main
   git push origin v1.1.0
   ```

6. **Create GitHub Release**:
   - Go to the repository's Releases page
   - Click "Draft a new release"
   - Select the tag you just created (v1.1.0)
   - Title: "Version 1.1.0"
   - Description: Copy the relevant section from CHANGELOG.md
   - Click "Publish release"

7. **Verify the release**:
   - Check that CI/CD workflows complete successfully
   - Verify the release appears on GitHub
   - Test the release in a clean environment

### Release Checklist

Before creating a release, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Code coverage is acceptable (`pytest --cov=app`)
- [ ] All pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Documentation is up to date (`cd docs && make html`)
- [ ] VERSION file is updated
- [ ] CHANGELOG.md is updated with all changes
- [ ] No uncommitted changes
- [ ] All CI/CD checks pass on main branch

### Hotfix Releases

For urgent bug fixes:

1. Create a hotfix branch from the release tag:
   ```bash
   git checkout -b hotfix/1.0.1 v1.0.0
   ```

2. Make the fix and commit:
   ```bash
   git commit -m "fix: critical bug description"
   ```

3. Update VERSION and CHANGELOG.md:
   ```bash
   echo "1.0.1" > VERSION
   # Update CHANGELOG.md with fix details
   git add VERSION CHANGELOG.md
   git commit -m "chore: release version 1.0.1"
   ```

4. Merge to main and tag:
   ```bash
   git checkout main
   git merge hotfix/1.0.1
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin main
   git push origin v1.0.1
   ```

5. Create GitHub release as described above

### Release Automation

The project includes a GitHub Actions workflow (`.github/workflows/release.yml`) that automates the release process:

- Triggers on version tag pushes (v*.*.*)
- Validates version format and consistency
- Runs full test suite on multiple Python versions
- Builds Sphinx documentation
- Extracts changelog entries for the version
- Creates GitHub release with release notes and documentation archive

To use the automated workflow:

```bash
# After updating VERSION and CHANGELOG.md
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

The workflow will handle the rest automatically.

For detailed information about the release workflow, testing, and troubleshooting, see [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md).

### Version History

All releases are documented in:
- `CHANGELOG.md`: Detailed change history
- `VERSION`: Current version number
- GitHub Releases: Release notes and artifacts
- Git tags: Version markers in repository history

## Troubleshooting

This section covers common issues you might encounter during development and their solutions.

### Pre-commit Hook Issues

#### Hooks Not Running

**Problem:** Pre-commit hooks don't run when you commit.

**Solution:**
```bash
# Reinstall hooks
pre-commit install

# Verify installation
pre-commit run --all-files
```

#### Hook Installation Fails

**Problem:** `pre-commit install` fails with permission errors.

**Solution:**
```bash
# Ensure you're in the project root
cd /path/to/fastapi-crud-backend

# Check git is initialized
git status

# Try installing with verbose output
pre-commit install -v
```

#### Black Formatting Conflicts

**Problem:** Black reformats code differently than expected.

**Solution:**
- Black is opinionated and deterministic
- Accept Black's formatting to maintain consistency
- If you must exclude a file, add it to `pyproject.toml`:
  ```toml
  [tool.black]
  extend-exclude = '''
  /(
    specific_file\.py
  )/
  '''
  ```

#### MyPy Type Errors

**Problem:** MyPy reports type errors in your code.

**Solution:**
```bash
# Run MyPy to see all errors
mypy app/

# Common fixes:
# 1. Add type annotations
def my_function(param: str) -> int:
    return len(param)

# 2. Use Optional for nullable values
from typing import Optional
def get_user(id: str) -> Optional[User]:
    return user_or_none

# 3. Ignore specific lines (use sparingly)
result = some_untyped_library()  # type: ignore
```

### Testing Issues

#### Tests Fail Locally But Pass in CI

**Problem:** Tests pass in CI but fail on your machine (or vice versa).

**Solution:**
```bash
# Ensure clean test environment
pytest --cache-clear

# Check for leftover test data
rm -f test.db app.db

# Verify Python version matches CI
python --version

# Run tests with same settings as CI
pytest --cov=app --cov-report=xml
```

#### MongoDB Tests Skipped

**Problem:** MongoDB tests are being skipped with "MongoDB not available".

**Solution:**
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# Start MongoDB if not running
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Docker
docker start mongodb
# or
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Verify connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').server_info())"
```

#### Hypothesis Generates Failing Examples

**Problem:** Property-based tests fail with specific counterexamples.

**Solution:**
1. **Examine the counterexample** - Hypothesis shows the minimal failing case
2. **Determine if it's a bug** - Is the behavior correct for this input?
3. **Fix the code or test**:
   - If it's a bug: Fix the implementation
   - If it's invalid input: Update the strategy to exclude it
   - If it's expected behavior: Update the test assertion

```python
# Example: Excluding invalid inputs
from hypothesis import given, assume
from tests.strategies import resource_create_strategy

@given(resource_data=resource_create_strategy())
async def test_create(resource_data):
    # Skip invalid cases
    assume(len(resource_data.name) > 0)
    # Test continues...
```

#### Test Database Pollution

**Problem:** Tests fail due to data from previous test runs.

**Solution:**
```bash
# Clean all test databases
rm -f test.db app.db

# For MongoDB, tests use unique databases
# But you can manually clean if needed
mongosh --eval "db.getMongo().getDBNames().forEach(function(name) {
  if (name.startsWith('test_')) db.getSiblingDB(name).dropDatabase();
})"

# Run tests with fresh fixtures
pytest --cache-clear
```

### Dependency Issues

#### Dependency Installation Fails

**Problem:** `pip install -r requirements.txt` fails.

**Solution:**
```bash
# Update pip first
pip install --upgrade pip

# Try installing with verbose output
pip install -v -r requirements.txt

# If specific package fails, try installing it separately
pip install problematic-package

# Check for conflicting packages
pip check

# As last resort, recreate virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Dependency Conflicts

**Problem:** pip reports dependency conflicts.

**Solution:**
```bash
# Check for conflicts
pip check

# View dependency tree
pip install pipdeptree
pipdeptree

# Recompile requirements with latest compatible versions
pip-compile --upgrade requirements.in
pip-compile --upgrade requirements-dev.in

# Install fresh
pip install -r requirements.txt -r requirements-dev.txt
```

#### Safety Reports Vulnerabilities

**Problem:** `safety check` reports security vulnerabilities.

**Solution:**
```bash
# View detailed vulnerability report
safety check --full-report

# Update specific vulnerable package
pip-compile --upgrade-package vulnerable-package requirements.in

# If no fix available, check if it affects your usage
# Document the decision to accept the risk (if appropriate)
# Or find an alternative package
```

### Database Issues

#### SQLite Database Locked

**Problem:** "database is locked" error.

**Solution:**
```bash
# Stop all running instances of the application
pkill -f "python main.py"

# Remove lock file
rm -f app.db-journal

# If problem persists, recreate database
rm app.db
python scripts/init_db.py
```

#### MongoDB Connection Refused

**Problem:** "Connection refused" when connecting to MongoDB.

**Solution:**
```bash
# Check if MongoDB is running
mongosh

# Check MongoDB status
# macOS
brew services list | grep mongodb

# Linux
sudo systemctl status mongod

# Check if port is in use
lsof -i :27017
# or
netstat -an | grep 27017

# Check connection string format
# Correct: mongodb://localhost:27017
# Incorrect: mongodb://localhost:27017/
```

#### MongoDB Authentication Failed

**Problem:** "Authentication failed" error.

**Solution:**
```bash
# Verify credentials in .env file
cat .env | grep MONGODB

# Test connection with mongosh
mongosh "mongodb://username:password@localhost:27017/admin"

# Check authentication database
# Default is 'admin', but might be different
MONGODB_AUTH_SOURCE=admin  # or your auth database
```

### Documentation Issues

#### Sphinx Build Fails

**Problem:** `make html` fails with errors.

**Solution:**
```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Clean previous builds
cd docs
make clean

# Build with verbose output
sphinx-build -v source build/html

# Common issues:
# 1. Missing docstrings - Add them to your code
# 2. Import errors - Ensure all dependencies installed
# 3. Syntax errors in .rst files - Check RST syntax
```

#### Missing API Documentation

**Problem:** API endpoints don't appear in generated docs.

**Solution:**
1. **Add docstrings** to your endpoint functions:
   ```python
   @router.get("/resources")
   async def list_resources():
       """
       List all resources.

       Returns:
           List of all resources in the system.
       """
       pass
   ```

2. **Rebuild documentation:**
   ```bash
   cd docs
   make clean
   make html
   ```

### Environment Configuration Issues

#### Settings Not Loading

**Problem:** Application doesn't load settings from .env file.

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check file format (no spaces around =)
# Correct: DATABASE_TYPE=sqlite
# Incorrect: DATABASE_TYPE = sqlite

# Verify environment variable names
cat .env

# Test settings loading
python -c "from config.settings import get_settings; print(get_settings())"
```

#### Wrong Environment Loaded

**Problem:** Application loads wrong environment configuration.

**Solution:**
```bash
# Check ENVIRONMENT variable
echo $ENVIRONMENT

# Explicitly set environment
export ENVIRONMENT=development

# Or use specific .env file
cp .env.development .env

# Verify loaded settings
python -c "from config.settings import get_settings; s = get_settings(); print(f'Environment: {s.environment}')"
```

### Git and Version Control Issues

#### Large Files Blocked

**Problem:** Pre-commit hook blocks commit due to large files.

**Solution:**
```bash
# Check file sizes
git ls-files | xargs ls -lh | sort -k5 -h

# Remove large files from staging
git reset HEAD large_file.bin

# Add to .gitignore if it shouldn't be tracked
echo "large_file.bin" >> .gitignore

# If you must commit large files, use Git LFS
git lfs install
git lfs track "*.bin"
```

#### Merge Conflicts in Generated Files

**Problem:** Merge conflicts in requirements.txt or other generated files.

**Solution:**
```bash
# For requirements.txt conflicts:
# 1. Accept one version
git checkout --theirs requirements.txt

# 2. Recompile from .in file
pip-compile requirements.in

# 3. Commit the result
git add requirements.txt
git commit -m "Resolve requirements.txt conflict"
```

### Performance Issues

#### Tests Run Slowly

**Problem:** Test suite takes too long to run.

**Solution:**
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Run only fast tests
pytest -m "not slow"

# Skip property tests during development
pytest -m "not property"

# Use faster database for tests
# SQLite in-memory is faster than MongoDB for tests
```

#### Application Starts Slowly

**Problem:** Application takes long time to start.

**Solution:**
```bash
# Check for slow imports
python -X importtime main.py 2>&1 | grep "import time"

# Disable auto-reload in production
API_RELOAD=false python main.py

# Use production ASGI server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### CI/CD Issues

#### GitHub Actions Failing

**Problem:** CI pipeline fails but tests pass locally.

**Solution:**
1. **Check Python version** - CI might use different version
2. **Check environment variables** - CI needs secrets configured
3. **Check service dependencies** - MongoDB service might not be ready
4. **Review CI logs** - Look for specific error messages

```yaml
# Add debugging to workflow
- name: Debug environment
  run: |
    python --version
    pip list
    env | sort
```

#### Coverage Threshold Not Met

**Problem:** CI fails due to insufficient code coverage.

**Solution:**
```bash
# Check current coverage
pytest --cov=app --cov-report=term-missing

# Identify uncovered lines
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Add tests for uncovered code
# Or adjust threshold in .coveragerc if appropriate
```

### Common Error Messages

#### "ModuleNotFoundError: No module named 'app'"

**Solution:**
```bash
# Ensure you're in project root
pwd

# Reinstall in development mode
pip install -e .

# Or add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### "RuntimeError: Event loop is closed"

**Solution:**
```python
# Use pytest-asyncio properly
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

#### "CircularDependencyError" in Tests

**Solution:**
```python
# When creating test data, ensure no circular dependencies
# Bad:
resource_a = await repo.create({"name": "A", "dependencies": ["B"]})
resource_b = await repo.create({"name": "B", "dependencies": ["A"]})

# Good:
resource_a = await repo.create({"name": "A", "dependencies": []})
resource_b = await repo.create({"name": "B", "dependencies": [resource_a.id]})
```

### Getting More Help

If you're still stuck after trying these solutions:

1. **Check existing issues** - Someone might have encountered the same problem
2. **Search the documentation** - Check README, docs/, and other .md files
3. **Enable debug logging** - Set `LOG_LEVEL=DEBUG` in your .env file
4. **Create a minimal reproduction** - Isolate the problem
5. **Open an issue** - Provide:
   - Python version (`python --version`)
   - Operating system
   - Steps to reproduce
   - Full error message
   - What you've already tried

## Getting Help

If you have questions or need help:

- Check the [Troubleshooting](#troubleshooting) section above
- Search existing issues for similar problems
- Review the documentation in `docs/` and `README.md`
- Open an issue for bugs or feature requests
- Be respectful and constructive in all interactions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
