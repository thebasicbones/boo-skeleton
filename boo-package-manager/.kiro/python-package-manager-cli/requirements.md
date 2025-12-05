# Requirements Document

## Introduction

This document specifies the requirements for a Python package manager CLI tool called "boo" that combines functionality from pip, pipdeptree, and other package management tools. The CLI leverages the existing boo-package-manager backend infrastructure, where:

- **Resources represent Python packages** with metadata (name, version, description)
- **Dependencies track package requirements** (e.g., requests depends on urllib3)
- **Topological sorting determines installation order** (install dependencies before dependents)
- **Circular dependency detection prevents conflicts** (e.g., A→B→A is invalid)
- **Cascade delete handles uninstallation** (remove packages and their orphaned dependencies)
- **Search/filter enables package discovery** (find packages by name, description, or tags)

The CLI will act as a frontend to this backend, translating package management operations into CRUD operations on resources.

## Architecture Overview

### Existing Backend (boo-package-manager)

The boo-package-manager is a FastAPI-based backend located in the `boo-package-manager/` directory with the following structure:

```
boo-package-manager/
├── app/
│   ├── routers/resources.py          # REST API endpoints
│   ├── services/
│   │   ├── resource_service.py       # Business logic
│   │   └── topological_sort_service.py  # Dependency ordering
│   ├── repositories/                 # Data access layer
│   ├── models/                       # Database models
│   ├── schemas.py                    # Pydantic schemas
│   ├── exceptions.py                 # Custom exceptions
│   └── database_factory.py           # Database abstraction
├── config/settings.py                # Configuration
└── main.py                          # FastAPI application
```

**Key Backend Features Used by CLI:**

1. **CRUD Operations** (`app/routers/resources.py`):
   - `POST /api/resources` - Create package (install)
   - `GET /api/resources` - List all packages
   - `GET /api/resources/{id}` - Get package details
   - `PUT /api/resources/{id}` - Update package (upgrade)
   - `DELETE /api/resources/{id}?cascade=true` - Delete package (uninstall)

2. **Search & Filter** (`app/routers/resources.py`):
   - `GET /api/search?q=<query>` - Search packages, returns results in topological order

3. **Topological Sort** (`app/services/topological_sort_service.py`):
   - Kahn's algorithm implementation
   - Determines correct installation order (dependencies before dependents)
   - Used by search endpoint to return ordered results

4. **Circular Dependency Detection** (`app/services/topological_sort_service.py`):
   - Validates dependency graphs on create/update
   - Raises `CircularDependencyError` with cycle path
   - Prevents impossible dependency situations

5. **Cascade Delete** (`app/services/resource_service.py`):
   - Deletes a package and all packages that depend on it
   - Tracks and reports number of packages removed

6. **Database Support** (`app/database_factory.py`):
   - MongoDB (production)
   - SQLite (development)
   - Repository pattern for database abstraction

### New CLI Component (This Spec)

The CLI will be a new component that:

1. **Wraps the Backend API**: Translates user commands into HTTP requests to the backend
2. **Manages Local Packages**: Uses pip as the underlying installer (via subprocess)
3. **Syncs with Backend**: Keeps backend Resources in sync with locally installed packages
4. **Provides User Interface**: Rich terminal UI with colors, progress bars, and formatted output

**Why Use pip?**

For the MVP, boo uses pip as the underlying package installer because:
- **Proven & Reliable**: pip is mature and handles all PyPI package formats (wheels, source distributions, etc.)
- **Faster Development**: Allows us to focus on dependency management and UX improvements
- **Full Compatibility**: Works with all existing PyPI packages without modification
- **Lower Maintenance**: pip team handles installation edge cases and updates

**What boo adds on top of pip:**
- **Smart Dependency Resolution**: Backend validates and orders dependencies before installation
- **Conflict Prevention**: Detects circular dependencies before attempting installation
- **Team Collaboration**: Centralized tracking of packages across projects
- **Better UX**: Rich terminal output, progress tracking, and helpful error messages
- **Advanced Features**: Dependency trees, security auditing, lock files, and more

