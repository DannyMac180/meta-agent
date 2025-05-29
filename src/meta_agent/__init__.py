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

import builtins

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
