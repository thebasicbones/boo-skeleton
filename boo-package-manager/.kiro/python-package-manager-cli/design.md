# Design Document

## Overview

The boo CLI is a Python package manager that enhances pip with intelligent dependency management, conflict detection, and team collaboration features. It acts as a frontend to the existing boo-package-manager backend, leveraging its topological sorting and circular dependency detection capabilities while using pip for actual package installation.

**Design Philosophy:**
- **Enhance, don't replace**: Use pip for installation, add value through dependency management
- **Backend-first**: Let the backend handle complex dependency logic
- **User-friendly**: Provide rich terminal UI with clear feedback
- **Team-oriented**: Enable collaboration through centralized package tracking

## How the CLI Uses the Existing Backend

### Backend Code Reuse Strategy

The CLI leverages the existing `boo-package-manager/` backend without modification. The backend is already running as a FastAPI service with all the dependency management logic we need.

**Existing Backend Structure:**
```
boo-package-manager/
├── app/
│   ├── routers/resources.py          # ← CLI calls these endpoints
│   ├── services/
│   │   ├── resource_service.py       # ← Business logic we leverage
│   │   └── topological_sort_service.py  # ← Dependency ordering
│   ├── repositories/                 # ← Data access (MongoDB/SQLite)
│   ├── schemas.py                    # ← Request/response models
│   └── exceptions.py                 # ← Error types we handle
├── config/settings.py                # ← Backend configuration
└── main.py                          # ← FastAPI app (already running)
```

### Concrete Integration Examples

#### Example 1: Install Command Using Backend

**User Command:**
```bash
boo install requests
```

**CLI Implementation:**
```python
# cli/commands/install.py
async def install_package(package_name: str):
    # Step 1: Fetch metadata from PyPI
    pypi_client = PyPIClient()
    metadata = await pypi_client.get_package_metadata(package_name)
    
    # Step 2: Create Resource in backend
    # This calls: POST /api/resources
    # Which invokes: resource_service.create_resource()
    backend_client = BackendClient(config.backend_url)
    resource = await backend_client.create_resource(
        name=metadata["name"],
        version=metadata["version"],
        dependencies=metadata["dependencies"]  # e.g., ["urllib3", "certifi"]
    )
    
    # Step 3: Backend validates and returns topological order
    # The backend's resource_service.create_resource() calls:
    # - topological_sort_service.validate_no_cycles()
    # - topological_sort_service.topological_sort()
    
    # Step 4: Install packages in order using pip
    for dep in resource["dependencies"]:
        await pip_wrapper.install(dep)
    await pip_wrapper.install(package_name)
```

**Backend Code Being Used:**
```python
# boo-package-manager/app/services/resource_service.py (existing code)
async def create_resource(self, data: ResourceCreate) -> ResourceResponse:
    # Validate dependencies and check cycles
    temp_id = "temp_new_resource_id"
    await self._validate_and_check_cycles(temp_id, data.dependencies)
    
    # Create the resource
    resource = await self.repository.create(data)
    return self._resource_to_response(resource)
```

#### Example 2: Tree Command Using Topological Sort

**User Command:**
```bash
boo tree
```

**CLI Implementation:**
```python
# cli/commands/tree.py
async def show_tree():
    # Step 1: Fetch all resources from backend
    # This calls: GET /api/resources
    # Which invokes: resource_service.get_all_resources()
    backend_client = BackendClient(config.backend_url)
    resources = await backend_client.list_resources()
    
    # Step 2: Backend already has them in topological order
    # The backend's search endpoint uses topological_sort_service
    
    # Step 3: Build tree structure from ordered resources
    tree = build_tree_from_resources(resources)
    
    # Step 4: Display using Rich
    ui.print_tree(tree)
```

**Backend Code Being Used:**
```python
# boo-package-manager/app/services/topological_sort_service.py (existing code)
@staticmethod
def topological_sort(resources: list[dict]) -> list[dict]:
    """
    Sort resources in topological order using Kahn's algorithm.
    Dependencies appear before dependents in the result.
    """
    # ... Kahn's algorithm implementation ...
    # This is the core logic the CLI relies on
```

#### Example 3: Check Command Using Circular Dependency Detection

