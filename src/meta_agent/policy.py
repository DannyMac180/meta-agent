"""Policy check utilities for guardrails.

Provides an async ``PolicyChecker`` that evaluates text against
configured rules and custom plugins.
"""

from __future__ import annotations

import re
from typing import Awaitable, Callable, List, Optional

from meta_agent.generators.guardrail_generator import (
    GuardrailAction,
    GuardrailConfig,
    GuardrailRule,
)


class PolicyChecker:
    """Evaluate text against guardrail policy rules."""

    def __init__(self, config: Optional[GuardrailConfig] = None) -> None:
        self.checks: List[Callable[[str], Awaitable[str]]] = []
        if config is not None:
            self.add_from_config(config)

    def add_from_config(self, config: GuardrailConfig) -> None:
        """Add checks from a :class:`GuardrailConfig`."""

        for rule in config.rules:
            pattern = re.compile(rule.pattern)

            def _make_check(
                p: re.Pattern[str], r: GuardrailRule
            ) -> Callable[[str], Awaitable[str]]:
                if r.action is GuardrailAction.REDACT:

                    async def _check(text: str) -> str:
                        return p.sub("[REDACTED]", text)

                else:  # DENY or FLAG -> raise error on match

                    async def _check(text: str) -> str:
                        if p.search(text):
                            raise ValueError(f"Policy violation: {r.name}")
                        return text

                return _check

            self.checks.append(_make_check(pattern, rule))

    def add_check(self, check: Callable[[str], Awaitable[str]]) -> None:
        """Register a custom check plugin."""

        self.checks.append(check)

    async def run(self, text: str) -> str:
        """Run all checks sequentially and return possibly modified text."""

        for check in self.checks:
            text = await check(text)
        return text


async def build_policy_guardrails(
    config: GuardrailConfig,
) -> List[Callable[[str], Awaitable[None]]]:
    """Helper to create router-compatible guardrails from a config."""

    checker = PolicyChecker(config)

    async def guard(text: str) -> None:
        await checker.run(text)

    return [guard]
