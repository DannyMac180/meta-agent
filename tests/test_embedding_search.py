"""Tests for embedding-based template search."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from meta_agent.embedding_search import EmbeddingMatch, EmbeddingTemplateSearch
from meta_agent.template_registry import TemplateRegistry


class TestEmbeddingMatch:
    """Test EmbeddingMatch data class."""
    
    def test_init(self):
        match = EmbeddingMatch(
            slug="test-template",
            version="1.0.0",
            similarity=0.85,
            preview="Test template content...",
            metadata={"title": "Test Template"},
        )
        
        assert match.slug == "test-template"
        assert match.version == "1.0.0"
        assert match.similarity == 0.85
        assert match.preview == "Test template content..."
        assert match.metadata == {"title": "Test Template"}


class TestEmbeddingTemplateSearch:
    """Test embedding-based template search."""
    
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
            {"slug": "code-reviewer", "current_version": "2.0.0"},
        ]
        registry.load_template.side_effect = lambda slug, version: {
            ("chatbot-assistant", "1.0.0"): "You are a helpful chatbot assistant.",
            ("data-analyst", "1.0.0"): "You are a data analyst specialized in insights.",
            ("code-reviewer", "2.0.0"): "You are a code reviewer checking for bugs.",
        }.get((slug, version), "")
        
        return registry
    
    @pytest.fixture
    def setup_metadata_files(self, temp_dir):
        """Create metadata files for test templates."""
        # Create directory structure and metadata files
        templates_data = [
            ("chatbot-assistant", "1.0.0", {
                "title": "Chatbot Assistant",
                "description": "Helpful conversational assistant",
                "category": "conversation",
                "tags": ["chatbot", "assistant"],
            }),
            ("data-analyst", "1.0.0", {
                "title": "Data Analyst",
                "description": "Data analysis and insights specialist",
                "category": "analysis",
                "tags": ["data", "analysis"],
            }),
            ("code-reviewer", "2.0.0", {
                "title": "Code Reviewer",
                "description": "Automated code review and suggestions",
                "category": "development",
                "tags": ["code", "review"],
                "requires_structured_outputs": True,
            }),
        ]
        
        for slug, version, metadata in templates_data:
            template_dir = temp_dir / slug.replace(" ", "_").lower() / f"v{version.replace('.', '_')}"
            template_dir.mkdir(parents=True, exist_ok=True)
            
            metadata_file = template_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)
    
    def test_init_default(self):
        search = EmbeddingTemplateSearch()
        assert search.registry is not None
        assert search.model_name == "openai:text-embedding-3-small"  # Default
        assert not search._is_indexed
    
    def test_init_custom_model(self, mock_registry):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            model_name="local:all-MiniLM-L6-v2"
        )
        assert search.registry == mock_registry
        assert search.model_name == "local:all-MiniLM-L6-v2"
    
    def test_build_index(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        search.build_index()
        
        assert search._is_indexed
        assert len(search._template_data) == 3
        assert len(search._embeddings) == 3
        
        # Check template data structure
        template = search._template_data[0]
        assert "slug" in template
        assert "version" in template
        assert "content" in template
        assert "metadata" in template
        assert "searchable_text" in template
    
    def test_build_index_with_cache(self, temp_dir, mock_registry, setup_metadata_files):
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=cache_dir
        )
        
        # Build index first time
        search.build_index()
        assert search._is_indexed
        
        # Reset and build again (should load from cache)
        search._is_indexed = False
        search._template_data.clear()
        search._embeddings.clear()
        
        search.build_index()
        assert search._is_indexed
        assert len(search._template_data) == 3
    
    def test_search_basic(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        results = search.search("chatbot assistant")
        
        assert isinstance(results, list)
        assert len(results) <= 5  # Default limit
        
        for result in results:
            assert isinstance(result, EmbeddingMatch)
            assert result.similarity >= 0.1  # Default threshold
    
    def test_search_with_filters(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        # Search with category filter
        results = search.search("assistant", category="conversation")
        assert all(
            result.metadata.get("category") == "conversation"
            for result in results
        )
        
        # Search with tags filter
        results = search.search("code", tags=["review"])
        assert all(
            "review" in result.metadata.get("tags", [])
            for result in results
        )
    
    def test_search_capability_filtering(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        # Search without structured_outputs capability
        # Should exclude code-reviewer which requires it
        results = search.search("code review", capabilities=[])
        code_reviewer_results = [r for r in results if r.slug == "code-reviewer"]
        assert len(code_reviewer_results) == 0
        
        # Search with structured_outputs capability
        # Should include code-reviewer
        results = search.search("code review", capabilities=["structured_outputs"])
        code_reviewer_results = [r for r in results if r.slug == "code-reviewer"]
        assert len(code_reviewer_results) > 0
    
    def test_search_similarity_threshold(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        # High threshold should return fewer results
        results_high = search.search("test", similarity_threshold=0.9)
        results_low = search.search("test", similarity_threshold=0.1)
        
        assert len(results_high) <= len(results_low)
    
    def test_search_limit(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        results = search.search("assistant", limit=2)
        assert len(results) <= 2
    
    def test_create_searchable_text(self, temp_dir, mock_registry):
        search = EmbeddingTemplateSearch(registry=mock_registry, cache_dir=temp_dir)
        
        content = "You are a helpful assistant."
        metadata = {
            "title": "Assistant",
            "description": "Helpful AI assistant",
            "tags": ["helpful", "assistant"],
            "slug": "test-assistant",
        }
        
        searchable = search._create_searchable_text(content, metadata)
        
        assert "You are a helpful assistant." in searchable
        assert "Assistant" in searchable
        assert "Helpful AI assistant" in searchable
        assert "helpful" in searchable
        assert "assistant" in searchable
        assert "test-assistant" in searchable
    
    def test_check_capability_requirements(self, temp_dir, mock_registry):
        search = EmbeddingTemplateSearch(registry=mock_registry, cache_dir=temp_dir)
        
        # Template requiring structured outputs
        metadata = {"requires_structured_outputs": True}
        assert search._check_capability_requirements(metadata, set())  # Should filter out
        assert not search._check_capability_requirements(metadata, {"structured_outputs"})  # Should keep
        
        # Template requiring web search
        metadata = {"requires_web_search": True}
        assert search._check_capability_requirements(metadata, set())  # Should filter out
        assert not search._check_capability_requirements(metadata, {"web_search"})  # Should keep
        
        # Template with web search tool
        metadata = {"tools": ["web_search", "calculator"]}
        assert search._check_capability_requirements(metadata, set())  # Should filter out
        assert not search._check_capability_requirements(metadata, {"web_search"})  # Should keep
    
    def test_cosine_similarity(self, temp_dir, mock_registry):
        search = EmbeddingTemplateSearch(registry=mock_registry, cache_dir=temp_dir)
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert search._cosine_similarity(vec1, vec2) == pytest.approx(1.0)
        
        # Test orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert search._cosine_similarity(vec1, vec2) == pytest.approx(0.0)
        
        # Test different length vectors
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert search._cosine_similarity(vec1, vec2) == 0.0
    
    def test_clear_cache(self, temp_dir, mock_registry, setup_metadata_files):
        cache_dir = temp_dir / "cache"
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=cache_dir
        )
        
        # Build index to create cache
        search.build_index()
        assert search._is_indexed
        
        cache_file = cache_dir / f"embeddings_{search.model_name.replace(':', '_')}.pkl"
        assert cache_file.exists()
        
        # Clear cache
        search.clear_cache()
        assert not cache_file.exists()
        assert not search._is_indexed
    
    def test_get_index_stats(self, temp_dir, mock_registry, setup_metadata_files):
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        # Before indexing
        stats = search.get_index_stats()
        assert stats["indexed"] is False
        
        # After indexing
        search.build_index()
        stats = search.get_index_stats()
        
        assert stats["indexed"] is True
        assert stats["template_count"] == 3
        assert stats["model_name"] == search.model_name
        assert stats["embedding_dimension"] > 0
        assert "cache_dir" in stats
    
    def test_load_metadata_missing_file(self, temp_dir, mock_registry):
        search = EmbeddingTemplateSearch(registry=mock_registry, cache_dir=temp_dir)
        
        # Try to load metadata for non-existent file
        metadata = search._load_metadata("nonexistent", "1.0.0")
        assert metadata == {}
    
    def test_search_empty_index(self, temp_dir, mock_registry):
        # Mock registry with no templates
        mock_registry.list_templates.return_value = []
        
        search = EmbeddingTemplateSearch(
            registry=mock_registry,
            cache_dir=temp_dir / "cache"
        )
        
        results = search.search("test query")
        assert results == []
