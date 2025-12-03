# Contributing to FastAPI CRUD Backend

Thank you for your interest in contributing to this project! This guide will help you get started with development and understand our workflows.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Testing](#testing)
- [Dependency Management](#dependency-management)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

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

## Getting Help

If you have questions or need help:

- Open an issue for bugs or feature requests
- Check existing issues and documentation first
- Be respectful and constructive in all interactions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
