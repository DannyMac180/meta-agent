from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Mapping, Sequence, Optional

from .models import BundleMetadata
from .__about__ import __version__


class BundleGenerator:
    """Generate the on-disk bundle structure for a generated agent."""

    def __init__(self, bundle_dir: str | Path) -> None:
        self.bundle_dir = Path(bundle_dir)

    def _write_file(self, relative: str | Path, content: str) -> str:
        path = self.bundle_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def generate(
        self,
        agent_code: str,
        tests: Optional[Mapping[str, str]] = None,
        requirements: Optional[Sequence[str]] = None,
        readme: str = "",
        guardrails_manifest: str = "",
        templates: Optional[Mapping[str, str]] = None,
    ) -> BundleMetadata:
        """Generate bundle files and return metadata."""

        checksums: dict[str, str] = {}

        checksums["agent.py"] = self._write_file("agent.py", agent_code)

        tests = tests or {}
        if not tests:
            (self.bundle_dir / "tests").mkdir(parents=True, exist_ok=True)
        for name, content in tests.items():
            checksums[f"tests/{name}"] = self._write_file(Path("tests") / name, content)

        req_content = "\n".join(requirements or [])
        checksums["requirements.txt"] = self._write_file("requirements.txt", req_content)

        checksums["README.md"] = self._write_file("README.md", readme)

        (self.bundle_dir / "traces").mkdir(parents=True, exist_ok=True)

        (self.bundle_dir / "guardrails").mkdir(parents=True, exist_ok=True)
        if guardrails_manifest:
            checksums["guardrails/manifest.json"] = self._write_file(
                "guardrails/manifest.json", guardrails_manifest
            )

        for rel, content in (templates or {}).items():
            checksums[str(rel)] = self._write_file(rel, content)

        metadata = BundleMetadata(meta_agent_version=__version__)
        metadata.custom["checksums"] = checksums
        with open(self.bundle_dir / "bundle.json", "w", encoding="utf-8") as f:
            json.dump(json.loads(metadata.model_dump_json()), f, indent=2)
        return metadata
