"""Template validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time
import re

from jinja2 import Environment, TemplateSyntaxError, meta

from .dependency_manager import DependencyManager
from .template_schema import TemplateMetadata

from .models.validation_result import ValidationResult


@dataclass
class TemplateTestCase:
    """Simple structure for validating template output."""

    context: Dict[str, Any]
    expected_output: str | None = None


class TemplateValidator:
    """Validate templates via syntax and optional test cases."""

    def __init__(
        self,
        env: Optional[Environment] = None,
        dep_manager: Optional[DependencyManager] = None,
    ) -> None:
        self.env = env or Environment()
        self.dep_manager = dep_manager or DependencyManager()

    _SHELL_PATTERNS = [
        (r"os\.system\(", "os.system usage"),
        (r"subprocess\.", "subprocess usage"),
        (r"`.+?`", "shell backticks"),
        (r"shell=True", "shell=True"),
    ]

    _DISALLOWED_LICENSES = {"GPL", "AGPL"}

    def _scan_shell_commands(self, content: str) -> List[str]:
        issues: List[str] = []
        for pattern, desc in self._SHELL_PATTERNS:
            if re.search(pattern, content):
                issues.append(f"shell command detected: {desc}")
        return issues

    def _scan_licenses(self, metadata: TemplateMetadata) -> List[str]:
        issues: List[str] = []
        if not metadata.tools:
            return issues
        try:
            _, licenses, _ = self.dep_manager.resolve(metadata.tools)
        except Exception as exc:  # pragma: no cover - dependency errors rare
            issues.append(f"dependency resolution failed: {exc}")
            return issues
        for pkg, lic in licenses.items():
            if any(tag in lic for tag in self._DISALLOWED_LICENSES):
                issues.append(f"non-permissive license for {pkg}: {lic}")
        return issues

    def validate(
        self,
        content: str,
        test_cases: Optional[List[TemplateTestCase]] = None,
        *,
        max_render_seconds: float = 1.0,
        metadata: Optional[TemplateMetadata] = None,
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

        # security scans -------------------------------------------------
        errors.extend(self._scan_shell_commands(content))
        if metadata is not None:
            errors.extend(self._scan_licenses(metadata))

        success = not errors
        return ValidationResult(success=success, errors=errors, coverage=0.0)
