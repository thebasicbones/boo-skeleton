# MongoDB Setup for Testing

## Current Status

The property-based tests for CRUD round-trip consistency have been implemented and are working correctly:

- ✅ **SQLAlchemy tests**: Passing (100 examples tested)
- ⏭️ **MongoDB tests**: Skipped (MongoDB not available)

## Why MongoDB Tests Are Skipped

The tests automatically detect if MongoDB is available on your system. Currently, MongoDB is not installed or running, so the MongoDB-specific tests are gracefully skipped. This is the expected behavior and allows development to continue without MongoDB.

## Running MongoDB Tests

To run the full test suite including MongoDB tests, you need to have MongoDB running. Here are your options:

### Option 1: Install MongoDB Locally (Homebrew on macOS)

```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Verify it's running
mongosh --eval "db.version()"
```

### Option 2: Use Docker

```bash
# Pull and run MongoDB container
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Verify it's running
docker ps | grep mongodb
```

### Option 3: Use MongoDB Atlas (Cloud)

Set environment variables to point to your MongoDB Atlas cluster:

```bash
export DATABASE_URL="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
export MONGODB_DATABASE="fastapi_crud_test"
```

## Running Tests After MongoDB Setup

Once MongoDB is available, run the tests:

```bash
# Run all CRUD round-trip tests
python -m pytest tests/test_property_crud_roundtrip_consistency.py -v

# Run only MongoDB tests
python -m pytest tests/test_property_crud_roundtrip_consistency.py::test_mongodb_crud_roundtrip_consistency -v

# Run backend equivalence test
python -m pytest tests/test_property_crud_roundtrip_consistency.py::test_backend_equivalence_crud_roundtrip -v
```

## Test Coverage

The implemented property tests verify:

1. **SQLAlchemy CRUD Round-trip**: Creates a resource and verifies all fields are preserved when retrieved
2. **MongoDB CRUD Round-trip**: Same verification for MongoDB backend
3. **Backend Equivalence**: Verifies both backends behave identically for the same operations

Each test runs 100 iterations (50 for equivalence test) with randomly generated data using Hypothesis property-based testing.

## Environment Variables

For MongoDB testing, you can configure:

```bash
# MongoDB connection URL (default: mongodb://localhost:27017)
export DATABASE_URL="mongodb://localhost:27017"

# Database name for testing (default: fastapi_crud_test)
export MONGODB_DATABASE="fastapi_crud_test"

# Connection timeout in milliseconds (default: 5000)
export MONGODB_TIMEOUT="5000"
```

## CI/CD Considerations

For continuous integration, consider:

1. Using Docker Compose to spin up MongoDB for tests
2. Using GitHub Actions with MongoDB service containers
3. Configuring test databases to be automatically cleaned up after tests

Example GitHub Actions configuration:

```yaml
services:
  mongodb:
    image: mongo:7.0
    ports:
      - 27017:27017
```


## Migrating from SQLite to MongoDB

The project includes a migration script to help you migrate existing data from SQLite to MongoDB.

### Migration Script Location

```
scripts/migrate_sqlite_to_mongodb.py
```

### Migration Options

#### 1. Full Migration with Validation

Migrate all data from SQLite to MongoDB and validate the migration:

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing
```

#### 2. Export to JSON Only

Export SQLite data to a JSON file for backup or manual inspection:

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --export-only \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --output backup.json
```

#### 3. Import from JSON Only

Import previously exported JSON data into MongoDB:

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
| `--validate` | Validate data integrity after migration | `True` (default) |
| `--no-validate` | Skip validation after migration | `False` |
| `--export-only` | Only export SQLite data to JSON | `False` |
| `--import-only` | Only import JSON to MongoDB | `False` |

### Migration Process

The migration script performs the following steps:

1. **Export**: Reads all resources from SQLite database including dependencies
2. **Import**: Writes resources to MongoDB with proper document structure
3. **Validation** (optional): Verifies that all data was migrated correctly by:
   - Comparing resource counts
   - Validating each resource's fields
   - Checking dependency relationships

### Migration Validation

The validation step ensures data integrity by:

- Verifying resource counts match between SQLite and MongoDB
- Checking that all resource IDs exist in both databases
- Validating that field values (name, description) are identical
- Ensuring dependency relationships are preserved

If validation fails, the script will:
- Report the number of errors found
- Display the first 10 validation errors
- Exit with a non-zero status code

### Example Migration Workflow

```bash
# Step 1: Backup current SQLite data
python scripts/migrate_sqlite_to_mongodb.py \
  --export-only \
  --output backup_$(date +%Y%m%d).json

# Step 2: Start MongoDB (if not already running)
brew services start mongodb-community
# or
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Step 3: Perform migration with validation
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db fastapi_crud \
  --validate \
  --clear-existing

# Step 4: Update application configuration
export DATABASE_TYPE=mongodb
export DATABASE_URL=mongodb://localhost:27017
export MONGODB_DATABASE=fastapi_crud

# Step 5: Restart application
python main.py
```

### Troubleshooting Migration

**Error: "Failed to connect to MongoDB"**
- Ensure MongoDB is running: `mongosh --eval "db.version()"`
- Check the connection URL is correct
- Verify network connectivity

**Error: "Duplicate key error"**
- Use `--clear-existing` flag to remove existing data before import
- Or manually clear the MongoDB collection: `mongosh fastapi_crud --eval "db.resources.deleteMany({})"`

**Validation Failures**
- Check that both databases are accessible during validation
- Ensure no other processes are modifying the databases during migration
- Review the validation error messages for specific issues

### Performance Considerations

- The script imports resources in batches of 100 for better performance
- Large databases (>10,000 resources) may take several minutes to migrate
- Progress is reported during import to track migration status
- Indexes are created automatically after import

### Safety Features

- The script never modifies the source SQLite database
- Use `--clear-existing` flag to explicitly clear MongoDB data
- Validation is enabled by default to catch migration issues
- All operations are logged with clear status messages
