# Template System Documentation

## Overview

This directory contains the template system for the FastAPI CRUD CLI scaffolding tool. The system uses a hybrid approach combining:

1. **Jinja2 templates** (`.j2` files) - For files that need customization based on user input
2. **Static source files** - For files that remain the same across all projects
3. **Manifest-driven generation** - YAML manifest controls which files to include

## Directory Structure

```
templates/
├── README.md                    # This file
├── template_manifest.yaml       # Defines which files to copy/render
├── project/                     # Jinja2 templates (.j2 files)
│   ├── .env.j2
│   ├── .gitignore.j2
│   ├── pyproject.toml.j2
│   ├── requirements.txt.j2
│   ├── README.md.j2
│   ├── main.py.j2
│   ├── app/
│   │   ├── database_factory.py.j2
│   │   ├── database_sqlalchemy.py.j2
│   │   └── database_mongodb.py.j2
│   ├── config/
│   │   └── settings.py.j2
│   ├── tests/
│   │   ├── conftest.py.j2
│   │   └── test_api_endpoints.py.j2
│   └── scripts/
│       └── populate_example.py.j2
└── static/                      # Static assets
    ├── styles.css
    └── app.js
```

## Template Manifest

The `template_manifest.yaml` file defines three types of files:

### 1. Static Files
Files copied directly from the source project without modification:
```yaml
static_files:
  - source: app/schemas.py
    dest: app/schemas.py
  - source: app/exceptions.py
    dest: app/exceptions.py
    condition: database_type == 'sqlite'  # Optional condition
```

### 2. Template Files
Files rendered with Jinja2 using user configuration:
```yaml
template_files:
  - template: project/.env.j2
    dest: .env
  - template: project/main.py.j2
    dest: main.py
    executable: true  # Make file executable
```

### 3. Empty Files
Files created as empty placeholders:
```yaml
empty_files:
  - tests/__init__.py
```

## Template Variables

Templates have access to these variables:

### Core Variables
- `project_name` - User-provided project name
- `project_slug` - Normalized Python package name
- `description` - Project description
- `author_name` - Author name
- `author_email` - Author email

### Database Configuration
- `database_type` - Selected database ('sqlite', 'mongodb', 'postgresql')
- `database_config` - Database-specific configuration dict
  - For MongoDB: `mongodb_url`, `database_name`
  - For PostgreSQL: `host`, `port`, `username`, `password`, `database_name`

### Feature Flags
- `include_examples` - Include example scripts
- `include_dev_tools` - Include development tools (pytest, black, ruff, mypy)
- `include_static` - Include static frontend files

### Auto-Generated
- `current_date` - Current date in YYYY-MM-DD format

## Conditional Inclusion

Files can be conditionally included using Python expressions:

```yaml
- template: project/app/database_mongodb.py.j2
  dest: app/database_mongodb.py
  condition: database_type == 'mongodb'
```

Supported conditions:
- `database_type == 'mongodb'`
- `database_type in ['sqlite', 'postgresql']`
- `include_dev_tools`
- `include_examples`
- `include_static`

## Jinja2 Template Syntax

### Variables
```jinja2
{{ project_name }}
{{ database_type }}
```

### Conditionals
```jinja2
{% if database_type == 'mongodb' -%}
MONGODB_URL={{ database_config.mongodb_url }}
{% elif database_type == 'sqlite' -%}
DATABASE_URL=sqlite+aiosqlite:///./app.db
{% endif -%}
```

### Loops
```jinja2
{% for dep in dependencies -%}
{{ dep }}
{% endfor -%}
```

### Whitespace Control
- `{%- ... %}` - Strip whitespace before
- `{% ... -%}` - Strip whitespace after
- `{%- ... -%}` - Strip whitespace both sides

## Template Engine

The `TemplateEngine` class (`cli/template_engine.py`) handles:

1. Loading the manifest
2. Building the context from user configuration
3. Evaluating conditions
4. Copying static files from source
5. Rendering Jinja2 templates
6. Creating empty files
7. Setting file permissions

## Adding New Templates

### To add a new Jinja2 template:

1. Create the template file in `project/` with `.j2` extension
2. Add entry to `template_manifest.yaml` under `template_files`
3. Use template variables as needed

### To add a new static file:

1. Add entry to `template_manifest.yaml` under `static_files`
2. Specify source path (relative to project root)
3. Specify destination path (relative to generated project)

### To add conditional files:

Add a `condition` field with a Python expression:
```yaml
- template: project/special_feature.py.j2
  dest: app/special_feature.py
  condition: include_special_feature
```

## Best Practices

1. **Minimize templates** - Only create `.j2` files for files that truly need customization
2. **Use conditionals** - Leverage Jinja2 conditionals instead of creating multiple template variants
3. **Keep it DRY** - Use template inheritance and includes for shared content
4. **Test conditions** - Ensure conditional expressions work with all configuration combinations
5. **Document variables** - Add comments in templates explaining what variables are used

## Example: Adding PostgreSQL Support

1. Update `database_configs.yaml` with PostgreSQL configuration
2. Add PostgreSQL-specific templates if needed
3. Update `database_factory.py.j2` to handle PostgreSQL
4. Update `settings.py.j2` with PostgreSQL settings
5. Update manifest conditions to include PostgreSQL

## Troubleshooting

### Template not found
- Check the path in `template_manifest.yaml` matches the actual file location
- Ensure the template file has `.j2` extension if it's a Jinja2 template

### Variable not defined
- Check that the variable is included in the context (see `_build_context` in `template_engine.py`)
- Verify the variable name matches exactly (case-sensitive)

### Condition not working
- Test the condition expression in Python REPL
- Ensure all variables used in the condition are available in the context
- Check for typos in variable names

### File not being generated
- Check if there's a condition that's evaluating to False
- Verify the manifest entry is correctly formatted
- Check the logs for any error messages
