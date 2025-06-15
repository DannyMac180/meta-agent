"""Benchmark runner for embedding models on template retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .embedding_models import (
    EmbeddingModel,
    EmbeddingModelBenchmark,
    EmbeddingModelSelector,
    EmbeddingMetrics,
    LocalEmbeddingModel,
    OpenAIEmbeddingModel,
)
from .template_registry import TemplateRegistry


class TemplateBenchmarkRunner:
    """Run benchmarks specifically for template retrieval scenarios."""

    def __init__(
        self,
        registry: Optional[TemplateRegistry] = None,
        results_dir: Optional[Path] = None,
    ):
        self.registry = registry or TemplateRegistry()
        self.results_dir = results_dir or (Path.cwd() / ".benchmark_results")
        self.results_dir.mkdir(exist_ok=True)

    def create_test_queries(self) -> List[str]:
        """Create a diverse set of test queries for benchmarking."""
        return [
            # General purpose queries
            "chatbot assistant",
            "data analysis automation",
            "code review helper",
            "content generation",
            "customer support agent",
            # Specific functionality queries
            "web scraping and data extraction",
            "email automation",
            "document summarization",
            "API integration",
            "workflow automation",
            # Technical queries
            "python development",
            "machine learning model",
            "database management",
            "cloud deployment",
            "security audit",
            # Vague/ambiguous queries (testing robustness)
            "help me with work",
            "make something useful",
            "automate my tasks",
            "improve productivity",
            "solve problems",
        ]

    def get_test_templates(self) -> List[Dict[str, Any]]:
        """Get test templates from the registry."""
        templates = []

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
                / "metadata.json"
            )

            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except (OSError, json.JSONDecodeError):
                metadata = {}

            templates.append(
                {
                    "slug": slug,
                    "version": version,
                    "content": content,
                    "metadata": metadata,
                }
            )

        return templates

    def get_default_models(self) -> List[EmbeddingModel]:
        """Get the default set of models to benchmark."""
        return [
            OpenAIEmbeddingModel("text-embedding-3-small"),
            OpenAIEmbeddingModel("text-embedding-3-large"),
            OpenAIEmbeddingModel("text-embedding-ada-002"),
            LocalEmbeddingModel("all-MiniLM-L6-v2"),
            LocalEmbeddingModel("all-mpnet-base-v2"),
            LocalEmbeddingModel("gte-large"),
        ]

    def run_benchmark(
        self,
        models: Sequence[EmbeddingModel] | None = None,
        save_results: bool = True,
    ) -> List[EmbeddingMetrics]:
        """Run the complete benchmark suite."""
        models = models or self.get_default_models()
        test_templates = self.get_test_templates()
        test_queries = self.create_test_queries()

        if not test_templates:
            # Create mock templates for testing
            test_templates = self._create_mock_templates()

        # Run benchmark
        benchmark = EmbeddingModelBenchmark(test_templates, test_queries)
        results = benchmark.run_benchmark(models)

        if save_results:
            self._save_results(results)

        return results

    def _create_mock_templates(self) -> List[Dict[str, Any]]:
        """Create mock templates for testing when no real templates exist."""
        return [
            {
                "slug": "chatbot-assistant",
                "version": "1.0.0",
                "content": "You are a helpful chatbot assistant. Respond to user queries with helpful information.",
                "metadata": {
                    "title": "Chatbot Assistant",
                    "description": "General purpose conversational assistant",
                    "category": "conversation",
                    "tags": ["chatbot", "assistant", "conversation"],
                },
            },
            {
                "slug": "data-analyst",
                "version": "1.0.0",
                "content": "You are a data analyst. Help users analyze datasets and generate insights.",
                "metadata": {
                    "title": "Data Analyst",
                    "description": "Specialized agent for data analysis tasks",
                    "category": "analysis",
                    "tags": ["data", "analysis", "insights"],
                },
            },
            {
                "slug": "code-reviewer",
                "version": "1.0.0",
                "content": "You are a code reviewer. Examine code for bugs, style issues, and improvements.",
                "metadata": {
                    "title": "Code Reviewer",
                    "description": "Automated code review and suggestions",
                    "category": "development",
                    "tags": ["code", "review", "programming"],
                },
            },
            {
                "slug": "content-creator",
                "version": "1.0.0",
                "content": "You are a content creator. Generate creative and engaging content for various purposes.",
                "metadata": {
                    "title": "Content Creator",
                    "description": "Creative content generation assistant",
                    "category": "creative",
                    "tags": ["content", "creative", "writing"],
                },
            },
            {
                "slug": "api-integrator",
                "version": "1.0.0",
                "content": "You are an API integration specialist. Help users connect and work with APIs.",
                "metadata": {
                    "title": "API Integrator",
                    "description": "Specialized in API integration and automation",
                    "category": "technical",
                    "tags": ["api", "integration", "automation"],
                    "requires_web_search": True,
                },
            },
        ]

    def _save_results(self, results: List[EmbeddingMetrics]) -> None:
        """Save benchmark results to file."""
        results_file = self.results_dir / "embedding_benchmark_results.json"

        results_data = []
        for result in results:
            results_data.append(
                {
                    "model_name": result.model_name,
                    "indexing_time": result.indexing_time,
                    "avg_inference_time": result.avg_inference_time,
                    "cost_per_1k_tokens": result.cost_per_1k_tokens,
                    "recall_at_5": result.recall_at_5,
                    "mrr": result.mrr,
                }
            )

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": self._get_timestamp(),
                    "results": results_data,
                },
                f,
                indent=2,
            )

    def load_saved_results(self) -> Optional[List[EmbeddingMetrics]]:
        """Load previously saved benchmark results."""
        results_file = self.results_dir / "embedding_benchmark_results.json"

        if not results_file.exists():
            return None

        try:
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = []
            for item in data.get("results", []):
                results.append(
                    EmbeddingMetrics(
                        model_name=item["model_name"],
                        indexing_time=item["indexing_time"],
                        avg_inference_time=item["avg_inference_time"],
                        cost_per_1k_tokens=item["cost_per_1k_tokens"],
                        recall_at_5=item["recall_at_5"],
                        mrr=item["mrr"],
                    )
                )

            return results
        except (OSError, json.JSONDecodeError, KeyError):
            return None

    def print_results(self, results: List[EmbeddingMetrics]) -> None:
        """Print benchmark results in a readable format."""
        print("\n=== Embedding Model Benchmark Results ===\n")

        # Sort by recall@5 (accuracy)
        sorted_results = sorted(results, key=lambda x: x.recall_at_5, reverse=True)

        print(
            f"{'Model':<25} {'Recall@5':<10} {'MRR':<8} {'Index Time':<12} {'Query Time':<12} {'Cost/1k':<10}"
        )
        print("-" * 85)

        for result in sorted_results:
            print(
                f"{result.model_name:<25} "
                f"{result.recall_at_5:<10.3f} "
                f"{result.mrr:<8.3f} "
                f"{result.indexing_time:<12.3f} "
                f"{result.avg_inference_time:<12.4f} "
                f"${result.cost_per_1k_tokens:<9.4f}"
            )

        print()

        # Show recommendations
        selector = EmbeddingModelSelector(results)

        print("=== Recommendations ===")
        print(f"Best for accuracy: {selector.select_model(prioritize_accuracy=True)}")
        print(f"Best for speed: {selector.select_model(prioritize_speed=True)}")
        print(f"Best for cost: {selector.select_model(prioritize_cost=True)}")
        print(f"Best free option: {selector.select_model(max_cost_per_1k=0.0)}")
        print()

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().isoformat()


def run_embedding_benchmark() -> List[EmbeddingMetrics]:
    """Convenience function to run the embedding benchmark."""
    runner = TemplateBenchmarkRunner()

    print("Running embedding model benchmark...")
    print("This will test various embedding models for template retrieval quality.\n")

    results = runner.run_benchmark()
    runner.print_results(results)

    return results


if __name__ == "__main__":
    run_embedding_benchmark()
