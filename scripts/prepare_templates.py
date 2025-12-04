#!/usr/bin/env python3
"""
Script to prepare template files for CLI packaging.

This script copies the source files from the project root into the
templates/source directory so they can be packaged with the CLI tool.
"""

import shutil
from pathlib import Path


def main():
    """Copy source files from src/ to fastapi_crud_cli/source/ for packaging."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define source and destination
    source_root = project_root / "src"
    dest_root = project_root / "fastapi_crud_cli" / "source"

    if not source_root.exists():
        print(f"Error: Source directory not found: {source_root}")
        print("Please ensure the project structure has a 'src/' directory.")
        return

    # Create destination directory
    dest_root.mkdir(parents=True, exist_ok=True)

    # Files and directories to copy
    items_to_copy = [
        # App directory
        "app/__init__.py",
        "app/schemas.py",
        "app/exceptions.py",
        "app/error_handlers.py",
        "app/models/__init__.py",
        "app/models/sqlalchemy_resource.py",
        "app/repositories/__init__.py",
        "app/repositories/base_resource_repository.py",
        "app/repositories/sqlalchemy_resource_repository.py",
        "app/repositories/mongodb_resource_repository.py",
        "app/services/__init__.py",
        "app/services/resource_service.py",
        "app/services/topological_sort_service.py",
        "app/routers/__init__.py",
        "app/routers/resources.py",
        # Config directory
        "config/__init__.py",
        # Tests directory
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_api_endpoints.py",
        # Root files
        ".coveragerc",
        "pytest.ini",
        ".gitignore",
        "VERSION",
    ]

    print("Copying source files from src/ to fastapi_crud_cli/source/...")
    copied_count = 0
    skipped_count = 0

    for item in items_to_copy:
        source_path = source_root / item
        dest_path = dest_root / item

        if not source_path.exists():
            print(f"  ⚠ Skipped (not found): {item}")
            skipped_count += 1
            continue

        # Create parent directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source_path, dest_path)
        print(f"  ✓ Copied: {item}")
        copied_count += 1

    print("\nSummary:")
    print(f"  Copied: {copied_count} files")
    print(f"  Skipped: {skipped_count} files")
    print(f"\nTemplate source files are ready in: {dest_root}")


if __name__ == "__main__":
    main()