**User Command:**
```bash
boo check
```

**CLI Implementation:**
```python
# cli/commands/check.py
async def check_conflicts():
    # Step 1: Fetch all resources
    # This calls: GET /api/resources
    backend_client = BackendClient(config.backend_url)
    resources = await backend_client.list_resources()
    
    # Step 2: Try to validate (backend does the work)
    # The backend's topological_sort_service will detect cycles
    try:
        # Backend validates when we try to sort
        sorted_resources = await backend_client.search_resources("")
        ui.print_success("✓ No conflicts detected")
    except CircularDependencyError as e:
        # Backend detected a cycle and returned the path
        ui.print_error(f"✗ Circular dependency: {e.cycle_path}")
```

**Backend Code Being Used:**
```python
# boo-package-manager/app/services/topological_sort_service.py (existing code)
@staticmethod
def _find_cycle(graph: dict[str, list[str]], in_degree: dict[str, int]) -> list[str]:
    """
    Find a cycle in the graph using DFS.
    Returns: List of resource IDs forming a cycle
    """
    # ... DFS cycle detection ...
    # This is what catches circular dependencies
```

#### Example 4: Uninstall with Cascade Using Backend

**User Command:**
```bash
boo uninstall flask --cascade
```

**CLI Implementation:**
```python
# cli/commands/uninstall.py
async def uninstall_package(package_name: str, cascade: bool = False):
    # Step 1: Find the resource ID
    backend_client = BackendClient(config.backend_url)
    resources = await backend_client.search_resources(package_name)
    resource_id = resources[0]["id"]
    
    # Step 2: Delete with cascade
    # This calls: DELETE /api/resources/{id}?cascade=true
    # Which invokes: resource_service.delete_resource(id, cascade=True)
    await backend_client.delete_resource(resource_id, cascade=cascade)
    
    # Step 3: Backend handles finding all dependents and deleting them
    # We just need to uninstall the packages pip knows about
    await pip_wrapper.uninstall(package_name)
```

**Backend Code Being Used:**
```python
# boo-package-manager/app/services/resource_service.py (existing code)
async def delete_resource(self, resource_id: str, cascade: bool = False) -> None:
    """
    Delete a resource with optional cascade.
    If cascade=True, delete all resources that depend on this resource
    """
    # ... cascade delete logic ...
    success = await self.repository.delete(resource_id, cascade)
```

#### Example 5: Search Using Backend's Topological Sort

**User Command:**
```bash
boo search django
```

**CLI Implementation:**
```python
# cli/commands/search.py
async def search_packages(query: str):
    # Step 1: Call backend search
    # This calls: GET /api/search?q=django
    # Which invokes: resource_service.search_resources(query)
    backend_client = BackendClient(config.backend_url)
    results = await backend_client.search_resources(query)
    
    # Step 2: Backend returns results in topological order
    # The backend's search_resources() calls topological_sort_service
    
    # Step 3: Display results (already sorted correctly)
    ui.print_table(results, columns=["name", "version", "description"])
```

**Backend Code Being Used:**
```python
# boo-package-manager/app/services/resource_service.py (existing code)
async def search_resources(self, query: str | None = None) -> list[ResourceResponse]:
    """
    Search for resources and return them in topological order.
    """
    resources = await self.repository.search(query)
    
    # Sort topologically - this is the key feature we're using
    sorted_dicts = self.topo_service.topological_sort(resource_dicts)
    
    return results
```

### Backend API Endpoints Used by CLI

| CLI Command | Backend Endpoint | Backend Service Method | Purpose |
|-------------|------------------|------------------------|---------|
| `boo install` | `POST /api/resources` | `resource_service.create_resource()` | Create package, validate dependencies |
| `boo uninstall` | `DELETE /api/resources/{id}` | `resource_service.delete_resource()` | Remove package, optional cascade |
| `boo list` | `GET /api/resources` | `resource_service.get_all_resources()` | List all packages |
| `boo search` | `GET /api/search?q=` | `resource_service.search_resources()` | Search with topo sort |
| `boo tree` | `GET /api/resources` | `topological_sort_service.topological_sort()` | Get ordered packages |
| `boo check` | `GET /api/resources` | `topological_sort_service.validate_no_cycles()` | Detect conflicts |
| `boo update` | `PUT /api/resources/{id}` | `resource_service.update_resource()` | Update package version |
| `boo sync` | Multiple | Multiple | Sync local with backend |

