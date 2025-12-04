"""Output formatting module for CLI with Rich styling."""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree


class OutputFormatter:
    """Format and display CLI output with Rich styling."""

    def __init__(self, console: Console | None = None):
        """
        Initialize the output formatter.

        Args:
            console: Rich Console instance. If None, creates a new one.
        """
        self.console = console or Console()

    def display_welcome(self) -> None:
        """Display welcome banner with project branding."""
        welcome_text = """
[bold cyan]FastAPI CRUD CLI[/bold cyan]

[dim]Generate production-ready FastAPI projects with customizable
database backends and development configurations.[/dim]
        """
        panel = Panel(
            welcome_text.strip(),
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def display_progress(self, message: str) -> None:
        """
        Show progress message with spinner.

        Args:
            message: Progress message to display
        """
        self.console.print(f"[yellow]⋯[/yellow] {message}")

    def display_success(self, message: str) -> None:
        """
        Show success message with checkmark.

        Args:
            message: Success message to display
        """
        self.console.print(f"[green]✓[/green] {message}")

    def display_error(self, message: str, details: str | None = None) -> None:
        """
        Show error message with error symbol and optional details.

        Args:
            message: Brief error description
            details: Optional detailed error information
        """
        self.console.print(f"[red]✗ Error:[/red] {message}")
        if details:
            self.console.print(f"[dim]Details: {details}[/dim]")

    def display_summary_table(self, config: dict[str, Any]) -> None:
        """
        Display configuration summary as formatted table.

        Args:
            config: Configuration dictionary to display
        """
        table = Table(
            title="Project Configuration",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
        )
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Display configuration items
        for key, value in config.items():
            # Format key as human-readable
            display_key = key.replace("_", " ").title()

            # Format value based on type
            if isinstance(value, bool):
                display_value = "✓ Yes" if value else "✗ No"
            elif isinstance(value, list):
                display_value = ", ".join(str(v) for v in value) if value else "[dim]None[/dim]"
            elif isinstance(value, dict):
                display_value = "\n".join(f"{k}: {v}" for k, v in value.items())
            elif value is None:
                display_value = "[dim]Not specified[/dim]"
            else:
                display_value = str(value)

            table.add_row(display_key, display_value)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def display_file_tree(self, files: list[Path], base_dir: Path | None = None) -> None:
        """
        Display generated files as tree structure.

        Args:
            files: List of file paths to display
            base_dir: Base directory for relative path calculation
        """
        if not files:
            self.console.print("[dim]No files to display[/dim]")
            return

        # Determine base directory
        if base_dir is None and files:
            base_dir = files[0].parent if files[0].is_file() else files[0]

        # Create tree structure
        tree = Tree(
            f"[bold cyan]{base_dir.name if base_dir else 'Project'}[/bold cyan]",
            guide_style="cyan",
        )

        # Build directory structure
        dir_nodes: dict[Path, Tree] = {base_dir: tree}

        # Sort files for consistent display
        sorted_files = sorted(files, key=lambda p: (str(p.parent), p.name))

        for file_path in sorted_files:
            # Calculate relative path
            try:
                rel_path = file_path.relative_to(base_dir) if base_dir else file_path
            except ValueError:
                rel_path = file_path

            # Build path components
            parts = rel_path.parts
            current_base = base_dir

            # Create intermediate directories
            for i, part in enumerate(parts[:-1]):
                current_base = current_base / part if current_base else Path(part)

                if current_base not in dir_nodes:
                    parent_path = current_base.parent
                    parent_node = dir_nodes.get(parent_path, tree)
                    dir_nodes[current_base] = parent_node.add(f"[bold blue]{part}/[/bold blue]")

            # Add file
            parent_path = file_path.parent
            parent_node = dir_nodes.get(parent_path, tree)

            # Style based on file type
            filename = parts[-1] if parts else str(file_path)
            if filename.startswith("."):
                style = "dim"
            elif filename.endswith((".py", ".sh")):
                style = "green"
            elif filename.endswith((".md", ".txt", ".rst")):
                style = "yellow"
            elif filename.endswith((".json", ".yaml", ".yml", ".toml")):
                style = "cyan"
            else:
                style = "white"

            parent_node.add(f"[{style}]{filename}[/{style}]")

        self.console.print()
        self.console.print(tree)
        self.console.print()

    def display_next_steps(self, project_dir: Path) -> None:
        """
        Display post-generation instructions and next steps.

        Args:
            project_dir: Path to the generated project directory
        """
        next_steps = f"""
[bold cyan]Next Steps:[/bold cyan]

1. Navigate to your project:
   [green]cd {project_dir.name}[/green]

2. Activate the virtual environment:
   [green]source venv/bin/activate[/green]  [dim]# On Windows: venv\\Scripts\\activate[/dim]

3. Review your environment configuration:
   [green]cat .env[/green]
   [dim]# Your database and app settings are already configured[/dim]

4. Run the development server:
   [green]python main.py[/green]
   [dim]# Or: uvicorn main:app --reload[/dim]

5. Visit the API documentation:
   [cyan]http://localhost:8000/docs[/cyan]

[bold green]✓[/bold green] Virtual environment created
[bold green]✓[/bold green] Dependencies installed
[bold green]✓[/bold green] Environment variables configured

[bold]Happy coding! 🚀[/bold]
        """
        panel = Panel(
            next_steps.strip(),
            border_style="green",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def create_progress_context(self, description: str = "Processing...") -> Progress:
        """
        Create a Rich Progress context manager for long-running operations.

        Args:
            description: Description of the operation

        Returns:
            Progress: Rich Progress instance for use in context manager
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )

    def display_info(self, message: str) -> None:
        """
        Display informational message.

        Args:
            message: Information message to display
        """
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def display_warning(self, message: str) -> None:
        """
        Display warning message.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[yellow]⚠[/yellow] {message}")
