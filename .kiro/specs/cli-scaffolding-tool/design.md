# Design Document: FastAPI CRUD CLI Scaffolding Tool

## Overview

The FastAPI CRUD CLI is a command-line scaffolding tool that transforms the existing FastAPI CRUD Backend into a reusable project generator. The tool provides an interactive, visually rich terminal interface for creating new FastAPI projects with customizable database backends (SQLite, MongoDB, PostgreSQL) and development configurations.

The design follows a template-based approach where the existing codebase serves as the source template, and user inputs drive the customization of generated projects. The tool leverages Click for CLI framework, Rich for terminal UI, and Jinja2 for template rendering.

**Key Design Principles:**
- Interactive and user-friendly CLI experience with visual feedback
- Template-based generation preserving the existing architecture
- Modular design allowing easy addition of new database backends
- Comprehensive validation and error handling
- Zero-configuration installation via pip

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                          │
│                  (fastapi-crud command)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐    ┌──────────┐    ┌──────────┐
    │ create │    │   list   │    │   info   │
    │command │    │ command  │    │ command  │
    └────┬───┘    └──────────┘    └──────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              Interactive Prompt System                       │
│  (Collects: name, database, config, author, options)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Validation Layer                             │
│  (Validates: names, paths, database configs, formats)       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Template Engine                                 │
│  (Jinja2 rendering with user configuration)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              File System Generator                           │
│  (Creates directories, files, and configurations)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Output & Feedback System                        │
│  (Progress indicators, success messages, summaries)         │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **User invokes CLI command** → Entry point parses command and arguments
2. **Command handler activates** → Appropriate command (create/list/info) executes
3. **Interactive prompts display** → User provides configuration inputs
4. **Validation occurs** → All inputs validated before proceeding
5. **User confirms** → Summary displayed for final approval
6. **Template rendering** → Jinja2 processes templates with user config
7. **File generation** → Directory structure and files created
8. **Feedback provided** → Progress updates and final summary displayed

## Components and Interfaces

### 1. CLI Entry Point Module (`cli/main.py`)

**Responsibility:** Main entry point for the CLI tool, command registration, and global options.

**Interface:**
```python
@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """FastAPI CRUD Backend Scaffolding Tool"""
    pass

@cli.command()
@click.option('--non-interactive', is_flag=True, help='Skip prompts, use defaults')
@click.pass_context
def create(ctx, non_interactive):
    """Create a new FastAPI CRUD project"""
    pass

@cli.command()
def list():
    """List available database backend options"""
    pass

@cli.command()
@click.argument('database_type')
def info(database_type):
    """Show detailed information about a database backend"""
    pass
```

**Key Responsibilities:**
- Register all CLI commands
- Handle version and help flags
- Initialize Rich console for output
- Coordinate command execution

### 2. Interactive Prompt Module (`cli/prompts.py`)

**Responsibility:** Handle all user interactions and input collection with Rich formatting.

**Interface:**
```python
class ProjectPrompts:
    def __init__(self, console: Console):
        self.console = console
    
    def prompt_project_name(self, default: str = "my-fastapi-project") -> str:
        """Prompt for project name with validation"""
        pass
    
    def prompt_database_type(self) -> str:
        """Prompt for database selection with descriptions"""
        pass
    
    def prompt_database_config(self, db_type: str) -> dict:
        """Prompt for database-specific configuration"""
        pass
    
    def prompt_project_metadata(self) -> dict:
        """Prompt for author, description, etc."""
        pass
    
    def prompt_optional_features(self) -> dict:
        """Prompt for dev tools, examples, etc."""
        pass
    
    def confirm_generation(self, config: dict) -> bool:
        """Display summary and ask for confirmation"""
        pass
```

**Design Decisions:**
- Use Rich's `Prompt` class for styled input collection
- Provide sensible defaults for all prompts
- Use `questionary` or Rich's built-in choice prompts for selections
- Display help text and examples inline with prompts

### 3. Validation Module (`cli/validators.py`)

**Responsibility:** Validate all user inputs before project generation.

**Interface:**
```python
class ProjectValidator:
    @staticmethod
    def validate_project_name(name: str) -> tuple[bool, str]:
        """Validate project name format"""
        pass
    
    @staticmethod
    def validate_directory_available(path: Path) -> tuple[bool, str]:
        """Check if directory exists and handle conflicts"""
        pass
    
    @staticmethod
    def validate_mongodb_url(url: str) -> tuple[bool, str]:
        """Validate MongoDB connection string format"""
        pass
    
    @staticmethod
    def validate_postgres_config(config: dict) -> tuple[bool, str]:
        """Validate PostgreSQL configuration parameters"""
        pass
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format"""
        pass
```

