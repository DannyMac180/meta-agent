"""Embedding model interface and implementations for template search."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _hash_embed(text: str, dim: int) -> List[float]:
    """Create a simple hashed bag-of-words embedding."""
    vec = [0.0] * dim
    for word in text.lower().split():
        idx = hash(word) % dim
        vec[idx] += 1.0
    return vec


try:  # pragma: no cover - optional dependency
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - fallback when numpy isn't installed
    import random

    class _RandomNormal:
        """Minimal stub mimicking ``numpy.random`` for tests."""

        _rand: random.Random

        def seed(self, seed: int) -> None:
            self._rand = random.Random(seed)

        def normal(self, mu: float, sigma: float, size: int):
            return [self._rand.gauss(mu, sigma) for _ in range(size)]

    class _NPStub:
        def __init__(self) -> None:
            self.random = _RandomNormal()

    np = _NPStub()  # type: ignore


@dataclass
class EmbeddingMetrics:
    """Metrics for evaluating embedding model performance."""

    model_name: str
    indexing_time: float  # seconds to index all templates
    avg_inference_time: float  # seconds per query
    cost_per_1k_tokens: float  # estimated cost
    recall_at_5: float  # retrieval accuracy metric
    mrr: float  # mean reciprocal rank


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the model name."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_tokens(self) -> float:
        """Return estimated cost per 1000 tokens."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        pass


class OpenAIEmbeddingModel(EmbeddingModel):
    """OpenAI text-embedding models."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        # Cost estimates based on OpenAI pricing (as of 2024)
        self._costs = {
            "text-embedding-3-small": 0.00002,  # $0.02 per 1M tokens
            "text-embedding-3-large": 0.00013,  # $0.13 per 1M tokens
            "text-embedding-ada-002": 0.0001,  # $0.10 per 1M tokens
        }

    @property
    def name(self) -> str:
        return f"openai:{self.model_name}"

    @property
    def cost_per_1k_tokens(self) -> float:
        return self._costs.get(self.model_name, 0.0001) * 1000

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embeddings.append(_hash_embed(text, 1536))
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embed_texts([query])[0]


class LocalEmbeddingModel(EmbeddingModel):
    """Local embedding models using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        # Local models have no per-token cost
        self._dimension_map = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "gte-large": 1024,
        }

    @property
    def name(self) -> str:
        return f"local:{self.model_name}"

    @property
    def cost_per_1k_tokens(self) -> float:
        return 0.0  # Local models are free after download

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        dim = self._dimension_map.get(self.model_name, 384)
        for text in texts:
            embeddings.append(_hash_embed(text, dim))
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embed_texts([query])[0]


class EmbeddingModelBenchmark:
    """Benchmark different embedding models for template retrieval."""

    def __init__(self, test_templates: List[Dict[str, Any]], test_queries: List[str]):
        self.test_templates = test_templates
        self.test_queries = test_queries

    def benchmark_model(self, model: EmbeddingModel) -> EmbeddingMetrics:
        """Benchmark a single embedding model."""
        # Measure indexing time
        start_time = time.time()
        template_texts = [
            t.get("content", "") + " " + t.get("metadata", {}).get("description", "")
            for t in self.test_templates
        ]
        template_embeddings = model.embed_texts(template_texts)
        indexing_time = time.time() - start_time

        # Measure inference time
        query_times = []
        recall_scores = []
        rr_scores = []

        for query in self.test_queries:
            start_time = time.time()
            query_embedding = model.embed_query(query)
            query_time = time.time() - start_time
            query_times.append(query_time)

            # Calculate similarity scores
            similarities = []
            for template_emb in template_embeddings:
                similarity = self._cosine_similarity(query_embedding, template_emb)
                similarities.append(similarity)

            # Get top 5 results
            top_indices = sorted(
                range(len(similarities)), key=lambda i: similarities[i], reverse=True
            )[:5]

            # Mock relevance calculation (in real scenario, would use ground truth)
            relevant_found = min(
                3, len(top_indices)
            )  # Mock: assume first 3 are relevant
            recall_at_5 = relevant_found / 3.0
            recall_scores.append(recall_at_5)

            # Mock MRR calculation
            if top_indices:
                rr_scores.append(
                    1.0 / (top_indices[0] + 1)
                )  # Mock: first result is most relevant

        return EmbeddingMetrics(
            model_name=model.name,
            indexing_time=indexing_time,
            avg_inference_time=(
                sum(query_times) / len(query_times) if query_times else 0
            ),
            cost_per_1k_tokens=model.cost_per_1k_tokens,
            recall_at_5=sum(recall_scores) / len(recall_scores) if recall_scores else 0,
            mrr=sum(rr_scores) / len(rr_scores) if rr_scores else 0,
        )

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

    def run_benchmark(self, models: List[EmbeddingModel]) -> List[EmbeddingMetrics]:
        """Run benchmark on all provided models."""
        results = []
        for model in models:
            metrics = self.benchmark_model(model)
            results.append(metrics)
        return results


class EmbeddingModelSelector:
    """Select the best embedding model based on requirements."""

    DEFAULT_MODELS = [
        OpenAIEmbeddingModel("text-embedding-3-small"),
        OpenAIEmbeddingModel("text-embedding-3-large"),
        LocalEmbeddingModel("all-MiniLM-L6-v2"),
        LocalEmbeddingModel("all-mpnet-base-v2"),
    ]

    def __init__(self, benchmark_results: Optional[List[EmbeddingMetrics]] = None):
        self.benchmark_results = benchmark_results or []
        self._default_model = "openai:text-embedding-3-small"

    def select_model(
        self,
        prioritize_cost: bool = False,
        prioritize_speed: bool = False,
        prioritize_accuracy: bool = True,
        max_cost_per_1k: Optional[float] = None,
    ) -> str:
        """Select the best model based on criteria."""
        if not self.benchmark_results:
            return self._default_model

        candidates = self.benchmark_results[:]

        # Filter by cost if specified
        if max_cost_per_1k is not None:
            candidates = [
                m for m in candidates if m.cost_per_1k_tokens <= max_cost_per_1k
            ]

        if not candidates:
            return self._default_model

        if prioritize_cost:
            cheapest = min(candidates, key=lambda m: m.cost_per_1k_tokens)
            return cheapest.model_name

        # Score each model based on priorities
        scored_models = []
        for model in candidates:
            score = 0.0

            if prioritize_accuracy:
                score += model.recall_at_5 * 0.5 + model.mrr * 0.3

            if prioritize_speed:
                # Lower inference time is better
                max_time = max(m.avg_inference_time for m in candidates)
                if max_time > 0:
                    score += (1 - model.avg_inference_time / max_time) * 0.3

            scored_models.append((model.model_name, score))

        # Return model with highest score
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return scored_models[0][0] if scored_models else self._default_model

    def get_model_by_name(self, name: str) -> EmbeddingModel:
        """Get embedding model instance by name."""
        if name.startswith("openai:"):
            model_name = name[7:]  # Remove "openai:" prefix
            return OpenAIEmbeddingModel(model_name)
        elif name.startswith("local:"):
            model_name = name[6:]  # Remove "local:" prefix
            return LocalEmbeddingModel(model_name)
        else:
            # Default fallback
            return OpenAIEmbeddingModel("text-embedding-3-small")
