# Publishing Guide

This guide explains how to build and publish the FastAPI CRUD CLI package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing)

2. **API Tokens**: Generate API tokens for authentication:
   - PyPI: Account Settings → API tokens → Add API token
   - TestPyPI: Account Settings → API tokens → Add API token

3. **Build Tools**: Install required packages:
   ```bash
   pip install build twine
   ```

## Pre-Publishing Checklist

Before publishing, ensure:

- [ ] Version number updated in `fastapi_crud_cli/__version__.py`
- [ ] CHANGELOG.md updated with release notes
- [ ] All tests passing (`pytest`)
- [ ] Documentation up to date
- [ ] CLI_README.md reviewed and accurate
- [ ] pyproject.toml metadata complete
- [ ] MANIFEST.in includes all necessary files
- [ ] No sensitive information in code or config files

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info
```

### 2. Build Distribution Files

```bash
# Build source distribution and wheel
python -m build
```

This creates:
- `dist/fastapi_crud_cli-X.Y.Z.tar.gz` (source distribution)
- `dist/fastapi_crud_cli-X.Y.Z-py3-none-any.whl` (wheel)

### 3. Verify Build Contents

```bash
# List contents of the wheel
unzip -l dist/fastapi_crud_cli-*.whl

# List contents of the source distribution
tar -tzf dist/fastapi_crud_cli-*.tar.gz
```

Verify that:
- All template files are included
- CLI module files are present
- No test files or development artifacts included
- YAML configuration files included

## Testing the Package

### 1. Test Installation Locally

```bash
# Create a test virtual environment
python -m venv test-env
source test-env/bin/activate

# Install the built wheel
pip install dist/fastapi_crud_cli-*.whl

# Test the CLI
fastapi-crud --version
fastapi-crud list
fastapi-crud info sqlite

# Test project generation
mkdir test-project
cd test-project
fastapi-crud create
# Follow prompts and verify project generation

# Clean up
deactivate
cd ..
rm -rf test-env test-project
```

### 2. Upload to TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

### 3. Test Installation from TestPyPI

```bash
# Create a fresh virtual environment
python -m venv testpypi-env
source testpypi-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    fastapi-crud-cli

# Test the installation
fastapi-crud --version
fastapi-crud list

# Clean up
deactivate
rm -rf testpypi-env
```

## Publishing to PyPI

### 1. Final Verification

```bash
# Run all tests
pytest

# Check package with twine
python -m twine check dist/*
```

### 2. Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

### 3. Verify Publication

Visit your package page:
- https://pypi.org/project/fastapi-crud-cli/

Check:
- Package metadata displays correctly
- README renders properly
- All classifiers are correct
- Links work

### 4. Test Installation from PyPI

```bash
# Create a fresh virtual environment
python -m venv pypi-test-env
source pypi-test-env/bin/activate

# Install from PyPI
pip install fastapi-crud-cli

# Test the installation
fastapi-crud --version
fastapi-crud create

# Clean up
deactivate
rm -rf pypi-test-env
```

## Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### Updating Version

1. **Update version in `__version__.py`:**
   ```python
   __version__ = "0.2.0"
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [0.2.0] - 2024-01-15
   
   ### Added
   - New feature X
   - New feature Y
   
   ### Changed
   - Improved Z
   
   ### Fixed
   - Bug fix A
   ```

3. **Commit changes:**
   ```bash
   git add fastapi_crud_cli/__version__.py CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   ```

4. **Create git tag:**
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Setup:
1. Add PyPI API token to GitHub Secrets as `PYPI_API_TOKEN`
2. Create a release on GitHub
3. Package automatically builds and publishes

## Post-Publication

### 1. Announce Release

- Update project README with new version
- Post announcement on relevant forums/communities
- Update documentation site (if applicable)

### 2. Monitor Issues

- Watch for installation issues
- Respond to bug reports
- Track download statistics on PyPI

### 3. Update Documentation

- Ensure all documentation reflects new version
- Update examples if API changed
- Add migration guide for breaking changes

## Troubleshooting

### Upload Fails with "File already exists"

PyPI doesn't allow re-uploading the same version:

**Solution**: Increment version number and rebuild

```bash
# Update version in __version__.py
# Rebuild
rm -rf dist/
python -m build
python -m twine upload dist/*
```

### Template Files Missing in Published Package

**Solution**: Update MANIFEST.in and rebuild

```bash
# Verify MANIFEST.in includes:
recursive-include fastapi_crud_cli/templates *

# Rebuild
rm -rf dist/
python -m build

# Verify contents
unzip -l dist/fastapi_crud_cli-*.whl | grep templates
```

### Import Errors After Installation

**Solution**: Verify package structure

```bash
# Check installed package
pip show -f fastapi-crud-cli

# Verify imports work
python -c "from fastapi_crud_cli.cli.main import cli; print('OK')"
```

### README Not Rendering on PyPI

**Solution**: Validate README format

```bash
# Install readme_renderer
pip install readme_renderer

# Check README
python -m readme_renderer CLI_README.md
```

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use API tokens** instead of username/password
3. **Scope tokens appropriately** (project-specific when possible)
4. **Rotate tokens regularly**
5. **Use GitHub Secrets** for CI/CD
6. **Enable 2FA** on PyPI account

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

## Support

For publishing issues:
- [PyPI Support](https://pypi.org/help/)
- [Python Packaging Discourse](https://discuss.python.org/c/packaging/)
- [GitHub Issues](https://github.com/yourusername/fastapi-crud-cli/issues)
