"""Minimal stub of the OpenAI Python SDK used for tests."""


class APIConnectionError(Exception):
    """Placeholder API connection error."""

    def __init__(self, request=None):
        self.request = request


class APITimeoutError(Exception):
    """Placeholder API timeout error."""

    def __init__(self, request=None):
        self.request = request


class AuthenticationError(Exception):
    """Placeholder authentication error."""

    def __init__(self, message: str = "", response=None, body=None):
        super().__init__(message)
        self.response = response
        self.body = body


class _ChatCompletions:
    def create(self, *args, **kwargs):  # pragma: no cover - stub method
        raise NotImplementedError


class _Chat:
    def __init__(self):
        self.completions = _ChatCompletions()


class OpenAI:
    """Simplified client stub."""

    def __init__(self, *args, **kwargs):
        self.chat = _Chat()


__all__ = [
    "OpenAI",
    "APIConnectionError",
    "APITimeoutError",
    "AuthenticationError",
]
__version__ = "0.0.0"