### Backend Features We Leverage

1. **Topological Sorting** (`topological_sort_service.py`):
   - Kahn's algorithm implementation
   - Determines installation order
   - Used by search, tree, and install commands

2. **Circular Dependency Detection** (`topological_sort_service.py`):
   - DFS-based cycle detection
   - Returns cycle path for display
   - Used by check and install commands

3. **Cascade Delete** (`resource_service.py`):
   - Finds all dependent resources
   - Deletes entire dependency chain
   - Used by uninstall command

4. **Resource CRUD** (`resource_service.py`):
   - Create, read, update, delete operations
   - Validation on create/update
   - Used by all commands

5. **Database Abstraction** (`database_factory.py`):
   - MongoDB or SQLite support
   - Repository pattern
   - CLI doesn't need to know which DB is used

### Running the Backend

The CLI expects the backend to be running. Users can start it with:

```bash
cd boo-package-manager
uvicorn main:app --reload
```

The CLI will connect to `http://localhost:8000` by default (configurable via `boo config set backend_url`).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Boo CLI                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Commands   │  │   API Client │  │  Pip Wrapper │     │
│  │              │──│              │  │              │     │
│  │ install      │  │ HTTP Client  │  │ subprocess   │     │
│  │ uninstall    │  │ Auth         │  │ pip calls    │     │
│  │ list         │  │ Error        │  │              │     │
│  │ tree         │  │ Handling     │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  UI Layer    │  │    Config    │  │    Cache     │     │
│  │              │  │              │  │              │     │
│  │ Rich Console │  │ Settings     │  │ Local DB     │     │
│  │ Formatters   │  │ Credentials  │  │ Metadata     │     │
│  │ Progress     │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ▼                            ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│   Boo Backend (FastAPI) │  │      PyPI Registry      │
│                         │  │                         │
│  • CRUD Operations      │  │  • Package Metadata     │
│  • Topological Sort     │  │  • Package Downloads    │
│  • Circular Dep Check   │  │                         │
│  • MongoDB/SQLite       │  │                         │
└─────────────────────────┘  └─────────────────────────┘
```

### Component Breakdown

#### 1. Commands Layer
- Entry point for user commands
- Parses arguments and options
- Orchestrates operations across other components
- Handles command-specific logic

#### 2. API Client
- HTTP client for backend communication
- Authentication and session management
- Request/response serialization
- Error handling and retries

#### 3. Pip Wrapper
- Subprocess management for pip commands
- Output parsing and progress tracking
- Error detection and reporting
- Version compatibility handling

#### 4. UI Layer
- Rich terminal output with colors and formatting
- Progress bars and spinners
- Table formatting for lists
- Tree visualization for dependencies

#### 5. Config Management
- User configuration storage
- Backend URL and credentials
- CLI preferences and defaults
- Environment-specific settings

#### 6. Cache Layer
- Local SQLite database for metadata
- Offline operation support
- Performance optimization
- Sync state tracking

## Components and Interfaces

### 1. Command Interface

All commands implement a common interface:

```python
from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    """Base class for all CLI commands"""
    
    @abstractmethod
    async def execute(self, args: dict[str, Any]) -> int:
        """
        Execute the command.
        
        Args:
            args: Parsed command arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """Return help text for the command"""
        pass
```

### 2. Backend API Client

```python
from typing import Optional
import httpx

class BackendClient:
    """Client for communicating with boo-package-manager backend"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
        )
    
    async def create_resource(self, name: str, version: str, 
                            dependencies: list[str]) -> dict:
        """Create a package resource in the backend"""
        pass
    
    async def get_resource(self, resource_id: str) -> dict:
        """Get a package resource by ID"""
        pass
    
    async def list_resources(self) -> list[dict]:
        """List all package resources"""
        pass
    
    async def search_resources(self, query: str) -> list[dict]:
        """Search for package resources (returns topologically sorted)"""
        pass
    
    async def update_resource(self, resource_id: str, 
                            data: dict) -> dict:
        """Update a package resource"""
        pass
    
    async def delete_resource(self, resource_id: str, 
                            cascade: bool = False) -> None:
        """Delete a package resource"""
        pass
