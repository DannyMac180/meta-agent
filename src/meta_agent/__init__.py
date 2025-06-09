# meta_agent package init
"""Top-level package for the meta-agent project.

The only runtime side-effect introduced here is to expose
``patch`` from ``unittest.mock`` as a built-in if it is not
already present.  A couple of our test modules use the bare
identifier ``patch`` without importing it; adding the alias
here prevents a ``NameError`` during test collection/execution
while remaining completely harmless in regular usage.
"""
# ruff: noqa: E402
from __future__ import annotations

import builtins
from typing import Any

from pydantic import BaseModel

from .bundle import Bundle
from .template_schema import (
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
    IOContract,
)
from .template_registry import TemplateRegistry
from .template_creator import TemplateCreator, validate_template
from .template_mixer import TemplateMixer
from .template_validator import TemplateValidator, TemplateTestCase
from .template_sharing import TemplateSharingManager
from .template_index import TemplateIndex

# Expose `patch` globally for tests that forget to import it.
try:
    # Only add if it hasn't been defined elsewhere to avoid clobbering.
    if not hasattr(builtins, "patch"):
        from unittest.mock import (
            patch as _patch,
        )  # Lazy import to avoid unnecessary overhead.

        builtins.patch = _patch  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    # Failing to add the helper must never break runtime code, so swallow
    # any unexpected error silently – tests will fail loudly if they rely
    # on it and something went wrong here.
    pass

# ---------------------------------------------------------------------------
# Pydantic compatibility helpers
# ---------------------------------------------------------------------------
try:

    def _ensure_pydantic_methods(cls: type[BaseModel]) -> None:
        """Ensure ``model_dump`` and ``model_dump_json`` exist on ``cls``."""

        if not hasattr(cls, "model_dump"):

            def _model_dump(self: BaseModel, *args: Any, **kwargs: Any) -> Any:
                return self.dict(*args, **kwargs)

            cls.model_dump = _model_dump  # type: ignore[attr-defined]

        if not hasattr(cls, "model_dump_json"):

            def _model_dump_json(self: BaseModel, *args: Any, **kwargs: Any) -> str:
                return self.json(*args, **kwargs)

            cls.model_dump_json = _model_dump_json  # type: ignore[attr-defined]

    # Patch BaseModel itself
    _ensure_pydantic_methods(BaseModel)

    # Patch any subclasses defined before this module was imported
    for _sub in list(BaseModel.__subclasses__()):
        _ensure_pydantic_methods(_sub)

    # Ensure future subclasses also get patched automatically
    _orig_init_subclass = BaseModel.__init_subclass__

    def _patched_init_subclass(cls, **kwargs: Any) -> None:  # type: ignore[override]
        _orig_init_subclass(**kwargs)
        _ensure_pydantic_methods(cls)

    BaseModel.__init_subclass__ = classmethod(_patched_init_subclass)  # type: ignore[assignment]
except Exception:  # pragma: no cover - should never fail at runtime
    pass

__all__ = [
    "Bundle",
    "TemplateCategory",
    "TemplateComplexity",
    "TemplateMetadata",
    "IOContract",
    "TemplateRegistry",
    "TemplateCreator",
    "validate_template",
    "TemplateMixer",
    "TemplateValidator",
    "TemplateTestCase",
    "TemplateSharingManager",
    "TemplateIndex",
]
