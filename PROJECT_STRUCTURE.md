# Project Structure

This document explains the organization of the FastAPI CRUD CLI project.

## Overview

The project is organized into two main parts:
1. **Source Application** (`src/`) - The actual FastAPI application that serves as the template
2. **CLI Tool** (`fastapi_crud_cli/`) - The command-line tool that generates new projects

## Directory Structure

```
boo-skeleton/
├── src/                              # Source FastAPI application (EDIT HERE)
│   ├── app/                          # Application code
│   │   ├── models/                   # Database models
│   │   ├── repositories/             # Data access layer
│   │   ├── routers/                  # API endpoints
│   │   ├── services/                 # Business logic
│   │   ├── schemas.py                # Pydantic models
│   │   ├── exceptions.py             # Custom exceptions
│   │   └── error_handlers.py         # Error handling
│   ├── config/                       # Configuration
│   │   └── settings.py               # Settings management
│   ├── tests/                        # Test suite
│   │   ├── conftest.py               # Test fixtures
│   │   └── test_*.py                 # Test files
│   ├── main.py                       # Application entry point
│   ├── .coveragerc                   # Coverage configuration
│   ├── pytest.ini                    # Pytest configuration
│   └── VERSION                       # Version file
│
├── fastapi_crud_cli/                 # CLI tool package
│   ├── cli/                          # CLI implementation
│   │   ├── main.py                   # CLI entry point
│   │   ├── generator.py              # Project generator
│   │   ├── prompts.py                # Interactive prompts
│   │   ├── output.py                 # Output formatting
│   │   ├── template_engine.py        # Template rendering
│   │   ├── validators.py             # Input validation
│   │   ├── database_configs.py       # Database configurations
│   │   └── database_configs.yaml     # Database config data
│   ├── templates/                    # Jinja2 templates
│   │   ├── project/                  # Template files (.j2)
│   │   │   ├── .env.j2
│   │   │   ├── main.py.j2
│   │   │   ├── README.md.j2
│   │   │   ├── requirements.txt.j2
│   │   │   └── ...
│   │   ├── static/                   # Static assets
│   │   └── template_manifest.yaml    # File generation manifest
│   ├── source/                       # Bundled source files (AUTO-GENERATED)
│   │   ├── app/                      # Copy of src/app/
│   │   ├── config/                   # Copy of src/config/
│   │   └── tests/                    # Copy of src/tests/
│   ├── utils/                        # Utility modules
│   ├── __init__.py
│   └── __version__.py
│
├── scripts/                          # Development scripts
│   ├── prepare_templates.py          # Sync src/ → fastapi_crud_cli/source/
│   └── README.md                     # Scripts documentation
│
├── docs/                             # Documentation
├── .github/                          # GitHub workflows
├── .kiro/                            # Kiro IDE configuration
│
├── pyproject.toml                    # Project metadata & dependencies
├── MANIFEST.in                       # Package manifest
├── requirements.txt                  # Application dependencies
├── README.md                         # Main documentation
├── CLI_README.md                     # CLI tool documentation
├── CHANGELOG.md                      # Version history
└── ...
```

## Key Concepts

### Source Directory (`src/`)

This is where you develop and maintain the FastAPI application code. All changes to the application logic, models, routes, etc., should be made here.

**Why separate?**
- Clean separation between the application and the CLI tool
- Easy to test the application independently
- No code duplication during development

### CLI Tool (`fastapi_crud_cli/`)

This is the command-line tool that generates new FastAPI projects. It includes:
- Interactive prompts for configuration
- Template rendering engine
- Project generation logic
- Automated setup (venv, dependencies, .env)

### Bundled Source (`fastapi_crud_cli/source/`)

This directory contains a copy of the `src/` files that gets bundled with the CLI tool when distributed via pip. 

**Important:** This directory is AUTO-GENERATED. Never edit files here directly!

### Templates (`fastapi_crud_cli/templates/`)

Jinja2 templates for files that need customization based on user input (database type, project name, etc.).

## Development Workflow

### 1. Making Changes to the Application

```bash
# Edit files in src/
vim src/app/schemas.py

# Test locally
cd src
python main.py

# Run tests
pytest
```

