"""Tests for main CLI entry point."""

import pytest
from typer.testing import CliRunner
from boo.main import app
from boo import __version__

runner = CliRunner()


def test_version() -> None:
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help() -> None:
    """Test help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "boo" in result.stdout.lower()
    assert "package manager" in result.stdout.lower()


def test_install_command_exists() -> None:
    """Test install command is available."""
    result = runner.invoke(app, ["install", "--help"])
    assert result.exit_code == 0
    assert "install" in result.stdout.lower()


def test_uninstall_command_exists() -> None:
    """Test uninstall command is available."""
    result = runner.invoke(app, ["uninstall", "--help"])
    assert result.exit_code == 0
    assert "uninstall" in result.stdout.lower()


def test_list_command_exists() -> None:
    """Test list command is available."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0


def test_tree_command_exists() -> None:
    """Test tree command is available."""
    result = runner.invoke(app, ["tree", "--help"])
    assert result.exit_code == 0
    assert "tree" in result.stdout.lower()


def test_search_command_exists() -> None:
    """Test search command is available."""
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "search" in result.stdout.lower()


def test_check_command_exists() -> None:
    """Test check command is available."""
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout.lower()


def test_update_command_exists() -> None:
    """Test update command is available."""
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    assert "update" in result.stdout.lower()


def test_sync_command_exists() -> None:
    """Test sync command is available."""
    result = runner.invoke(app, ["sync", "--help"])
    assert result.exit_code == 0
    assert "sync" in result.stdout.lower()
