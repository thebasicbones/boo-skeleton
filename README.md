# FastAPI CRUD Backend

A RESTful API backend with topological sorting capabilities for managing resources with dependencies. Supports both SQLite and MongoDB as database backends.

## Features

- 🚀 RESTful API with FastAPI
- 🔄 Topological sorting for dependency management
- 💾 Dual database backend support (SQLite and MongoDB)
- ✅ Comprehensive test suite with property-based testing
- 📊 Automatic API documentation (Swagger/ReDoc)
- 🔍 Resource search capabilities
- 🔗 Cascade delete for dependent resources

## Project Structure

```
.
├── app/
│   ├── models/          # Database models (SQLAlchemy)
│   ├── repositories/    # Data access layer (abstract + implementations)
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── database_factory.py      # Database backend selection
│   ├── database_sqlalchemy.py   # SQLite/SQLAlchemy connection
│   ├── database_mongodb.py      # MongoDB connection
│   ├── exceptions.py            # Custom exceptions
│   └── error_handlers.py        # Error handling
├── scripts/             # Utility scripts (migration, etc.)
├── static/              # Frontend HTML/CSS/JS files
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── venv/               # Virtual environment
```

## Quick Start

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database Backend

Copy the example environment file and configure your database:

```bash
cp .env.example .env
```

