"""
Validation module for FastAPI CRUD CLI scaffolding tool.

This module provides validation functions for project configuration inputs
including project names, directory availability, database configurations,
and email formats.
"""

import re
from pathlib import Path
from urllib.parse import urlparse


class ProjectValidator:
    """Validator class for project configuration inputs."""

    @staticmethod
    def validate_project_name(name: str) -> tuple[bool, str]:
        """
        Validate project name format.

        Project names must contain only alphanumeric characters, hyphens, and underscores.
        They cannot be empty or consist only of whitespace.

        Args:
            name: The project name to validate

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.

        Examples:
            >>> ProjectValidator.validate_project_name("my-project")
            (True, "")
            >>> ProjectValidator.validate_project_name("my_project_123")
            (True, "")
            >>> ProjectValidator.validate_project_name("my project!")
            (False, "Project name must contain only alphanumeric characters, hyphens, and underscores")
        """
        if not name or not name.strip():
            return False, "Project name cannot be empty"

        # Pattern: alphanumeric, hyphens, and underscores only
        pattern = r"^[a-zA-Z0-9_-]+$"

        if not re.match(pattern, name):
            return False, (
                "Project name must contain only alphanumeric characters, hyphens, and underscores. "
                "Examples: 'my-project', 'my_project', 'project123'"
            )

        return True, ""

    @staticmethod
    def validate_directory_available(path: Path) -> tuple[bool, str]:
        """
        Check if directory is available for project creation.

        Validates that the target directory either doesn't exist or is empty.

        Args:
            path: Path object representing the target directory

        Returns:
            Tuple of (is_available, message). Message describes the conflict if not available.

        Examples:
            >>> ProjectValidator.validate_directory_available(Path("/tmp/new-project"))
            (True, "")
            >>> ProjectValidator.validate_directory_available(Path("/tmp/existing"))
            (False, "Directory '/tmp/existing' already exists. Choose a different name or remove the existing directory.")
        """
        if not path.exists():
            return True, ""

        if path.is_file():
            return False, (
                f"A file named '{path.name}' already exists at this location. "
                "Please choose a different project name."
            )

        # Directory exists - check if it's empty
        if path.is_dir():
            try:
                if any(path.iterdir()):
                    return False, (
                        f"Directory '{path}' already exists and is not empty. "
                        "Choose a different name or remove the existing directory."
                    )
                else:
                    # Empty directory is acceptable
                    return True, ""
            except PermissionError:
                return False, (
                    f"Permission denied accessing directory '{path}'. "
                    "Please check directory permissions."
                )

        return True, ""

    @staticmethod
    def validate_mongodb_url(url: str) -> tuple[bool, str]:
        """
        Validate MongoDB connection string format.

        Performs basic format validation without attempting to connect.
        Accepts mongodb:// and mongodb+srv:// schemes.

        Args:
            url: MongoDB connection URL string

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.

        Examples:
            >>> ProjectValidator.validate_mongodb_url("mongodb://localhost:27017")
            (True, "")
            >>> ProjectValidator.validate_mongodb_url("mongodb+srv://cluster.mongodb.net")
            (True, "")
            >>> ProjectValidator.validate_mongodb_url("http://localhost:27017")
            (False, "MongoDB URL must start with 'mongodb://' or 'mongodb+srv://'")
        """
        if not url or not url.strip():
            return False, "MongoDB URL cannot be empty"

        url = url.strip()

        # Check for valid MongoDB schemes
        if not (url.startswith("mongodb://") or url.startswith("mongodb+srv://")):
            return False, (
                "MongoDB URL must start with 'mongodb://' or 'mongodb+srv://'. "
                "Examples: 'mongodb://localhost:27017', 'mongodb+srv://cluster.mongodb.net'"
            )

        # Basic URL parsing validation
        try:
            parsed = urlparse(url)

            # Ensure there's a netloc (host) component
            if not parsed.netloc:
                return False, (
                    "MongoDB URL must include a host. " "Example: 'mongodb://localhost:27017'"
                )

            # For mongodb:// (not srv), validate port if present
            if url.startswith("mongodb://") and ":" in parsed.netloc:
                # Extract port from netloc (format: host:port or user:pass@host:port)
                netloc_parts = parsed.netloc.split("@")
                host_port = netloc_parts[-1]  # Get the host:port part

                if ":" in host_port:
                    port_str = host_port.split(":")[-1]
                    try:
                        port = int(port_str)
                        if port < 1 or port > 65535:
                            return False, f"Port number must be between 1 and 65535, got {port}"
                    except ValueError:
                        return False, f"Invalid port number: '{port_str}'"

            return True, ""

        except Exception as e:
            return False, f"Invalid MongoDB URL format: {str(e)}"

    @staticmethod
    def validate_postgres_config(config: dict) -> tuple[bool, str]:
        """
        Validate PostgreSQL configuration parameters.

        Validates host, port, database name, username, and password.

        Args:
            config: Dictionary containing PostgreSQL configuration with keys:
                   - host: Database host (required)
                   - port: Database port (required, must be 1-65535)
                   - database: Database name (required)
                   - username: Database username (required)
                   - password: Database password (optional)

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.

        Examples:
            >>> config = {"host": "localhost", "port": 5432, "database": "mydb", "username": "user"}
            >>> ProjectValidator.validate_postgres_config(config)
            (True, "")
        """
        required_fields = ["host", "port", "database", "username"]

        # Check for required fields
        for field in required_fields:
            if field not in config:
                return False, f"PostgreSQL configuration missing required field: '{field}'"

            if not config[field]:
                return False, f"PostgreSQL '{field}' cannot be empty"

        # Validate host
        host = config["host"]
        if not isinstance(host, str) or not host.strip():
            return False, "PostgreSQL host must be a non-empty string"

        # Validate port
        port = config["port"]
        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                return False, f"PostgreSQL port must be between 1 and 65535, got {port_int}"
        except (ValueError, TypeError):
            return False, f"PostgreSQL port must be a valid integer, got '{port}'"

        # Validate database name
        database = config["database"]
        if not isinstance(database, str) or not database.strip():
            return False, "PostgreSQL database name must be a non-empty string"

        # Validate database name format (PostgreSQL naming rules)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", database):
            return False, (
                "PostgreSQL database name must start with a letter or underscore, "
                "and contain only letters, numbers, and underscores"
            )

        # Validate username
        username = config["username"]
        if not isinstance(username, str) or not username.strip():
            return False, "PostgreSQL username must be a non-empty string"

        # Password is optional, but if provided, validate it's a string
        if "password" in config and config["password"] is not None:
            if not isinstance(config["password"], str):
                return False, "PostgreSQL password must be a string"

        return True, ""

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Validate email format using basic RFC 5322 rules.

        Performs basic email format validation without attempting to verify
        the email address exists.

        Args:
            email: Email address string to validate

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.

        Examples:
            >>> ProjectValidator.validate_email("user@example.com")
            (True, "")
            >>> ProjectValidator.validate_email("invalid.email")
            (False, "Email must contain '@' symbol")
        """
        if not email or not email.strip():
            return False, "Email cannot be empty"

        email = email.strip()

        # Basic RFC 5322 email validation pattern
        # This is a simplified pattern that covers most common cases
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if "@" not in email:
            return False, "Email must contain '@' symbol"

        if not re.match(pattern, email):
            return False, (
                "Invalid email format. Email must be in the format 'user@example.com'. "
                "Local part can contain letters, numbers, dots, underscores, percent, plus, and hyphens. "
                "Domain must have at least one dot and a valid TLD."
            )

        # Additional validation: check for consecutive dots
        if ".." in email:
            return False, "Email cannot contain consecutive dots"

        # Check local and domain parts
        local, domain = email.rsplit("@", 1)

        if not local:
            return False, "Email local part (before @) cannot be empty"

        if not domain:
            return False, "Email domain part (after @) cannot be empty"

        if local.startswith(".") or local.endswith("."):
            return False, "Email local part cannot start or end with a dot"

        if domain.startswith(".") or domain.endswith("."):
            return False, "Email domain cannot start or end with a dot"

        return True, ""
