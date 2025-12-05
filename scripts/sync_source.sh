#!/bin/bash
# Sync source code from src/ to fastapi_crud_cli/source/
# This ensures the CLI uses the latest code when generating projects

set -e

SOURCE_DIR="src"
TARGET_DIR="fastapi_crud_cli/source"

echo "🔄 Syncing source code from $SOURCE_DIR to $TARGET_DIR..."

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Sync app directory
echo "  📁 Syncing app/..."
rsync -av --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.log' \
    "$SOURCE_DIR/app/" "$TARGET_DIR/app/"

# Sync config directory
echo "  📁 Syncing config/..."
rsync -av --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    "$SOURCE_DIR/config/" "$TARGET_DIR/config/"

# Sync tests directory
echo "  📁 Syncing tests/..."
rsync -av --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    "$SOURCE_DIR/tests/" "$TARGET_DIR/tests/"

# Copy individual files
echo "  📄 Syncing configuration files..."
cp "$SOURCE_DIR/.coveragerc" "$TARGET_DIR/.coveragerc"
cp "$SOURCE_DIR/pytest.ini" "$TARGET_DIR/pytest.ini"
cp "$SOURCE_DIR/VERSION" "$TARGET_DIR/VERSION"

# Copy .gitignore if it exists
if [ -f "$SOURCE_DIR/.gitignore" ]; then
    cp "$SOURCE_DIR/.gitignore" "$TARGET_DIR/.gitignore"
fi

echo "✅ Sync complete!"
echo ""
echo "📊 Summary:"
echo "  - app/ directory synced"
echo "  - config/ directory synced"
echo "  - tests/ directory synced"
echo "  - Configuration files synced"
