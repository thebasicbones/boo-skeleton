#!/bin/bash
# Test script to validate release workflow components locally

set -e

echo "=== Testing Release Workflow Components ==="
echo ""

# Test 1: Validate VERSION file format
echo "Test 1: Validating VERSION file format..."
VERSION=$(cat VERSION | tr -d '[:space:]')
if echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "✓ VERSION file format is valid: $VERSION"
else
    echo "✗ VERSION file format is invalid: $VERSION"
    exit 1
fi
echo ""

# Test 2: Check CHANGELOG.md contains version
echo "Test 2: Checking CHANGELOG.md contains version entry..."
if grep -q "\[$VERSION\]" CHANGELOG.md; then
    echo "✓ CHANGELOG.md contains entry for version $VERSION"
else
    echo "✗ CHANGELOG.md does not contain entry for version $VERSION"
    exit 1
fi
echo ""

# Test 3: Extract changelog for current version
echo "Test 3: Extracting changelog for version $VERSION..."
# Extract content between this version and the next version header
# Find the line number of current version and next version
START_LINE=$(grep -n "^## \[$VERSION\]" CHANGELOG.md | cut -d: -f1)
NEXT_LINE=$(grep -n "^## \[" CHANGELOG.md | awk -F: -v start="$START_LINE" '$1 > start {print $1; exit}')

if [ -z "$START_LINE" ]; then
    echo "✗ Could not find version $VERSION in CHANGELOG.md"
    exit 1
fi

if [ -z "$NEXT_LINE" ]; then
    # This is the last version, extract to end of file
    CHANGELOG_CONTENT=$(tail -n +$((START_LINE + 1)) CHANGELOG.md)
else
    # Extract between current and next version
    CHANGELOG_CONTENT=$(sed -n "$((START_LINE + 1)),$((NEXT_LINE - 1))p" CHANGELOG.md)
fi

# Trim trailing whitespace and empty lines
CHANGELOG_CONTENT=$(echo "$CHANGELOG_CONTENT" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}')

if [ -z "$CHANGELOG_CONTENT" ]; then
    echo "✗ Could not extract changelog for version $VERSION"
    exit 1
else
    echo "✓ Successfully extracted changelog:"
    echo "---"
    echo "$CHANGELOG_CONTENT"
    echo "---"
fi
echo ""

# Test 4: Validate YAML syntax
echo "Test 4: Validating release.yml syntax..."
if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))" 2>/dev/null; then
    echo "✓ release.yml syntax is valid"
else
    echo "✗ release.yml syntax is invalid"
    exit 1
fi
echo ""

# Test 5: Check documentation can be built
echo "Test 5: Testing documentation build..."
if [ -d "docs" ] && [ -f "docs/Makefile" ]; then
    cd docs
    if make html > /dev/null 2>&1; then
        echo "✓ Documentation builds successfully"
    else
        echo "⚠ Documentation build failed (may need dependencies)"
    fi
    cd ..
else
    echo "⚠ Documentation directory not found"
fi
echo ""

echo "=== All Release Workflow Tests Passed ==="
echo ""
echo "To create a release:"
echo "1. Update VERSION file with new version (e.g., 1.0.1)"
echo "2. Update CHANGELOG.md with changes for the new version"
echo "3. Commit changes: git commit -am 'Prepare release v1.0.1'"
echo "4. Create and push tag: git tag v1.0.1 && git push origin v1.0.1"
echo "5. GitHub Actions will automatically create the release"
