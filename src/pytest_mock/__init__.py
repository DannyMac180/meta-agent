from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


class MockerFixture:
    AsyncMock = AsyncMock

    def patch(self, *args, **kwargs):  # noqa: D401
        return patch(*args, **kwargs)


@pytest.fixture
def mocker() -> MockerFixture:  # pragma: no cover - simple fixture
    return MockerFixture()


def pytest_configure(config):  # pragma: no cover - plugin auto-discovery
    # The fixture is provided via the module; no additional setup required.
    return None
