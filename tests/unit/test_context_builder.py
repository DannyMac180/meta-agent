"""
Unit tests for the ContextBuilder class.
"""

import pytest
from unittest.mock import MagicMock

from meta_agent.generators.context_builder import ContextBuilder


class TestContextBuilder:
    """Tests for the ContextBuilder class."""

    @pytest.fixture
    def builder(self):
        """Fixture for a ContextBuilder instance."""
        return ContextBuilder()

    @pytest.fixture
    def builder_with_examples(self):
        """Fixture for a ContextBuilder instance with example repository."""
        examples = {
            "weather_tool": {
                "description": "Gets weather information for a location",
                "implementation": "def get_weather(location): pass"
            },
            "calculator_tool": {
                "description": "Performs arithmetic calculations",
                "implementation": "def calculate(expression): pass"
            },
            "file_tool": {
                "description": "Reads and writes files",
                "implementation": "def read_file(path): pass"
            }
        }
        return ContextBuilder(examples_repository=examples)

    @pytest.fixture
    def mock_tool_spec(self):
        """Fixture for a mock tool specification."""
        spec = MagicMock()
        spec.name = "calculator"
        spec.description = "A tool for performing arithmetic calculations"
        spec.input_params = [
            {"name": "expression", "type": "string", "description": "Math expression to evaluate", "required": True},
            {"name": "precision", "type": "integer", "description": "Decimal precision", "required": False, "default": 2}
        ]
        spec.output_format = {"description": "Result of the calculation", "type": "number"}
        spec.constraints = ["No unsafe eval", "Handle division by zero"]
        return spec

    def test_initialization(self, builder):
        """Test that the ContextBuilder initializes correctly."""
        assert hasattr(builder, 'examples_repository')
        assert builder.examples_repository == {}
        assert hasattr(builder, 'logger')

    def test_initialization_with_examples(self, builder_with_examples):
        """Test initialization with examples repository."""
        assert len(builder_with_examples.examples_repository) == 3
        assert "weather_tool" in builder_with_examples.examples_repository
        assert "calculator_tool" in builder_with_examples.examples_repository
        assert "file_tool" in builder_with_examples.examples_repository

    def test_build_context(self, builder, mock_tool_spec):
        """Test building context from a tool specification."""
        context = builder.build_context(mock_tool_spec)
        
        assert "tool_purpose" in context
        assert "input_output_formats" in context
        assert "similar_examples" in context
        assert "best_practices" in context
        assert "constraints" in context
        
        assert context["tool_purpose"] == mock_tool_spec.description
        assert context["constraints"] == mock_tool_spec.constraints
        assert isinstance(context["similar_examples"], list)
        assert isinstance(context["best_practices"], list)

    def test_get_input_output_formats(self, builder, mock_tool_spec):
        """Test getting input and output formats."""
        formats = builder._get_input_output_formats(mock_tool_spec)
        
        assert "inputs" in formats
        assert "output" in formats
        assert len(formats["inputs"]) == 2
        
        # Check first input parameter
        assert formats["inputs"][0]["name"] == "expression"
        assert formats["inputs"][0]["type"] == "string"
        assert formats["inputs"][0]["required"] is True
        
        # Check second input parameter
        assert formats["inputs"][1]["name"] == "precision"
        assert formats["inputs"][1]["type"] == "integer"
        assert formats["inputs"][1]["required"] is False
        assert formats["inputs"][1]["default"] == 2
        
        # Check output format
        assert formats["output"]["description"] == "Result of the calculation"
        assert formats["output"]["type"] == "number"

    def test_get_input_output_formats_string_output(self, builder):
        """Test getting input and output formats with string output."""
        spec = MagicMock()
        spec.input_params = []
        spec.output_format = "A simple string output"
        
        formats = builder._get_input_output_formats(spec)
        
        assert formats["output"]["description"] == "A simple string output"
        assert formats["output"]["type"] == "unknown"

    def test_get_input_output_formats_no_output(self, builder):
        """Test getting input and output formats with no output specified."""
        spec = MagicMock()
        spec.input_params = []
        spec.output_format = None
        
        formats = builder._get_input_output_formats(spec)
        
        assert formats["output"]["description"] == "No output format specified"
        assert formats["output"]["type"] == "unknown"

    def test_find_similar_examples_no_repository(self, builder, mock_tool_spec):
        """Test finding similar examples with no examples repository."""
        examples = builder._find_similar_examples(mock_tool_spec)
        
        assert isinstance(examples, list)
        assert len(examples) == 0

    def test_find_similar_examples_with_matches(self, builder_with_examples, mock_tool_spec):
        """Test finding similar examples with matching examples."""
        examples = builder_with_examples._find_similar_examples(mock_tool_spec)
        
        assert isinstance(examples, list)
        assert len(examples) > 0
        # The calculator_tool should be a match
        assert any(ex["name"] == "calculator_tool" for ex in examples)

    def test_find_similar_examples_no_matches(self):
        """Test finding similar examples with no matching examples."""
        examples = {
            "weather_tool": {
                "description": "Gets weather information for a location",
                "implementation": "def get_weather(location): pass"
            },
            "file_tool": {
                "description": "Reads and writes files",
                "implementation": "def read_file(path): pass"
            }
        }
        builder = ContextBuilder(examples_repository=examples)
        
        spec = MagicMock()
        spec.name = "unique_tool"
        spec.description = "A completely unique tool with no similarities"
        
        similar = builder._find_similar_examples(spec)
        
        assert isinstance(similar, list)
        assert len(similar) == 0

    def test_get_best_practices_common(self, builder, mock_tool_spec):
        """Test getting common best practices."""
        practices = builder._get_best_practices(mock_tool_spec)
        
        assert isinstance(practices, list)
        assert len(practices) > 0
        # Check for some common practices
        assert any("descriptive variable names" in p.lower() for p in practices)
        assert any("error handling" in p.lower() for p in practices)
        assert any("type hints" in p.lower() for p in practices)

    def test_get_best_practices_api_tool(self, builder):
        """Test getting best practices for API tools."""
        spec = MagicMock()
        spec.name = "weather_api"
        spec.description = "Fetches weather data from an API endpoint"
        
        practices = builder._get_best_practices(spec)
        
        assert isinstance(practices, list)
        # Check for API-specific practices
        assert any("requests library" in p.lower() for p in practices)
        assert any("retry logic" in p.lower() for p in practices)
        assert any("rate limiting" in p.lower() for p in practices)

    def test_get_best_practices_data_tool(self, builder):
        """Test getting best practices for data processing tools."""
        spec = MagicMock()
        spec.name = "data_processor"
        spec.description = "Processes and transforms data"
        
        practices = builder._get_best_practices(spec)
        
        assert isinstance(practices, list)
        # Check for data-specific practices
        assert any("data structures" in p.lower() for p in practices)
        assert any("memory usage" in p.lower() for p in practices)
        assert any("validation" in p.lower() for p in practices)

    def test_get_best_practices_file_tool(self, builder):
        """Test getting best practices for file manipulation tools."""
        spec = MagicMock()
        spec.name = "file_reader"
        spec.description = "Reads and writes files"
        
        practices = builder._get_best_practices(spec)
        
        assert isinstance(practices, list)
        # Check for file-specific practices
        assert any("context managers" in p.lower() for p in practices)
        assert any("file operations" in p.lower() for p in practices)
        assert any("file existence" in p.lower() for p in practices)
