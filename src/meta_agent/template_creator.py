"""Interface for creating user defined templates."""

from __future__ import annotations

from typing import Optional, Tuple


from .template_validator import TemplateValidator

from .template_registry import TemplateRegistry
from .template_schema import TemplateMetadata


def validate_template(content: str) -> Tuple[bool, str]:
    """Check that the template is valid Jinja2 and passes security scan."""
    validator = TemplateValidator()
    result = validator.validate(content)
    return result.success, "; ".join(result.errors)


class TemplateCreator:
    """Create and register templates."""

    def __init__(
        self,
        registry: Optional[TemplateRegistry] = None,
        validator: Optional[TemplateValidator] = None,
    ) -> None:
        self.registry = registry or TemplateRegistry()
        self.validator = validator or TemplateValidator()

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
            result = self.validator.validate(content, metadata=metadata)
            if not result.success:
                raise ValueError(
                    "Template validation failed: " + "; ".join(result.errors)
                )
        if not content.strip():
            raise ValueError("Template content cannot be empty")
        return self.registry.register(metadata, content, version)
