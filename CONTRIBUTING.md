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

The project includes a GitHub Actions workflow (`.github/workflows/release.yml`) that automates parts of the release process:

- Triggers on version tag pushes (v*.*.*)
- Runs full test suite
- Builds documentation
- Creates GitHub release with changelog

To use the automated workflow:

```bash
# After updating VERSION and CHANGELOG.md
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

The workflow will handle the rest automatically.

### Version History

All releases are documented in:
- `CHANGELOG.md`: Detailed change history
- `VERSION`: Current version number
- GitHub Releases: Release notes and artifacts
- Git tags: Version markers in repository history

## Getting Help

If you have questions or need help:

- Open an issue for bugs or feature requests
- Check existing issues and documentation first
- Be respectful and constructive in all interactions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