```

### 3. Pip Wrapper

```python
import subprocess
from typing import Optional

class PipWrapper:
    """Wrapper around pip for package installation"""
    
    async def install(self, package: str, version: Optional[str] = None) -> bool:
        """
        Install a package using pip.
        
        Args:
            package: Package name
            version: Optional version specifier
            
        Returns:
            True if installation succeeded
        """
        pass
    
    async def uninstall(self, package: str) -> bool:
        """Uninstall a package using pip"""
        pass
    
    async def list_installed(self) -> list[dict]:
        """List all installed packages"""
        pass
    
    async def get_package_info(self, package: str) -> dict:
        """Get information about an installed package"""
        pass
    
    def parse_requirements(self, file_path: str) -> list[dict]:
        """Parse a requirements.txt file"""
        pass
```

### 4. PyPI Client

```python
import httpx

class PyPIClient:
    """Client for fetching package metadata from PyPI"""
    
    def __init__(self):
        self.base_url = "https://pypi.org/pypi"
        self.client = httpx.AsyncClient()
    
    async def get_package_metadata(self, package: str, 
                                  version: Optional[str] = None) -> dict:
        """
        Fetch package metadata from PyPI.
        
        Returns:
            {
                "name": "requests",
                "version": "2.31.0",
                "dependencies": ["urllib3", "certifi", ...],
                "description": "...",
                "author": "...",
                ...
            }
        """
        pass
    
    async def search_packages(self, query: str, limit: int = 20) -> list[dict]:
        """Search for packages on PyPI"""
        pass
    
    async def get_latest_version(self, package: str) -> str:
        """Get the latest version of a package"""
        pass
```

### 5. UI Components

```python
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress

class UI:
    """Rich terminal UI components"""
    
    def __init__(self):
        self.console = Console()
    
    def print_success(self, message: str) -> None:
        """Print success message in green"""
        pass
    
    def print_error(self, message: str) -> None:
        """Print error message in red"""
        pass
    
    def print_warning(self, message: str) -> None:
        """Print warning message in yellow"""
        pass
    
    def print_table(self, data: list[dict], columns: list[str]) -> None:
        """Print data as a formatted table"""
        pass
    
    def print_tree(self, root: dict, children_key: str = "dependencies") -> None:
        """Print hierarchical tree structure"""
        pass
    
    def progress_bar(self, total: int, description: str) -> Progress:
        """Create a progress bar"""
        pass
```

## Data Models

### Package Resource (Backend)

```python
from pydantic import BaseModel
from datetime import datetime

class PackageResource(BaseModel):
    """Package resource stored in backend"""
    id: str
    name: str
    version: str
    description: Optional[str] = None
    dependencies: list[str] = []  # List of package IDs
    created_at: datetime
    updated_at: datetime
```

### Local Package (CLI Cache)

```python
class LocalPackage(BaseModel):
    """Package information cached locally"""
    name: str
    version: str
    location: str  # Installation path
    dependencies: list[str]  # List of package names
    resource_id: Optional[str] = None  # Backend resource ID
    installed_at: datetime
    synced: bool = False  # Whether synced with backend
```

### Configuration

```python
class Config(BaseModel):
    """CLI configuration"""
    backend_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    cache_dir: str = "~/.boo/cache"
    auto_sync: bool = True
    default_format: str = "table"  # table, json, tree
    color_output: bool = True
```

## Data Models


### Lock File Format

```python
class LockFile(BaseModel):
    """Lock file format for reproducible installations"""
    version: str = "1.0"
    packages: dict[str, PackageLock]
    generated_at: datetime
    python_version: str
    
class PackageLock(BaseModel):
    """Individual package entry in lock file"""
    version: str
    dependencies: dict[str, str]  # name -> version
    hashes: list[str]  # SHA256 hashes for verification
    source: str = "pypi"  # pypi, git, local, etc.
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Installation Properties

Property 1: Installation order follows topological sort
*For any* set of packages with dependencies, when installing, the CLI should install packages in the topological order returned by the backend, ensuring dependencies are installed before dependents.
**Validates: Requirements 1.4**

