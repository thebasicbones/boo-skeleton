# Documentation

This directory contains the Sphinx documentation for the FastAPI CRUD Backend project.

## Building the Documentation

### Prerequisites

Install the documentation dependencies:

```bash
pip install -r docs/requirements.txt
```

### Build HTML Documentation

From the `docs/` directory:

```bash
make html
```

The generated HTML documentation will be in `docs/build/html/`.

### View the Documentation

Open `docs/build/html/index.html` in your web browser:

```bash
# macOS
open build/html/index.html

# Linux
xdg-open build/html/index.html

# Windows
start build/html/index.html
```

### Clean Build Files

To remove all generated documentation:

```bash
make clean
```

## Documentation Structure

```
docs/
├── source/
│   ├── conf.py              # Sphinx configuration
│   ├── index.rst            # Documentation home page
│   ├── architecture.rst     # Architecture overview
│   ├── testing.rst          # Testing guide
│   ├── api/                 # API reference documentation
│   │   ├── routers.rst      # API endpoints
│   │   ├── services.rst     # Business logic
│   │   ├── repositories.rst # Database layer
│   │   ├── schemas.rst      # Data models
│   │   └── exceptions.rst   # Custom exceptions
│   ├── _static/             # Static files (CSS, images)
│   └── _templates/          # Custom templates
├── build/                   # Generated documentation (gitignored)
├── Makefile                 # Build commands
└── requirements.txt         # Documentation dependencies
```

## Available Make Commands

- `make html` - Build HTML documentation
- `make clean` - Remove all build files
- `make help` - Show all available commands

## Updating Documentation

### Adding New Pages

1. Create a new `.rst` file in `docs/source/`
2. Add it to the `toctree` in `index.rst`
3. Rebuild with `make html`

### Documenting Code

The documentation automatically extracts docstrings from Python code. To document a new module:

1. Add comprehensive docstrings to your code
2. Create a new `.rst` file in `docs/source/api/`
3. Use the `automodule` directive:

```rst
My Module
=========

.. automodule:: app.my_module
   :members:
   :undoc-members:
   :show-inheritance:
```

4. Add the new file to the `toctree` in `index.rst`

## Docstring Style

This project uses Google-style docstrings. Example:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Longer description with more details about what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
        TypeError: When param1 is not a string

    Example::

        result = my_function("hello", 42)
        print(result)  # True
    """
    pass
```

## Troubleshooting

### Import Errors

If you see import errors when building documentation, ensure:

1. All project dependencies are installed: `pip install -r requirements.txt`
2. The project root is in the Python path (handled by `conf.py`)

### Missing Modules

If modules aren't appearing in the documentation:

1. Check that the module has docstrings
2. Verify the module is imported correctly in the `.rst` file
3. Run `make clean` and rebuild

### Warnings

Sphinx may show warnings about:

- Malformed docstrings - Fix the docstring format
- Missing references - Add the referenced item or fix the link
- Duplicate labels - Ensure section titles are unique

## Continuous Integration

Documentation builds are tested in CI to ensure:

- All documentation builds without errors
- No broken links
- All modules are documented

See `.github/workflows/` for CI configuration.
