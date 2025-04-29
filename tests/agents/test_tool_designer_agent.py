import pytest
from meta_agent.agents.tool_designer_agent import ToolDesignerAgent, CodeGenerationError

# --- Test Fixtures ---

VALID_YAML_SPEC = '''
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
'''

VALID_DICT_SPEC = {
    "name": "multiply_numbers",
    "purpose": "Multiplies two numbers.",
    "input_parameters": [
        {"name": "x", "type": "float", "description": "First number", "required": True},
        {"name": "y", "type": "float", "description": "Second number", "required": False, "default": 1.0}
    ],
    "output_format": "float"
}

INVALID_YAML_SPEC = '''
name: incomplete_tool
# Missing purpose and output_format
input_parameters:
  - name: data
    type: string
'''

# --- Test Cases ---

def test_design_tool_success_yaml():
    """Test successful tool design from a YAML string spec."""
    agent = ToolDesignerAgent()
    generated_code = agent.design_tool(VALID_YAML_SPEC)
    assert "def calculate_sum(a: int, b: int) -> int:" in generated_code
    assert "Calculates the sum of two integers." in generated_code
    assert "logger.info(f\"Running tool 'calculate_sum'" in generated_code
    assert "return result" in generated_code

def test_design_tool_success_dict():
    """Test successful tool design from a dictionary spec."""
    agent = ToolDesignerAgent()
    generated_code = agent.design_tool(VALID_DICT_SPEC)
    # The current template outputs '= None' for optional parameters
    assert "def multiply_numbers(x: float, y: float = None) -> float:" in generated_code
    assert "Multiplies two numbers." in generated_code
    assert "logger.info(f\"Running tool 'multiply_numbers'" in generated_code
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

# Potential future test: Mock CodeGenerator to raise CodeGenerationError
# def test_design_tool_generation_error():
#     agent = ToolDesignerAgent()
#     with patch('meta_agent.generators.tool_code_generator.ToolCodeGenerator.generate') as mock_generate:
#         mock_generate.side_effect = CodeGenerationError("Mocked generation failure")
#         with pytest.raises(CodeGenerationError) as excinfo:
#             agent.design_tool(VALID_YAML_SPEC)
#         assert "Mocked generation failure" in str(excinfo.value)
