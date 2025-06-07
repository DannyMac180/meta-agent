from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from .sandbox.sandbox_manager import SandboxManager


class TemplateGovernance:
    """Handle template signing, verification and linting."""

    def __init__(self, secret: str, cache_path: str | Path | None = None) -> None:
        self.secret = secret.encode("utf-8")
        self.cache_path = Path(cache_path or "template_signatures.json")
        if self.cache_path.exists():
            try:
                self.cache: Dict[str, str] = json.loads(self.cache_path.read_text())
            except Exception:
                self.cache = {}
        else:
            self.cache = {}

    # --------------------------------------------------------------
    def _save_cache(self) -> None:
        self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")

    def sign(self, content: str) -> str:
        """Sign ``content`` and store signature in the cache."""
        signature = hmac.new(
            self.secret, content.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self.cache[checksum] = signature
        self._save_cache()
        return signature

    def verify(self, content: str, signature: str) -> bool:
        """Verify ``content`` against ``signature``."""
        expected = hmac.new(
            self.secret, content.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        valid = hmac.compare_digest(expected, signature)
        if valid:
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if checksum not in self.cache:
                self.cache[checksum] = signature
                self._save_cache()
        return valid

    def lint(self, content: str) -> List[str]:
        """Run Ruff linting on ``content`` and return issues."""
        proc = subprocess.run(
            ["ruff", "--quiet", "--stdin-filename", "template.py", "-"],
            input=content.encode("utf-8"),
            capture_output=True,
        )
        output = proc.stdout.decode()
        return [line.strip() for line in output.splitlines() if line.strip()]

    def run_unsigned(self, code_dir: Path, command: List[str]) -> Tuple[int, str, str]:
        """Execute ``command`` in a sandbox for unsigned templates."""
        manager = SandboxManager()
        return manager.run_code_in_sandbox(code_dir, command)
