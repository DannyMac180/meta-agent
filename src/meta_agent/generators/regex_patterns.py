"""Default regex patterns for content filtering."""

from __future__ import annotations

import re
from typing import Dict, Iterable

from .guardrail_generator import GuardrailConfig, GuardrailRule

# Predefined regex patterns for common sensitive data
DEFAULT_REGEX_PATTERNS: Dict[str, str] = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "password": r"(?i)password",
}


def build_default_regex_config(
    additional_patterns: Dict[str, str] | None = None,
) -> GuardrailConfig:
    """Return a :class:`GuardrailConfig` with default regex rules.

    Args:
        additional_patterns: Optional extra name->pattern mappings to include.

    Returns:
        GuardrailConfig: Config populated with regex guardrail rules.
    """
    patterns: Dict[str, str] = {**DEFAULT_REGEX_PATTERNS}
    if additional_patterns:
        patterns.update(additional_patterns)

    config = GuardrailConfig()
    for name, pattern in patterns.items():
        # validate pattern by compiling; GuardrailRule will also validate
        re.compile(pattern)
        config.add_rule(GuardrailRule(name=name, pattern=pattern))
    return config
