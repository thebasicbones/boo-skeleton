# SQLite to MongoDB Migration Script

This script migrates data from SQLite to MongoDB while preserving all resource data and relationships.

## Features

- **Export**: Exports all resources from SQLite to JSON format
- **Import**: Imports JSON data into MongoDB with proper document structure
- **Validation**: Verifies data integrity by comparing SQLite and MongoDB data
- **Progress Reporting**: Shows real-time progress during migration
- **Error Handling**: Gracefully handles errors and provides detailed error messages
- **Dry Run Mode**: Test migration without actually modifying data
- **Batch Processing**: Efficiently handles large datasets with batch inserts

## Prerequisites

1. Python 3.8 or higher
2. SQLite database with existing data
3. MongoDB server running and accessible
4. Required Python packages (already in requirements.txt):
   - sqlalchemy
   - aiosqlite
   - motor
   - pymongo

## Usage

### Basic Migration

Migrate with default settings (SQLite at `./app.db` to MongoDB at `localhost:27017`):

```bash
python scripts/migrate_sqlite_to_mongodb.py
```

### Custom Database URLs

Specify custom database connections:

```bash
python scripts/migrate_sqlite_to_mongodb.py \
  --sqlite-url sqlite+aiosqlite:///./my_app.db \
  --mongodb-url mongodb://localhost:27017 \
  --mongodb-db my_database
```

### Dry Run

Test the migration without actually modifying data:

```bash
python scripts/migrate_sqlite_to_mongodb.py --dry-run
```

### Using Environment Variables

You can also set database URLs via environment variables:

```bash
export SQLITE_URL="sqlite+aiosqlite:///./app.db"
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DATABASE="fastapi_crud"

python scripts/migrate_sqlite_to_mongodb.py
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sqlite-url` | SQLite database URL | `sqlite+aiosqlite:///./app.db` |
| `--mongodb-url` | MongoDB connection URL | `mongodb://localhost:27017` |
| `--mongodb-db` | MongoDB database name | `fastapi_crud` |
| `--output-file` | Intermediate JSON file path | `migration_data.json` |
| `--dry-run` | Perform dry run without modifying data | `False` |

## Migration Process

The script performs the following steps:

### 1. Export from SQLite
- Connects to SQLite database
- Fetches all resources with their dependencies
- Converts to JSON format
- Saves to intermediate JSON file

### 2. Import to MongoDB
- Connects to MongoDB
- Checks for existing data (prompts to clear if found)
- Converts datetime strings to datetime objects
- Maps `id` field to `_id` for MongoDB
- Inserts resources in batches for performance
- Creates indexes on `name` and `dependencies` fields

### 3. Validate Data Integrity
- Compares resource counts between databases
- Validates each resource field-by-field:
  - Name
  - Description
  - Dependencies
  - Timestamps
- Reports any mismatches or errors

### 4. Summary Report
- Shows migration statistics
- Lists any errors encountered
- Confirms successful migration

## Output Example

```
============================================================
SQLite to MongoDB Migration Tool
============================================================

[1/4] Exporting data from SQLite...
      Database: sqlite+aiosqlite:///./app.db
      Found 150 resources
      ✓ Exported 150 resources
      ✓ Data saved to migration_data.json

[2/4] Importing data to MongoDB...
      Database: mongodb://localhost:27017/fastapi_crud
      ✓ Connected to MongoDB
      Importing 150 resources...
      ✓ Imported 150 resources
      ✓ Indexes created

[3/4] Validating data integrity...
      SQLite resources: 150
      MongoDB resources: 150
      Validating 150 resources...
      ✓ Validated 150 resources

[4/4] Migration complete

============================================================
MIGRATION SUMMARY
============================================================
Resources exported from SQLite: 150
Resources imported to MongoDB:  150
Validation passed:               150
Validation failed:               0

✓ Migration completed successfully with no errors!
============================================================
```

## Error Handling

The script handles various error scenarios:

- **Connection Errors**: If SQLite or MongoDB is unreachable
- **Duplicate Keys**: If resources already exist in MongoDB (prompts user)
- **Validation Errors**: If data doesn't match between databases
- **Timeout Errors**: If operations take too long

All errors are logged and included in the summary report.

## Data Mapping

### SQLite to MongoDB Field Mapping

| SQLite Field | MongoDB Field | Notes |
|--------------|---------------|-------|
| `id` | `_id` | Primary key mapping |
| `name` | `name` | Direct mapping |
| `description` | `description` | Direct mapping |
| `dependencies` | `dependencies` | Array of resource IDs |
| `created_at` | `created_at` | Converted to MongoDB datetime |
| `updated_at` | `updated_at` | Converted to MongoDB datetime |

### Relationship Handling

- SQLite uses a junction table (`resource_dependencies`) for many-to-many relationships
- MongoDB stores dependencies as an array of resource IDs within each document
- The script preserves all dependency relationships during migration

## Troubleshooting

### MongoDB Connection Failed

**Error**: `Failed to connect to MongoDB`

**Solution**: 
- Ensure MongoDB is running: `mongod --version`
- Check connection URL is correct
- Verify network connectivity

### Validation Failed

**Error**: `X resources failed validation`

**Solution**:
- Check the error details in the summary
- Verify both databases are accessible
- Re-run migration if needed

### Duplicate Key Errors

**Error**: `Some documents already exist`

**Solution**:
- The script will prompt to clear existing data
- Or manually clear the MongoDB collection before migration

## Best Practices

1. **Backup First**: Always backup your SQLite database before migration
2. **Test with Dry Run**: Use `--dry-run` to verify the migration plan
3. **Check MongoDB Space**: Ensure sufficient disk space in MongoDB
4. **Monitor Progress**: Watch the progress indicators during migration
5. **Verify Results**: Review the validation summary after migration
6. **Keep JSON File**: The intermediate JSON file can be used for rollback

## Rollback

If you need to rollback the migration:

1. The intermediate JSON file contains all exported data
2. You can manually import it back to SQLite if needed
3. Or simply restore from your SQLite backup

## Performance

- Batch size: 100 resources per batch
- Typical speed: ~1000 resources per second (depends on hardware)
- Memory usage: Minimal (streaming approach)

## Support

For issues or questions:
1. Check the error messages in the summary report
2. Review the MongoDB and SQLite logs
3. Ensure all prerequisites are met
4. Verify database connectivity

## Related Documentation

- [MongoDB Setup Guide](../MONGODB_SETUP.md)
- [Requirements Document](../.kiro/specs/mongodb-integration/requirements.md)
- [Design Document](../.kiro/specs/mongodb-integration/design.md)