**Validation Rules:**
- Project names: alphanumeric, hyphens, underscores only
- Directory conflicts: prompt for overwrite or new name
- Database URLs: format validation (no connection testing)
- Email: basic RFC 5322 format validation

### 4. Template Engine Module (`cli/template_engine.py`)

**Responsibility:** Render project files from templates using Jinja2.

**Interface:**
```python
class TemplateEngine:
    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def render_file(self, template_name: str, context: dict) -> str:
        """Render a single template file"""
        pass
    
    def render_project(self, config: dict, output_dir: Path):
        """Render entire project structure"""
        pass
    
    def get_template_context(self, config: dict) -> dict:
        """Build Jinja2 context from user configuration"""
        pass
```

**Template Variables:**
- `project_name`: User-provided project name
- `project_slug`: Normalized name for Python packages
- `database_type`: Selected database (sqlite/mongodb/postgresql)
- `database_config`: Database-specific settings
- `author_name`, `author_email`: Project metadata
- `include_examples`: Boolean for example scripts
- `include_dev_tools`: Boolean for development dependencies
- `description`: Project description

### 5. File Generator Module (`cli/generator.py`)

**Responsibility:** Create directory structure and write files to disk.

**Interface:**
```python
class ProjectGenerator:
    def __init__(self, console: Console):
        self.console = console
        self.template_engine = TemplateEngine(get_template_dir())
    
    def generate_project(self, config: dict, output_dir: Path):
        """Generate complete project structure"""
        pass
    
    def create_directory_structure(self, base_dir: Path, config: dict):
        """Create all necessary directories"""
        pass
    
    def generate_source_files(self, base_dir: Path, config: dict):
        """Generate Python source files"""
        pass
    
    def generate_config_files(self, base_dir: Path, config: dict):
        """Generate configuration files (.env, pyproject.toml, etc.)"""
        pass
    
    def generate_documentation(self, base_dir: Path, config: dict):
        """Generate README and other docs"""
        pass
    
    def copy_static_assets(self, base_dir: Path, config: dict):
        """Copy static files (if included)"""
        pass
```

**Directory Structure Generated:**
```
{project_name}/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── repositories/
│   ├── routers/
│   ├── services/
│   ├── database_factory.py
│   ├── database_{db_type}.py
│   ├── exceptions.py
│   ├── error_handlers.py
│   └── schemas.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
├── static/ (optional)
├── scripts/ (optional)
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── README.md
└── main.py
```

### 6. Output Formatter Module (`cli/output.py`)

**Responsibility:** Format and display all CLI output with Rich styling.

**Interface:**
```python
class OutputFormatter:
    def __init__(self, console: Console):
        self.console = console
    
    def display_welcome(self):
        """Display welcome banner"""
        pass
    
    def display_progress(self, message: str):
        """Show progress message with spinner"""
        pass
    
    def display_success(self, message: str):
        """Show success message with checkmark"""
        pass
    
    def display_error(self, message: str, details: str = None):
        """Show error message with details"""
        pass
    
    def display_summary_table(self, config: dict):
        """Display configuration summary as table"""
        pass
    
    def display_file_tree(self, files: list[Path]):
        """Display generated files as tree"""
        pass
    
    def display_next_steps(self, project_dir: Path):
        """Display post-generation instructions"""
        pass
```

**Styling Conventions:**
- Success: Green with ✓ symbol
- Error: Red with ✗ symbol
- Info: Blue with ℹ symbol
- Prompts: Cyan with ❯ symbol
- Progress: Yellow with spinner
- Headers: Bold and underlined

### 7. Database Configuration Module (`cli/database_configs.py`)

**Responsibility:** Define database-specific configurations and prompts.

**Interface:**
```python
class DatabaseConfig:
    name: str
    description: str
    dependencies: list[str]
    env_variables: dict[str, str]
    
    def get_prompts(self) -> list[dict]:
        """Return list of prompts for this database"""
        pass
    
    def generate_env_content(self, user_config: dict) -> str:
        """Generate .env file content"""
        pass

class SQLiteConfig(DatabaseConfig):
    pass

class MongoDBConfig(DatabaseConfig):
    pass

class PostgreSQLConfig(DatabaseConfig):
    pass

DATABASE_CONFIGS = {
    'sqlite': SQLiteConfig(),
    'mongodb': MongoDBConfig(),
    'postgresql': PostgreSQLConfig(),
}
```