Think of it like how **yarn** and **npm** both use the npm registry, or how **poetry** uses pip internally - the value is in the dependency management and user experience, not reinventing package installation.

**CLI Architecture:**

```
boo-cli/                              # New CLI component
├── boo/
│   ├── commands/                     # Command implementations
│   │   ├── install.py               # boo install
│   │   ├── uninstall.py             # boo uninstall
│   │   ├── list.py                  # boo list
│   │   ├── tree.py                  # boo tree
│   │   ├── search.py                # boo search
│   │   └── ...
│   ├── api/
│   │   └── client.py                # Backend API client
│   ├── package_manager/
│   │   └── pip_wrapper.py           # Wrapper around pip
│   ├── ui/
│   │   ├── console.py               # Rich console output
│   │   └── formatters.py            # Output formatting
│   ├── config.py                    # CLI configuration
│   └── main.py                      # CLI entry point
├── tests/                           # Test suite
└── pyproject.toml                   # Package metadata
```

**Data Flow Example (Install Command):**

```
User: boo install requests
    ↓
1. CLI fetches package metadata from PyPI API
    ↓
2. CLI calls backend: POST /api/resources
   {
     "name": "requests",
     "version": "2.31.0",
     "dependencies": ["urllib3", "certifi", "charset-normalizer", "idna"]
   }
    ↓
3. Backend validates dependencies (checks for circular dependencies)
    ↓
4. Backend performs topological sort and returns installation order:
   [urllib3, certifi, charset-normalizer, idna, requests]
    ↓
5. CLI installs packages in order using pip subprocess:
   - subprocess.run(["pip", "install", "urllib3"])
   - subprocess.run(["pip", "install", "certifi"])
   - subprocess.run(["pip", "install", "charset-normalizer"])
   - subprocess.run(["pip", "install", "idna"])
   - subprocess.run(["pip", "install", "requests"])
    ↓
6. CLI verifies installation and updates backend with actual installed versions
    ↓
7. CLI displays success message with dependency tree
```

**Key Insight:** Boo doesn't replace pip - it enhances it with better dependency management, conflict detection, and team collaboration features.

### Integration Points

| CLI Operation | Backend Endpoint | Backend Service | Purpose |
|---------------|------------------|-----------------|---------|
| `boo install` | `POST /api/resources` | `resource_service.create_resource()` | Create package resource, validate dependencies |
| `boo uninstall` | `DELETE /api/resources/{id}` | `resource_service.delete_resource()` | Remove package, optionally cascade |
| `boo list` | `GET /api/resources` | `resource_service.get_all_resources()` | Retrieve all packages |
| `boo search` | `GET /api/search?q=` | `resource_service.search_resources()` | Search and return in topo order |
| `boo tree` | `GET /api/resources` | `topological_sort_service.topological_sort()` | Build dependency tree |
| `boo check` | `GET /api/resources` | `topological_sort_service.validate_no_cycles()` | Detect conflicts |
| `boo update` | `PUT /api/resources/{id}` | `resource_service.update_resource()` | Update package version |
| `boo sync` | Multiple endpoints | Multiple services | Sync local with backend |

This architecture allows the CLI to leverage the backend's robust dependency management while providing a familiar command-line interface for Python developers.

## Glossary

- **CLI**: Command Line Interface - the text-based interface for user interaction
- **Package**: A Python package represented as a Resource in the backend (name, version, description, dependencies)
- **Dependency Tree**: A hierarchical representation of package dependencies, computed via topological sort
- **Virtual Environment**: An isolated Python environment for package installation
- **Package Registry**: PyPI or the boo backend's resource database
- **Boo Backend**: The existing FastAPI-based boo-package-manager service with CRUD + topological sort
- **Conflict**: Circular dependency detected by the backend's validation logic
- **Lock File**: A snapshot of all installed packages with exact versions
- **Topological Order**: The correct installation sequence where dependencies are installed before dependents
- **Cascade Delete**: Removing a package and all packages that depend on it

