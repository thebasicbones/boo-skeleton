# Pull Request

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test coverage improvement
- [ ] DevOps/Infrastructure change

## Related Issues

<!-- Link to related issues using #issue_number -->

Closes #
Related to #

## Changes Made

<!-- List the specific changes made in this PR -->

-
-
-

## Testing

<!-- Describe the testing you've done -->

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Property-based tests added (if applicable)
- [ ] Manual testing completed
- [ ] Tested with SQLite backend
- [ ] Tested with MongoDB backend (if applicable)

### Test Commands Run

```bash
# Example:
pytest -v
pytest --cov=app
```

## Code Quality

<!-- Confirm code quality checks -->

- [ ] Code follows project style guidelines
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Black formatting applied
- [ ] Ruff linting passes
- [ ] MyPy type checking passes
- [ ] No new warnings introduced

## Documentation

<!-- Confirm documentation updates -->

- [ ] Code comments added/updated
- [ ] Docstrings added/updated for new functions/classes
- [ ] README updated (if needed)
- [ ] API documentation updated (if needed)
- [ ] CHANGELOG.md updated (see below)

## Changelog

<!--
IMPORTANT: Update CHANGELOG.md with your changes!

Add your changes to the [Unreleased] section of CHANGELOG.md under the appropriate category:
- Added: for new features
- Changed: for changes in existing functionality
- Deprecated: for soon-to-be removed features
- Removed: for now removed features
- Fixed: for any bug fixes
- Security: in case of vulnerabilities

Example:
### Added
- New endpoint for batch resource creation
- Support for resource tagging

### Fixed
- Circular dependency detection for complex graphs
-->

- [ ] CHANGELOG.md updated with changes in the [Unreleased] section

## Breaking Changes

<!-- If this PR includes breaking changes, describe them here and provide migration instructions -->

None

## Deployment Notes

<!-- Any special deployment considerations or steps -->

None

## Screenshots

<!-- If applicable, add screenshots to help explain your changes -->

## Checklist

<!-- Final checklist before submitting -->

- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
- [ ] I have updated the CHANGELOG.md file

## Additional Notes

<!-- Any additional information that reviewers should know -->
