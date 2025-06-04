from __future__ import annotations

# ruff: noqa: E402

"""Simple governance helpers for user-provided templates."""

import subprocess
from typing import Optional

try:
    from ruff.__main__ import find_ruff_bin
except Exception:  # pragma: no cover - ruff very unlikely missing

    def find_ruff_bin() -> str:  # type: ignore
        return "ruff"


class TemplateGovernance:
    """Validate template code using Ruff."""

    def __init__(self, ruff_path: Optional[str] = None) -> None:
        self.ruff_path = ruff_path or find_ruff_bin()

    def lint_template(self, content: str) -> bool:
        """Return ``True`` if ``content`` passes Ruff linting."""
        try:
            result = subprocess.run(
                [self.ruff_path, "check", "-", "--quiet", "--no-cache"],
                input=content,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False
