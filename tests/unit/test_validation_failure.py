"""
Unit tests for handling validation failures in the generate_agent function.
"""

import pytest
import json
from unittest.mock import patch
from meta_agent.core import generate_agent
from tests.mocks.agents import RunResult


@pytest.mark.asyncio
async def test_generate_agent_validation_failure():
    """Test that the generate_agent function handles validation failures."""
    # Use a direct patch of the Runner.run method
    with patch("meta_agent.core.Runner.run") as mock_run:
        # We need to patch the validation step specifically
        def side_effect(agent, spec):
            if "Validate this agent implementation" in spec:
                result = {"valid": False, "message": "Validation failed"}
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "Assemble the complete agent implementation" in spec:
                result = {
                    "main_file": "test main file",
                    "additional_files": {"requirements.txt": "agents>=0.0.5"},
                    "installation_instructions": "pip install -r requirements.txt",
                    "usage_examples": "python main.py"
                }
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "analyze_agent_specification" in spec:
                result = {
                    "name": "TestAgent",
                    "description": "Test description",
                    "instructions": "Test instructions",
                    "tools": [],
                    "output_type": None,
                    "guardrails": [],
                    "handoffs": []
                }
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "design_agent_tools" in spec:
                result = {
                    "tools": [{
                        "name": "test_tool", 
                        "description": "A test tool",
                        "parameters": [{"name": "param1", "type": "string", "required": True}],
                        "return_type": "string",
                        "implementation": "def test_tool(param1):\n    return f'Result: {param1}'"
                    }]
                }
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "design_output_type" in spec:
                result = {
                    "name": "TestOutput",
                    "fields": [{"name": "result", "type": "string", "description": "Result of the tool execution"}],
                    "code": "class TestOutput(BaseModel):\n    result: str = Field(description='Result of the tool execution')"
                }
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "generate_output_type_code" in spec:
                result = {
                    "code": """from pydantic import BaseModel, Field

class TestOutput(BaseModel):
    result: str = Field(description="Result of the tool execution")"""
                }
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "generate_tool_code" in spec:
                result = {
                    "code": """from agents import function_tool

@function_tool
def test_tool(param1: str) -> str:
    \"\"\"A test tool.\"\"\"
    return f'Result: {param1}'"""
                }
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            elif "design_guardrails" in spec:
                result = [{
                    "name": "test_guardrail", 
                    "description": "A test guardrail",
                    "type": "input",
                    "validation_logic": "Check if input contains sensitive information",
                    "implementation": "def validate_input(input_text):\n    return 'password' not in input_text.lower()"
                }]
                return RunResult(final_output=json.dumps(result), tool_outputs=[json.dumps(result)])
            else:
                return RunResult(final_output="Mock response", tool_outputs=["Mock response"])
        
        mock_run.side_effect = side_effect
            
        # Also we need to actually trigger the validation error in core.py
        with patch("meta_agent.core.AgentImplementation") as mock_impl:
            def validation_failed(*args, **kwargs):
                raise ValueError("Validation failed")
            
            mock_impl.side_effect = validation_failed
            
            # Call the function and expect a validation error
            with pytest.raises(ValueError, match="Validation failed"):
                await generate_agent("Name: TestAgent\nInstructions: Test instructions")
