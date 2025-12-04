"""
File generator module for creating FastAPI CRUD projects.

This module orchestrates the project generation process by coordinating
template rendering, file creation, and directory structure setup.
"""

from pathlib import Path
from typing import Any

from rich.console import Console

from .database_configs import get_database_config
from .output import OutputFormatter
from .template_engine import TemplateEngine


class ProjectGenerator:
    """Orchestrates project generation from templates and configuration."""

    def __init__(self, console: Console | None = None):
        """
        Initialize the project generator.

        Args:
            console: Rich Console instance. If None, creates a new one.
        """
        self.console = console or Console()
        self.output = OutputFormatter(self.console)

    def generate_project(self, config: dict[str, Any], output_dir: Path) -> bool:
        """
        Generate complete project structure.

        This is the main orchestration method that coordinates all generation steps.

        Args:
            config: Complete project configuration dictionary
            output_dir: Target directory for project generation

        Returns:
            True if generation succeeded, False otherwise
        """
        try:
            # Display progress
            self.output.display_progress("Creating project structure...")

            # Create base directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create directory structure
            self.create_directory_structure(output_dir, config)

            # Generate source files
            source_files = self.generate_source_files(output_dir, config)

            # Generate configuration files
            config_files = self.generate_config_files(output_dir, config)

            # Generate documentation
            doc_files = self.generate_documentation(output_dir, config)

            # Copy static assets if requested
            static_files = []
            if config.get("include_static", False):
                static_files = self.copy_static_assets(output_dir, config)

            # Collect all created files
            all_files = source_files + config_files + doc_files + static_files

            self.output.display_success(f"Project '{config['project_name']}' created successfully!")

            # Display file tree
            if all_files:
                self.output.display_file_tree(all_files, output_dir)

            # Verify requirements.txt exists before proceeding
            requirements_file = output_dir / "requirements.txt"
            if not requirements_file.exists():
                self.output.display_warning(
                    "requirements.txt not found. Skipping virtual environment setup."
                )
                return True

            # Setup virtual environment and install dependencies
            self.console.print()
            self.output.display_progress("Setting up virtual environment...")

            venv_success = self._setup_virtual_environment(output_dir)
            if not venv_success:
                self.output.display_warning(
                    "Virtual environment setup failed. You'll need to set it up manually."
                )
            else:
                self.output.display_success("Virtual environment created")

                # Install dependencies
                self.output.display_progress("Installing dependencies (this may take a moment)...")
                install_success = self._install_dependencies(output_dir)

                if not install_success:
                    self.output.display_warning(
                        "Dependency installation failed. You can install them manually with: pip install -r requirements.txt"
                    )
                else:
                    self.output.display_success("Dependencies installed successfully")

            return True

        except Exception as e:
            self.output.display_error("Project generation failed", str(e))
            return False

    def create_directory_structure(self, base_dir: Path, config: dict[str, Any]) -> list[Path]:
        """
        Create all necessary directories for the project.

        Args:
            base_dir: Base project directory
            config: Project configuration

        Returns:
            List of created directory paths
        """
        created_dirs = []

        # Core directories
        core_dirs = [
            "app",
            "app/models",
            "app/repositories",
            "app/routers",
            "app/services",
            "config",
            "tests",
        ]

        # Optional directories
        if config.get("include_examples", False):
            core_dirs.append("scripts")

        if config.get("include_static", False):
            core_dirs.append("static")

        # Create directories
        for dir_path in core_dirs:
            full_path = base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)

        return created_dirs

    def generate_source_files(self, base_dir: Path, config: dict[str, Any]) -> list[Path]:
        """
        Generate Python source files using templates.

        Args:
            base_dir: Base project directory
            config: Project configuration

        Returns:
            List of created file paths
        """
        created_files = []

        # Get template directory
        template_dir = self._get_template_dir()
        source_dir = self._get_source_dir()

        # Initialize template engine
        engine = TemplateEngine(template_dir, source_dir)

        # Render project using template engine
        rendered_files = engine.render_project(config, base_dir, self.output)
        created_files.extend(rendered_files)

        return created_files

    def generate_config_files(self, base_dir: Path, config: dict[str, Any]) -> list[Path]:
        """
        Generate configuration files (.env, pyproject.toml, etc.).

        Args:
            base_dir: Base project directory
            config: Project configuration

        Returns:
            List of created file paths
        """
        created_files = []

        # Generate .env file
        env_file = self._generate_env_file(base_dir, config)
        if env_file:
            created_files.append(env_file)

        return created_files

    def generate_documentation(self, base_dir: Path, config: dict[str, Any]) -> list[Path]:
        """
        Generate documentation files (README, etc.).

        Args:
            base_dir: Base project directory
            config: Project configuration

        Returns:
            List of created file paths
        """
        # Documentation is handled by template engine
        return []

    def copy_static_assets(self, base_dir: Path, config: dict[str, Any]) -> list[Path]:
        """
        Copy static files if included.

        Args:
            base_dir: Base project directory
            config: Project configuration

        Returns:
            List of created file paths
        """
        # Static assets are handled by template engine
        return []

    def _generate_env_file(self, base_dir: Path, config: dict[str, Any]) -> Path | None:
        """
        Generate .env file with database-specific configuration.

        Args:
            base_dir: Base project directory
            config: Project configuration

        Returns:
            Path to created .env file or None if failed
        """
        try:
            # Get database configuration
            db_type = config.get("database_type", "sqlite")
            db_config = get_database_config(db_type)

            # Generate environment content
            db_user_config = config.get("database_config", {})
            env_content = db_config.generate_env_content(db_user_config)

            # Add additional environment variables from user input
            env_variables = config.get("env_variables", {})
            if env_variables:
                env_content += "\n# Application Configuration\n"
                for key, value in env_variables.items():
                    env_content += f"{key}={value}\n"

            # Write .env file
            env_file = base_dir / ".env"
            env_file.write_text(env_content)

            self.output.display_progress("Generated: .env")
            return env_file

        except Exception as e:
            self.output.display_error("Failed to generate .env file", str(e))
            return None

    def _get_template_dir(self) -> Path:
        """
        Get the template directory path.

        Returns:
            Path to templates directory
        """
        # Get package directory
        import fastapi_crud_cli

        package_dir = Path(fastapi_crud_cli.__file__).parent
        return package_dir / "templates"

    def _get_source_dir(self) -> Path:
        """
        Get the source directory for static files.

        Returns:
            Path to source directory containing files to copy
        """
        # Get package directory
        import fastapi_crud_cli

        package_dir = Path(fastapi_crud_cli.__file__).parent

        # For development: use src/ directory in workspace root
        workspace_root = package_dir.parent
        src_dir = workspace_root / "src"
        if src_dir.exists() and (src_dir / "app").exists():
            return src_dir

        # For installed package: use bundled source files
        bundled_source = package_dir / "source"
        if bundled_source.exists():
            return bundled_source

        # Fallback: workspace root (legacy support)
        if (workspace_root / "app").exists():
            return workspace_root

        # Last resort: raise error
        raise FileNotFoundError(
            "Source files not found. Please ensure the project is properly set up."
        )

    def _setup_virtual_environment(self, project_dir: Path) -> bool:
        """
        Create a virtual environment in the project directory.

        Args:
            project_dir: Path to the project directory

        Returns:
            True if successful, False otherwise
        """
        import subprocess
        import sys

        try:
            venv_path = project_dir / "venv"

            # Create virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                self.console.print(f"[dim]Error: {result.stderr}[/dim]")
                return False

            return True

        except subprocess.TimeoutExpired:
            self.console.print("[dim]Virtual environment creation timed out[/dim]")
            return False
        except Exception as e:
            self.console.print(f"[dim]Error creating virtual environment: {e}[/dim]")
            return False

    def _install_dependencies(self, project_dir: Path) -> bool:
        """
        Install project dependencies from requirements.txt.

        Args:
            project_dir: Path to the project directory

        Returns:
            True if successful, False otherwise
        """
        import subprocess
        import sys

        try:
            venv_path = project_dir / "venv"
            requirements_file = project_dir / "requirements.txt"

            if not requirements_file.exists():
                self.console.print("[dim]requirements.txt not found[/dim]")
                return False

            # Determine pip executable path based on OS
            if sys.platform == "win32":
                pip_executable = venv_path / "Scripts" / "pip.exe"
            else:
                pip_executable = venv_path / "bin" / "pip"

            if not pip_executable.exists():
                self.console.print(f"[dim]Pip executable not found at {pip_executable}[/dim]")
                return False

            # Install dependencies
            result = subprocess.run(
                [str(pip_executable), "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                check=False,
                cwd=str(project_dir),
            )

            if result.returncode != 0:
                self.console.print(f"[dim]Error: {result.stderr}[/dim]")
                return False

            return True

        except subprocess.TimeoutExpired:
            self.console.print("[dim]Dependency installation timed out[/dim]")
            return False
        except Exception as e:
            self.console.print(f"[dim]Error installing dependencies: {e}[/dim]")
            return False
