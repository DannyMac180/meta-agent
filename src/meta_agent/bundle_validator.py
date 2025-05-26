from __future__ import annotations

import hashlib
import json
import os
import py_compile
import subprocess
from pathlib import Path
from typing import List

from .models import BundleMetadata
from .models.validation_result import ValidationResult


class BundleValidator:
    """Validate the contents of a generated agent bundle."""

    def __init__(self, bundle_dir: str | Path) -> None:
        self.bundle_dir = Path(bundle_dir)

    def _load_metadata(self) -> BundleMetadata:
        with open(self.bundle_dir / "bundle.json", encoding="utf-8") as f:
            data = json.load(f)
        return BundleMetadata(**data)

    def _validate_checksums(self, metadata: BundleMetadata, errors: List[str]) -> None:
        checksums = metadata.custom.get("checksums", {})
        for rel, expected in checksums.items():
            path = self.bundle_dir / rel
            if not path.exists():
                errors.append(f"missing file {rel}")
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                errors.append(f"checksum mismatch for {rel}")

    def _validate_requirements(self, errors: List[str]) -> None:
        req_path = self.bundle_dir / "requirements.txt"
        if not req_path.exists():
            errors.append("requirements.txt missing")
            return
        for line in req_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" not in line:
                errors.append(f"unpinned requirement: {line}")

    def _validate_agent(self, errors: List[str]) -> None:
        try:
            py_compile.compile(str(self.bundle_dir / "agent.py"), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"agent.py failed to compile: {exc.msg}")

    def _run_tests(self, errors: List[str]) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.bundle_dir)
        result = subprocess.run(
            ["pytest", "tests", "-c", "/dev/null", "-x"],
            cwd=self.bundle_dir,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            errors.append("tests failed")

    def validate(self) -> ValidationResult:
        errors: List[str] = []
        try:
            metadata = self._load_metadata()
        except Exception as exc:  # pragma: no cover - invalid json path rare
            errors.append(f"invalid bundle metadata: {exc}")
            return ValidationResult(success=False, errors=errors, coverage=0.0)

        self._validate_checksums(metadata, errors)
        self._validate_requirements(errors)
        self._validate_agent(errors)

        if not errors:
            self._run_tests(errors)

        success = not errors
        return ValidationResult(success=success, errors=errors, coverage=0.0)
