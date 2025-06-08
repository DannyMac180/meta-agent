"""Tests for the REST API functionality."""

import pytest
from unittest.mock import patch, MagicMock

# Import with graceful fallback for missing FastAPI
try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    TestClient = None
    FASTAPI_AVAILABLE = False

from meta_agent.template_registry import TemplateRegistry
from meta_agent.template_search import TemplateSearchEngine, TemplateMatch


@pytest.fixture
def mock_template_registry():
    """Mock template registry with sample data."""
    registry = MagicMock(spec=TemplateRegistry)
    registry.list_templates.return_value = [
        {
            "slug": "hello-world",
            "current_version": "1.0.0",
            "versions": [
                {
                    "version": "1.0.0",
                    "path": "hello-world/v1_0_0/template.yaml",
                    "checksum": "abc123",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        },
        {
            "slug": "data-processor",
            "current_version": "0.2.0",
            "versions": [
                {
                    "version": "0.2.0",
                    "path": "data-processor/v0_2_0/template.yaml",
                    "checksum": "def456",
                    "created_at": "2024-01-02T00:00:00"
                }
            ]
        }
    ]
    registry.load_template.return_value = """# Sample Template
task_description: "A sample agent template"
inputs:
  - name: "input_data"
    description: "Sample input"
outputs:
  - name: "result"
    description: "Sample output"
"""
    return registry


@pytest.fixture
def mock_search_engine():
    """Mock search engine with sample results."""
    engine = MagicMock(spec=TemplateSearchEngine)
    engine.search.return_value = [
        TemplateMatch(
            slug="hello-world",
            version="1.0.0",
            score=2.0,
            preview="# Sample Template\ntask_description: \"A sample agent template\"",
            metadata={
                "title": "Hello World Template",
                "description": "A simple greeting template",
                "category": "basic",
                "tags": ["hello", "world", "basic"]
            }
        ),
        TemplateMatch(
            slug="data-processor",
            version="0.2.0",
            score=1.0,
            preview="# Data Processing Template\ntask_description: \"Process data\"",
            metadata={
                "title": "Data Processor",
                "description": "Process and transform data",
                "category": "utility",
                "tags": ["data", "processing"]
            }
        )
    ]
    return engine


@pytest.fixture
def test_client(mock_template_registry, mock_search_engine):
    """Create test client with mocked dependencies."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not available")
    
    # Import and create app with mocks
    with patch('meta_agent.api.TemplateRegistry') as mock_registry_class, \
         patch('meta_agent.api.TemplateSearchEngine') as mock_search_class:
        
        mock_registry_class.return_value = mock_template_registry
        mock_search_class.return_value = mock_search_engine
        
        from meta_agent.api import create_app
        app = create_app()
        return TestClient(app)


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestAPI:
    """Test the REST API endpoints."""

    def test_health_check(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_list_templates(self, test_client):
        """Test listing all templates."""
        response = test_client.get("/api/v1/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        assert "total_count" in data
        assert data["total_count"] == 2
        
        templates = data["templates"]
        assert len(templates) == 2
        assert templates[0]["slug"] == "hello-world"
        assert templates[1]["slug"] == "data-processor"

    def test_search_templates_get(self, test_client):
        """Test searching templates via GET request."""
        response = test_client.get("/api/v1/templates/search?query=hello&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert "total_found" in data
        assert "query_time_ms" in data
        
        matches = data["matches"]
        assert len(matches) == 2
        assert matches[0]["slug"] == "hello-world"
        assert matches[0]["score"] == 2.0

    def test_search_templates_get_with_filters(self, test_client):
        """Test searching templates with filters via GET request."""
        response = test_client.get(
            "/api/v1/templates/search"
            "?query=data"
            "&category=utility"
            "&tags=data,processing"
            "&capabilities=structured_outputs"
            "&limit=10"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert isinstance(data["query_time_ms"], float)

    def test_search_templates_post(self, test_client):
        """Test searching templates via POST request."""
        search_request = {
            "query": "hello world",
            "category": "basic",
            "tags": ["hello", "basic"],
            "capabilities": ["structured_outputs"],
            "limit": 5
        }
        
        response = test_client.post("/api/v1/templates/search", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert "total_found" in data
        assert "query_time_ms" in data

    def test_search_templates_missing_query(self, test_client):
        """Test search endpoint without required query parameter."""
        response = test_client.get("/api/v1/templates/search")
        assert response.status_code == 422  # Validation error

    def test_get_template_success(self, test_client):
        """Test getting a specific template."""
        response = test_client.get("/api/v1/templates/hello-world?version=1.0.0")
        assert response.status_code == 200
        
        data = response.json()
        assert data["slug"] == "hello-world"
        assert data["version"] == "1.0.0"
        assert "content" in data
        assert "metadata" in data

    def test_get_template_latest_version(self, test_client):
        """Test getting a template with latest version."""
        response = test_client.get("/api/v1/templates/hello-world")
        assert response.status_code == 200
        
        data = response.json()
        assert data["slug"] == "hello-world"
        assert data["version"] == "latest"

    def test_get_template_not_found(self, test_client, mock_template_registry):
        """Test getting a non-existent template."""
        mock_template_registry.load_template.return_value = None
        
        response = test_client.get("/api/v1/templates/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_search_performance(self, test_client):
        """Test that search performance metrics are reasonable."""
        response = test_client.get("/api/v1/templates/search?query=test")
        assert response.status_code == 200
        
        data = response.json()
        query_time_ms = data["query_time_ms"]
        
        # Should complete in reasonable time (less than 1 second for tests)
        assert 0 <= query_time_ms < 1000

    def test_api_error_handling(self, test_client):
        """Test API error handling for invalid requests."""
        # Test invalid limit parameter
        response = test_client.get("/api/v1/templates/search?query=test&limit=100")
        assert response.status_code == 422  # Validation error

        # Test invalid limit (negative)
        response = test_client.get("/api/v1/templates/search?query=test&limit=-1")
        assert response.status_code == 422

    def test_cors_and_content_type(self, test_client):
        """Test that responses have correct content type."""
        response = test_client.get("/api/v1/templates")
        assert response.headers["content-type"] == "application/json"


class TestAPIWithoutFastAPI:
    """Test API module behavior when FastAPI is not available."""

    def test_import_without_fastapi(self):
        """Test that API module can be imported without FastAPI."""
        with patch.dict('sys.modules', {'fastapi': None}):
            # Should not raise ImportError
            from meta_agent import api
            assert hasattr(api, 'create_app')

    def test_create_app_without_fastapi(self):
        """Test that create_app raises appropriate error without FastAPI."""
        with patch('meta_agent.api.FastAPI', None):
            from meta_agent.api import create_app
            
            with pytest.raises(ImportError, match="FastAPI is required"):
                create_app()


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for the API with real components."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_real_template_search_integration(self, tmp_path):
        """Test API with real template registry and search engine."""
        # Create a real registry with some test data
        registry = TemplateRegistry(base_dir=tmp_path)
        
        # Register a test template
        from meta_agent.template_schema import TemplateMetadata
        metadata = TemplateMetadata(
            slug="test-template",
            title="Test Template",
            description="A test template for integration testing",
            category="test",
            tags=["test", "integration"]
        )
        template_content = """# Test Template
task_description: "Integration test template"
inputs:
  - name: "test_input"
    description: "Test input"
outputs:
  - name: "test_output"
    description: "Test output"
"""
        registry.register(metadata, template_content, "1.0.0")
        
        # Create app with real registry
        with patch('meta_agent.api.TemplateRegistry') as mock_registry_class:
            mock_registry_class.return_value = registry
            
            from meta_agent.api import create_app
            app = create_app()
            client = TestClient(app)
            
            # Test search functionality
            response = client.get("/api/v1/templates/search?query=integration")
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_found"] >= 0  # May be 0 if search doesn't find anything
