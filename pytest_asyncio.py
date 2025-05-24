import asyncio
import inspect
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark a test as running with asyncio"
    )


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    test_func = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_func):
        asyncio.run(test_func(**pyfuncitem.funcargs))
        return True
    return None
