"""Template validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time

from jinja2 import Environment, TemplateSyntaxError, meta

from .models.validation_result import ValidationResult


@dataclass
class TemplateTestCase:
    """Simple structure for validating template output."""

    context: Dict[str, Any]
    expected_output: str | None = None


class TemplateValidator:
    """Validate templates via syntax and optional test cases."""

    def __init__(self, env: Optional[Environment] = None) -> None:
        self.env = env or Environment()

    def validate(
        self,
        content: str,
        test_cases: Optional[List[TemplateTestCase]] = None,
        *,
        max_render_seconds: float = 1.0,
    ) -> ValidationResult:
        """Validate ``content`` and optionally run ``test_cases``."""
        errors: List[str] = []
        try:
            parsed = self.env.parse(content)
        except TemplateSyntaxError as exc:  # pragma: no cover - jinja2 message
            errors.append(f"syntax error: {exc}")
            return ValidationResult(success=False, errors=errors, coverage=0.0)

        undeclared = meta.find_undeclared_variables(parsed)
        if test_cases:
            template = self.env.from_string(content)
            for case in test_cases:
                missing = undeclared - case.context.keys()
                if missing:
                    errors.append(f"missing variables {sorted(missing)}")
                    continue
                start = time.perf_counter()
                output = template.render(**case.context)
                duration = time.perf_counter() - start
                if duration > max_render_seconds:
                    errors.append("template rendering too slow")
                if (
                    case.expected_output is not None
                    and output.strip() != case.expected_output.strip()
                ):
                    errors.append("output mismatch")
        success = not errors
        return ValidationResult(success=success, errors=errors, coverage=0.0)
