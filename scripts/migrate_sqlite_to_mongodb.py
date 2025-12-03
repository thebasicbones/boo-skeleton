#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to MongoDB.

This script:
1. Exports all resources from SQLite database to JSON format
2. Imports the JSON data into MongoDB
3. Validates data integrity after migration
4. Provides progress reporting and error handling

Usage:
    python scripts/migrate_sqlite_to_mongodb.py [--sqlite-url URL] [--mongodb-url URL] [--mongodb-db NAME] [--dry-run]

Examples:
    # Migrate with default settings
    python scripts/migrate_sqlite_to_mongodb.py

    # Migrate with custom database URLs
    python scripts/migrate_sqlite_to_mongodb.py --sqlite-url sqlite+aiosqlite:///./app.db --mongodb-url mongodb://localhost:27017 --mongodb-db fastapi_crud

    # Dry run to see what would be migrated without actually migrating
    python scripts/migrate_sqlite_to_mongodb.py --dry-run
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.models.sqlalchemy_resource import Resource


class MigrationStats:
    """Track migration statistics"""

    def __init__(self):
        self.resources_exported = 0
        self.resources_imported = 0
        self.validation_passed = 0
        self.validation_failed = 0
        self.errors: list[str] = []

    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Resources exported from SQLite: {self.resources_exported}")
        print(f"Resources imported to MongoDB:  {self.resources_imported}")
        print(f"Validation passed:               {self.validation_passed}")
        print(f"Validation failed:               {self.validation_failed}")

        if self.errors:
            print(f"\nErrors encountered: {len(self.errors)}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("\n✓ Migration completed successfully with no errors!")
        print("=" * 60)


async def export_sqlite_to_json(
    sqlite_url: str, output_file: str, stats: MigrationStats
) -> list[dict[str, Any]]:
    """
    Export all resources from SQLite database to JSON format.

    Args:
        sqlite_url: SQLite database connection URL
        output_file: Path to output JSON file
        stats: MigrationStats object to track progress

    Returns:
        List of resource dictionaries
    """
    print("\n[1/4] Exporting data from SQLite...")
    print(f"      Database: {sqlite_url}")

    try:
        # Create SQLite engine
        engine = create_async_engine(
            sqlite_url,
            connect_args={"check_same_thread": False} if "sqlite" in sqlite_url else {},
            echo=False,
        )

        # Create session
        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        resources_data = []

        async with AsyncSessionLocal() as session:
            # Fetch all resources with dependencies
            result = await session.execute(
                select(Resource).options(selectinload(Resource.dependencies))
            )
            resources = result.scalars().all()

            print(f"      Found {len(resources)} resources")

            # Convert to dictionaries
            for resource in resources:
                resource_dict = {
                    "id": resource.id,
                    "name": resource.name,
                    "description": resource.description,
                    "dependencies": [dep.id for dep in resource.dependencies],
                    "created_at": resource.created_at.isoformat(),
                    "updated_at": resource.updated_at.isoformat(),
                }
                resources_data.append(resource_dict)
                stats.resources_exported += 1

                # Progress indicator
                if stats.resources_exported % 10 == 0:
                    print(f"      Exported {stats.resources_exported} resources...", end="\r")

            print(f"      ✓ Exported {stats.resources_exported} resources")

        # Close engine
        await engine.dispose()

        # Write to JSON file
        with open(output_file, "w") as f:
            json.dump(resources_data, f, indent=2)

        print(f"      ✓ Data saved to {output_file}")

        return resources_data

    except Exception as e:
        error_msg = f"Failed to export from SQLite: {str(e)}"
        stats.errors.append(error_msg)
        print(f"      ✗ {error_msg}")
        raise


async def import_json_to_mongodb(
    mongodb_url: str,
    mongodb_db: str,
    resources_data: list[dict[str, Any]],
    stats: MigrationStats,
    dry_run: bool = False,
) -> None:
    """
    Import resources from JSON data into MongoDB.

    Args:
        mongodb_url: MongoDB connection URL
        mongodb_db: MongoDB database name
        resources_data: List of resource dictionaries to import
        stats: MigrationStats object to track progress
        dry_run: If True, don't actually import data
    """
    print("\n[2/4] Importing data to MongoDB...")
    print(f"      Database: {mongodb_url}/{mongodb_db}")

    if dry_run:
        print(f"      DRY RUN: Would import {len(resources_data)} resources")
        stats.resources_imported = len(resources_data)
        return

    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)

        # Verify connection
        await client.admin.command("ping")
        print("      ✓ Connected to MongoDB")

        # Get database and collection
        db = client[mongodb_db]
        collection = db.resources

        # Check if collection already has data
        existing_count = await collection.count_documents({})
        if existing_count > 0:
            print(f"      Warning: Collection already contains {existing_count} documents")
            response = input("      Do you want to clear existing data? (yes/no): ")
            if response.lower() == "yes":
                await collection.delete_many({})
                print(f"      ✓ Cleared {existing_count} existing documents")
            else:
                print("      Keeping existing data, will attempt to insert new documents")

        # Convert datetime strings back to datetime objects for MongoDB
        for resource in resources_data:
            resource["created_at"] = datetime.fromisoformat(resource["created_at"])
            resource["updated_at"] = datetime.fromisoformat(resource["updated_at"])
            # Map 'id' to '_id' for MongoDB
            resource["_id"] = resource.pop("id")

        # Insert resources
        if resources_data:
            print(f"      Importing {len(resources_data)} resources...")

            # Insert in batches for better performance
            batch_size = 100
            for i in range(0, len(resources_data), batch_size):
                batch = resources_data[i : i + batch_size]
                try:
                    result = await collection.insert_many(batch, ordered=False)
                    stats.resources_imported += len(result.inserted_ids)
                    print(
                        f"      Imported {stats.resources_imported}/{len(resources_data)} resources...",
                        end="\r",
                    )
                except Exception as e:
                    # Handle duplicate key errors gracefully
                    if "duplicate key" in str(e).lower():
                        # Count successful inserts in this batch
                        for doc in batch:
                            if await collection.find_one({"_id": doc["_id"]}) is not None:
                                stats.resources_imported += 1
                        print("      Warning: Some documents already exist, skipped duplicates")
                    else:
                        raise

            print(f"      ✓ Imported {stats.resources_imported} resources")

        # Create indexes
        print("      Creating indexes...")
        await collection.create_index("name")
        await collection.create_index("dependencies")
        print("      ✓ Indexes created")

        # Close client
        client.close()

    except Exception as e:
        error_msg = f"Failed to import to MongoDB: {str(e)}"
        stats.errors.append(error_msg)
        print(f"      ✗ {error_msg}")
        raise


