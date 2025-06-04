from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch


class MockerFixture:
    """Minimal stand-in for pytest-mock's MockerFixture."""

    AsyncMock = AsyncMock

    def patch(self, *args, **kwargs):
        return patch(*args, **kwargs)


@pytest.fixture
def mocker() -> MockerFixture:
    """Provide a basic mocker fixture."""

    return MockerFixture()
