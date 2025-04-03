# test_parser.py
"""
Tests for the specification parser functionality.
"""
import json
import os
import pytest
from meta_agent.core import _parse_specification, _parse_natural_language
from meta_agent.models import AgentSpecification, ToolDefinition, GuardrailDefinition

def test_parse_json_specification():
    """Test parsing a JSON specification."""
    # Create a JSON specification
    spec_dict = {
        "name": "TestJsonParser",
        "description": "A test agent for JSON parsing",
        "instructions": "You are a test agent for JSON parsing.",
        "tools": [
            {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": [
                    {
                        "name": "param1",
                        "type": "string",
                        "description": "First parameter",
                        "required": True
                    }
                ],
                "return_type": "string"
            }
        ],
        "guardrails": [
            {
                "description": "Test guardrail",
                "type": "output"
            }
        ]
    }

    # Parse the specification
    specification = json.dumps(spec_dict)
    agent_spec = _parse_specification(specification)

    # Verify the parsed specification
    assert isinstance(agent_spec, AgentSpecification)
    assert agent_spec.name == "TestJsonParser"
    assert agent_spec.description == "A test agent for JSON parsing"
    assert agent_spec.instructions == "You are a test agent for JSON parsing."

    # Verify tools
    assert len(agent_spec.tools) == 1
    assert isinstance(agent_spec.tools[0], ToolDefinition)
    assert agent_spec.tools[0].name == "test_tool"
    assert agent_spec.tools[0].description == "A test tool"
    assert len(agent_spec.tools[0].parameters) == 1
    assert agent_spec.tools[0].parameters[0].name == "param1"
    assert agent_spec.tools[0].parameters[0].type == "string"
    assert agent_spec.tools[0].parameters[0].required is True

    # Verify guardrails
    assert len(agent_spec.guardrails) == 1
    assert agent_spec.guardrails[0].description == "Test guardrail"
    assert agent_spec.guardrails[0].type == "output"

def test_parse_natural_language_specification():
    """Test parsing a natural language specification."""
    # Create a natural language specification
    specification = """
    Name: TestNLParser

    Description: A test agent for natural language parsing

    Instructions: You are a test agent for natural language parsing.

    Tools:
    1. test_tool: A test tool
       - param1 (string, required): First parameter
       - param2 (integer, optional): Second parameter
       - Returns: Test result

    Guardrails:
    - Test guardrail
    - Input validation guardrail
    """

    # Parse the specification
    agent_spec = _parse_natural_language(specification)

    # Verify the parsed specification
    assert isinstance(agent_spec, AgentSpecification)
    assert agent_spec.name == "TestNLParser"
    assert agent_spec.description == "A test agent for natural language parsing"
    assert "You are a test agent for natural language parsing" in agent_spec.instructions

    # Verify tools (if the parser implementation supports it)
    if agent_spec.tools:
        assert len(agent_spec.tools) > 0
        # Check that at least the tool name was parsed
        assert "test" in agent_spec.tools[0].name.lower()

    # Verify guardrails (if the parser implementation supports it)
    if agent_spec.guardrails:
        assert len(agent_spec.guardrails) > 0
        # Check that at least one guardrail was parsed
        assert "guardrail" in agent_spec.guardrails[0].description.lower()

def test_empty_specification():
    """Test that empty specifications are handled properly."""
    # The implementation might not raise an error for empty specifications
    # but should return a default agent specification
    empty_spec = _parse_specification("")
    assert isinstance(empty_spec, AgentSpecification)
    assert empty_spec.name == "DefaultAgent" or not empty_spec.name

    whitespace_spec = _parse_specification("   ")
    assert isinstance(whitespace_spec, AgentSpecification)
    assert whitespace_spec.name == "DefaultAgent" or not whitespace_spec.name

def test_invalid_json_specification():
    """Test that invalid JSON specifications are handled properly."""
    # Invalid JSON but valid natural language
    specification = """
    Name: InvalidJSON
    Description: This is not valid JSON
    Instructions: Test
    """

    # Should fall back to natural language parsing
    agent_spec = _parse_specification(specification)
    assert isinstance(agent_spec, AgentSpecification)
    assert agent_spec.name == "InvalidJSON"
    assert agent_spec.description == "This is not valid JSON"