async def validate_migration(
    sqlite_url: str, mongodb_url: str, mongodb_db: str, stats: MigrationStats, dry_run: bool = False
) -> bool:
    """
    Validate that data was migrated correctly by comparing SQLite and MongoDB.

    Args:
        sqlite_url: SQLite database connection URL
        mongodb_url: MongoDB connection URL
        mongodb_db: MongoDB database name
        stats: MigrationStats object to track progress
        dry_run: If True, skip validation

    Returns:
        True if validation passed, False otherwise
    """
    print("\n[3/4] Validating data integrity...")

    if dry_run:
        print("      DRY RUN: Skipping validation")
        return True

    try:
        # Connect to SQLite
        engine = create_async_engine(
            sqlite_url,
            connect_args={"check_same_thread": False} if "sqlite" in sqlite_url else {},
            echo=False,
        )
        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)
        db = client[mongodb_db]
        collection = db.resources

        # Get all resources from both databases
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Resource).options(selectinload(Resource.dependencies))
            )
            sqlite_resources = {r.id: r for r in result.scalars().all()}

        mongo_resources = {}
        cursor = collection.find({})
        async for doc in cursor:
            mongo_resources[doc["_id"]] = doc

        # Compare counts
        sqlite_count = len(sqlite_resources)
        mongo_count = len(mongo_resources)

        print(f"      SQLite resources: {sqlite_count}")
        print(f"      MongoDB resources: {mongo_count}")

        if sqlite_count != mongo_count:
            error_msg = f"Resource count mismatch: SQLite={sqlite_count}, MongoDB={mongo_count}"
            stats.errors.append(error_msg)
            print(f"      ✗ {error_msg}")
            return False

        # Validate each resource
        print(f"      Validating {sqlite_count} resources...")

        for resource_id, sqlite_resource in sqlite_resources.items():
            if resource_id not in mongo_resources:
                error_msg = f"Resource {resource_id} missing in MongoDB"
                stats.errors.append(error_msg)
                stats.validation_failed += 1
                continue

            mongo_doc = mongo_resources[resource_id]

            # Validate fields
            validation_passed = True

            if sqlite_resource.name != mongo_doc["name"]:
                error_msg = f"Name mismatch for {resource_id}: '{sqlite_resource.name}' != '{mongo_doc['name']}'"
                stats.errors.append(error_msg)
                validation_passed = False

            if sqlite_resource.description != mongo_doc.get("description"):
                error_msg = f"Description mismatch for {resource_id}"
                stats.errors.append(error_msg)
                validation_passed = False

            # Validate dependencies
            sqlite_deps = sorted([dep.id for dep in sqlite_resource.dependencies])
            mongo_deps = sorted(mongo_doc.get("dependencies", []))

            if sqlite_deps != mongo_deps:
                error_msg = (
                    f"Dependencies mismatch for {resource_id}: {sqlite_deps} != {mongo_deps}"
                )
                stats.errors.append(error_msg)
                validation_passed = False

            if validation_passed:
                stats.validation_passed += 1
            else:
                stats.validation_failed += 1

            # Progress indicator
            total_validated = stats.validation_passed + stats.validation_failed
            if total_validated % 10 == 0:
                print(f"      Validated {total_validated}/{sqlite_count} resources...", end="\r")

        print(f"      ✓ Validated {stats.validation_passed} resources")

        if stats.validation_failed > 0:
            print(f"      ✗ {stats.validation_failed} resources failed validation")

        # Close connections
        await engine.dispose()
        client.close()

        return stats.validation_failed == 0

    except Exception as e:
        error_msg = f"Validation failed: {str(e)}"
        stats.errors.append(error_msg)
        print(f"      ✗ {error_msg}")
        return False


