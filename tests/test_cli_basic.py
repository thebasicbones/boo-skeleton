"""Basic tests for the CLI tool."""

import pytest
from click.testing import CliRunner
from fastapi_crud_cli.cli.main import cli


def test_cli_help():
    """Test that CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "fastapi-crud" in result.output.lower() or "usage" in result.output.lower()


def test_cli_version():
    """Test that CLI version command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
