"""Main CLI entry point for FastAPI CRUD scaffolding tool."""

import click
from rich.console import Console

from fastapi_crud_cli.__version__ import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="fastapi-crud")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    FastAPI CRUD Backend Scaffolding Tool.

    Generate new FastAPI projects with customizable database backends
    and development configurations through an interactive CLI.
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Skip prompts and use default values (not yet implemented)",
)
def create(non_interactive: bool) -> None:
    """
    Create a new FastAPI CRUD project.

    This command guides you through an interactive process to configure
    and generate a new FastAPI project with your chosen database backend
    and development tools.
    """
    from pathlib import Path

    from .generator import ProjectGenerator
    from .output import OutputFormatter
    from .prompts import ProjectPrompts

    # Initialize components
    output = OutputFormatter(console)
    prompts = ProjectPrompts(console)
    generator = ProjectGenerator(console)

    try:
        # Display welcome message
        output.display_welcome()

        # Collect user input through interactive prompts
        project_name = prompts.prompt_project_name()
        database_type = prompts.prompt_database_type()
        database_config = prompts.prompt_database_config(database_type)
        env_variables = prompts.prompt_environment_variables(database_type)
        metadata = prompts.prompt_project_metadata()
        optional_features = prompts.prompt_optional_features()

        # Build complete project configuration
        config = {
            "project_name": project_name,
            "project_slug": project_name.lower().replace("-", "_"),
            "database_type": database_type,
            "database_config": database_config,
            "env_variables": env_variables,
            "author_name": metadata["author_name"],
            "author_email": metadata["author_email"],
            "description": metadata["description"],
            "include_examples": optional_features["include_examples"],
            "include_dev_tools": optional_features["include_dev_tools"],
            "include_static": optional_features["include_static"],
        }

        # Display configuration summary and ask for confirmation
        confirmed = prompts.confirm_generation(config)

        if not confirmed:
            console.print()
            output.display_info("Project generation cancelled by user.")
            console.print()
            return

        # Generate the project
        console.print()
        output_dir = Path.cwd() / project_name

        success = generator.generate_project(config, output_dir)

        if success:
            # Display next steps
            output.display_next_steps(output_dir)
        else:
            console.print()
            output.display_error(
                "Project generation failed", "Please check the error messages above and try again."
            )
            console.print()

    except KeyboardInterrupt:
        # Handle user cancellation (Ctrl+C)
        console.print()
        console.print()
        output.display_info("Project generation cancelled by user.")
        console.print()

    except Exception as e:
        # Handle unexpected errors
        console.print()
        console.print()
        output.display_error("An unexpected error occurred", str(e))
        console.print()
        raise


@cli.command()
def list() -> None:
    """
    List available database backend options.

    Displays a formatted table of all supported database backends
    with their descriptions and key features.
    """
    from rich.table import Table

    from .database_configs import DATABASE_CONFIGS
    from .output import OutputFormatter

    output = OutputFormatter(console)

    # Create table for database options
    table = Table(
        title="Available Database Backends",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    table.add_column("Database Type", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    # Add each database configuration to the table
    for db_type, config in DATABASE_CONFIGS.items():
        table.add_row(db_type, config.description)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Use 'fastapi-crud info <database-type>' for detailed information[/dim]")
    console.print()


@cli.command()
@click.argument("database_type", required=False)
def info(database_type: str | None) -> None:
    """
    Show detailed information about a database backend.

    Displays requirements, features, dependencies, and environment
    variables for the specified database type.

    Example:
        fastapi-crud info mongodb
    """
    from difflib import get_close_matches

    from rich.panel import Panel
    from rich.table import Table

    from .database_configs import DATABASE_CONFIGS
    from .output import OutputFormatter

    output = OutputFormatter(console)

    # Check if database type was provided
    if not database_type:
        console.print()
        output.display_error(
            "Missing database type argument",
            "Please specify a database type (sqlite, mongodb, or postgresql)",
        )
        console.print()
        console.print("[dim]Example: fastapi-crud info mongodb[/dim]")
        console.print()
        return

    # Normalize database type to lowercase
    database_type = database_type.lower()

    # Check if database type is valid
    if database_type not in DATABASE_CONFIGS:
        # Find closest matches for suggestions
        available_types = list(DATABASE_CONFIGS.keys())
        suggestions = get_close_matches(database_type, available_types, n=1, cutoff=0.6)

        console.print()
        output.display_error(
            f"Invalid database type: {database_type}",
            f"Available options: {', '.join(available_types)}",
        )

        if suggestions:
            console.print()
            console.print(f"[yellow]Did you mean:[/yellow] [cyan]{suggestions[0]}[/cyan]?")

        console.print()
        return

    # Get database configuration
    config = DATABASE_CONFIGS[database_type]

    # Display database information
    console.print()

    # Header panel
    header = Panel(
        f"[bold cyan]{config.name}[/bold cyan]\n\n{config.description}",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(header)
    console.print()

    # Dependencies table
    deps_table = Table(
        title="Required Dependencies",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    deps_table.add_column("Package", style="green")

    for dep in config.dependencies:
        deps_table.add_row(dep)

    console.print(deps_table)
    console.print()

    # Environment variables table
    env_table = Table(
        title="Environment Variables",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    env_table.add_column("Variable", style="cyan", no_wrap=True)
    env_table.add_column("Default Value", style="white")

    for var_name, var_value in config.env_variables.items():
        env_table.add_row(var_name, var_value)

    console.print(env_table)
    console.print()

    # Configuration prompts
    prompts = config.get_prompts()
    if prompts:
        prompts_table = Table(
            title="Configuration Prompts",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
        )
        prompts_table.add_column("Setting", style="cyan", no_wrap=True)
        prompts_table.add_column("Default", style="white")

        for prompt in prompts:
            setting_name = prompt["name"].replace("_", " ").title()
            default_value = prompt.get("default", "[dim]None[/dim]")
            # Mask password defaults
            if prompt.get("type") == "password" and default_value:
                default_value = "********"
            prompts_table.add_row(setting_name, str(default_value))

        console.print(prompts_table)
        console.print()

    # Usage hint
    console.print(
        "[dim]Use 'fastapi-crud create' to generate a new project with this database[/dim]"
    )
    console.print()


if __name__ == "__main__":
    cli()