async def migrate(
    sqlite_url: str,
    mongodb_url: str,
    mongodb_db: str,
    output_file: str = "migration_data.json",
    dry_run: bool = False,
) -> bool:
    """
    Main migration function that orchestrates the entire process.

    Args:
        sqlite_url: SQLite database connection URL
        mongodb_url: MongoDB connection URL
        mongodb_db: MongoDB database name
        output_file: Path to intermediate JSON file
        dry_run: If True, don't actually migrate data

    Returns:
        True if migration succeeded, False otherwise
    """
    stats = MigrationStats()

    print("=" * 60)
    print("SQLite to MongoDB Migration Tool")
    print("=" * 60)

    if dry_run:
        print("\n*** DRY RUN MODE - No data will be modified ***\n")

    try:
        # Step 1: Export from SQLite
        resources_data = await export_sqlite_to_json(sqlite_url, output_file, stats)

        # Step 2: Import to MongoDB
        await import_json_to_mongodb(mongodb_url, mongodb_db, resources_data, stats, dry_run)

        # Step 3: Validate migration
        validation_passed = await validate_migration(
            sqlite_url, mongodb_url, mongodb_db, stats, dry_run
        )

        # Step 4: Print summary
        print("\n[4/4] Migration complete")
        stats.print_summary()

        return validation_passed and len(stats.errors) == 0

    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        stats.errors.append(str(e))
        stats.print_summary()
        return False


def main():
    """Command-line interface for the migration script"""
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to MongoDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate with default settings
  python scripts/migrate_sqlite_to_mongodb.py

  # Migrate with custom database URLs
  python scripts/migrate_sqlite_to_mongodb.py \\
    --sqlite-url sqlite+aiosqlite:///./app.db \\
    --mongodb-url mongodb://localhost:27017 \\
    --mongodb-db fastapi_crud

  # Dry run to see what would be migrated
  python scripts/migrate_sqlite_to_mongodb.py --dry-run
        """,
    )

    parser.add_argument(
        "--sqlite-url",
        default=os.getenv("SQLITE_URL", "sqlite+aiosqlite:///./app.db"),
        help="SQLite database URL (default: sqlite+aiosqlite:///./app.db)",
    )

    parser.add_argument(
        "--mongodb-url",
        default=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        help="MongoDB connection URL (default: mongodb://localhost:27017)",
    )

    parser.add_argument(
        "--mongodb-db",
        default=os.getenv("MONGODB_DATABASE", "fastapi_crud"),
        help="MongoDB database name (default: fastapi_crud)",
    )

    parser.add_argument(
        "--output-file",
        default="migration_data.json",
        help="Intermediate JSON file for exported data (default: migration_data.json)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without actually migrating data"
    )

    args = parser.parse_args()

    # Run migration
    success = asyncio.run(
        migrate(
            sqlite_url=args.sqlite_url,
            mongodb_url=args.mongodb_url,
            mongodb_db=args.mongodb_db,
            output_file=args.output_file,
            dry_run=args.dry_run,
        )
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
