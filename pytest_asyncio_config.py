import asyncio
import pytest_mock


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as running in an event loop")
    # Also register the simple mocker fixture from our local pytest_mock module
    if not config.pluginmanager.hasplugin("pytest_mock"):
        try:
            pytest_mock.pytest_configure(config)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - ignore if already registered
            pass


def pytest_pyfunc_call(pyfuncitem):
    testfunc = pyfuncitem.obj
    if asyncio.iscoroutinefunction(testfunc):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            args = {
                name: pyfuncitem.funcargs[name]
                for name in pyfuncitem._fixtureinfo.argnames
            }
            loop.run_until_complete(pyfuncitem.obj(**args))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None
