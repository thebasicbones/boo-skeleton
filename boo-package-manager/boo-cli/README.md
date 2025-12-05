# Boo CLI

A Python package manager CLI that enhances pip with intelligent dependency management, conflict detection, and team collaboration features.

## Features

- 🚀 **Smart Installation**: Automatic topological sorting ensures dependencies are installed in the correct order
- 🔍 **Conflict Detection**: Detects circular dependencies before installation
- 🌳 **Dependency Trees**: Visualize package dependencies in a tree structure
- 🔄 **Team Sync**: Centralized package tracking across projects and teams
- 📦 **Lock Files**: Generate reproducible installations
- 🔒 **Security Auditing**: Check for vulnerable dependencies
- 🎨 **Rich UI**: Beautiful terminal output with colors and progress bars

## Installation

```bash
cd boo-cli
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# Install a package
boo install requests

# List installed packages
boo list

# Show dependency tree
boo tree

# Check for conflicts
boo check

# Search for packages
boo search django

# Uninstall a package
boo uninstall requests
```

## Requirements

- Python 3.9+
- Running boo-package-manager backend (see ../README.md)

## Architecture

The CLI acts as a frontend to the boo-package-manager backend:

```
User → Boo CLI → Backend API → Database
              ↓
            pip (for actual installation)
```

## Development

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=boo --cov-report=html

# Format code
black boo tests
ruff check boo tests

# Type checking
mypy boo
```

### Project Structure

```
boo-cli/
├── boo/
│   ├── commands/       # Command implementations
│   ├── api/           # Backend API client
│   ├── package_manager/  # Pip wrapper
│   ├── ui/            # Terminal UI components
│   └── main.py        # CLI entry point
├── tests/             # Test suite
└── pyproject.toml     # Package configuration
```

## Documentation

For full documentation, see the [design document](../.kiro/python-package-manager-cli/design.md).

## License

MIT
