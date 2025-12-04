"""
Interactive prompts module for FastAPI CRUD CLI.

This module provides interactive prompts for collecting project configuration
from users, including project name, database type, metadata, and optional features.
"""

import subprocess
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.prompt import Confirm, Prompt

from .database_configs import DATABASE_CONFIGS, get_database_config
from .output import OutputFormatter
from .validators import ProjectValidator


class ProjectPrompts:
    """Handle all user interactions and input collection with Rich formatting."""

    def __init__(self, console: Console | None = None):
        """
        Initialize the project prompts handler.

        Args:
            console: Rich Console instance. If None, creates a new one.
        """
        self.console = console or Console()
        self.output = OutputFormatter(self.console)
        self.validator = ProjectValidator()

    def prompt_project_name(self, default: str = "my-fastapi-project") -> str:
        """
        Prompt for project name with validation.

        Repeatedly prompts until a valid project name is provided.
        Project names must contain only alphanumeric characters, hyphens, and underscores.

        Args:
            default: Default project name to suggest

        Returns:
            Validated project name string
        """
        self.console.print()
        self.console.print("[bold cyan]Project Configuration[/bold cyan]")
        self.console.print()

        while True:
            project_name = Prompt.ask(
                "[cyan]❯[/cyan] Project name",
                default=default,
                console=self.console,
            )

            # Validate project name
            is_valid, error_message = self.validator.validate_project_name(project_name)

            if not is_valid:
                self.output.display_error("Invalid project name", error_message)
                continue

            # Check if directory is available
            project_path = Path.cwd() / project_name
            is_available, conflict_message = self.validator.validate_directory_available(
                project_path
            )

            if not is_available:
                self.output.display_warning(conflict_message)
                overwrite = Confirm.ask(
                    "[yellow]❯[/yellow] Do you want to use this name anyway?",
                    default=False,
                    console=self.console,
                )
                if not overwrite:
                    continue

            return project_name

    def prompt_database_type(self) -> str:
        """
        Prompt for database selection with descriptions.

        Displays available database options (SQLite, MongoDB, PostgreSQL)
        with descriptions and prompts user to select one.

        Returns:
            Selected database type identifier (sqlite, mongodb, postgresql)
        """
        self.console.print()
        self.console.print("[bold cyan]Database Configuration[/bold cyan]")
        self.console.print()

        # Display available database options
        self.console.print("[dim]Available database backends:[/dim]")
        for i, (_db_type, config) in enumerate(DATABASE_CONFIGS.items(), 1):
            self.console.print(
                f"  [cyan]{i}.[/cyan] [bold]{config.name}[/bold] - {config.description}"
            )

        self.console.print()

        # Create mapping of choices
        db_types = list(DATABASE_CONFIGS.keys())
        choices_map = {str(i): db_type for i, db_type in enumerate(db_types, 1)}
        choices_map.update({db_type: db_type for db_type in db_types})

        while True:
            choice = Prompt.ask(
                "[cyan]❯[/cyan] Select database type",
                choices=list(choices_map.keys()),
                default="1",
                console=self.console,
            )

            selected_db = choices_map.get(choice)
            if selected_db:
                return selected_db

    def prompt_database_config(self, db_type: str) -> dict[str, Any]:
        """
        Prompt for database-specific configuration.

        Delegates to database-specific prompts based on the selected database type.
        Validates inputs according to database requirements.

        Args:
            db_type: Database type identifier (sqlite, mongodb, postgresql)

        Returns:
            Dictionary containing database-specific configuration values
        """
        config = get_database_config(db_type)
        prompts = config.get_prompts()
        user_config: dict[str, Any] = {}

        self.console.print()
        self.console.print(
            "[dim]Configure your database connection (these will be saved to .env)[/dim]"
        )
        self.console.print()

        for prompt_spec in prompts:
            name = prompt_spec["name"]
            message = prompt_spec["message"]
            default = prompt_spec.get("default", "")
            prompt_type = prompt_spec.get("type", "text")

            while True:
                # Handle password prompts differently
                if prompt_type == "password":
                    value = Prompt.ask(
                        f"[cyan]❯[/cyan] {message}",
                        password=True,
                        default=default,
                        console=self.console,
                    )
                else:
                    value = Prompt.ask(
                        f"[cyan]❯[/cyan] {message}",
                        default=default,
                        console=self.console,
                    )

                # Validate based on database type and field
                if db_type == "mongodb" and name == "mongodb_url":
                    is_valid, error_msg = self.validator.validate_mongodb_url(value)
                    if not is_valid:
                        self.output.display_error("Invalid MongoDB URL", error_msg)
                        continue

                # Store the value
                user_config[name] = value
                break

        # For PostgreSQL, validate the complete configuration
        if db_type == "postgresql":
            is_valid, error_msg = self.validator.validate_postgres_config(user_config)
            if not is_valid:
                self.output.display_error("Invalid PostgreSQL configuration", error_msg)
                # Re-prompt for the entire configuration
                return self.prompt_database_config(db_type)

        return user_config

    def prompt_environment_variables(self, db_type: str) -> dict[str, str]:
        """
        Prompt for additional environment variables.

        Collects environment-specific settings like environment type,
        debug mode, and other configuration options.

        Args:
            db_type: Database type identifier (for context)

        Returns:
            Dictionary containing environment variable key-value pairs
        """
        self.console.print()
        self.console.print("[bold cyan]Environment Configuration[/bold cyan]")
        self.console.print()
        self.console.print("[dim]These settings will be saved to your .env file[/dim]")
        self.console.print()

        env_vars: dict[str, str] = {}

        # Environment type
        self.console.print("[dim]Available environments:[/dim]")
        self.console.print("  [cyan]1.[/cyan] development - Local development with debug enabled")
        self.console.print("  [cyan]2.[/cyan] staging - Pre-production testing environment")
        self.console.print("  [cyan]3.[/cyan] production - Production deployment")
        self.console.print()

        env_choice = Prompt.ask(
            "[cyan]❯[/cyan] Select environment",
            choices=["1", "2", "3", "development", "staging", "production"],
            default="1",
            console=self.console,
        )

        # Map choice to environment name
        env_map = {
            "1": "development",
            "2": "staging",
            "3": "production",
            "development": "development",
            "staging": "staging",
            "production": "production",
        }
        env_vars["ENVIRONMENT"] = env_map[env_choice]

        # API settings
        api_host = Prompt.ask(
            "[cyan]❯[/cyan] API host",
            default="0.0.0.0",
            console=self.console,
        )
        env_vars["API_HOST"] = api_host

        api_port = Prompt.ask(
            "[cyan]❯[/cyan] API port",
            default="8000",
            console=self.console,
        )
        env_vars["API_PORT"] = api_port

        # Debug mode (auto-set based on environment)
        if env_vars["ENVIRONMENT"] == "development":
            env_vars["DEBUG"] = "true"
        else:
            debug = Confirm.ask(
                "[cyan]❯[/cyan] Enable debug mode?",
                default=False,
                console=self.console,
            )
            env_vars["DEBUG"] = "true" if debug else "false"

        # CORS origins
        cors_origins = Prompt.ask(
            "[cyan]❯[/cyan] CORS allowed origins (comma-separated)",
            default="http://localhost:3000,http://localhost:8000",
            console=self.console,
        )
        env_vars["CORS_ORIGINS"] = cors_origins

        return env_vars

    def prompt_project_metadata(self) -> dict[str, str]:
        """
        Prompt for project metadata (author, description, etc.).

        Attempts to read author information from git config as defaults.

        Returns:
            Dictionary containing:
                - author_name: Project author name
                - author_email: Project author email
                - description: Project description
        """
        self.console.print()
        self.console.print("[bold cyan]Project Metadata[/bold cyan]")
        self.console.print()

        # Try to get git config defaults
        author_name = self._get_git_config("user.name", "")
        author_email = self._get_git_config("user.email", "")

        # Prompt for author name
        author_name = Prompt.ask(
            "[cyan]❯[/cyan] Author name",
            default=author_name if author_name else "Your Name",
            console=self.console,
        )

        # Prompt for author email with validation
        while True:
            author_email = Prompt.ask(
                "[cyan]❯[/cyan] Author email",
                default=author_email if author_email else "you@example.com",
                console=self.console,
            )

            # Validate email format
            is_valid, error_msg = self.validator.validate_email(author_email)
            if not is_valid:
                self.output.display_error("Invalid email format", error_msg)
                continue

            break

        # Prompt for project description
        description = Prompt.ask(
            "[cyan]❯[/cyan] Project description",
            default="A FastAPI CRUD backend application",
            console=self.console,
        )

        return {
            "author_name": author_name,
            "author_email": author_email,
            "description": description,
        }

    def prompt_optional_features(self) -> dict[str, bool]:
        """
        Prompt for optional features (examples, dev tools, etc.).

        Asks user whether to include:
        - Example scripts and sample data
        - Development tools (pytest, black, ruff, mypy)
        - Static files directory

        Returns:
            Dictionary containing boolean flags for optional features:
                - include_examples: Whether to include example scripts
                - include_dev_tools: Whether to include development tools
                - include_static: Whether to include static files directory
        """
        self.console.print()
        self.console.print("[bold cyan]Optional Features[/bold cyan]")
        self.console.print()

        include_examples = Confirm.ask(
            "[cyan]❯[/cyan] Include example scripts and sample data?",
            default=True,
            console=self.console,
        )

        include_dev_tools = Confirm.ask(
            "[cyan]❯[/cyan] Include development tools (pytest, black, ruff, mypy)?",
            default=True,
            console=self.console,
        )

        include_static = Confirm.ask(
            "[cyan]❯[/cyan] Include static files directory?",
            default=True,
            console=self.console,
        )

        return {
            "include_examples": include_examples,
            "include_dev_tools": include_dev_tools,
            "include_static": include_static,
        }

    def confirm_generation(self, config: dict[str, Any]) -> bool:
        """
        Display configuration summary and ask for confirmation.

        Shows a formatted table of all configuration options and prompts
        the user to confirm before proceeding with project generation.

        Args:
            config: Complete project configuration dictionary

        Returns:
            True if user confirms, False if user cancels
        """
        self.console.print()
        self.console.print("[bold cyan]Configuration Summary[/bold cyan]")
        self.console.print()

        # Display configuration summary
        self.output.display_summary_table(config)

        # Ask for confirmation
        confirmed = Confirm.ask(
            "[cyan]❯[/cyan] Generate project with this configuration?",
            default=True,
            console=self.console,
        )

        return confirmed

    def _get_git_config(self, key: str, default: str = "") -> str:
        """
        Get git configuration value.

        Attempts to read a git config value using subprocess.
        Falls back to default if git is not available or key is not set.

        Args:
            key: Git config key (e.g., 'user.name', 'user.email')
            default: Default value if git config is unavailable

        Returns:
            Git config value or default
        """
        try:
            result = subprocess.run(
                ["git", "config", key],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Git not available or command failed
            pass

        return default