### 2. Preparing for Distribution

Before building the package or testing the CLI:

```bash
# Sync source files to CLI package
python3 scripts/prepare_templates.py

# This copies src/ → fastapi_crud_cli/source/
```

### 3. Testing the CLI Tool

```bash
# Install in development mode
pip install -e .

# Test the CLI
fastapi-crud create

# Or run directly
python -m fastapi_crud_cli.cli.main create
```

### 4. Building the Package

```bash
# Prepare templates
python3 scripts/prepare_templates.py

# Build
python -m build

# The resulting wheel/tarball includes fastapi_crud_cli/source/
```

## How the CLI Works

### During Development

When you run the CLI during development (from the repo):

1. CLI looks for source files in `src/` directory
2. If found, uses them directly (no duplication needed)
3. Copies files from `src/` to generated projects

### After Installation (via pip)

When users install the CLI via pip:

1. The package includes `fastapi_crud_cli/source/` (bundled)
2. CLI uses these bundled files
3. Copies files from `fastapi_crud_cli/source/` to generated projects

### File Resolution Logic

The `_get_source_dir()` method in `generator.py`:

```python
def _get_source_dir(self) -> Path:
    # 1. Try src/ (development)
    if src_dir.exists():
        return src_dir
    
    # 2. Try bundled source (installed package)
    if bundled_source.exists():
        return bundled_source
    
    # 3. Fallback or error
```

## File Types

### Static Files (Copied As-Is)

Files that don't need customization:
- `src/app/schemas.py`
- `src/app/exceptions.py`
- `src/config/__init__.py`
- etc.

These are listed in `template_manifest.yaml` under `static_files`.

### Template Files (Rendered with Jinja2)

Files that need customization:
- `.env.j2` - Database configuration
- `main.py.j2` - Project name, imports
- `README.md.j2` - Project documentation
- `requirements.txt.j2` - Dependencies based on database type

These are listed in `template_manifest.yaml` under `template_files`.

## Best Practices

### DO:
- ✅ Edit files in `src/` directory
- ✅ Run `prepare_templates.py` before building
- ✅ Test both the application and CLI tool
- ✅ Keep `src/` and templates in sync

### DON'T:
- ❌ Edit files in `fastapi_crud_cli/source/` directly
- ❌ Commit without running `prepare_templates.py`
- ❌ Duplicate code between `src/` and CLI tool
- ❌ Forget to update templates when changing structure

## Automation

### Pre-commit Hook (Future)

Consider adding a pre-commit hook to automatically run `prepare_templates.py`:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: prepare-templates
        name: Prepare CLI templates
        entry: python3 scripts/prepare_templates.py
        language: system
        pass_filenames: false
```

### CI/CD Integration

In your GitHub Actions workflow:

```yaml
- name: Prepare templates
  run: python3 scripts/prepare_templates.py

- name: Build package
  run: python -m build
```

## Troubleshooting

### "Source files not found" error

**Problem:** CLI can't find source files to copy.

**Solution:**
```bash
# Ensure src/ directory exists
ls src/app

# Run prepare_templates.py
python3 scripts/prepare_templates.py

# Verify bundled source
ls fastapi_crud_cli/source/app
```

### Generated projects missing files

**Problem:** Some files aren't being copied to generated projects.

**Solution:**
1. Check `template_manifest.yaml` includes the files
2. Verify files exist in `src/`
3. Run `prepare_templates.py` again
4. Check file paths in manifest match actual structure

### Changes not reflected in generated projects

**Problem:** You edited `src/` but generated projects still have old code.

**Solution:**
```bash
# Sync changes
python3 scripts/prepare_templates.py

# Reinstall CLI in development mode
pip install -e .

# Test again
fastapi-crud create
```

## Summary

The project structure separates concerns:
- **`src/`** - Application development (edit here)
- **`fastapi_crud_cli/source/`** - Bundled copy (auto-generated)
- **`fastapi_crud_cli/templates/`** - Customizable templates

Always run `prepare_templates.py` before building or distributing the package to ensure the bundled source is up-to-date.