## Requirements

### Requirement 1

**User Story:** As a Python developer, I want to install packages from PyPI, so that I can add dependencies to my project.

#### Acceptance Criteria

1. WHEN a user executes `boo install <package-name>` THEN the CLI SHALL fetch package metadata from PyPI, create a Resource in the backend, and install the package
2. WHEN a user executes `boo install <package-name>==<version>` THEN the CLI SHALL install the specific version and store it in the backend
3. WHEN a user executes `boo install -r requirements.txt` THEN the CLI SHALL parse the file, create Resources for each package, and use topological sort to determine installation order
4. WHEN installing packages THEN the CLI SHALL use the backend's topological sort endpoint to determine the correct installation order
5. WHEN a package installation fails THEN the CLI SHALL display a clear error message and rollback the Resource creation in the backend

### Requirement 2

**User Story:** As a Python developer, I want to uninstall packages, so that I can remove unused dependencies from my project.

#### Acceptance Criteria

1. WHEN a user executes `boo uninstall <package-name>` THEN the CLI SHALL query the backend for packages that depend on it and uninstall the package
2. WHEN a user uninstalls a package with dependents THEN the CLI SHALL use the backend's search to find dependent packages and warn the user
3. WHEN a user executes `boo uninstall <package-name> --cascade` THEN the CLI SHALL use the backend's cascade delete to remove the package and all dependents
4. WHEN a package uninstallation completes THEN the CLI SHALL delete the Resource from the backend and display a confirmation message
5. WHEN a user attempts to uninstall a non-existent package THEN the CLI SHALL receive a 404 from the backend and display an error message

### Requirement 3

**User Story:** As a Python developer, I want to view installed packages in a tree structure, so that I can understand dependency relationships.

#### Acceptance Criteria

1. WHEN a user executes `boo tree` THEN the CLI SHALL fetch all Resources from the backend and build a hierarchical tree from their dependencies
2. WHEN displaying the dependency tree THEN the CLI SHALL show each package with its version and dependencies indented beneath it
3. WHEN a user executes `boo tree <package-name>` THEN the CLI SHALL fetch the specific Resource and recursively fetch its dependencies to build a subtree
4. WHEN a user executes `boo tree --depth <n>` THEN the CLI SHALL limit the tree traversal to n levels deep
5. WHEN circular dependencies exist THEN the CLI SHALL receive a CircularDependencyError from the backend and display it in the tree

### Requirement 4

**User Story:** As a Python developer, I want to detect dependency conflicts, so that I can resolve version incompatibilities.

#### Acceptance Criteria

1. WHEN a user executes `boo check` THEN the CLI SHALL fetch all Resources from the backend and validate their dependency graph
2. WHEN the backend detects circular dependencies THEN the CLI SHALL display the cycle path returned by the CircularDependencyError
3. WHEN a user installs a package that would create a conflict THEN the backend's validation SHALL reject the Resource creation and the CLI SHALL display the error
4. WHEN no conflicts are detected THEN the CLI SHALL display a success message confirming environment health
5. WHEN the CLI detects conflicts THEN the CLI SHALL use the backend's topological sort to suggest a valid installation order

### Requirement 5

**User Story:** As a Python developer, I want to list all installed packages, so that I can see what is in my environment.

#### Acceptance Criteria

1. WHEN a user executes `boo list` THEN the CLI SHALL call the backend's GET /api/resources endpoint to retrieve all packages
2. WHEN a user executes `boo list --outdated` THEN the CLI SHALL compare backend Resource versions with PyPI latest versions
3. WHEN a user executes `boo list --format json` THEN the CLI SHALL output the Resources in JSON format
4. WHEN displaying outdated packages THEN the CLI SHALL show the Resource version and latest PyPI version
5. WHEN a user executes `boo list --filter <pattern>` THEN the CLI SHALL use the backend's GET /api/search endpoint with the pattern

