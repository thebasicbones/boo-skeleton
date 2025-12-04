# Release Process

This document describes the automated release process for the FastAPI CRUD Backend project.

## Overview

The project uses semantic versioning (MAJOR.MINOR.PATCH) and automated GitHub Actions workflows to create releases. When a version tag is pushed, the workflow automatically:

1. Validates the version format and consistency
2. Runs the full test suite
3. Builds documentation
4. Extracts changelog entries
5. Creates a GitHub release with release notes and documentation

## Prerequisites

- Write access to the repository
- Ability to push tags
- All tests passing on the main branch

## Release Steps

### 1. Prepare the Release

Update the VERSION file with the new version number:

```bash
echo "1.0.1" > VERSION
```

### 2. Update the CHANGELOG

Add a new section to `CHANGELOG.md` for the new version:

```markdown
## [1.0.1] - 2024-12-05

### Added
- New feature descriptions

### Fixed
- Bug fix descriptions
```

Make sure to follow the [Keep a Changelog](https://keepachangelog.com/) format.

### 3. Commit Changes

```bash
git add VERSION CHANGELOG.md
git commit -m "Prepare release v1.0.1"
git push origin main
```

### 4. Create and Push Tag

```bash
git tag v1.0.1
git push origin v1.0.1
```


### 5. Monitor the Release Workflow

Once the tag is pushed, GitHub Actions will automatically:

- Validate the version format matches semantic versioning
- Verify VERSION file matches the tag
- Check CHANGELOG.md contains the version entry
- Run tests on Python 3.10, 3.11, and 3.12
- Build Sphinx documentation
- Extract changelog for the version
- Create a GitHub release with:
  - Release notes from CHANGELOG.md
  - Documentation archive (tar.gz)
  - Automatic source code archives

Monitor the workflow at: `https://github.com/YOUR_ORG/YOUR_REPO/actions`

## Release Types

### Regular Release

For normal releases, use standard semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release
- `v1.0.1` - Patch release

### Pre-release

For pre-releases, append a suffix:
- `v1.0.0-alpha.1` - Alpha release
- `v1.0.0-beta.1` - Beta release
- `v1.0.0-rc.1` - Release candidate

Pre-releases are automatically marked as "pre-release" in GitHub.

## Testing the Release Process

Before creating an actual release, you can test the workflow locally:

```bash
./test_release_workflow.sh
```

This script validates:
- VERSION file format
- CHANGELOG.md structure
- Changelog extraction logic
- Workflow YAML syntax
- Documentation build

## Troubleshooting

### Version Mismatch Error

If the workflow fails with "VERSION file does not match tag":
- Ensure VERSION file contains only the version number (e.g., `1.0.1`)
- Ensure the tag matches exactly (e.g., `v1.0.1`)
- No extra whitespace or newlines

### Missing Changelog Entry

If the workflow fails with "CHANGELOG.md does not contain entry":
- Add a section with `## [VERSION] - DATE` format
- Ensure the version number matches exactly

### Test Failures

If tests fail during the release:
- Fix the failing tests
- Push the fixes to main
- Delete and recreate the tag:
  ```bash
  git tag -d v1.0.1
  git push origin :refs/tags/v1.0.1
  git tag v1.0.1
  git push origin v1.0.1
  ```

## Rollback

If a release needs to be rolled back:

1. Delete the GitHub release (in GitHub UI)
2. Delete the tag locally and remotely:
   ```bash
   git tag -d v1.0.1
   git push origin :refs/tags/v1.0.1
   ```
3. Fix the issues
4. Create a new patch release

## Best Practices

1. **Always test before releasing**: Run the full test suite locally
2. **Review the changelog**: Ensure all changes are documented
3. **Use descriptive commit messages**: They help generate changelogs
4. **Follow semantic versioning**: Breaking changes = major, features = minor, fixes = patch
5. **Keep releases small**: Smaller, frequent releases are easier to manage
6. **Document breaking changes**: Clearly mark breaking changes in CHANGELOG.md

## Automation Details

The release workflow (`.github/workflows/release.yml`) consists of four jobs:

1. **validate**: Checks version format and changelog
2. **test**: Runs full test suite on multiple Python versions
3. **build-docs**: Builds Sphinx documentation
4. **create-release**: Creates GitHub release with artifacts

All jobs must pass for the release to be created.
