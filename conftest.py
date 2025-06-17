"""Test-suite shim: fixes methods defined without *self* inside test classes.

Pytest injects the instance as the first positional arg; if a test method is
defined with *no* parameters this yields a `TypeError`.  We wrap such callables
so they accept arbitrary positional arguments and forward the call.
"""

from __future__ import annotations

import inspect
from types import FunctionType
from typing import Any, Callable


def _wrap_noarg(func: Callable[[], Any]) -> Callable[..., Any]:
    """Return a wrapper that discards extraneous positional arguments."""

    def _wrapper(*_args: Any, **_kwargs: Any) -> Any:  # noqa: D401
        return func()

    _wrapper.__name__ = func.__name__
    _wrapper.__doc__ = func.__doc__
    _wrapper.__qualname__ = func.__qualname__
    return _wrapper


def pytest_collection_modifyitems(session, config, items):  # type: ignore[unused-argument]
    """Patch collected items in-place before execution."""
    for item in items:
        func = getattr(item, "function", None)
        if isinstance(func, FunctionType):
            try:
                sig = inspect.signature(func)
            except (TypeError, ValueError):
                continue
            if len(sig.parameters) == 0:
                patched = _wrap_noarg(func)
                item.obj = patched
                # Newer pytest versions expose `function` as *read-only* property.
                if hasattr(item, "function"):
                    try:
                        setattr(item, "function", patched)
                    except AttributeError:
                        # Ignore if attribute is read-only (pytest ≥8)
                        pass
                # Pytest ≤7 keeps a private ref
                if hasattr(item, "_obj"):
                    item._obj = patched