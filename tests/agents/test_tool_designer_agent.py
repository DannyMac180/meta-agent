import pytest
from unittest.mock import patch, MagicMock
import jinja2
from meta_agent.agents.tool_designer_agent import ToolDesignerAgent, CodeGenerationError

# --- Test Fixtures ---

VALID_YAML_SPEC = """
name: calculate_sum
purpose: Calculates the sum of two integers.
input_parameters:
  - name: a
    type: integer
    description: The first integer.
    required: true
  - name: b
    type: integer
    description: The second integer.
    required: true
output_format: integer
"""

VALID_DICT_SPEC = {
    "name": "multiply_numbers",
    "purpose": "Multiplies two numbers.",
    "input_parameters": [
        {"name": "x", "type": "float", "description": "First number", "required": True},
        {
            "name": "y",
            "type": "float",
            "description": "Second number",
            "required": False,
            "default": 1.0,
        },
    ],
    "output_format": "float",
}

INVALID_YAML_SPEC = """
name: incomplete_tool
# Missing purpose and output_format
input_parameters:
  - name: data
    type: string
"""

# --- Test Cases ---


def test_design_tool_success_yaml():
    """Test successful tool design from a YAML string spec."""
    agent = ToolDesignerAgent()
    generated_code = agent.design_tool(VALID_YAML_SPEC)
    assert "def calculate_sum(" in generated_code
    assert "a: int," in generated_code
    assert "b: int" in generated_code
    assert "-> int:" in generated_code
    assert "Calculates the sum of two integers." in generated_code
    assert 'logger.info(f"Running tool: calculate_sum")' in generated_code
    assert "return result" in generated_code


def test_design_tool_success_dict():
    """Test successful tool design from a dictionary spec."""
    agent = ToolDesignerAgent()
    generated_code = agent.design_tool(VALID_DICT_SPEC)
    # The current template outputs '= None' for optional parameters
    assert "def multiply_numbers(" in generated_code
    assert "x: float," in generated_code
    assert "y: float = None" in generated_code
    assert "-> float:" in generated_code
    assert "Multiplies two numbers." in generated_code
    assert 'logger.info(f"Running tool: multiply_numbers")' in generated_code
    assert "return result" in generated_code


def test_design_tool_invalid_spec():
    """Test that designing with an invalid spec raises ValueError."""
    agent = ToolDesignerAgent()
    with pytest.raises(ValueError) as excinfo:
        agent.design_tool(INVALID_YAML_SPEC)
    assert "Invalid tool specification:" in str(excinfo.value)
    # Check for specific missing fields mentioned in the error
    assert "purpose" in str(excinfo.value)
    assert "output_format" in str(excinfo.value)

    # Invalid name identifier test
    # Already tested missing fields; next test invalid identifier


def test_design_tool_invalid_name_identifier():
    agent = ToolDesignerAgent()
    bad_spec = {
        "name": "123invalid",
        "purpose": "Invalid name tool",
        "input_parameters": [],
        "output_format": "int",
    }
    with pytest.raises(ValueError) as excinfo:
        agent.design_tool(bad_spec)
    assert "Tool name must be a valid Python identifier" in str(excinfo.value)


def test_design_tool_duplicate_param_names():
    agent = ToolDesignerAgent()
    bad_spec = {
        "name": "duplicate_param_tool",
        "purpose": "Test duplicate params",
        "input_parameters": [
            {"name": "a", "type": "int", "description": "first", "required": True},
            {"name": "a", "type": "int", "description": "second", "required": True},
        ],
        "output_format": "int",
    }
    with pytest.raises(ValueError) as excinfo:
        agent.design_tool(bad_spec)
    assert 'Duplicate parameter name "a" found' in str(excinfo.value)


# Async run tests
@pytest.mark.asyncio
async def test_run_success_dict_async():
    agent = ToolDesignerAgent()
    result = await agent.run(VALID_DICT_SPEC)
    assert result["status"] == "success"
    output = result["output"]
    assert isinstance(output, dict)
    assert "code" in output and "tests" in output and "docs" in output


@pytest.mark.asyncio
async def test_run_missing_template():
    # Using non-existent template should produce error status
    agent = ToolDesignerAgent(template_name="nonexistent.j2")
    result = await agent.run(VALID_DICT_SPEC)
    assert result["status"] == "error"
    assert "Tool template 'nonexistent.j2' not found" in result["error"]


# Test for template rendering error
def test_design_tool_generation_error():
    agent = ToolDesignerAgent()

    # Create a mock template that raises an exception when render is called
    mock_template = MagicMock()
    mock_template.render.side_effect = Exception("Mocked rendering failure")

    # Patch the get_template method to return our mock
    with patch.object(agent.jinja_env, "get_template", return_value=mock_template):
        with pytest.raises(CodeGenerationError) as excinfo:
            agent.design_tool(VALID_YAML_SPEC)

        assert "Failed to render template: Mocked rendering failure" in str(excinfo.value)

@pytest.mark.asyncio
def test_run_with_research(monkeypatch):
    calls = []

    class DummyResearch:
        def research(self, name: str, purpose: str):
            calls.append((name, purpose))
            return ["info"]

    agent = ToolDesignerAgent(research_manager=DummyResearch(), enable_research=True)
    result = await agent.run(VALID_DICT_SPEC)
    assert result['status'] == 'success'
    assert calls == [(VALID_DICT_SPEC['name'], VALID_DICT_SPEC['purpose'])]
