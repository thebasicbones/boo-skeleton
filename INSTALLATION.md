# Installation Guide

This guide covers different methods for installing the FastAPI CRUD CLI tool.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

Verify your Python version:

```bash
python --version
# or
python3 --version
```

## Installation Methods

### Method 1: Install from PyPI (Recommended)

Once published to PyPI, install using pip:

```bash
pip install fastapi-crud-cli
```

Verify the installation:

```bash
fastapi-crud --version
```

### Method 2: Install from Source

Clone the repository and install in development mode:

```bash
# Clone the repository
git clone https://github.com/yourusername/fastapi-crud-cli.git
cd fastapi-crud-cli

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Method 3: Install with pipx (Isolated Installation)

[pipx](https://pypa.github.io/pipx/) installs the CLI in an isolated environment:

```bash
# Install pipx if not already installed
python -m pip install --user pipx
python -m pipx ensurepath

# Install fastapi-crud-cli
pipx install fastapi-crud-cli
```

Benefits of pipx:
- Isolated environment (no dependency conflicts)
- Globally available command
- Easy to upgrade and uninstall

### Method 4: Install from Local Build

Build and install from a local wheel:

```bash
# Install build tools
pip install build

# Build the package
python -m build

# Install the built wheel
pip install dist/fastapi_crud_cli-0.1.0-py3-none-any.whl
```

## Upgrading

### Upgrade from PyPI

```bash
pip install --upgrade fastapi-crud-cli
```

### Upgrade with pipx

```bash
pipx upgrade fastapi-crud-cli
```

## Uninstalling

### Uninstall with pip

```bash
pip uninstall fastapi-crud-cli
```

### Uninstall with pipx

```bash
pipx uninstall fastapi-crud-cli
```

## Verifying Installation

After installation, verify that the CLI is working:

```bash
# Check version
fastapi-crud --version

# Display help
fastapi-crud --help

# List available commands
fastapi-crud list
```

Expected output:

```
$ fastapi-crud --version
fastapi-crud, version 0.1.0

$ fastapi-crud --help
Usage: fastapi-crud [OPTIONS] COMMAND [ARGS]...

  FastAPI CRUD Backend Scaffolding Tool.

  Generate new FastAPI projects with customizable database backends and
  development configurations through an interactive CLI.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  create  Create a new FastAPI CRUD project.
  info    Show detailed information about a database backend.
  list    List available database backend options.
```

## Troubleshooting

### Command Not Found

If you get a "command not found" error after installation:

**Solution 1: Check PATH**

```bash
# Find where pip installs scripts
python -m site --user-base

# Add to PATH (add to ~/.bashrc or ~/.zshrc for persistence)
export PATH="$PATH:$(python -m site --user-base)/bin"
```

**Solution 2: Use python -m**

```bash
python -m fastapi_crud_cli.cli.main --help
```

**Solution 3: Use pipx**

```bash
pipx install fastapi-crud-cli
```

### Permission Errors

If you encounter permission errors during installation:

**Solution 1: Use --user flag**

```bash
pip install --user fastapi-crud-cli
```

**Solution 2: Use virtual environment**

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi-crud-cli
```

### Template Files Not Found

If the CLI reports missing template files:

**Solution: Reinstall with --force-reinstall**

```bash
pip install --force-reinstall fastapi-crud-cli
```

### Dependency Conflicts

If you encounter dependency conflicts:

**Solution 1: Use virtual environment**

```bash
python -m venv fastapi-crud-env
source fastapi-crud-env/bin/activate
pip install fastapi-crud-cli
```

**Solution 2: Use pipx**

```bash
pipx install fastapi-crud-cli
```

## Development Installation

For contributing to the project:

```bash
# Clone the repository
git clone https://github.com/yourusername/fastapi-crud-cli.git
cd fastapi-crud-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Platform-Specific Notes

### macOS

```bash
# Using Homebrew Python
brew install python@3.10
pip3 install fastapi-crud-cli
```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3-pip
pip3 install fastapi-crud-cli

# Fedora/RHEL
sudo dnf install python3.10 python3-pip
pip3 install fastapi-crud-cli
```

### Windows

```powershell
# Using Python installer from python.org
# Install Python 3.10+ with "Add to PATH" option checked

# Install the CLI
pip install fastapi-crud-cli

# Verify installation
fastapi-crud --version
```

## Next Steps

After successful installation:

1. **Create your first project:**
   ```bash
   fastapi-crud create
   ```

2. **Explore available options:**
   ```bash
   fastapi-crud list
   fastapi-crud info mongodb
   ```

3. **Read the documentation:**
   - [CLI_README.md](CLI_README.md) - CLI usage guide
   - [README.md](README.md) - Project overview

## Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Search [existing issues](https://github.com/yourusername/fastapi-crud-cli/issues)
3. Create a [new issue](https://github.com/yourusername/fastapi-crud-cli/issues/new) with:
   - Your Python version (`python --version`)
   - Your OS and version
   - Installation method used
   - Complete error message
   - Steps to reproduce

## Support

- **Documentation**: [GitHub README](https://github.com/yourusername/fastapi-crud-cli#readme)
- **Issues**: [GitHub Issues](https://github.com/yourusername/fastapi-crud-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fastapi-crud-cli/discussions)
