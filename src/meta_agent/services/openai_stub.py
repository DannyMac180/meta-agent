"""Fallback stub for the OpenAI SDK used in tests.

This module provides minimal class definitions that mirror the parts of the
``openai`` package required by the tests. It allows the project to run without
the real OpenAI dependency installed.
"""

from typing import Any


class APIError(Exception):
    """Base error for OpenAI API failures."""


class AuthenticationError(APIError):
    """Authentication failed."""


class APIConnectionError(APIError):
    """API connection error."""


class APITimeoutError(APIError):
    """API timeout error."""


class _ChatCompletions:
    def create(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - stub
        raise NotImplementedError("OpenAI SDK not available")


class _Chat:
    def __init__(self) -> None:
        self.completions = _ChatCompletions()


class OpenAI:
    """Minimal OpenAI client stub."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.chat = _Chat()