Edit `.env` to choose your database backend (see [Database Configuration](#database-configuration) below).

## Database Configuration

The application supports two database backends: **SQLite** (default) and **MongoDB**. Choose the backend that best fits your deployment needs.

### SQLite Configuration (Default)

SQLite is the default backend, ideal for development and small deployments:

```bash
# .env file
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./app.db
```

**Advantages:**
- Zero configuration required
- File-based, no separate server needed
- Perfect for development and testing
- Included in Python standard library

### MongoDB Configuration

MongoDB is recommended for production deployments requiring scalability:

#### Local MongoDB

```bash
# .env file
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud
```

#### MongoDB Atlas (Cloud)

```bash
# .env file
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=fastapi_crud
```

#### MongoDB with Authentication

```bash
# .env file
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_crud
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_AUTH_SOURCE=admin
```

### MongoDB Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_TYPE` | Database backend type (`sqlite` or `mongodb`) | Yes | `sqlite` |
| `DATABASE_URL` | Database connection URL | Yes | `sqlite:///./app.db` |
| `MONGODB_DATABASE` | MongoDB database name | Yes (for MongoDB) | - |
| `MONGODB_USERNAME` | MongoDB username | No | - |
| `MONGODB_PASSWORD` | MongoDB password | No | - |
| `MONGODB_AUTH_SOURCE` | Authentication database | No | `admin` |
| `MONGODB_TIMEOUT` | Connection timeout (milliseconds) | No | `5000` |

### Setting Up MongoDB

#### Option 1: Install MongoDB Locally (macOS)

```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Verify it's running
mongosh --eval "db.version()"
```

#### Option 2: Install MongoDB Locally (Linux)

```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option 3: Use Docker

```bash
# Pull and run MongoDB container
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Verify it's running
docker ps | grep mongodb

# Stop MongoDB
docker stop mongodb

# Start MongoDB again
docker start mongodb
```

#### Option 4: Use MongoDB Atlas (Cloud)

1. Sign up for a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier available)
3. Create a database user with read/write permissions
4. Whitelist your IP address or use `0.0.0.0/0` for development
5. Get your connection string from the "Connect" button
6. Update your `.env` file with the connection string

### Docker Compose Setup

For a complete development environment with MongoDB:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_TYPE=mongodb
      - DATABASE_URL=mongodb://mongodb:27017
      - MONGODB_DATABASE=fastapi_crud
    depends_on:
      - mongodb
    volumes:
      - .:/app

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=fastapi_crud

volumes:
  mongodb_data:
```

Run with:

```bash
docker-compose up -d
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **SQLAlchemy**: SQL toolkit and ORM (for SQLite backend)
- **Motor**: Async MongoDB driver (for MongoDB backend)
- **PyMongo**: MongoDB driver (Motor dependency)
- **Pydantic**: Data validation using Python type annotations
- **Pytest**: Testing framework
- **Hypothesis**: Property-based testing library
- **HTTPx**: HTTP client for testing

## Running the Application

### Option 1: Using the startup script

```bash
./run.sh
```

### Option 2: Using Python directly

```bash
python main.py
```

### Option 3: Using Uvicorn directly

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at:
- **API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Resources

- `POST /api/resources` - Create a new resource
- `GET /api/resources` - List all resources
- `GET /api/resources/{id}` - Get a specific resource
- `PUT /api/resources/{id}` - Update a resource
- `DELETE /api/resources/{id}?cascade=true` - Delete a resource (with optional cascade)
- `GET /api/search?q=query` - Search resources with topological sorting

### System

- `GET /` - API information
- `GET /health` - Health check endpoint

## Testing

Run all tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_api_endpoints.py -v
```

Run property-based tests only:

```bash
pytest tests/test_property_*.py -v
```

### MongoDB Testing

Some property-based tests require MongoDB to be running. If MongoDB is not available, these tests will be automatically skipped.

To run MongoDB tests, ensure MongoDB is running locally:

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Or install MongoDB locally and start the service
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

Set the test database environment variable:

```bash
export MONGODB_DATABASE=fastapi_crud_test
```

Then run the tests:

```bash
pytest tests/test_property_mongodb_*.py -v
```

## Migrating from SQLite to MongoDB

If you have existing data in SQLite and want to migrate to MongoDB, use the provided migration script.

### Quick Migration

```bash
# Ensure MongoDB is running
brew services start mongodb-community  # macOS
# or
docker start mongodb  # Docker

# Run migration with validation
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing
```

### Migration Options

The migration script supports several modes:

#### 1. Full Migration with Validation

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing
```

#### 2. Export SQLite Data to JSON

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --export-only \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --output backup.json
```

#### 3. Import JSON to MongoDB

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --import-only \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --input backup.json \
  --clear-existing
```

### Migration Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sqlite-url` | SQLite database URL | `sqlite+aiosqlite:///./app.db` |
| `--mongodb-url` | MongoDB connection URL | `mongodb://localhost:27017` |
| `--mongodb-db` | MongoDB database name | `fastapi_crud` |
| `--output` | Output JSON file for export | `resources_export.json` |
| `--input` | Input JSON file for import | `resources_export.json` |
| `--clear-existing` | Clear existing MongoDB data before import | `False` |
| `--validate` | Validate data integrity after migration | `True` |
| `--no-validate` | Skip validation after migration | `False` |
| `--export-only` | Only export SQLite data to JSON | `False` |
| `--import-only` | Only import JSON to MongoDB | `False` |

### Post-Migration Steps

After successful migration:

1. **Update your `.env` file:**
   ```bash
   DATABASE_TYPE=mongodb
   DATABASE_URL=mongodb://localhost:27017
   MONGODB_DATABASE=fastapi_crud
   ```

2. **Restart the application:**
   ```bash
   python main.py
   ```

3. **Verify the migration:**
   - Check the API documentation: http://localhost:8000/docs
   - Test resource retrieval: `GET /api/resources`
   - Verify resource counts match

For detailed migration documentation, see [scripts/README_MIGRATION.md](scripts/README_MIGRATION.md).

## Troubleshooting

### MongoDB Connection Issues

**Problem:** `Failed to connect to MongoDB`

**Solutions:**
- Verify MongoDB is running: `mongosh --eval "db.version()"`
- Check the connection URL in your `.env` file
- Ensure MongoDB is listening on the correct port (default: 27017)
- Check firewall settings
- For MongoDB Atlas, verify IP whitelist settings

**Problem:** `Authentication failed`

**Solutions:**
- Verify username and password are correct
- Check `MONGODB_AUTH_SOURCE` is set correctly (usually `admin`)
- Ensure the user has read/write permissions on the database
- For MongoDB Atlas, verify database user is created in the Atlas UI

### MongoDB Performance Issues

**Problem:** Slow queries or timeouts

**Solutions:**
- Increase `MONGODB_TIMEOUT` in your `.env` file
- Check MongoDB indexes are created: `mongosh fastapi_crud --eval "db.resources.getIndexes()"`
- Monitor MongoDB performance: `mongosh --eval "db.serverStatus()"`
- For large datasets, consider adding more indexes

### Migration Issues

**Problem:** Migration validation fails

**Solutions:**
- Ensure both SQLite and MongoDB are accessible during migration
- Check that no other processes are modifying the databases
- Review validation error messages for specific issues
- Try re-running the migration with `--clear-existing`

**Problem:** Duplicate key errors during migration

**Solutions:**
- Use `--clear-existing` flag to remove existing data before import
- Or manually clear the MongoDB collection:
  ```bash
  mongosh fastapi_crud --eval "db.resources.deleteMany({})"
  ```

### Application Startup Issues

**Problem:** Application fails to start with MongoDB

**Solutions:**
- Check all required environment variables are set
- Verify MongoDB connection string format
- Check application logs for detailed error messages
- Test MongoDB connection manually: `mongosh <your-connection-url>`

**Problem:** Tests are skipped

**Solutions:**
- Ensure MongoDB is running for MongoDB tests
- Set `MONGODB_DATABASE` environment variable for tests
- Check test output for skip reasons

### Data Consistency Issues

**Problem:** Data appears different between SQLite and MongoDB

**Solutions:**
- Run migration validation: use `--validate` flag
- Check that timestamps are in UTC
- Verify dependency relationships are preserved
- Compare resource counts: SQLite vs MongoDB

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ServerSelectionTimeoutError` | MongoDB not reachable | Start MongoDB service |
| `OperationFailure: Authentication failed` | Invalid credentials | Check username/password |
| `ConfigurationError: Invalid URI` | Malformed connection string | Verify DATABASE_URL format |
| `DuplicateKeyError` | Resource ID already exists | Use `--clear-existing` or check for duplicates |
| `NetworkTimeout` | Network issues or slow connection | Increase MONGODB_TIMEOUT |

### Getting Help

If you encounter issues not covered here:

1. Check the application logs in `app.log`
2. Review MongoDB logs: `mongosh --eval "db.adminCommand({ getLog: 'global' })"`
3. Verify your configuration matches the examples in `.env.example`
4. Check the [MongoDB documentation](https://docs.mongodb.com/)
5. Review the spec documents in `.kiro/specs/mongodb-integration/`

### Debug Mode

Enable debug logging for more detailed information:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Run application
python main.py
```

## Additional Resources

- **MongoDB Setup Guide**: [MONGODB_SETUP.md](MONGODB_SETUP.md)
- **Migration Guide**: [scripts/README_MIGRATION.md](scripts/README_MIGRATION.md)
- **Testing Guide**: [tests/README_TESTING.md](tests/README_TESTING.md)
- **Requirements Document**: [.kiro/specs/mongodb-integration/requirements.md](.kiro/specs/mongodb-integration/requirements.md)
- **Design Document**: [.kiro/specs/mongodb-integration/design.md](.kiro/specs/mongodb-integration/design.md)
