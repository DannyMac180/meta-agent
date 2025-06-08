"""User feedback utilities such as progress bars and notifications."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Iterator, TypeVar

import click

from .cli_output import CLIOutput


T = TypeVar("T")


class NotificationSeverity(Enum):
    """Severity levels for notifications."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class UserFeedback:
    """Provide progress bars, notifications and error suggestions."""

    def __init__(self, cli_output: CLIOutput | None = None) -> None:
        self.cli_output = cli_output or CLIOutput()

    def notify(self, message: str, severity: NotificationSeverity = NotificationSeverity.INFO) -> None:
        """Display a notification with the appropriate style."""
        if severity is NotificationSeverity.SUCCESS:
            self.cli_output.success(message)
        elif severity is NotificationSeverity.WARNING:
            self.cli_output.warning(message)
        elif severity in (NotificationSeverity.ERROR, NotificationSeverity.CRITICAL):
            self.cli_output.error(message)
        else:
            self.cli_output.info(message)

    def progress_iter(self, iterable: Iterable[T], *, description: str = "Working") -> Iterator[T]:
        """Yield items from ``iterable`` while displaying a progress bar."""
        with click.progressbar(iterable, label=description) as bar:
            for item in bar:
                yield item

    def error_suggestion(self, error_message: str) -> str | None:
        """Return a suggestion string for the given error message and output it."""
        suggestions = {
            "failed to load": "Check that the file path exists and is readable.",
            "network": "Ensure your internet connection is available.",
        }
        error_lower = error_message.lower()
        for token, suggestion in suggestions.items():
            if token in error_lower:
                self.cli_output.info(f"Suggestion: {suggestion}")
                return suggestion
        return None

    def copy_to_clipboard(self, text: str) -> bool:
        """Attempt to copy ``text`` to the clipboard; return True if successful."""
        try:
            import pyperclip  # type: ignore
        except Exception:
            return False
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False
