"""Utilities for consistent CLI output with colors and verbosity levels."""

from __future__ import annotations

import click


class CLIOutput:
    """Manage colored terminal output with verbosity control."""

    def __init__(self, verbosity: int = 1) -> None:
        self.verbosity = verbosity

    def set_verbosity(self, verbosity: int) -> None:
        """Set the current verbosity level."""
        self.verbosity = verbosity

    def _echo(
        self,
        message: str,
        *,
        fg: str | None = None,
        bold: bool = False,
        err: bool = False,
        level: int = 1,
    ) -> None:
        if self.verbosity >= level:
            click.secho(message, fg=fg, bold=bold, err=err)

    def info(self, message: str, *, level: int = 1) -> None:
        """Output an informational message."""
        self._echo(message, fg="cyan", level=level)

    def success(self, message: str, *, level: int = 1) -> None:
        """Output a success message."""
        self._echo(message, fg="green", bold=True, level=level)

    def warning(self, message: str, *, level: int = 1) -> None:
        """Output a warning message."""
        self._echo(message, fg="yellow", level=level)

    def error(self, message: str, *, level: int = 1) -> None:
        """Output an error message."""
        self._echo(message, fg="red", bold=True, err=True, level=level)