Property 2: Version pinning is preserved
*For any* package and version combination, when installing with a version specifier (e.g., `package==1.2.3`), the CLI should pass the exact version to both the backend Resource and pip.
**Validates: Requirements 1.2**

Property 3: Installation rollback on failure
*For any* package installation that fails, the CLI should delete the created Resource from the backend, ensuring no orphaned Resources exist.
**Validates: Requirements 1.5**

Property 4: Requirements file completeness
*For any* valid requirements.txt file, when installing from it, the CLI should create a Resource for each package and install all packages in topological order.
**Validates: Requirements 1.3**

### Uninstallation Properties

Property 5: Cascade delete completeness
*For any* package with dependents, when uninstalling with `--cascade`, the CLI should call the backend's cascade delete endpoint and remove all dependent packages.
**Validates: Requirements 2.3**

Property 6: Uninstall cleanup
*For any* successful package uninstallation, the CLI should delete the corresponding Resource from the backend.
**Validates: Requirements 2.4**

Property 7: Dependent warning display
*For any* package with dependents, when uninstalling without `--cascade`, the CLI should query the backend and display a warning listing all dependent packages.
**Validates: Requirements 2.2**

### Dependency Tree Properties

Property 8: Tree structure correctness
*For any* set of packages with dependencies, when displaying a tree, each package should appear with its dependencies as children, maintaining the hierarchical structure.
**Validates: Requirements 3.1, 3.2**

Property 9: Subtree isolation
*For any* package, when displaying its tree with `boo tree <package>`, only that package and its transitive dependencies should appear in the output.
**Validates: Requirements 3.3**

Property 10: Depth limiting
*For any* dependency tree and depth limit n, when displaying with `--depth n`, no package should appear more than n levels deep from the root.
**Validates: Requirements 3.4**

### Conflict Detection Properties

Property 11: Circular dependency detection
*For any* dependency graph, when checking for conflicts, if the backend returns a CircularDependencyError, the CLI should display the cycle path.
**Validates: Requirements 4.2, 4.3**

Property 12: Validation completeness
*For any* set of installed packages, when running `boo check`, the CLI should fetch all Resources from the backend and validate the complete dependency graph.
**Validates: Requirements 4.1**

Property 13: Healthy environment confirmation
*For any* dependency graph with no circular dependencies, when running `boo check`, the CLI should display a success message.
**Validates: Requirements 4.4**

### List and Search Properties

Property 14: List completeness
*For any* set of packages in the backend, when running `boo list`, all packages should appear in the output.
**Validates: Requirements 5.1**

Property 15: Outdated detection accuracy
*For any* package where the backend version differs from the latest PyPI version, when running `boo list --outdated`, that package should appear in the output with both versions displayed.
**Validates: Requirements 5.2, 5.4**

Property 16: JSON output validity
*For any* set of packages, when running `boo list --format json`, the output should be valid JSON containing all packages.
**Validates: Requirements 5.3**

Property 17: Search result ordering
*For any* search query, the results returned by the CLI should maintain the topological order provided by the backend.
**Validates: Requirements 6.5**

Property 18: Search result limiting
*For any* search query with `--limit n`, the CLI should display at most n results.
**Validates: Requirements 6.3**

Property 19: Search result completeness
*For any* search result, the displayed information should include the package name, description, and dependencies from the backend Resource.
**Validates: Requirements 6.2**

### Update Properties

Property 20: Update version display
*For any* package update, the CLI should display both the old version (from backend Resource) and new version (from PyPI).
**Validates: Requirements 7.4**

Property 21: Bulk update completeness
*For any* set of packages, when running `boo update --all`, the CLI should attempt to update every package.
**Validates: Requirements 7.2**

Property 22: Update conflict prevention
*For any* package update that would create a circular dependency, the backend should reject the update and the CLI should display the error.
**Validates: Requirements 7.3**

Property 23: Dry-run safety
*For any* set of packages, when running `boo update --dry-run`, no backend update endpoints should be called.
**Validates: Requirements 7.5**

### Lock File Properties

Property 24: Lock file completeness
*For any* set of installed packages, when generating a lock file, all packages and their transitive dependencies should be included with exact versions.
**Validates: Requirements 8.1, 8.2**

