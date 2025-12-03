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
