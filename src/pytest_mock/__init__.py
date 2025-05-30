from __future__ import annotations
import sys
import pytest
from unittest.mock import patch, AsyncMock


class MockerFixture:
    AsyncMock = AsyncMock

    def patch(self, *args, **kwargs):  # noqa: D401
        return patch(*args, **kwargs)


def pytest_configure(config):  # pragma: no cover - register fixture
    @pytest.fixture
    def mocker():
        return MockerFixture()

    if not config.pluginmanager.hasplugin("pytest_mock"):
        config.pluginmanager.register(sys.modules[__name__])