### Requirement 6

**User Story:** As a Python developer, I want to search for packages, so that I can discover packages to install.

#### Acceptance Criteria

1. WHEN a user executes `boo search <query>` THEN the CLI SHALL call the backend's GET /api/search?q=<query> endpoint
2. WHEN displaying search results THEN the CLI SHALL show the Resource name, description, and dependencies from the backend
3. WHEN a user executes `boo search <query> --limit <n>` THEN the CLI SHALL display at most n results from the backend response
4. WHEN no packages match the search query THEN the CLI SHALL receive an empty list from the backend and display a message
5. WHEN search results are available THEN the CLI SHALL display them in topological order as returned by the backend

### Requirement 7

**User Story:** As a Python developer, I want to update packages, so that I can get the latest features and security fixes.

#### Acceptance Criteria

1. WHEN a user executes `boo update <package-name>` THEN the CLI SHALL fetch the latest version from PyPI and use the backend's PUT /api/resources/{id} to update the Resource
2. WHEN a user executes `boo update --all` THEN the CLI SHALL iterate through all Resources and update each one
3. WHEN updating a package would break dependencies THEN the backend's validation SHALL detect circular dependencies and reject the update
4. WHEN a package update completes THEN the CLI SHALL display the old Resource version and new Resource version
5. WHEN a user executes `boo update --dry-run` THEN the CLI SHALL fetch latest versions but not call the backend's update endpoint

### Requirement 8

**User Story:** As a Python developer, I want to generate a lock file, so that I can ensure reproducible installations.

#### Acceptance Criteria

1. WHEN a user executes `boo lock` THEN the CLI SHALL generate a lock file with exact versions of all installed packages
2. WHEN generating a lock file THEN the CLI SHALL include transitive dependencies with their exact versions
3. WHEN a user executes `boo install --locked` THEN the CLI SHALL install packages using the exact versions from the lock file
4. WHEN the lock file is outdated THEN the CLI SHALL warn the user when installing
5. WHEN generating a lock file THEN the CLI SHALL include package hashes for verification

### Requirement 9

**User Story:** As a Python developer, I want to sync my environment with the boo backend, so that I can track packages across projects and teams.

#### Acceptance Criteria

1. WHEN a user executes `boo sync` THEN the CLI SHALL compare local packages with backend Resources and create/update Resources as needed
2. WHEN syncing with the backend THEN the CLI SHALL use the backend's POST /api/resources and PUT /api/resources/{id} endpoints
3. WHEN a user executes `boo sync --pull` THEN the CLI SHALL fetch all Resources from GET /api/resources and install missing packages
4. WHEN the backend is unavailable THEN the CLI SHALL cache operations locally and retry when the backend is reachable
5. WHEN syncing completes THEN the CLI SHALL display a summary showing created, updated, and deleted Resources

### Requirement 10

**User Story:** As a Python developer, I want to visualize dependency graphs, so that I can understand complex dependency relationships.

#### Acceptance Criteria

1. WHEN a user executes `boo graph` THEN the CLI SHALL fetch all Resources from the backend and build a graph from their dependencies
2. WHEN generating a graph THEN the CLI SHALL support output formats including ASCII art, DOT, and JSON
3. WHEN a user executes `boo graph --output graph.png` THEN the CLI SHALL convert the Resource dependency data to an image file
4. WHEN displaying the graph THEN the CLI SHALL use the backend's CircularDependencyError response to highlight cycles
5. WHEN a user executes `boo graph <package-name>` THEN the CLI SHALL fetch the Resource and its transitive dependencies to build a subgraph

### Requirement 11

**User Story:** As a Python developer, I want to analyze package security, so that I can identify vulnerable dependencies.

#### Acceptance Criteria