Property 25: Lock file round-trip
*For any* set of packages, generating a lock file then installing from it should result in the same package versions being installed.
**Validates: Requirements 8.3**

Property 26: Lock file hash inclusion
*For any* package in a lock file, the entry should include at least one SHA256 hash for verification.
**Validates: Requirements 8.5**

### Sync Properties

Property 27: Sync operation correctness
*For any* set of local packages, when running `boo sync`, the CLI should create Resources for new packages and update Resources for changed packages in the backend.
**Validates: Requirements 9.1, 9.2**

Property 28: Pull sync completeness
*For any* set of backend Resources, when running `boo sync --pull`, all Resources not installed locally should be installed.
**Validates: Requirements 9.3**

Property 29: Offline operation caching
*For any* operation when the backend is unavailable, the CLI should cache the operation locally and not fail.
**Validates: Requirements 9.4**

Property 30: Sync summary accuracy
*For any* sync operation, the displayed summary should accurately count created, updated, and deleted Resources.
**Validates: Requirements 9.5**

### Graph Properties

Property 31: Graph structure correctness
*For any* set of packages with dependencies, when generating a graph, the graph should accurately represent all dependency relationships.
**Validates: Requirements 10.1**

Property 32: Graph format validity
*For any* dependency graph, when exporting to DOT or JSON format, the output should be valid according to the format specification.
**Validates: Requirements 10.2**

Property 33: Graph image generation
*For any* dependency graph, when exporting to an image file, the file should be created and be a valid image format.
**Validates: Requirements 10.3**

Property 34: Subgraph isolation
*For any* package, when generating a graph for that package, only the package and its transitive dependencies should appear in the graph.
**Validates: Requirements 10.5**

### Security Audit Properties

Property 35: Audit completeness
*For any* set of installed packages, when running `boo audit`, all packages should be checked against vulnerability databases.
**Validates: Requirements 11.1**

Property 36: Vulnerability display completeness
*For any* vulnerability found, the CLI should display the vulnerability name, severity level, and affected versions.
**Validates: Requirements 11.2**

Property 37: Auto-fix attempt
*For any* vulnerable package with a safe version available, when running `boo audit --fix`, the CLI should attempt to upgrade to the safe version.
**Validates: Requirements 11.3**

Property 38: Remediation suggestions
*For any* vulnerability that cannot be auto-fixed, the CLI should display manual remediation steps.
**Validates: Requirements 11.5**

### Virtual Environment Properties

Property 39: Environment creation
*For any* valid environment name, when running `boo env create <name>`, a new virtual environment should be created.
**Validates: Requirements 12.1**

Property 40: Environment listing completeness
*For any* set of managed virtual environments, when running `boo env list`, all environments should appear in the output.
**Validates: Requirements 12.3**

Property 41: Environment deletion
*For any* existing virtual environment, when running `boo env delete <name>`, the environment should be removed.
**Validates: Requirements 12.4**

Property 42: Active environment display
*For any* command executed within a virtual environment, the CLI output should include the active environment name.
**Validates: Requirements 12.5**

### Export Properties

Property 43: Export completeness
*For any* set of installed packages, when running `boo export`, all packages should appear in the generated requirements.txt file.
**Validates: Requirements 13.1**

Property 44: Export format validity
*For any* set of packages, when exporting to poetry or conda format, the generated file should be valid according to the format specification.
**Validates: Requirements 13.2, 13.3**

Property 45: Top-level dependency filtering
*For any* set of packages, when exporting without `--all`, only top-level dependencies (not transitive) should be included.
**Validates: Requirements 13.4**

Property 46: Transitive dependency inclusion
*For any* set of packages, when exporting with `--all`, all transitive dependencies should be included.
**Validates: Requirements 13.5**

### Configuration Properties

Property 47: Config round-trip
*For any* valid configuration key-value pair, setting a value then getting it should return the same value.
**Validates: Requirements 14.1, 14.2**

Property 48: Config listing completeness
*For any* configuration state, when running `boo config list`, all configuration settings should be displayed.
**Validates: Requirements 14.3**

