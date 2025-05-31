"""Persistent search index for templates."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Dict, List, Optional

from .template_registry import TemplateRegistry, METADATA_FILE_NAME


class TemplateIndex:
    """Manage a simple on-disk index of templates for quick search."""

    INDEX_FILE_NAME = "index.json"

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self.registry = registry or TemplateRegistry()
        self.index_path = self.registry.templates_dir / self.INDEX_FILE_NAME
        self._index: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    def load(self) -> None:
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except (OSError, json.JSONDecodeError):  # pragma: no cover - corrupt file
                self._index = []
        else:
            self._index = []

    def save(self) -> None:
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)

    # ------------------------------------------------------------------
    def rebuild(self) -> None:
        """Rebuild the index from all registered templates."""
        self._index = []
        for entry in self.registry.list_templates():
            slug = entry["slug"]
            for version_info in entry.get("versions", []):
                version = version_info["version"]
                path = self.registry.templates_dir / version_info["path"]
                metadata_path = path.parent / METADATA_FILE_NAME
                try:
                    content = path.read_text(encoding="utf-8")
                except OSError:  # pragma: no cover - file missing
                    continue
                checksum = sha256(content.encode("utf-8")).hexdigest()
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                except (OSError, json.JSONDecodeError):
                    metadata = {}
                self._index.append(
                    {
                        "slug": slug,
                        "version": version,
                        "path": str(path.relative_to(self.registry.templates_dir)),
                        "checksum": checksum,
                        "metadata": metadata,
                        "content": content,
                    }
                )
        self.save()

    # ------------------------------------------------------------------
    def needs_rebuild(self) -> bool:
        """Return True if stored checksums differ from source files."""
        if not self.index_path.exists():
            return True
        if not self._index:
            self.load()
        for item in self._index:
            template_path = self.registry.templates_dir / item["path"]
            try:
                content = template_path.read_text(encoding="utf-8")
            except OSError:  # file removed
                return True
            checksum = sha256(content.encode("utf-8")).hexdigest()
            if checksum != item.get("checksum"):
                return True
        # check for new templates not in index
        seen = {(i["slug"], i["version"]) for i in self._index}
        for entry in self.registry.list_templates():
            slug = entry["slug"]
            for version_info in entry.get("versions", []):
                if (slug, version_info["version"]) not in seen:
                    return True
        return False

    def ensure_up_to_date(self) -> None:
        if self.needs_rebuild():
            self.rebuild()
        else:
            self.load()

    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search the index using a simple token overlap ranking."""
        if not self._index:
            self.ensure_up_to_date()
        tokens = [t.lower() for t in query.split() if t]
        results = []
        for item in self._index:
            meta = item.get("metadata", {})
            if category and meta.get("category") != category:
                continue
            if tags and not all(t in meta.get("tags", []) for t in tags):
                continue
            haystack = " ".join(
                [
                    item.get("content", ""),
                    meta.get("title", ""),
                    meta.get("description", ""),
                    meta.get("slug", ""),
                    " ".join(meta.get("tags", [])),
                ]
            ).lower()
            score = sum(1 for tok in tokens if tok in haystack)
            if score:
                results.append({**item, "score": float(score)})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]
