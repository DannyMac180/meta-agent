import pytest
from unittest.mock import MagicMock

from meta_agent.generators.prompt_builder import PromptBuilder
from meta_agent.generators.prompt_templates import PROMPT_TEMPLATES


class TestPromptBuilder:
    """Tests for the PromptBuilder class."""

    @pytest.fixture
    def prompt_builder(self):
        """Create a PromptBuilder instance with test templates."""
        test_templates = {
            "default": "Tool: {name}\nDescription: {description}\nInputs: {input_params}\nOutput: {output_format}\nConstraints: {constraints}",
            "api_caller": "API Tool: {name}\nDescription: {description}\nInputs: {input_params}\nOutput: {output_format}\nConstraints: {constraints}",
            "data_processor": "Data Tool: {name}\nDescription: {description}\nInputs: {input_params}\nOutput: {output_format}\nConstraints: {constraints}",
            "file_manipulator": "File Tool: {name}\nDescription: {description}\nInputs: {input_params}\nOutput: {output_format}\nConstraints: {constraints}"
        }
        return PromptBuilder(prompt_templates=test_templates)
    
    @pytest.fixture
    def real_prompt_builder(self):
        """Create a PromptBuilder instance with real templates from the codebase."""
        return PromptBuilder(prompt_templates=PROMPT_TEMPLATES)

    def test_build_prompt_for_api_tool(self, prompt_builder):
        """Test building a prompt for an API tool."""
        # Arrange
        spec = MagicMock()
        spec.name = "weather_api"
        spec.description = "Fetches weather data from an API"
        spec.input_params = [
            {"name": "city", "type": "string", "description": "City name", "required": True},
            {"name": "units", "type": "string", "description": "Units (metric/imperial)", "required": False, "default": "metric"}
        ]
        spec.output_format = "JSON weather data"
        spec.constraints = ["Rate limited to 60 requests per minute"]
        
        # Act
        result = prompt_builder.build_prompt(spec)
        
        # Assert
        assert "API Tool: weather_api" in result
        assert "Fetches weather data from an API" in result
        assert "city" in result
        assert "units" in result
        assert "JSON weather data" in result
        assert "Rate limited" in result

    def test_build_prompt_for_data_processor(self, prompt_builder):
        """Test building a prompt for a data processing tool."""
        # Arrange
        spec = MagicMock()
        spec.name = "csv_parser"
        spec.description = "Parses CSV data into structured format"
        spec.input_params = [
            {"name": "csv_data", "type": "string", "description": "CSV content", "required": True},
            {"name": "has_header", "type": "boolean", "description": "Whether CSV has a header row", "required": False, "default": True}
        ]
        spec.output_format = "List of dictionaries"
        spec.constraints = ["Maximum 10MB file size"]
        
        # Act
        result = prompt_builder.build_prompt(spec)
        
        # Assert
        assert "Data Tool: csv_parser" in result
        assert "Parses CSV data" in result
        assert "csv_data" in result
        assert "has_header" in result
        assert "List of dictionaries" in result
        assert "Maximum 10MB" in result

    def test_build_prompt_for_file_manipulator(self, prompt_builder):
        """Test building a prompt for a file manipulation tool."""
        # Arrange
        spec = MagicMock()
        spec.name = "file_reader"
        spec.description = "Reads content from a file"
        spec.input_params = [
            {"name": "file_path", "type": "string", "description": "Path to the file", "required": True},
            {"name": "encoding", "type": "string", "description": "File encoding", "required": False, "default": "utf-8"}
        ]
        spec.output_format = "File content as string"
        spec.constraints = ["Only read files in the current directory"]
        
        # Act
        result = prompt_builder.build_prompt(spec)
        
        # Assert
        assert "File Tool: file_reader" in result
        assert "Reads content from a file" in result
        assert "file_path" in result
        assert "encoding" in result
        assert "File content as string" in result
        assert "Only read files" in result

    def test_build_prompt_for_default_tool(self, prompt_builder):
        """Test building a prompt for a default tool (no specific type)."""
        # Arrange
        spec = MagicMock()
        spec.name = "random_generator"
        spec.description = "Generates random numbers"
        spec.input_params = [
            {"name": "min", "type": "integer", "description": "Minimum value", "required": True},
            {"name": "max", "type": "integer", "description": "Maximum value", "required": True}
        ]
        spec.output_format = "Random integer"
        spec.constraints = ["Values must be positive"]
        
        # Act
        result = prompt_builder.build_prompt(spec)
        
        # Assert
        assert "Tool: random_generator" in result
        assert "Generates random numbers" in result
        assert "min" in result
        assert "max" in result
        assert "Random integer" in result
        assert "Values must be positive" in result

    def test_determine_tool_type_api_caller(self, prompt_builder):
        """Test determining the tool type for an API caller."""
        # Arrange
        spec = MagicMock()
        spec.name = "weather_api"
        spec.description = "Fetches weather data from an API endpoint"
        
        # Act
        tool_type = prompt_builder._determine_tool_type(spec)
        
        # Assert
        assert tool_type == "api_caller"

    def test_determine_tool_type_data_processor(self, prompt_builder):
        """Test determining the tool type for a data processor."""
        # Arrange
        spec = MagicMock()
        spec.name = "data_transformer"
        spec.description = "Transforms and processes data formats"
        
        # Act
        tool_type = prompt_builder._determine_tool_type(spec)
        
        # Assert
        assert tool_type == "data_processor"

    def test_determine_tool_type_file_manipulator(self, prompt_builder):
        """Test determining the tool type for a file manipulator."""
        # Arrange
        spec = MagicMock()
        spec.name = "file_reader"
        spec.description = "Reads and processes files"
        
        # Act
        tool_type = prompt_builder._determine_tool_type(spec)
        
        # Assert
        assert tool_type == "file_manipulator"

    def test_determine_tool_type_default(self, prompt_builder):
        """Test determining the tool type for a tool with no specific type."""
        # Arrange
        spec = MagicMock()
        spec.name = "calculator"
        spec.description = "Performs calculations"
        
        # Act
        tool_type = prompt_builder._determine_tool_type(spec)
        
        # Assert
        assert tool_type == "default"

    def test_format_input_params(self, prompt_builder):
        """Test formatting input parameters."""
        # Arrange
        input_params = [
            {"name": "param1", "type": "string", "description": "First parameter", "required": True},
            {"name": "param2", "type": "integer", "description": "Second parameter", "required": False, "default": 0},
            {"name": "param3", "type": "boolean", "description": "Third parameter", "required": False}
        ]
        
        # Act
        result = prompt_builder._format_input_params(input_params)
        
        # Assert
        assert "param1 (string): First parameter [Required]" in result
        assert "param2 (integer): Second parameter [Default: 0]" in result
        assert "param3 (boolean): Third parameter" in result
        # Ensure only param1 has the [Required] tag, none in param2 entry
        assert "[Required]" not in result.split("param2")[1].split("param3")[0]

    def test_format_input_params_empty(self, prompt_builder):
        """Test formatting empty input parameters."""
        # Arrange
        input_params = []
        
        # Act
        result = prompt_builder._format_input_params(input_params)
        
        # Assert
        assert result == "No input parameters"

    def test_format_constraints(self, prompt_builder):
        """Test formatting constraints."""
        # Arrange
        constraints = [
            "Must be secure",
            "Must handle errors gracefully",
            "Must be efficient"
        ]
        
        # Act
        result = prompt_builder._format_constraints(constraints)
        
        # Assert
        assert "- Must be secure" in result
        assert "- Must handle errors gracefully" in result
        assert "- Must be efficient" in result

    def test_format_constraints_empty(self, prompt_builder):
        """Test formatting empty constraints."""
        # Arrange
        constraints = []
        
        # Act
        result = prompt_builder._format_constraints(constraints)
        
        # Assert
        assert result == "No specific constraints"

    def test_build_prompt_with_missing_fields(self, prompt_builder):
        """Test building a prompt with missing fields."""
        # Arrange
        spec = MagicMock()
        # No name or description
        spec.input_params = []
        spec.output_format = "Some output"
        spec.constraints = []
        
        # Act
        result = prompt_builder.build_prompt(spec)
        
        # Assert
        assert "Tool: Unnamed Tool" in result
        assert "Description: No description provided" in result
        assert "No input parameters" in result
        assert "Some output" in result
        assert "No specific constraints" in result

    def test_build_prompt_with_real_templates(self, real_prompt_builder):
        """Test building a prompt with the real templates from the codebase."""
        # Arrange
        spec = MagicMock()
        spec.name = "weather_api"
        spec.description = "Fetches weather data from an API"
        spec.input_params = [
            {"name": "city", "type": "string", "description": "City name", "required": True},
            {"name": "units", "type": "string", "description": "Units (metric/imperial)", "required": False, "default": "metric"}
        ]
        spec.output_format = "JSON weather data"
        spec.constraints = ["Rate limited to 60 requests per minute"]
        
        # Act
        result = real_prompt_builder.build_prompt(spec)
        
        # Assert
        assert "You are an expert Python developer" in result
        assert "weather_api" in result
        assert "Fetches weather data from an API" in result
        assert "city" in result
        assert "units" in result
        assert "JSON weather data" in result
        assert "Rate limited" in result
        assert "requests library" in result  # Should use the API caller template