## Data Models

### Configuration Data Structure

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectConfig:
    """Complete project configuration"""
    project_name: str
    project_slug: str  # Normalized for Python
    description: str
    author_name: str
    author_email: str
    database_type: str
    database_config: dict
    include_examples: bool
    include_dev_tools: bool
    include_static: bool
    output_directory: Path

@dataclass
class DatabaseConnectionConfig:
    """Database-specific connection settings"""
    type: str  # sqlite, mongodb, postgresql
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    additional_params: dict = None
```

### Template Metadata

```python
@dataclass
class TemplateFile:
    """Metadata for a template file"""
    source_path: str  # Path in template directory
    dest_path: str  # Path in generated project
    is_template: bool  # Whether to render with Jinja2
    condition: Optional[str] = None  # Condition for inclusion
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated:

- Properties 5.1, 5.3, 5.4, 5.5 all test that specific files/directories exist after generation - these can be combined into a single comprehensive "project structure completeness" property
- Properties 4.4 and 4.5 both test database-specific file generation - these can be combined into a single property about database configuration consistency
- Property 2.5 (project generation) is subsumed by the more specific properties about what gets generated

The following properties represent unique, non-redundant validation:

**Property 1: Project name validation**
*For any* string input as a project name, the validation should accept only strings containing alphanumeric characters, hyphens, and underscores, and reject all others.
**Validates: Requirements 2.3**

**Property 2: Project structure completeness**
*For any* valid project configuration, the generated project should contain all required directories (app/, tests/, config/, static/, scripts/) and configuration files (.env.example, .gitignore, pyproject.toml, README.md, requirements.txt).
**Validates: Requirements 5.1, 5.3, 5.4, 5.5**

**Property 3: Database configuration consistency**
*For any* database type selection (SQLite, MongoDB, PostgreSQL), the generated project should include the appropriate database-specific dependencies in requirements.txt and corresponding environment variables in the .env file.
**Validates: Requirements 4.4, 4.5**

**Property 4: Development tools inclusion**
*For any* project configuration where development tools are enabled, the generated requirements.txt should contain pytest, black, ruff, and mypy, and corresponding configuration files should be created.
**Validates: Requirements 6.5**

**Property 5: Invalid database parameter rejection**
*For any* invalid database connection parameters (malformed URLs, invalid ports, etc.), the validation should reject the input and provide an error message.
**Validates: Requirements 8.2**

**Property 6: Template file accessibility**
*For any* template file included in the package, it should be accessible to the CLI tool at runtime after installation.
**Validates: Requirements 9.5**

**Property 7: Database info command completeness**
*For any* valid database type, running the info command should display information including requirements and features.
**Validates: Requirements 10.2**

**Property 8: Invalid database type suggestion**
*For any* invalid database type provided to the info command, the tool should display available options and suggest the closest match.
**Validates: Requirements 10.5**

## Error Handling

### Error Categories and Handling Strategies

#### 1. User Input Errors

**Validation Errors:**
- Invalid project names → Display format requirements and examples
- Invalid email formats → Show RFC 5322 format example
- Invalid database URLs → Provide format examples for each database type
- Invalid port numbers → Show valid range (1-65535)

**Strategy:** Catch validation errors early, display clear messages with examples, allow user to retry without restarting.

#### 2. File System Errors

**Directory Conflicts:**
- Project directory already exists → Prompt user to overwrite, rename, or cancel
- Permission denied → Display clear error with suggested resolution (check permissions)
- Disk space issues → Display error with space requirements

**Strategy:** Check for conflicts before generation starts, provide clear options for resolution.

#### 3. Template Errors

**Missing Templates:**
- Template file not found → Display error and list available templates
- Template rendering errors → Show Jinja2 error with context

**Strategy:** Validate template availability during package installation, provide fallback templates if possible.

#### 4. Package Installation Errors

**Dependency Issues:**
- Missing dependencies → Display installation command
- Version conflicts → Show conflicting packages and suggested resolution

**Strategy:** Use comprehensive dependency specifications in setup, provide troubleshooting guide in documentation.

### Error Message Format