Property 49: Config loading
*For any* valid configuration file, when the CLI starts, all settings from the file should be loaded.
**Validates: Requirements 14.4**

Property 50: Invalid config handling
*For any* invalid configuration value, the CLI should display an error and use the default value.
**Validates: Requirements 14.5**

### Help System Properties

Property 51: Command help completeness
*For any* command, when running `boo <command> --help`, the output should include command syntax, options, and usage examples.
**Validates: Requirements 15.2, 15.3**

Property 52: Command suggestion
*For any* invalid command, the CLI should suggest similar valid commands based on string similarity.
**Validates: Requirements 15.4**

## Error Handling

### Error Categories

1. **Network Errors**
   - Backend unavailable
   - PyPI unreachable
   - Timeout errors

2. **Validation Errors**
   - Circular dependencies
   - Invalid package names
   - Version conflicts

3. **Installation Errors**
   - Pip failures
   - Permission errors
   - Disk space issues

4. **User Errors**
   - Invalid commands
   - Missing arguments
   - Invalid configuration

### Error Handling Strategy

```python
class BooError(Exception):
    """Base exception for all boo errors"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class NetworkError(BooError):
    """Network-related errors"""
    pass

class ValidationError(BooError):
    """Validation errors"""
    pass

class InstallationError(BooError):
    """Installation errors"""
    pass

class UserError(BooError):
    """User input errors"""
    pass
```

### Error Recovery

1. **Retry Logic**: Automatic retry for transient network errors (3 attempts with exponential backoff)
2. **Rollback**: Automatic rollback of backend Resources on installation failure
3. **Offline Mode**: Cache operations when backend is unavailable
4. **Graceful Degradation**: Continue with reduced functionality when optional services fail

### Error Messages

All error messages should:
- Be clear and actionable
- Include context about what went wrong
- Suggest next steps for resolution
- Use color coding (red for errors, yellow for warnings)

Example:
```
❌ Error: Failed to install package 'requests'

Reason: Circular dependency detected
Cycle: requests → urllib3 → requests

Suggestion: Remove the circular dependency by updating package versions

For more help, run: boo docs errors/circular-dependency
```

## Testing Strategy

### Unit Testing

**Framework**: pytest

**Coverage Areas**:
- Command parsing and validation
- API client request/response handling
- Pip wrapper subprocess management
- UI formatting and output
- Configuration loading and validation
- Error handling and recovery

**Example Unit Tests**:
```python
def test_install_command_parses_package_name():
    """Test that install command correctly parses package name"""
    args = parse_args(["install", "requests"])
    assert args.command == "install"
    assert args.package == "requests"

def test_backend_client_handles_404():
    """Test that backend client raises NotFoundError on 404"""
    client = BackendClient("http://localhost:8000")
    with pytest.raises(NotFoundError):
        await client.get_resource("nonexistent-id")

def test_pip_wrapper_parses_version():
    """Test that pip wrapper correctly extracts version from output"""
    output = "requests==2.31.0"
    version = PipWrapper.parse_version(output)
    assert version == "2.31.0"
```

### Property-Based Testing

**Framework**: Hypothesis

**Configuration**: Each property test should run a minimum of 100 iterations.

**Test Tagging**: Each property-based test must include a comment with the format:
`# Feature: python-package-manager-cli, Property X: <property_text>`

**Coverage Areas**:
- Installation order correctness
- Dependency tree building
- Lock file round-trips
- Configuration round-trips
- Export format validity

