"""Tests for embedding benchmark runner."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from meta_agent.embedding_benchmark import TemplateBenchmarkRunner
from meta_agent.embedding_models import EmbeddingMetrics, LocalEmbeddingModel
from meta_agent.template_registry import TemplateRegistry


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory fixture for module-level tests."""
    yield tmp_path


class TestTemplateBenchmarkRunner:
    """Test template benchmark runner."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def mock_registry(self, temp_dir):
        registry = Mock(spec=TemplateRegistry)
        registry.templates_dir = temp_dir
        registry.list_templates.return_value = [
            {"slug": "chatbot-assistant", "current_version": "1.0.0"},
            {"slug": "data-analyst", "current_version": "1.0.0"},
        ]
        registry.load_template.side_effect = lambda slug, version: {
            ("chatbot-assistant", "1.0.0"): "You are a helpful chatbot assistant.",
            ("data-analyst", "1.0.0"): "You are a data analyst.",
        }.get((slug, version), "")

        return registry

    @pytest.fixture
    def setup_metadata_files(self, temp_dir):
        """Create metadata files for test templates."""
        templates_data = [
            (
                "chatbot-assistant",
                "1.0.0",
                {
                    "title": "Chatbot Assistant",
                    "description": "Helpful conversational assistant",
                    "category": "conversation",
                    "tags": ["chatbot", "assistant"],
                },
            ),
            (
                "data-analyst",
                "1.0.0",
                {
                    "title": "Data Analyst",
                    "description": "Data analysis specialist",
                    "category": "analysis",
                    "tags": ["data", "analysis"],
                },
            ),
        ]

        for slug, version, metadata in templates_data:
            template_dir = (
                temp_dir
                / slug.replace(" ", "_").lower()
                / f"v{version.replace('.', '_')}"
            )
            template_dir.mkdir(parents=True, exist_ok=True)

            metadata_file = template_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)

    def test_init_default(self):
        runner = TemplateBenchmarkRunner()
        assert runner.registry is not None
        assert runner.results_dir == Path.cwd() / ".benchmark_results"

    def test_init_custom(self, temp_dir, mock_registry):
        results_dir = temp_dir / "results"
        runner = TemplateBenchmarkRunner(
            registry=mock_registry, results_dir=results_dir
        )

        assert runner.registry == mock_registry
        assert runner.results_dir == results_dir
        assert results_dir.exists()  # Should be created

    def test_create_test_queries(self):
        runner = TemplateBenchmarkRunner()
        queries = runner.create_test_queries()

        assert isinstance(queries, list)
        assert len(queries) > 0

        # Check for different types of queries
        query_text = " ".join(queries).lower()
        assert "chatbot" in query_text
        assert "data analysis" in query_text
        assert "automation" in query_text
        assert "help me" in query_text  # Vague query

    def test_get_test_templates(self, temp_dir, mock_registry, setup_metadata_files):
        runner = TemplateBenchmarkRunner(registry=mock_registry)
        templates = runner.get_test_templates()

        assert len(templates) == 2

        template = templates[0]
        assert "slug" in template
        assert "version" in template
        assert "content" in template
        assert "metadata" in template

    def test_get_default_models(self):
        runner = TemplateBenchmarkRunner()
        models = runner.get_default_models()

        assert len(models) == 6  # 3 OpenAI + 3 local models

        model_names = [model.name for model in models]
        assert "openai:text-embedding-3-small" in model_names
        assert "openai:text-embedding-3-large" in model_names
        assert "local:all-MiniLM-L6-v2" in model_names

    def test_create_mock_templates(self):
        runner = TemplateBenchmarkRunner()
        templates = runner._create_mock_templates()

        assert len(templates) == 5

        template = templates[0]
        assert "slug" in template
        assert "version" in template
        assert "content" in template
        assert "metadata" in template

        # Check metadata structure
        metadata = template["metadata"]
        assert "title" in metadata
        assert "description" in metadata
        assert "category" in metadata
        assert "tags" in metadata

    def test_run_benchmark_with_templates(
        self, temp_dir, mock_registry, setup_metadata_files
    ):
        runner = TemplateBenchmarkRunner(
            registry=mock_registry, results_dir=temp_dir / "results"
        )

        # Use only one model for faster testing
        models = [LocalEmbeddingModel("all-MiniLM-L6-v2")]

        results = runner.run_benchmark(models=models, save_results=False)

        assert len(results) == 1
        assert isinstance(results[0], EmbeddingMetrics)
        assert results[0].model_name == "local:all-MiniLM-L6-v2"

    def test_run_benchmark_with_mock_templates(self, temp_dir):
        # No real templates, should use mock templates
        mock_registry = Mock(spec=TemplateRegistry)
        mock_registry.list_templates.return_value = []

        runner = TemplateBenchmarkRunner(
            registry=mock_registry, results_dir=temp_dir / "results"
        )

        models = [LocalEmbeddingModel("all-MiniLM-L6-v2")]
        results = runner.run_benchmark(models=models, save_results=False)

        assert len(results) == 1
        assert isinstance(results[0], EmbeddingMetrics)

    def test_save_and_load_results(self, temp_dir):
        runner = TemplateBenchmarkRunner(results_dir=temp_dir)

        # Create sample metrics
        metrics = [
            EmbeddingMetrics(
                model_name="test-model",
                indexing_time=1.0,
                avg_inference_time=0.1,
                cost_per_1k_tokens=0.02,
                recall_at_5=0.8,
                mrr=0.7,
            )
        ]

        # Save results
        runner._save_results(metrics)

        # Check file was created
        results_file = temp_dir / "embedding_benchmark_results.json"
        assert results_file.exists()

        # Load and verify results
        loaded_metrics = runner.load_saved_results()
        assert loaded_metrics is not None
        assert len(loaded_metrics) == 1

        loaded = loaded_metrics[0]
        assert loaded.model_name == "test-model"
        assert loaded.indexing_time == 1.0
        assert loaded.recall_at_5 == 0.8

    def test_load_saved_results_no_file(self, temp_dir):
        runner = TemplateBenchmarkRunner(results_dir=temp_dir)
        results = runner.load_saved_results()
        assert results is None

    def test_load_saved_results_corrupted_file(self, temp_dir):
        runner = TemplateBenchmarkRunner(results_dir=temp_dir)

        # Create corrupted file
        results_file = temp_dir / "embedding_benchmark_results.json"
        with open(results_file, "w") as f:
            f.write("invalid json {")

        results = runner.load_saved_results()
        assert results is None

    def test_print_results(self, temp_dir, capsys):
        runner = TemplateBenchmarkRunner(results_dir=temp_dir)

        metrics = [
            EmbeddingMetrics(
                model_name="model-a",
                indexing_time=1.0,
                avg_inference_time=0.1,
                cost_per_1k_tokens=0.02,
                recall_at_5=0.8,
                mrr=0.7,
            ),
            EmbeddingMetrics(
                model_name="model-b",
                indexing_time=2.0,
                avg_inference_time=0.2,
                cost_per_1k_tokens=0.0,
                recall_at_5=0.6,
                mrr=0.5,
            ),
        ]

        runner.print_results(metrics)

        captured = capsys.readouterr()
        assert "Embedding Model Benchmark Results" in captured.out
        assert "model-a" in captured.out
        assert "model-b" in captured.out
        assert "Recommendations" in captured.out

    def test_get_timestamp(self):
        runner = TemplateBenchmarkRunner()
        timestamp = runner._get_timestamp()

        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format
        assert len(timestamp) > 10  # Should be a reasonable length


def test_run_embedding_benchmark_function(temp_dir):
    """Test the convenience function."""
    from meta_agent.embedding_benchmark import run_embedding_benchmark

    # Mock the runner to avoid long benchmark
    with patch(
        "meta_agent.embedding_benchmark.TemplateBenchmarkRunner"
    ) as mock_runner_class:
        mock_runner = Mock()
        mock_metrics = [
            EmbeddingMetrics(
                model_name="test-model",
                indexing_time=1.0,
                avg_inference_time=0.1,
                cost_per_1k_tokens=0.02,
                recall_at_5=0.8,
                mrr=0.7,
            )
        ]
        mock_runner.run_benchmark.return_value = mock_metrics
        mock_runner_class.return_value = mock_runner

        results = run_embedding_benchmark()

        assert results == mock_metrics
        mock_runner.run_benchmark.assert_called_once()
        mock_runner.print_results.assert_called_once_with(mock_metrics)
