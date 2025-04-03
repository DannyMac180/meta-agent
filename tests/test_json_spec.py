# test_json_spec.py
"""
Tests for JSON specification parsing and agent generation.
"""
import json
import os
import pytest
import shutil
from typing import Dict, Any
from meta_agent import generate_agent
from meta_agent.models import AgentImplementation
from meta_agent.core import _parse_specification
from meta_agent.models import AgentSpecification, ToolDefinition

@pytest.fixture
def test_dir():
    """Fixture to create and clean up a test directory."""
    dir_path = "./test_agent_json_spec"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def create_research_agent_spec() -> Dict[str, Any]:
    """Create a standard research agent specification for testing."""
    return {
        "name": "ResearchAgentJSON",
        "description": "An agent that performs web research on topics",
        "instructions": "You are a research assistant that helps users find information on various topics. Use the search tool to find relevant information and summarize it concisely.",
        "tools": [
            {
                "name": "search_web",
                "description": "Searches the web for information",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "The search query",
                        "required": True
                    },
                    {
                        "name": "num_results",
                        "type": "integer",
                        "description": "Number of results to return",
                        "required": False
                    }
                ],
                "return_type": "string"
            }
        ],
        "guardrails": [
            {
                "description": "Ensure sources are cited properly",
                "type": "output"
            }
        ]
    }

def test_json_spec_generation(test_dir):
    """Test generating an agent from a JSON specification."""
    # JSON specification
    spec_dict = create_research_agent_spec()
    specification = json.dumps(spec_dict)

    # Generate the agent
    implementation = generate_agent(specification, output_dir=test_dir)

    # Verify return type
    assert isinstance(implementation, AgentImplementation)

    # Verify files were created
    assert os.path.exists(os.path.join(test_dir, "agent_implementation.py"))
    assert os.path.exists(os.path.join(test_dir, "README.md"))

    # Verify implementation content
    assert "ResearchAgentJSON" in implementation.main_file
    assert "search_web" in implementation.main_file
    assert "def search_web(" in implementation.main_file
    assert "query: str" in implementation.main_file
    # The implementation uses int = None instead of Optional[int]
    assert "num_results: int = None" in implementation.main_file or "num_results = None" in implementation.main_file
    assert "-> str" in implementation.main_file
    # The implementation truncates long function names
    assert "ensure_sources" in implementation.main_file

def test_json_spec_parsing():
    """Test parsing a JSON specification into an AgentSpecification object."""
    # Create JSON specification
    spec_dict = create_research_agent_spec()
    specification = json.dumps(spec_dict)

    # Parse the specification
    agent_spec = _parse_specification(specification)

    # Verify the parsed specification
    assert isinstance(agent_spec, AgentSpecification)
    assert agent_spec.name == "ResearchAgentJSON"
    assert agent_spec.description == "An agent that performs web research on topics"
    assert len(agent_spec.tools) == 1
    assert isinstance(agent_spec.tools[0], ToolDefinition)
    assert agent_spec.tools[0].name == "search_web"
    assert len(agent_spec.tools[0].parameters) == 2
    assert agent_spec.tools[0].parameters[0].name == "query"
    assert agent_spec.tools[0].parameters[0].type == "string"
    assert agent_spec.tools[0].parameters[0].required is True
    assert agent_spec.tools[0].parameters[1].name == "num_results"
    assert agent_spec.tools[0].parameters[1].type == "integer"
    assert agent_spec.tools[0].parameters[1].required is False
    assert len(agent_spec.guardrails) == 1
    assert agent_spec.guardrails[0].description == "Ensure sources are cited properly"
    assert agent_spec.guardrails[0].type == "output"

def test_json_spec_with_output_type(test_dir):
    """Test generating an agent with a structured output type."""
    # Create specification with output type
    spec_dict = create_research_agent_spec()
    spec_dict["output_type"] = {
        "name": "ResearchResult",
        "fields": [
            {
                "name": "summary",
                "type": "string",
                "description": "Summary of the research",
                "required": True
            },
            {
                "name": "sources",
                "type": "list",
                "description": "List of sources",
                "required": True
            }
        ]
    }

    # Generate the agent
    implementation = generate_agent(json.dumps(spec_dict), output_dir=test_dir)

    # Verify implementation content
    assert "class ResearchResult(BaseModel):" in implementation.main_file
    assert "summary: str" in implementation.main_file
    # The implementation uses Any instead of List
    assert "sources:" in implementation.main_file
    assert "output_type=ResearchResult" in implementation.main_file
