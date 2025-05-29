"""Interface for creating user defined templates."""

from __future__ import annotations

from typing import Optional, Tuple

from jinja2 import Environment, TemplateSyntaxError

from .template_registry import TemplateRegistry
from .template_schema import TemplateMetadata


def validate_template(content: str) -> Tuple[bool, str]:
    """Check that the template is valid Jinja2."""
    try:
        Environment().parse(content)
    except TemplateSyntaxError as e:  # pragma: no cover - jinja2 handled
        return False, str(e)
    return True, ""


class TemplateCreator:
    """Create and register templates."""

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self.registry = registry or TemplateRegistry()

    def create(
        self,
        metadata: TemplateMetadata,
        content: str,
        *,
        version: str = "0.1.0",
        validate: bool = True,
    ) -> Optional[str]:
        """Register a template after optional validation."""
        if validate:
            ok, err = validate_template(content)
            if not ok:
                raise ValueError(f"Template validation failed: {err}")
        if not content.strip():
            raise ValueError("Template content cannot be empty")
        return self.registry.register(metadata, content, version)
