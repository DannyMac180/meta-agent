# test_generator.py
"""
Tests for the code generation functionality.
"""
import os
import pytest
import shutil
from meta_agent.generators.agent_generator import (
    generate_tool_code,
    generate_guardrail_code,
    generate_agent_code,
    generate_runner_code,
    assemble_agent_implementation
)
from meta_agent.models import (
    AgentSpecification,
    ToolDefinition,
    ToolParameter,
    GuardrailDefinition
)

@pytest.fixture
def test_dir():
    """Fixture to create and clean up a test directory."""
    dir_path = "./test_generator"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def test_generate_tool_code():
    """Test generating code for a tool."""
    # Create a tool definition
    tool = ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters=[
            ToolParameter(
                name="param1",
                type="string",
                description="First parameter",
                required=True
            ),
            ToolParameter(
                name="param2",
                type="integer",
                description="Second parameter",
                required=False
            )
        ],
        return_type="string"
    )
    
    # Generate code for the tool
    code = generate_tool_code(tool)
    
    # Verify the generated code
    assert "@function_tool" in code
    assert "def test_tool(" in code
    assert "param1: str" in code
    assert "param2: int = None" in code
    assert "-> str" in code
    assert "A test tool" in code
    assert "First parameter" in code
    assert "Second parameter" in code

def test_generate_guardrail_code():
    """Test generating code for a guardrail."""
    # Create a guardrail definition
    guardrail = GuardrailDefinition(
        description="Test guardrail",
        type="output"
    )
    
    # Generate code for the guardrail
    code = generate_guardrail_code(guardrail)
    
    # Verify the generated code
    assert "@output_guardrail" in code
    assert "def validate_test_guardrail(" in code
    assert "output_text: str" in code
    assert "-> GuardrailFunctionOutput" in code
    assert "Test guardrail" in code
    assert "return GuardrailFunctionOutput(is_valid=True)" in code

def test_generate_agent_code():
    """Test generating code for an agent."""
    # Create an agent specification
    spec = AgentSpecification(
        name="TestAgent",
        description="A test agent",
        instructions="You are a test agent.",
        tools=[
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters=[],
                return_type="string"
            )
        ],
        guardrails=[
            GuardrailDefinition(
                description="Test guardrail",
                type="output"
            )
        ]
    )
    
    # Generate code for the agent
    code = generate_agent_code(spec)
    
    # Verify the generated code
    assert "def create_agent():" in code
    assert "agent = Agent(" in code
    assert 'name="TestAgent"' in code
    assert "instructions=" in code
    assert "You are a test agent" in code
    assert "tools=[" in code
    assert "test_tool" in code
    assert "output_guardrails=[" in code
    assert "validate_test_guardrail" in code
    assert "return agent" in code

def test_generate_runner_code():
    """Test generating code for the runner."""
    # Generate code for the runner
    code = generate_runner_code()
    
    # Verify the generated code
    assert "async def run_agent(input_text: str):" in code
    assert "agent = create_agent()" in code
    assert "result = await Runner.run(agent, input_text)" in code
    assert "return result.final_output" in code
    assert "async def main():" in code
    assert "Agent is ready" in code
    assert "if __name__ == \"__main__\":" in code
    assert "asyncio.run(main())" in code

def test_assemble_agent_implementation():
    """Test assembling a complete agent implementation."""
    # Create an agent specification
    spec = AgentSpecification(
        name="TestAgent",
        description="A test agent",
        instructions="You are a test agent.",
        tools=[
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters=[],
                return_type="string"
            )
        ],
        guardrails=[
            GuardrailDefinition(
                description="Test guardrail",
                type="output"
            )
        ]
    )
    
    # Generate code components
    tool_code = [generate_tool_code(tool) for tool in spec.tools]
    guardrail_code = [generate_guardrail_code(guardrail) for guardrail in spec.guardrails]
    agent_code = generate_agent_code(spec)
    runner_code = generate_runner_code()
    
    # Assemble the implementation
    implementation = assemble_agent_implementation(
        spec=spec,
        tool_code=tool_code,
        output_type_code=None,
        guardrail_code=guardrail_code,
        agent_code=agent_code,
        runner_code=runner_code
    )
    
    # Verify the implementation
    assert "TestAgent - A test agent" in implementation
    assert "import asyncio" in implementation
    assert "import os" in implementation
    assert "from typing import Dict, List, Any, Optional" in implementation
    assert "from pydantic import BaseModel, Field" in implementation
    assert "from agents import Agent, Runner, function_tool, input_guardrail, output_guardrail, GuardrailFunctionOutput" in implementation
    assert "# Tool Definitions" in implementation
    assert "@function_tool" in implementation
    assert "def test_tool(" in implementation
    assert "# Guardrail Definitions" in implementation
    assert "@output_guardrail" in implementation
    assert "def validate_test_guardrail(" in implementation
    assert "# Agent Creation" in implementation
    assert "def create_agent():" in implementation
    assert "# Agent Runner" in implementation
    assert "async def run_agent(input_text: str):" in implementation
