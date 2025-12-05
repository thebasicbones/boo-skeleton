# Multi-Environment Configuration

This directory contains the multi-environment configuration system for the FastAPI CRUD Backend application.

## Overview

The application uses Pydantic Settings to provide type-safe, validated configuration management across different environments (development, staging, production).

## Configuration Files

### Environment-Specific Files

- **`.env.development`** - Development environment configuration (local development)
- **`.env.staging`** - Staging environment configuration (pre-production testing)
- **`.env.production.example`** - Production configuration template (copy to `.env.production`)

### Settings Module

- **`settings.py`** - Core settings class with validation and environment-aware configuration

## Usage

### Loading Settings

The settings are automatically loaded when the application starts:

```python
from config.settings import get_settings

settings = get_settings()
print(f"Running in {settings.environment} environment")
```

### Switching Environments

You can switch environments by:

1. **Using environment variables:**
   ```bash
   ENVIRONMENT=staging python main.py
   ```

2. **Copying the appropriate .env file:**
   ```bash
   cp .env.staging .env
   python main.py
   ```

3. **Setting the env_file in code (for testing):**
   ```python
   from config.settings import Settings
   settings = Settings(_env_file=".env.staging")
   ```

## Configuration Options

### Environment Settings

- `ENVIRONMENT` - Application environment (`development`, `staging`, `production`)

### Database Configuration

- `DATABASE_TYPE` - Database backend (`sqlite`, `mongodb`)
- `DATABASE_URL` - Database connection URL
- `MONGODB_DATABASE` - MongoDB database name (required for MongoDB)
- `MONGODB_USERNAME` - MongoDB username (optional)
- `MONGODB_PASSWORD` - MongoDB password (optional)
- `MONGODB_AUTH_SOURCE` - MongoDB authentication database (default: `admin`)
- `MONGODB_TIMEOUT` - MongoDB connection timeout in milliseconds (default: `5000`)

### API Configuration

- `API_HOST` - API server host (default: `0.0.0.0`)
- `API_PORT` - API server port (default: `8000`)
- `API_RELOAD` - Enable auto-reload for development (default: `false`)
- `DEBUG` - Enable debug mode (default: `false`)

### Application Metadata

- `APP_TITLE` - Application title (default: `FastAPI CRUD Backend`)
- `APP_VERSION` - Application version (default: `1.0.0`)

### Logging Configuration

- `LOG_LEVEL` - Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

### Security Configuration

- `SECRET_KEY` - Secret key for security features (MUST be changed in production!)
- `ALLOWED_ORIGINS` - CORS allowed origins (list of URLs)

## Environment-Specific Recommendations

### Development

- Use SQLite for simplicity
- Enable debug mode and auto-reload
- Set log level to DEBUG
- Allow all CORS origins for local testing

### Staging

- Use MongoDB or production-like database
- Disable debug mode and auto-reload
- Set log level to INFO
- Restrict CORS origins to staging domains
- Use staging-specific credentials

### Production

- Use MongoDB or production database with replication
- Disable debug mode and auto-reload
- Set log level to WARNING or ERROR
- Restrict CORS origins to production domains only
- Use strong, unique secret keys
- Never commit `.env.production` to version control!

## Security Best Practices

1. **Never commit sensitive files:**
   - `.env.production` is in `.gitignore`
   - Only commit `.env.production.example` as a template

2. **Use strong secret keys:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Restrict CORS origins:**
   - Never use `["*"]` in production
   - Specify exact domains

4. **Validate required variables:**
   - The settings system validates all required fields on startup
   - Missing required variables will cause the application to fail fast

## Validation

The settings system includes automatic validation:

- **Type checking:** All settings have type annotations
- **Value validation:** Enums for environment and database type
- **Required fields:** MongoDB database name is required when using MongoDB
- **Security warnings:** Warns about insecure configurations in production

## Example: Production Setup

1. Copy the production template:
   ```bash
   cp .env.production.example .env.production
   ```

2. Edit `.env.production` with your actual values:
   ```bash
   nano .env.production
   ```

3. Set strong credentials and keys

4. Run the application:
   ```bash
   ENVIRONMENT=production python main.py
   ```

## Troubleshooting

### Settings not loading

- Check that `.env` file exists in the project root
- Verify environment variable names match exactly (case-insensitive)
- Check for syntax errors in `.env` file

### MongoDB connection fails

- Verify `MONGODB_DATABASE` is set when `DATABASE_TYPE=mongodb`
- Check MongoDB URL format and credentials
- Ensure MongoDB server is running and accessible

### CORS errors

- Check `ALLOWED_ORIGINS` includes your frontend URL
- Verify the URL format (include protocol: `https://`)
- Check for trailing slashes in URLs

## Testing

For testing purposes, you can reload settings:

```python
from config.settings import reload_settings

# Change environment variables
import os
os.environ['ENVIRONMENT'] = 'staging'

# Reload settings
settings = reload_settings()
```
