"""Tools for sharing and collaborating on templates."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from .template_registry import TemplateRegistry, METADATA_FILE_NAME
from .template_creator import TemplateCreator
from .template_schema import (
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
)


class TemplateSharingManager:
    """Manage template export/import, ratings and simple merges."""

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self.registry = registry or TemplateRegistry()
        self.ratings_path = self.registry.templates_dir / "ratings.json"
        if not self.ratings_path.exists():
            self.ratings_path.write_text("{}", encoding="utf-8")

    # ------------------------------------------------------------------
    def _load_ratings(self) -> Dict[str, List[int]]:
        try:
            with open(self.ratings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_ratings(self, data: Dict[str, List[int]]) -> None:
        with open(self.ratings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    def export_template(self, slug: str, *, version: str = "latest") -> Dict[str, Any]:
        """Return a JSON-serialisable representation of a template."""
        content = self.registry.load_template(slug, version)
        if content is None:
            raise ValueError(f"Template {slug}@{version} not found")
        slug_sanitized = slug.replace(" ", "_").lower()
        if version == "latest":
            manifest = self.registry._load_manifest()
            version = manifest.get(slug_sanitized, {}).get("current_version", "0.1.0")
        meta_path = (
            self.registry.templates_dir
            / slug_sanitized
            / f"v{version.replace('.', '_')}"
            / METADATA_FILE_NAME
        )
        metadata: Dict[str, Any] = {}
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
        return {"metadata": metadata, "content": content}

    def import_template(self, data: Dict[str, Any]) -> Optional[str]:
        """Import a template from an exported dictionary."""
        meta = data.get("metadata") or {}
        content = data.get("content", "")
        if not meta:
            raise ValueError("Missing metadata")
        metadata = TemplateMetadata(
            slug=meta["slug"],
            title=meta.get("title", meta["slug"]),
            description=meta.get("description", ""),
            intended_use=meta.get("intended_use", ""),
            io_contract=meta.get("io_contract", {"input": "", "output": ""}),
            tools=meta.get("tools", []),
            guardrails=meta.get("guardrails", []),
            model_pref=meta.get("model_pref", ""),
            category=(
                TemplateCategory(meta.get("category"))
                if meta.get("category")
                else TemplateCategory.CONVERSATION
            ),
            subcategory=meta.get("subcategory"),
            complexity=(
                TemplateComplexity(meta.get("complexity"))
                if meta.get("complexity")
                else TemplateComplexity.BASIC
            ),
            created_by=meta.get("created_by", "unknown"),
            semver=meta.get("semver", "0.0.0"),
            last_test_passed=meta.get("last_test_passed"),
            tags=meta.get("tags", []),
            eval_score=meta.get("eval_score"),
            cost_estimate=meta.get("cost_estimate"),
            tokens_per_run=meta.get("tokens_per_run"),
        )
        version = meta.get("version", "0.1.0")
        creator = TemplateCreator(self.registry)
        return creator.create(metadata, content, version=version, validate=False)

    # ------------------------------------------------------------------
    def add_rating(self, slug: str, rating: int) -> None:
        """Store a user rating (1-5) for a template."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        ratings = self._load_ratings()
        key = slug.replace(" ", "_").lower()
        ratings.setdefault(key, []).append(rating)
        self._save_ratings(ratings)

    def get_rating(self, slug: str) -> Tuple[int, float]:
        """Return rating count and average for ``slug``."""
        ratings = self._load_ratings()
        key = slug.replace(" ", "_").lower()
        values = ratings.get(key, [])
        if not values:
            return 0, 0.0
        total = sum(values)
        return len(values), total / len(values)

    def showcase(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Return top rated templates as ``[(slug, average)]``."""
        ratings = self._load_ratings()
        avgs = [(slug, sum(vals) / len(vals)) for slug, vals in ratings.items() if vals]
        avgs.sort(key=lambda t: t[1], reverse=True)
        return avgs[:limit]

    # ------------------------------------------------------------------
    def merge_versions(self, slug: str, ours: str, theirs: str) -> str:
        """Naively merge two versions preferring ``theirs`` on conflict."""
        ours_content = self.registry.load_template(slug, ours) or ""
        theirs_content = self.registry.load_template(slug, theirs) or ""
        ours_lines = ours_content.splitlines()
        theirs_lines = theirs_content.splitlines()
        merged: List[str] = []
        max_len = max(len(ours_lines), len(theirs_lines))
        for i in range(max_len):
            if i < len(theirs_lines):
                merged.append(theirs_lines[i])
            elif i < len(ours_lines):
                merged.append(ours_lines[i])
        return "\n".join(merged)
