"""Tests for embedding models and selection."""

import pytest

from meta_agent.embedding_models import (
    EmbeddingModelBenchmark,
    EmbeddingModelSelector,
    EmbeddingMetrics,
    LocalEmbeddingModel,
    OpenAIEmbeddingModel,
)


class TestOpenAIEmbeddingModel:
    """Test OpenAI embedding model implementation."""
    
    def test_init_default(self):
        model = OpenAIEmbeddingModel()
        assert model.model_name == "text-embedding-3-small"
        assert model.name == "openai:text-embedding-3-small"
    
    def test_init_custom_model(self):
        model = OpenAIEmbeddingModel("text-embedding-3-large")
        assert model.model_name == "text-embedding-3-large"
        assert model.name == "openai:text-embedding-3-large"
    
    def test_cost_per_1k_tokens(self):
        model = OpenAIEmbeddingModel("text-embedding-3-small")
        assert model.cost_per_1k_tokens > 0
        
        large_model = OpenAIEmbeddingModel("text-embedding-3-large")
        assert large_model.cost_per_1k_tokens > model.cost_per_1k_tokens
    
    def test_embed_texts(self):
        model = OpenAIEmbeddingModel()
        texts = ["hello world", "test embedding"]
        embeddings = model.embed_texts(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536  # Default dimension
        assert len(embeddings[1]) == 1536
        assert isinstance(embeddings[0][0], float)
    
    def test_embed_query(self):
        model = OpenAIEmbeddingModel()
        embedding = model.embed_query("test query")
        
        assert len(embedding) == 1536
        assert isinstance(embedding[0], float)
    
    def test_consistent_embeddings(self):
        """Test that the same text produces the same embedding."""
        model = OpenAIEmbeddingModel()
        text = "consistent test"
        
        embedding1 = model.embed_query(text)
        embedding2 = model.embed_query(text)
        
        assert embedding1 == embedding2


class TestLocalEmbeddingModel:
    """Test local embedding model implementation."""
    
    def test_init_default(self):
        model = LocalEmbeddingModel()
        assert model.model_name == "all-MiniLM-L6-v2"
        assert model.name == "local:all-MiniLM-L6-v2"
    
    def test_init_custom_model(self):
        model = LocalEmbeddingModel("all-mpnet-base-v2")
        assert model.model_name == "all-mpnet-base-v2"
        assert model.name == "local:all-mpnet-base-v2"
    
    def test_cost_per_1k_tokens(self):
        model = LocalEmbeddingModel()
        assert model.cost_per_1k_tokens == 0.0  # Local models are free
    
    def test_embed_texts_dimensions(self):
        # Test different model dimensions
        mini_model = LocalEmbeddingModel("all-MiniLM-L6-v2")
        embeddings = mini_model.embed_texts(["test"])
        assert len(embeddings[0]) == 384
        
        mpnet_model = LocalEmbeddingModel("all-mpnet-base-v2")
        embeddings = mpnet_model.embed_texts(["test"])
        assert len(embeddings[0]) == 768
    
    def test_embed_query(self):
        model = LocalEmbeddingModel()
        embedding = model.embed_query("test query")
        
        assert len(embedding) == 384  # MiniLM dimension
        assert isinstance(embedding[0], float)


class TestEmbeddingModelBenchmark:
    """Test embedding model benchmarking."""
    
    @pytest.fixture
    def test_templates(self):
        return [
            {
                "content": "You are a helpful chatbot assistant",
                "metadata": {"description": "Conversational AI assistant"},
            },
            {
                "content": "You are a data analyst",
                "metadata": {"description": "Data analysis specialist"},
            },
            {
                "content": "You are a code reviewer",
                "metadata": {"description": "Code review automation"},
            },
        ]
    
    @pytest.fixture
    def test_queries(self):
        return ["chatbot helper", "data analysis", "code review"]
    
    def test_init(self, test_templates, test_queries):
        benchmark = EmbeddingModelBenchmark(test_templates, test_queries)
        assert benchmark.test_templates == test_templates
        assert benchmark.test_queries == test_queries
    
    def test_cosine_similarity(self, test_templates, test_queries):
        benchmark = EmbeddingModelBenchmark(test_templates, test_queries)
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert benchmark._cosine_similarity(vec1, vec2) == pytest.approx(1.0)
        
        # Test orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert benchmark._cosine_similarity(vec1, vec2) == pytest.approx(0.0)
        
        # Test opposite vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        assert benchmark._cosine_similarity(vec1, vec2) == pytest.approx(-1.0)
    
    def test_benchmark_model(self, test_templates, test_queries):
        benchmark = EmbeddingModelBenchmark(test_templates, test_queries)
        model = LocalEmbeddingModel()
        
        metrics = benchmark.benchmark_model(model)
        
        assert isinstance(metrics, EmbeddingMetrics)
        assert metrics.model_name == "local:all-MiniLM-L6-v2"
        assert metrics.indexing_time >= 0
        assert metrics.avg_inference_time >= 0
        assert metrics.cost_per_1k_tokens == 0.0
        assert 0 <= metrics.recall_at_5 <= 1
        assert 0 <= metrics.mrr <= 1
    
    def test_run_benchmark(self, test_templates, test_queries):
        benchmark = EmbeddingModelBenchmark(test_templates, test_queries)
        models = [
            LocalEmbeddingModel("all-MiniLM-L6-v2"),
            OpenAIEmbeddingModel("text-embedding-3-small"),
        ]
        
        results = benchmark.run_benchmark(models)
        
        assert len(results) == 2
        assert all(isinstance(r, EmbeddingMetrics) for r in results)
        assert results[0].model_name == "local:all-MiniLM-L6-v2"
        assert results[1].model_name == "openai:text-embedding-3-small"


class TestEmbeddingModelSelector:
    """Test embedding model selection logic."""
    
    @pytest.fixture
    def sample_metrics(self):
        return [
            EmbeddingMetrics(
                model_name="openai:text-embedding-3-small",
                indexing_time=1.0,
                avg_inference_time=0.1,
                cost_per_1k_tokens=0.02,
                recall_at_5=0.8,
                mrr=0.7,
            ),
            EmbeddingMetrics(
                model_name="openai:text-embedding-3-large",
                indexing_time=2.0,
                avg_inference_time=0.2,
                cost_per_1k_tokens=0.13,
                recall_at_5=0.9,
                mrr=0.85,
            ),
            EmbeddingMetrics(
                model_name="local:all-MiniLM-L6-v2",
                indexing_time=0.5,
                avg_inference_time=0.05,
                cost_per_1k_tokens=0.0,
                recall_at_5=0.6,
                mrr=0.5,
            ),
        ]
    
    def test_init_empty(self):
        selector = EmbeddingModelSelector()
        assert selector.benchmark_results == []
        assert selector._default_model == "openai:text-embedding-3-small"
    
    def test_init_with_metrics(self, sample_metrics):
        selector = EmbeddingModelSelector(sample_metrics)
        assert selector.benchmark_results == sample_metrics
    
    def test_select_model_default(self):
        selector = EmbeddingModelSelector()
        model = selector.select_model()
        assert model == "openai:text-embedding-3-small"
    
    def test_select_model_prioritize_accuracy(self, sample_metrics):
        selector = EmbeddingModelSelector(sample_metrics)
        model = selector.select_model(prioritize_accuracy=True)
        assert model == "openai:text-embedding-3-large"  # Highest recall+mrr
    
    def test_select_model_prioritize_cost(self, sample_metrics):
        selector = EmbeddingModelSelector(sample_metrics)
        model = selector.select_model(prioritize_cost=True)
        assert model == "local:all-MiniLM-L6-v2"  # Free model
    
    def test_select_model_prioritize_speed(self, sample_metrics):
        selector = EmbeddingModelSelector(sample_metrics)
        model = selector.select_model(prioritize_speed=True)
        # Should prefer the local model with fastest inference time
        assert model in ["local:all-MiniLM-L6-v2", "openai:text-embedding-3-small"]
    
    def test_select_model_max_cost_filter(self, sample_metrics):
        selector = EmbeddingModelSelector(sample_metrics)
        model = selector.select_model(max_cost_per_1k=0.05)
        # Should exclude the expensive large model
        assert model != "openai:text-embedding-3-large"
    
    def test_select_model_max_cost_zero(self, sample_metrics):
        selector = EmbeddingModelSelector(sample_metrics)
        model = selector.select_model(max_cost_per_1k=0.0)
        assert model == "local:all-MiniLM-L6-v2"  # Only free option
    
    def test_get_model_by_name_openai(self):
        selector = EmbeddingModelSelector()
        model = selector.get_model_by_name("openai:text-embedding-3-small")
        assert isinstance(model, OpenAIEmbeddingModel)
        assert model.model_name == "text-embedding-3-small"
    
    def test_get_model_by_name_local(self):
        selector = EmbeddingModelSelector()
        model = selector.get_model_by_name("local:all-MiniLM-L6-v2")
        assert isinstance(model, LocalEmbeddingModel)
        assert model.model_name == "all-MiniLM-L6-v2"
    
    def test_get_model_by_name_fallback(self):
        selector = EmbeddingModelSelector()
        model = selector.get_model_by_name("unknown:model")
        assert isinstance(model, OpenAIEmbeddingModel)
        assert model.model_name == "text-embedding-3-small"


class TestEmbeddingMetrics:
    """Test embedding metrics data class."""
    
    def test_init(self):
        metrics = EmbeddingMetrics(
            model_name="test-model",
            indexing_time=1.0,
            avg_inference_time=0.1,
            cost_per_1k_tokens=0.02,
            recall_at_5=0.8,
            mrr=0.7,
        )
        
        assert metrics.model_name == "test-model"
        assert metrics.indexing_time == 1.0
        assert metrics.avg_inference_time == 0.1
        assert metrics.cost_per_1k_tokens == 0.02
        assert metrics.recall_at_5 == 0.8
        assert metrics.mrr == 0.7
