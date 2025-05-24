import asyncio
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as running in an event loop"
    )


def pytest_pyfunc_call(pyfuncitem):
    testfunc = pyfuncitem.obj
    if asyncio.iscoroutinefunction(testfunc):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None