1. WHEN a user executes `boo audit` THEN the CLI SHALL check all installed packages against known vulnerability databases
2. WHEN vulnerabilities are found THEN the CLI SHALL display each vulnerability with severity level and affected versions
3. WHEN a user executes `boo audit --fix` THEN the CLI SHALL attempt to upgrade vulnerable packages to safe versions
4. WHEN no vulnerabilities are found THEN the CLI SHALL display a success message
5. WHEN the CLI cannot fix a vulnerability THEN the CLI SHALL suggest manual remediation steps

### Requirement 12

**User Story:** As a Python developer, I want to manage virtual environments, so that I can isolate project dependencies.

#### Acceptance Criteria

1. WHEN a user executes `boo env create <name>` THEN the CLI SHALL create a new virtual environment
2. WHEN a user executes `boo env activate <name>` THEN the CLI SHALL provide instructions to activate the environment
3. WHEN a user executes `boo env list` THEN the CLI SHALL display all managed virtual environments
4. WHEN a user executes `boo env delete <name>` THEN the CLI SHALL remove the specified virtual environment
5. WHEN operating within a virtual environment THEN the CLI SHALL display the active environment name in command output

### Requirement 13

**User Story:** As a Python developer, I want to export my environment, so that I can share it with others or deploy it.

#### Acceptance Criteria

1. WHEN a user executes `boo export` THEN the CLI SHALL generate a requirements.txt file with all installed packages
2. WHEN a user executes `boo export --format poetry` THEN the CLI SHALL generate a pyproject.toml file
3. WHEN a user executes `boo export --format conda` THEN the CLI SHALL generate an environment.yml file
4. WHEN exporting THEN the CLI SHALL include only top-level dependencies by default
5. WHEN a user executes `boo export --all` THEN the CLI SHALL include all transitive dependencies

### Requirement 14

**User Story:** As a Python developer, I want to configure the CLI behavior, so that I can customize it to my workflow.

#### Acceptance Criteria

1. WHEN a user executes `boo config set <key> <value>` THEN the CLI SHALL store the configuration setting
2. WHEN a user executes `boo config get <key>` THEN the CLI SHALL display the current value of the setting
3. WHEN a user executes `boo config list` THEN the CLI SHALL display all configuration settings
4. WHEN the CLI starts THEN the CLI SHALL load configuration from a config file in the user's home directory
5. WHEN a configuration setting is invalid THEN the CLI SHALL display an error message and use the default value

### Requirement 15

**User Story:** As a Python developer, I want helpful command documentation, so that I can learn how to use the CLI effectively.

#### Acceptance Criteria

1. WHEN a user executes `boo --help` THEN the CLI SHALL display a list of all available commands with brief descriptions
2. WHEN a user executes `boo <command> --help` THEN the CLI SHALL display detailed help for that specific command
3. WHEN displaying help THEN the CLI SHALL show command syntax, options, and usage examples
4. WHEN a user enters an invalid command THEN the CLI SHALL suggest similar valid commands
5. WHEN a user executes `boo docs` THEN the CLI SHALL open the online documentation in a web browser


## Future Enhancements

The following features are planned for future releases but are not part of the initial MVP:

### Advanced Package Management

- **Custom Package Installer**: Replace pip with a native boo installer for full control over installation process
  - Direct wheel and source distribution handling
  - Optimized installation pipeline
  - Better error recovery and rollback
  - Custom package format support
- **Package Publishing**: `boo publish` - Publish packages to PyPI or private registries
- **Private Registry Support**: Configure and use private package repositories
- **Package Signing**: Verify package integrity with GPG signatures
- **Multi-version Support**: Install and manage multiple versions of the same package side-by-side
- **Workspace Management**: Manage monorepos with multiple packages and shared dependencies

### Enhanced Dependency Management