All error messages follow this structure:
```
✗ Error: [Brief description]

Details: [Specific error information]

Suggestion: [How to resolve]
```

### Graceful Degradation

- If git config is unavailable for author defaults → Use empty strings as defaults
- If Rich formatting fails → Fall back to plain text output
- If optional features fail → Continue with core functionality, log warning

## Testing Strategy

### Unit Testing

The CLI tool will use pytest for unit testing with the following focus areas:

**Validation Logic:**
- Test `ProjectValidator` methods with valid and invalid inputs
- Test edge cases: empty strings, special characters, very long names
- Test database URL format validation for each database type

**Template Rendering:**
- Test `TemplateEngine` with various configurations
- Test that all template variables are properly substituted
- Test conditional template inclusion based on user options

**Configuration Building:**
- Test `ProjectConfig` creation from user inputs
- Test database-specific configuration generation
- Test metadata extraction from git config

**File Generation:**
- Test directory structure creation
- Test file writing with various content types
- Test handling of existing directories

### Property-Based Testing

The CLI tool will use Hypothesis for property-based testing with a minimum of 100 iterations per test:

**Property Test 1: Project name validation (Property 1)**
- Generate random strings with various character sets
- Verify that only alphanumeric, hyphens, and underscores pass validation
- Verify that strings with other characters fail validation
- **Feature: cli-scaffolding-tool, Property 1: Project name validation**

**Property Test 2: Project structure completeness (Property 2)**
- Generate random valid project configurations
- Create projects with each configuration
- Verify all required directories and files exist
- **Feature: cli-scaffolding-tool, Property 2: Project structure completeness**

**Property Test 3: Database configuration consistency (Property 3)**
- Generate configurations for each database type
- Verify requirements.txt contains database-specific dependencies
- Verify .env file contains appropriate environment variables
- **Feature: cli-scaffolding-tool, Property 3: Database configuration consistency**

**Property Test 4: Development tools inclusion (Property 4)**
- Generate configurations with dev tools enabled/disabled
- Verify dev dependencies present only when enabled
- Verify configuration files created only when enabled
- **Feature: cli-scaffolding-tool, Property 4: Development tools inclusion**

**Property Test 5: Invalid database parameter rejection (Property 5)**
- Generate invalid database connection parameters
- Verify validation rejects all invalid inputs
- Verify error messages are provided
- **Feature: cli-scaffolding-tool, Property 5: Invalid database parameter rejection**

**Property Test 6: Template file accessibility (Property 6)**
- Iterate through all template files in package
- Verify each template is accessible at runtime
- Verify template content can be read
- **Feature: cli-scaffolding-tool, Property 6: Template file accessibility**

**Property Test 7: Database info command completeness (Property 7)**
- For each valid database type, run info command
- Verify output contains requirements and features
- Verify output is non-empty and properly formatted
- **Feature: cli-scaffolding-tool, Property 7: Database info command completeness**

**Property Test 8: Invalid database type suggestion (Property 8)**
- Generate invalid database type names
- Verify error message displays available options
- Verify closest match suggestion is provided
- **Feature: cli-scaffolding-tool, Property 8: Invalid database type suggestion**

### Integration Testing

**End-to-End Tests:**
- Test complete project generation flow with various configurations
- Test generated projects can be installed and run
- Test that generated tests in new projects pass

**CLI Command Tests:**
- Test all CLI commands with Click's testing utilities
- Test command help output
- Test version display
- Test list and info commands

### Test Configuration

- Minimum 100 iterations for each property-based test
- Use temporary directories for file generation tests
- Clean up generated files after tests
- Mock user input for interactive prompt tests
- Use Click's `CliRunner` for command testing

## Implementation Considerations

### Template Organization

Templates will be organized in a `templates/` directory within the package:

```
fastapi_crud_cli/
├── templates/
│   ├── project/
│   │   ├── app/
│   │   │   ├── __init__.py.j2
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   └── ...
│   │   ├── config/
│   │   ├── tests/
│   │   ├── .env.j2
│   │   ├── .gitignore.j2
│   │   ├── README.md.j2
│   │   ├── requirements.txt.j2
│   │   └── pyproject.toml.j2
│   └── configs/
│       ├── sqlite.yaml
│       ├── mongodb.yaml
│       └── postgresql.yaml
```

### Package Structure

