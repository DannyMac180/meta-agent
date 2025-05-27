from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .models import BundleMetadata


class Bundle:
    """Helper for loading and introspecting generated bundles."""

    def __init__(self, bundle_dir: str | Path) -> None:
        self.bundle_dir = Path(bundle_dir)
        self._metadata: BundleMetadata | None = None

    @property
    def metadata(self) -> BundleMetadata:
        if self._metadata is None:
            self.refresh_metadata()
        assert self._metadata is not None
        return self._metadata

    def refresh_metadata(self) -> None:
        with open(self.bundle_dir / "bundle.json", encoding="utf-8") as f:
            data = json.load(f)
        self._metadata = BundleMetadata(**data)

    def list_files(self) -> List[str]:
        files: List[str] = []
        for path in self.bundle_dir.rglob("*"):
            if (
                path.is_file()
                and path.name != "bundle.json"
                and ".git" not in path.parts
            ):
                files.append(str(path.relative_to(self.bundle_dir)))
        return files

    def read_text(self, relative: str | Path) -> str:
        return (self.bundle_dir / relative).read_text(encoding="utf-8")

    @property
    def checksums(self) -> Dict[str, str]:
        return dict(self.metadata.custom.get("checksums", {}))