- **Dependency Resolution Strategies**: Configure resolution algorithms (e.g., prefer latest, prefer stable)
- **Peer Dependencies**: Support for peer dependency patterns like npm
- **Optional Dependencies**: Mark dependencies as optional with conditional installation
- **Dependency Constraints**: Define version constraints and compatibility matrices
- **Automatic Conflict Resolution**: AI-powered suggestions for resolving version conflicts

### Team Collaboration Features

- **Team Workspaces**: Share package configurations across team members via backend
- **Package Approval Workflow**: Require approval before installing certain packages
- **Usage Analytics**: Track which packages are used across projects and teams
- **Dependency Policies**: Enforce organizational policies (e.g., no GPL licenses, security requirements)
- **Change Notifications**: Alert team members when dependencies are updated

### Developer Experience

- **Interactive Mode**: `boo interactive` - Interactive package management with autocomplete
- **Shell Integration**: Autocomplete for bash/zsh/fish shells
- **IDE Plugins**: VSCode, PyCharm, and other IDE integrations
- **Package Recommendations**: Suggest packages based on project type and dependencies
- **Dependency Impact Analysis**: Show what will be affected before making changes

### Performance & Optimization

- **Parallel Installation**: Install multiple packages concurrently
- **Caching Layer**: Local cache for package metadata and downloads
- **Incremental Updates**: Only download changed files during updates
- **Bandwidth Optimization**: Resume interrupted downloads, delta updates
- **Build Caching**: Cache compiled packages for faster reinstallation

### Security & Compliance

- **License Scanning**: Identify and report package licenses
- **SBOM Generation**: Generate Software Bill of Materials (SBOM) for compliance
- **Vulnerability Scanning**: Continuous monitoring for new vulnerabilities
- **Supply Chain Security**: Verify package provenance and detect tampering
- **Compliance Reports**: Generate reports for security audits

### Advanced Visualization

- **Interactive Dependency Graph**: Web-based interactive graph explorer
- **Dependency Timeline**: Show how dependencies have changed over time
- **Impact Analysis**: Visualize what packages will be affected by changes
- **Comparison Views**: Compare dependency trees between environments
- **Export to Diagrams**: Generate architecture diagrams from dependencies

### Integration & Automation

- **CI/CD Integration**: Plugins for GitHub Actions, GitLab CI, Jenkins
- **Docker Integration**: Generate Dockerfiles with optimized layer caching
- **Kubernetes Support**: Generate K8s manifests with dependency information
- **Webhook Support**: Trigger actions when packages are installed/updated
- **API Access**: RESTful API for programmatic package management

### Platform Support

- **Windows Support**: Full Windows compatibility with PowerShell integration
- **Cross-platform Packages**: Manage platform-specific dependencies
- **ARM Support**: Native support for ARM architectures (M1/M2 Macs, Raspberry Pi)
- **WebAssembly**: Support for Python packages compiled to WASM

### Advanced Backend Features

- **Multi-tenancy**: Support multiple organizations/teams on shared backend
- **Backup & Restore**: Backup and restore package configurations
- **Audit Logging**: Detailed logs of all package operations
- **Role-Based Access Control**: Fine-grained permissions for package management
- **Replication**: Multi-region backend replication for global teams

### Package Discovery & Quality

- **Package Ratings**: Community ratings and reviews for packages
- **Quality Metrics**: Display package quality scores (tests, documentation, maintenance)
- **Trending Packages**: Show popular and trending packages
- **Alternative Suggestions**: Suggest alternative packages with similar functionality
- **Deprecation Warnings**: Alert when using deprecated packages

### Development Tools

- **Package Scaffolding**: `boo create` - Generate new package boilerplate
- **Dependency Upgrade Assistant**: Interactive tool to upgrade dependencies safely
- **Breaking Change Detection**: Analyze changelogs for breaking changes
- **Test Integration**: Run tests after dependency updates
- **Rollback Support**: Quickly rollback to previous package versions

These enhancements will be prioritized based on user feedback and community needs. Contributions are welcome!
