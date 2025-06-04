"""Data models for template metadata and categorisation."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

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


class IOContract(BaseModel):
    """Input/output contract for a template."""

    input: str = Field(..., description="Expected input description")
    output: str = Field(..., description="Expected output description")


class TemplateMetadata(BaseModel):
    """Metadata describing a reusable agent template."""

    slug: str = Field(..., description="Unique identifier for the template")
    title: str = Field(..., description="Human friendly name")
    description: str = Field(..., description="Short summary of the template")
    intended_use: str = Field(..., description="Primary scenario the template targets")
    io_contract: IOContract = Field(..., description="Expected inputs and outputs")
    tools: List[str] = Field(default_factory=list, description="Tools referenced")
    guardrails: List[str] = Field(
        default_factory=list, description="Guardrails applied"
    )
    model_pref: str = Field(..., description="Preferred model or provider")
    category: TemplateCategory = Field(..., description="Primary template category")
    subcategory: Optional[str] = Field(
        default=None, description="Optional secondary grouping"
    )
    complexity: TemplateComplexity = Field(
        default=TemplateComplexity.BASIC,
        description="Overall complexity level",
    )
    created_by: str = Field(..., description="Author or source of the template")
    semver: str = Field(..., description="Semantic version of the template")
    last_test_passed: Optional[str] = Field(
        default=None,
        description="ISO timestamp when tests last passed",
    )
    tags: List[str] = Field(default_factory=list, description="Additional labels")
    eval_score: Optional[float] = Field(
        default=None, description="Evaluation score from automated tests"
    )
    cost_estimate: Optional[float] = Field(
        default=None, description="Estimated cost per run in dollars"
    )
    tokens_per_run: Optional[int] = Field(
        default=None, description="Approximate token usage per run"
    )

    requires_structured_outputs: bool = Field(
        default=False,
        description="Template requires model structured outputs",
    )
    requires_web_search: bool = Field(
        default=False,
        description="Template requires web search capability",
    )

    class Config:
        use_enum_values = False
