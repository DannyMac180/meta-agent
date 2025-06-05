"""Embedding-based template search engine."""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .embedding_models import EmbeddingModelSelector
from .template_registry import TemplateRegistry, METADATA_FILE_NAME


@dataclass
class EmbeddingMatch:
    """Single embedding search result with similarity score."""

    slug: str
    version: str
    similarity: float
    preview: str
    metadata: Dict[str, Any]


class EmbeddingTemplateSearch:
    """Embedding-based template search engine."""

    def __init__(
        self,
        registry: Optional[TemplateRegistry] = None,
        model_name: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.registry = registry or TemplateRegistry()
        self.cache_dir = cache_dir or (Path.cwd() / ".template_embeddings")
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize model selector and get model
        selector = EmbeddingModelSelector()
        self.model_name = model_name or selector.select_model()
        self.model = selector.get_model_by_name(self.model_name)

        self._template_data: List[Dict[str, Any]] = []
        self._embeddings: List[List[float]] = []
        self._is_indexed = False

    def build_index(self, force_rebuild: bool = False) -> None:
        """Build embedding index for all templates."""
        cache_file = (
            self.cache_dir / f"embeddings_{self.model_name.replace(':', '_')}.pkl"
        )

        # Check if we can load from cache
        if not force_rebuild and cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)
                    self._template_data = cached_data["template_data"]
                    self._embeddings = cached_data["embeddings"]
                    self._is_indexed = True
                    return
            except (EOFError, pickle.PickleError, KeyError):
                # Cache is corrupted, rebuild
                pass

        # Build fresh index
        self._template_data.clear()
        self._embeddings.clear()

        # Collect all template data
        texts_to_embed = []
        for entry in self.registry.list_templates():
            slug = entry["slug"]
            version = entry.get("current_version")
            if not version:
                continue

            content = self.registry.load_template(slug, version) or ""
            metadata = self._load_metadata(slug, version)

            # Create searchable text combining content and metadata
            searchable_text = self._create_searchable_text(content, metadata)
            texts_to_embed.append(searchable_text)

            self._template_data.append(
                {
                    "slug": slug,
                    "version": version,
                    "content": content,
                    "metadata": metadata,
                    "searchable_text": searchable_text,
                }
            )

        # Generate embeddings
        if texts_to_embed:
            self._embeddings = self.model.embed_texts(texts_to_embed)

        # Cache the results
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(
                    {
                        "template_data": self._template_data,
                        "embeddings": self._embeddings,
                    },
                    f,
                )
        except (OSError, pickle.PickleError):
            # Cache write failed, but continue with in-memory index
            pass

        self._is_indexed = True

    def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        limit: int = 5,
        similarity_threshold: float = 0.1,
    ) -> List[EmbeddingMatch]:
        """Search templates using embedding similarity."""
        if not self._is_indexed:
            self.build_index()

        if not self._template_data or not self._embeddings:
            return []

        # Generate query embedding
        query_embedding = self.model.embed_query(query)

        # Calculate similarities and filter
        results: List[EmbeddingMatch] = []
        caps = set(capabilities or [])

        for i, template in enumerate(self._template_data):
            metadata = template["metadata"]

            # Apply filters
            if category and metadata.get("category") != category:
                continue
            if tags and not all(t in metadata.get("tags", []) for t in tags):
                continue
            if self._check_capability_requirements(metadata, caps):
                continue

            # Calculate similarity
            similarity = self._cosine_similarity(query_embedding, self._embeddings[i])

            if similarity >= similarity_threshold:
                preview = template["content"][:100].strip()
                results.append(
                    EmbeddingMatch(
                        slug=template["slug"],
                        version=template["version"],
                        similarity=similarity,
                        preview=preview,
                        metadata=metadata,
                    )
                )

        # Sort by similarity and return top results
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:limit]

    def _load_metadata(self, slug: str, version: str) -> Dict[str, Any]:
        """Load metadata for a template."""
        metadata_path = (
            self.registry.templates_dir
            / slug.replace(" ", "_").lower()
            / f"v{version.replace('.', '_')}"
            / METADATA_FILE_NAME
        )
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _create_searchable_text(self, content: str, metadata: Dict[str, Any]) -> str:
        """Create combined searchable text from content and metadata."""
        parts = [content]

        # Add metadata fields that are useful for search
        for field in ["title", "description", "intended_use", "slug"]:
            if field in metadata:
                parts.append(str(metadata[field]))

        # Add tags
        if "tags" in metadata:
            parts.extend(metadata["tags"])

        return " ".join(filter(None, parts))

    def _check_capability_requirements(
        self, metadata: Dict[str, Any], available_caps: set
    ) -> bool:
        """Check if template requirements match available capabilities.

        Returns True if template should be filtered out (requirements not met).
        """
        required_caps = []

        if metadata.get("requires_structured_outputs"):
            required_caps.append("structured_outputs")
        if metadata.get("requires_web_search"):
            required_caps.append("web_search")

        # Add other capability checks as needed
        for tool in metadata.get("tools", []):
            if tool in ["web_search", "browser"]:
                required_caps.append("web_search")

        return any(cap not in available_caps for cap in required_caps)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        cache_file = (
            self.cache_dir / f"embeddings_{self.model_name.replace(':', '_')}.pkl"
        )
        if cache_file.exists():
            cache_file.unlink()
        self._is_indexed = False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        if not self._is_indexed:
            return {"indexed": False}

        return {
            "indexed": True,
            "template_count": len(self._template_data),
            "model_name": self.model_name,
            "embedding_dimension": len(self._embeddings[0]) if self._embeddings else 0,
            "cache_dir": str(self.cache_dir),
        }
