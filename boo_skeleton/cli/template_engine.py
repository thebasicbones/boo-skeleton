"""
Template engine for rendering project files
"""

import shutil
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, Template

from boo_skeleton.cli.output import OutputFormatter


class TemplateEngine:
    """Engine for rendering project templates."""

    def __init__(self, template_dir: Path, source_dir: Path):
        """
        Initialize template engine.

        Args:
            template_dir: Directory containing Jinja2 templates and manifest
            source_dir: Directory containing source files to copy
        """
        self.template_dir = template_dir
        self.source_dir = source_dir

        # For Jinja2, use the project subdirectory
        project_template_dir = template_dir / "project"
        self.env = Environment(
            loader=FileSystemLoader(str(project_template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Load manifest from the main template directory
        manifest_path = template_dir / "template_manifest.yaml"
        if manifest_path.exists():
            with open(manifest_path) as f:
                self.manifest = yaml.safe_load(f)
        else:
            self.manifest = {"static_files": [], "template_files": [], "empty_files": []}

    def render_project(
        self, config: dict[str, Any], output_dir: Path, formatter: OutputFormatter
    ) -> list[Path]:
        """
        Render entire project structure.

        Args:
            config: Project configuration dictionary
            output_dir: Output directory for generated project
            formatter: Output formatter for progress messages

        Returns:
            List of created file paths
        """
        created_files = []
        context = self._build_context(config)

        # Create base directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process static files (copy from source)
        for file_spec in self.manifest.get("static_files", []):
            if self._should_include(file_spec, context):
                created = self._copy_static_file(file_spec, output_dir, formatter)
                if created:
                    created_files.append(created)

        # Process template files (render with Jinja2)
        for file_spec in self.manifest.get("template_files", []):
            if self._should_include(file_spec, context):
                created = self._render_template_file(file_spec, output_dir, context, formatter)
                if created:
                    created_files.append(created)

        # Create empty files
        for file_path in self.manifest.get("empty_files", []):
            created = self._create_empty_file(file_path, output_dir, formatter)
            if created:
                created_files.append(created)

        return created_files

    def _build_context(self, config: dict[str, Any]) -> dict[str, Any]:
        """Build Jinja2 context from configuration."""
        from datetime import datetime

        context = config.copy()
        context["current_date"] = datetime.now().strftime("%Y-%m-%d")

        # Normalize project slug
        if "project_name" in context and "project_slug" not in context:
            context["project_slug"] = (
                context["project_name"].lower().replace(" ", "_").replace("-", "_")
            )

        return context

    def _should_include(self, file_spec: dict, context: dict[str, Any]) -> bool:
        """Check if file should be included based on condition."""
        condition = file_spec.get("condition")
        if not condition:
            return True

        try:
            # Evaluate condition in context
            return eval(condition, {"__builtins__": {}}, context)
        except Exception:
            return False

    def _copy_static_file(
        self, file_spec: dict, output_dir: Path, formatter: OutputFormatter
    ) -> Path | None:
        """Copy a static file from source to output."""
        source_path = self.source_dir / file_spec["source"]
        dest_path = output_dir / file_spec["dest"]

        if not source_path.exists():
            formatter.display_warning(f"Source file not found: {source_path}")
            return None

        # Create parent directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source_path, dest_path)
        formatter.display_progress(f"Copied: {file_spec['dest']}")

        return dest_path

    def _render_template_file(
        self, file_spec: dict, output_dir: Path, context: dict[str, Any], formatter: OutputFormatter
    ) -> Path | None:
        """Render a template file with Jinja2."""
        template_path = file_spec["template"]
        dest_path = output_dir / file_spec["dest"]

        try:
            # Check if this is a copy-only file
            if file_spec.get("copy_only", False):
                # For copy-only files, look in the project template directory
                source_path = self.template_dir / "project" / template_path
                if not source_path.exists():
                    formatter.display_warning(f"Template file not found: {source_path}")
                    return None

                # Create parent directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(source_path, dest_path)
                formatter.display_progress(f"Copied: {file_spec['dest']}")
                return dest_path

            # Remove 'project/' prefix if present since we're already in that directory
            if template_path.startswith("project/"):
                template_path = template_path[8:]  # Remove 'project/' prefix

            # Load and render template
            template = self.env.get_template(template_path)
            content = template.render(**context)

            # Create parent directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Write rendered content
            dest_path.write_text(content)

            # Make executable if specified
            if file_spec.get("executable", False):
                dest_path.chmod(0o755)

            formatter.display_progress(f"Generated: {file_spec['dest']}")
            return dest_path

        except Exception as e:
            formatter.display_error(f"Failed to render {template_path}: {str(e)}")
            return None

    def _create_empty_file(
        self, file_path: str, output_dir: Path, formatter: OutputFormatter
    ) -> Path | None:
        """Create an empty file."""
        dest_path = output_dir / file_path

        # Create parent directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty file
        dest_path.touch()

        formatter.display_progress(f"Created: {file_path}")
        return dest_path

    def render_string(self, template_str: str, context: dict[str, Any]) -> str:
        """Render a template string."""
        template = Template(template_str)
        return template.render(**context)
