"""Guardrail generation utilities using Pydantic models."""

from __future__ import annotations

from enum import Enum
import re
from typing import Awaitable, Callable, List

from pydantic import BaseModel, Field

try:
    from pydantic import field_validator
except ImportError:  # Pydantic v1
    from pydantic import validator as field_validator


class GuardrailAction(str, Enum):
    """Supported actions when a guardrail is triggered."""

    DENY = "deny"
    REDACT = "redact"
    FLAG = "flag"


class GuardrailRule(BaseModel):
    """Single guardrail rule based on a regex pattern."""

    name: str = Field(..., description="Unique name of the guardrail rule")
    pattern: str = Field(..., description="Regex pattern to evaluate")
    action: GuardrailAction = Field(
        default=GuardrailAction.DENY, description="Action taken on match"
    )
    description: str | None = None

    @field_validator("pattern")
    @classmethod
    def validate_regex(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as exc:  # pragma: no cover - safety check
            raise ValueError(f"Invalid regex pattern: {exc}") from exc
        return v


class GuardrailConfig(BaseModel):
    """Collection of guardrail rules."""

    rules: List[GuardrailRule] = Field(default_factory=list)

    def add_rule(self, rule: GuardrailRule) -> None:
        """Add a new rule to the configuration."""

        self.rules.append(rule)

    @classmethod
    def from_dict(cls, data: dict) -> "GuardrailConfig":
        """Create a configuration from a dictionary."""

        return cls(**data)


def build_regex_guardrails(
    config: GuardrailConfig,
) -> List[Callable[[str], Awaitable[None]]]:
    """Build async guardrail callables from a configuration."""

    guards: List[Callable[[str], Awaitable[None]]] = []
    for rule in config.rules:
        pattern = re.compile(rule.pattern)

        async def guard(value: str, *, _p=pattern, _r=rule) -> None:
            if _p.search(value):
                raise ValueError(f"Guardrail '{_r.name}' triggered")

        guards.append(guard)
    return guards
