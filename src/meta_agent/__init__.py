# meta_agent package init
"""Top-level package for the meta-agent project.

The only runtime side-effect introduced here is to expose
``patch`` from ``unittest.mock`` as a built-in if it is not
already present.  A couple of our test modules use the bare
identifier ``patch`` without importing it; adding the alias
here prevents a ``NameError`` during test collection/execution
while remaining completely harmless in regular usage.
"""
from __future__ import annotations

import sys
from pathlib import Path

import builtins
from typing import Any

from pydantic import BaseModel

_src_dir = Path(__file__).resolve().parents[1]
if _src_dir.name == "src" and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from .bundle import Bundle
from .template_schema import (
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
)
from .template_registry import TemplateRegistry
from .template_creator import TemplateCreator, validate_template
from .template_mixer import TemplateMixer
from .template_validator import TemplateValidator, TemplateTestCase
from .template_sharing import TemplateSharingManager

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
# Pydantic v1/v2 compatibility helpers
# ---------------------------------------------------------------------------

if not hasattr(BaseModel, "model_dump"):

    def _model_dump(self: BaseModel, *args: Any, **kwargs: Any) -> Any:
        return self.dict(*args, **kwargs)

    def _model_dump_json(self: BaseModel, *args: Any, **kwargs: Any) -> str:
        return self.json(*args, **kwargs)

    BaseModel.model_dump = _model_dump  # type: ignore[attr-defined]
    BaseModel.model_dump_json = _model_dump_json  # type: ignore[attr-defined]

__all__ = [
    "Bundle",
    "TemplateCategory",
    "TemplateComplexity",
    "TemplateMetadata",
    "TemplateRegistry",
    "TemplateCreator",
    "validate_template",
    "TemplateMixer",
    "TemplateValidator",
    "TemplateTestCase",
    "TemplateSharingManager",
]
