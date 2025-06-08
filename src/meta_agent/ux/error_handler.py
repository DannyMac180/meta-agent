"""Central error handling utilities for UX modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any, TYPE_CHECKING

import logging

from meta_agent.utils.logging import setup_logging

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .cli_output import CLIOutput

logger = setup_logging(__name__)


@dataclass
class UXError(Exception):
    """Base error with optional context."""

    message: str
    context: Mapping[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


class CLIOutputError(UXError):
    """Raised when CLI output fails."""


class InteractiveError(UXError):
    """Raised when interactive input fails."""


class DiagramGenerationError(UXError):
    """Raised when diagram generation fails."""


class ErrorHandler:
    """Handle errors by logging and providing user feedback."""

    def __init__(
        self,
        cli_output: CLIOutput | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        from .cli_output import CLIOutput  # local import to avoid circular

        self.cli_output = cli_output or CLIOutput()
        self.logger = log or logger

    def handle(self, error: UXError) -> None:
        """Log the error and display the message via CLI."""
        msg = str(error)
        if error.context:
            self.logger.error("%s | context=%s", msg, error.context)
        else:
            self.logger.error(msg)
        try:
            self.cli_output.error(msg)
        except Exception:
            self.logger.error("Failed to output error message via CLI")
