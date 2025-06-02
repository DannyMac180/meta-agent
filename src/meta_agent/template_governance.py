"""Template signing, verification and linting utilities."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment

from .sandbox.sandbox_manager import SandboxExecutionError, SandboxManager
from .template_validator import TemplateValidator


class TemplateGovernance:
    """Manage template trust by signing and verifying content."""

    def __init__(
        self,
        cache_dir: str | Path = "template_cache",
        *,
        validator: TemplateValidator | None = None,
        sandbox_manager: SandboxManager | None = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.validator = validator or TemplateValidator()
        self._sandbox_manager = sandbox_manager
        self.signatures_path = self.cache_dir / "signatures.json"
        self._signatures: Dict[str, str] = self._load_signatures()

    # ------------------------------------------------------------------
    def _load_signatures(self) -> Dict[str, str]:
        try:
            with open(self.signatures_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):  # pragma: no cover - empty/invalid
            return {}

    def _save_signatures(self) -> None:
        with open(self.signatures_path, "w", encoding="utf-8") as f:
            json.dump(self._signatures, f, indent=2)

    # ------------------------------------------------------------------
    def sign_template(self, content: str) -> str:
        """Return sha256 signature for ``content`` and cache it."""
        signature = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self._signatures[signature] = content
        self._save_signatures()
        return signature

    def verify_template(self, content: str, signature: str) -> bool:
        """Check if ``content`` matches the cached ``signature``."""
        cached = self._signatures.get(signature)
        if not cached:
            return False
        return hashlib.sha256(content.encode("utf-8")).hexdigest() == signature

    # ------------------------------------------------------------------
    def lint_template(self, content: str) -> bool:
        """Run ``ruff`` on the provided Python code."""
        tmp = self.cache_dir / "lint_temp.py"
        tmp.write_text(content, encoding="utf-8")
        try:
            # use module invocation to avoid PATH issues
            cmd = [sys.executable, "-m", "ruff", "check", str(tmp)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        finally:
            tmp.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    def _get_sandbox_manager(self) -> SandboxManager:
        if self._sandbox_manager is None:
            self._sandbox_manager = SandboxManager()
        return self._sandbox_manager

    def run_unsigned_template(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        *,
        timeout: int = 10,
    ) -> str:
        """Render ``content`` and run the result inside a sandbox."""
        env = Environment()
        template = env.from_string(content)
        rendered = template.render(**(context or {}))
        tmp_dir = self.cache_dir / "sandbox"
        tmp_dir.mkdir(exist_ok=True)
        script_path = tmp_dir / "script.py"
        script_path.write_text(rendered, encoding="utf-8")
        manager = self._get_sandbox_manager()
        exit_code, out, err = manager.run_code_in_sandbox(
            tmp_dir, ["python", script_path.name], timeout=timeout
        )
        if exit_code != 0:
            raise SandboxExecutionError(err or "non-zero exit code")
        return out
