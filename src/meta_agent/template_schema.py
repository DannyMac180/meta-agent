"""Data models for template metadata and categorisation."""

from __future__ import annotations

from enum import Enum
from typing import List

try:  # pragma: no cover - pydantic v1 fallback
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover
    from pydantic import BaseModel, Field


class TemplateCategory(str, Enum):
    """High level grouping for templates."""

    CONVERSATION = "conversation"
    REASONING = "reasoning"
    CREATIVE = "creative"
    DATA_PROCESSING = "data_processing"
    INTEGRATION = "integration"


class TemplateComplexity(str, Enum):
    """Rough measure of how involved a template is."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TemplateMetadata(BaseModel):
    """Metadata describing a reusable agent template."""

    slug: str = Field(..., description="Unique identifier for the template")
    title: str = Field(..., description="Human friendly name")
    description: str = Field(..., description="Short summary of the template")
    category: TemplateCategory = Field(..., description="Primary template category")
    subcategory: str | None = Field(
        default=None, description="Optional secondary grouping"
    )
    complexity: TemplateComplexity = Field(
        default=TemplateComplexity.BASIC,
        description="Overall complexity level",
    )
    tags: List[str] = Field(default_factory=list, description="Additional labels")

    class Config:
        use_enum_values = False