```
fastapi-crud-cli/
├── fastapi_crud_cli/
│   ├── __init__.py
│   ├── __version__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── prompts.py
│   │   ├── validators.py
│   │   ├── generator.py
│   │   ├── template_engine.py
│   │   ├── output.py
│   │   └── database_configs.py
│   ├── templates/
│   └── utils/
├── tests/
├── setup.py
├── pyproject.toml
├── MANIFEST.in
├── README.md
└── requirements.txt
```

### Dependency Management

**Core Dependencies:**
- `click>=8.0.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `jinja2>=3.0.0` - Template rendering
- `pydantic>=2.0.0` - Configuration validation
- `questionary>=2.0.0` - Interactive prompts (optional, can use Rich)

**Development Dependencies:**
- `pytest>=7.0.0`
- `hypothesis>=6.0.0`
- `pytest-cov`
- `black`
- `ruff`

### Configuration File Formats

**Database Configuration (YAML):**
```yaml
name: MongoDB
description: NoSQL document database
dependencies:
  - pymongo>=4.0.0
  - motor>=3.0.0
env_variables:
  MONGODB_URL: mongodb://localhost:27017
  MONGODB_DB_NAME: my_database
prompts:
  - name: mongodb_url
    message: MongoDB connection URL
    default: mongodb://localhost:27017
  - name: database_name
    message: Database name
    default: my_database
```

### Entry Point Configuration

In `pyproject.toml`:
```toml
[project.scripts]
fastapi-crud = "fastapi_crud_cli.cli.main:cli"
```

Or in `setup.py`:
```python
entry_points={
    'console_scripts': [
        'fastapi-crud=fastapi_crud_cli.cli.main:cli',
    ],
}
```

### Template Variable Naming Conventions

- Use snake_case for all template variables
- Prefix boolean flags with `include_` or `enable_`
- Use `_config` suffix for configuration dictionaries
- Use `_list` suffix for list variables

### Progress Feedback Strategy

Use Rich's `Progress` context manager for file generation:
```python
with Progress() as progress:
    task = progress.add_task("Generating project...", total=total_files)
    for file in files:
        generate_file(file)
        progress.update(task, advance=1)
```

### Git Integration

Attempt to read git config for defaults:
```python
try:
    author_name = subprocess.check_output(['git', 'config', 'user.name']).decode().strip()
    author_email = subprocess.check_output(['git', 'config', 'user.email']).decode().strip()
except:
    author_name = ""
    author_email = ""
```

Fall back to empty strings if git is not available or configured.

## Security Considerations

1. **Path Traversal Prevention:** Validate that project names don't contain path separators or parent directory references
2. **Command Injection:** Don't execute user-provided strings as shell commands
3. **Template Injection:** Use Jinja2's autoescaping for any user-provided content in templates
4. **Credential Handling:** Never log or display passwords/credentials in plain text
5. **File Permissions:** Set appropriate permissions on generated files (especially .env files)

## Performance Considerations

1. **Template Caching:** Cache compiled Jinja2 templates for reuse
2. **Lazy Loading:** Load database configurations only when needed
3. **Parallel File Generation:** Consider using threading for independent file writes
4. **Minimal Dependencies:** Keep package size small by avoiding heavy dependencies

## Future Extensibility

### Plugin System (Future Enhancement)

Design allows for future plugin system where users can:
- Add custom database backends
- Define custom templates
- Add custom validation rules
- Extend CLI commands

### Configuration Presets (Future Enhancement)

Allow users to save and reuse configuration presets:
```bash
fastapi-crud create --preset my-mongo-setup
```

### Template Marketplace (Future Enhancement)

Support for downloading community templates:
```bash
fastapi-crud template install community/advanced-auth
```

## Design Rationale

### Why Click over argparse?
- Better support for nested commands
- Built-in support for interactive prompts
- Cleaner decorator-based API
- Better integration with testing utilities

### Why Rich over colorama?
- More comprehensive formatting options
- Built-in table, progress bar, and tree rendering
- Better cross-platform support
- Active development and maintenance

### Why Jinja2 over string templates?
- Powerful template logic (conditionals, loops)
- Template inheritance for reducing duplication
- Wide adoption and extensive documentation
- Security features (autoescaping)

### Why template-based over code generation?
- Easier to maintain and update templates
- Users can inspect and modify templates
- Clear separation between tool logic and generated code
- Supports complex conditional generation

### Why not use cookiecutter?
- Need tighter integration with existing codebase
- Want custom validation and interactive prompts
- Need database-specific logic and configuration
- Want to maintain control over the generation process
