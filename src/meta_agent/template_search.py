from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .template_registry import TemplateRegistry, METADATA_FILE_NAME


@dataclass
class TemplateMatch:
    """Single search result with relevance score."""

    slug: str
    version: str
    score: float
    preview: str
    metadata: Dict[str, Any]


class TemplateSearchEngine:
    """Very small full-text search over registered templates."""

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self.registry = registry or TemplateRegistry()
        self._index: List[Dict[str, Any]] = []

    def build_index(self) -> None:
        """Build an in-memory index of template metadata and content."""
        self._index.clear()
        for entry in self.registry.list_templates():
            slug = entry["slug"]
            version = entry.get("current_version")
            if not version:
                continue
            content = self.registry.load_template(slug, version) or ""
            metadata_path = (
                self.registry.templates_dir
                / slug.replace(" ", "_").lower()
                / f"v{version.replace('.', '_')}"
                / METADATA_FILE_NAME
            )
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except (OSError, json.JSONDecodeError):
                metadata = {}
            self._index.append(
                {
                    "slug": slug,
                    "version": version,
                    "metadata": metadata,
                    "content": content,
                }
            )

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[TemplateMatch]:
        """Return templates matching the query and optional filters.

        ``capabilities`` is a list of available provider features, e.g.
        ``["structured_outputs", "web_search"]``. Templates requiring
        capabilities not present in this list will be excluded from results.
        """
        if not self._index:
            self.build_index()
        tokens = [t.lower() for t in query.split() if t]
        caps = set(capabilities or [])
        results: List[TemplateMatch] = []
        for item in self._index:
            meta = item.get("metadata", {})
            if category and meta.get("category") != category:
                continue
            if tags and not all(t in meta.get("tags", []) for t in tags):
                continue
            if "requires_structured_outputs" in meta and meta[
                "requires_structured_outputs"
            ] and "structured_outputs" not in caps:
                continue
            if "requires_web_search" in meta and meta[
                "requires_web_search"
            ] and "web_search" not in caps:
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
                preview = item.get("content", "")[:100].strip()
                results.append(
                    TemplateMatch(
                        slug=item["slug"],
                        version=item["version"],
                        score=float(score),
                        preview=preview,
                        metadata=meta,
                    )
                )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
