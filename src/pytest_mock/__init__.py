from __future__ import annotations
import pytest
from unittest.mock import patch, AsyncMock


class MockerFixture:
    """Minimal stand-in for pytest-mock's fixture class."""

    AsyncMock = AsyncMock

    def patch(self, *args, **kwargs):
        return patch(*args, **kwargs)


@pytest.fixture
def mocker() -> MockerFixture:
    """Provide a minimal mocker fixture using ``unittest.mock``."""
    return MockerFixture()