**Example Property Tests**:
```python
from hypothesis import given, strategies as st

# Feature: python-package-manager-cli, Property 1: Installation order follows topological sort
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
async def test_installation_order_follows_topological_sort(package_names):
    """
    For any set of packages with dependencies, installation order should
    match the topological sort from the backend.
    """
    # Create mock packages with random dependencies
    packages = create_mock_packages(package_names)
    
    # Get installation order from CLI
    cli_order = await cli.get_installation_order(packages)
    
    # Get topological order from backend
    backend_order = await backend.topological_sort(packages)
    
    # Orders should match
    assert cli_order == backend_order

# Feature: python-package-manager-cli, Property 25: Lock file round-trip
@given(st.lists(st.tuples(st.text(), st.text()), min_size=1, max_size=20))
async def test_lock_file_round_trip(packages):
    """
    For any set of packages, generating a lock file then installing from it
    should result in the same versions.
    """
    # Install packages
    for name, version in packages:
        await cli.install(f"{name}=={version}")
    
    # Generate lock file
    await cli.lock()
    
    # Clear environment
    await cli.uninstall_all()
    
    # Install from lock file
    await cli.install(locked=True)
    
    # Verify versions match
    installed = await cli.list_installed()
    for name, version in packages:
        assert installed[name] == version

# Feature: python-package-manager-cli, Property 47: Config round-trip
@given(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=100))
async def test_config_round_trip(key, value):
    """
    For any valid config key-value pair, setting then getting should
    return the same value.
    """
    # Set config
    await cli.config_set(key, value)
    
    # Get config
    retrieved = await cli.config_get(key)
    
    # Should match
    assert retrieved == value
```

### Integration Testing

**Coverage Areas**:
- End-to-end command execution
- Backend API integration
- Pip subprocess integration
- File system operations

**Example Integration Tests**:
```python
@pytest.mark.integration
async def test_install_creates_backend_resource():
    """Test that installing a package creates a Resource in the backend"""
    # Install package
    result = await cli.run(["install", "requests"])
    assert result.exit_code == 0
    
    # Verify backend Resource was created
    resources = await backend.list_resources()
    assert any(r["name"] == "requests" for r in resources)
    
    # Verify package was installed via pip
    installed = await pip.list_installed()
    assert "requests" in installed

@pytest.mark.integration
async def test_uninstall_cascade_removes_dependents():
    """Test that cascade uninstall removes all dependent packages"""
    # Install packages with dependencies
    await cli.run(["install", "flask"])  # Depends on werkzeug, jinja2, etc.
    
    # Uninstall with cascade
    result = await cli.run(["uninstall", "werkzeug", "--cascade"])
    assert result.exit_code == 0
    
    # Verify flask was also removed (depends on werkzeug)
    installed = await pip.list_installed()
    assert "flask" not in installed
    assert "werkzeug" not in installed
```

### Test Fixtures

```python
@pytest.fixture
async def backend_client():
    """Provide a backend client for testing"""
    client = BackendClient("http://localhost:8000")
    yield client
    await client.close()

@pytest.fixture
async def clean_environment():
    """Provide a clean test environment"""
    # Clear all packages
    await cli.uninstall_all()
    
    # Clear backend
    await backend.delete_all_resources()
    
    yield
    
    # Cleanup
    await cli.uninstall_all()
    await backend.delete_all_resources()

@pytest.fixture
def mock_pypi():
    """Mock PyPI responses"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://pypi.org/pypi/requests/json",
            json={"info": {"version": "2.31.0", ...}},
            status=200
        )
        yield rsps
```

## Implementation Notes

### Technology Choices

1. **CLI Framework**: Click or Typer
   - Rich command parsing
   - Automatic help generation
   - Type hints support

2. **HTTP Client**: httpx
   - Async support
   - HTTP/2 support
   - Timeout handling

3. **Terminal UI**: Rich
   - Beautiful formatting
   - Progress bars
   - Tree visualization
   - Table formatting

4. **Configuration**: Pydantic Settings
   - Type validation
   - Environment variable support
   - JSON/YAML/TOML support

5. **Local Cache**: SQLite
   - Lightweight
   - No external dependencies
   - SQL query support

### Performance Considerations

1. **Parallel Operations**: Use asyncio for concurrent backend/PyPI requests
2. **Caching**: Cache PyPI metadata locally to reduce API calls
3. **Batch Operations**: Batch backend API calls when possible
4. **Lazy Loading**: Load configuration and cache only when needed

### Security Considerations

1. **API Key Storage**: Store backend API keys in system keyring
2. **HTTPS Only**: Enforce HTTPS for backend communication
3. **Package Verification**: Verify package hashes from lock files
4. **Input Validation**: Validate all user input before processing

### Compatibility

1. **Python Versions**: Support Python 3.9+
2. **Operating Systems**: Linux, macOS, Windows
3. **Pip Versions**: Support pip 20.0+
4. **Backend Versions**: Support boo-package-manager 1.0+
