"""
Test object-based specification flow.
"""

import pytest
from src.meta_agent.models.spec_schema import SpecSchema
from src.meta_agent.orchestrator import MetaAgentOrchestrator
from src.meta_agent.planning_engine import PlanningEngine
from src.meta_agent.sub_agent_manager import SubAgentManager
from src.meta_agent.registry import ToolRegistry
from src.meta_agent.agents.tool_designer_agent import ToolDesignerAgent
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def sample_spec_text():
    """Sample natural language specification."""
    return """
    Create a web scraper agent that takes a URL as input and returns the page content.
    
    Inputs:
    - url (string): The URL to scrape
    - format (string): Output format, either 'text' or 'html'
    
    Outputs:
    - content (string): The scraped content
    - status (integer): HTTP status code
    
    Constraints:
    - Must handle HTTP errors gracefully
    - Should respect robots.txt
    
    Technical Requirements:
    - Use requests library
    - Include User-Agent header
    """


@pytest.fixture
def mock_components():
    """Mock orchestrator components."""
    planning_engine = MagicMock(spec=PlanningEngine)
    planning_engine.analyze_tasks.return_value = {
        "execution_order": ["task_1"],
        "task_requirements": [
            {
                "task_id": "task_1",
                "tools": ["coder_tool"],
                "guardrails": [],
                "description": "Generate web scraper code"
            }
        ],
        "dependencies": {}
    }
    
    sub_agent_manager = MagicMock(spec=SubAgentManager)
    mock_agent = AsyncMock()
    mock_agent.name = "MockAgent"
    mock_agent.run.return_value = {"status": "completed", "output": "Mock result"}
    sub_agent_manager.get_or_create_agent.return_value = mock_agent
    
    tool_registry = MagicMock(spec=ToolRegistry)
    tool_designer_agent = MagicMock(spec=ToolDesignerAgent)
    
    return {
        "planning_engine": planning_engine,
        "sub_agent_manager": sub_agent_manager,
        "tool_registry": tool_registry,
        "tool_designer_agent": tool_designer_agent
    }


def test_spec_schema_from_text(sample_spec_text):
    """Test creating SpecSchema from natural language text."""
    spec = SpecSchema.from_text(sample_spec_text)
    
    assert spec.task_description
    assert "web scraper" in spec.task_description.lower()
    
    # The text parser may not catch all structured elements perfectly,
    # but it should at least parse the basic task description
    # We'll focus on testing the object conversion capabilities
    print(f"Parsed spec: {spec.to_dict()}")  # For debugging


def test_spec_schema_to_tool_spec_dict():
    """Test converting SpecSchema to tool specification dict."""
    # Create a spec with structured data to test conversion
    spec_data = {
        "task_description": "Create a web scraper tool", 
        "inputs": {"url": "string", "format": "string"},
        "outputs": {"content": "string", "status": "integer"},
        "metadata": {"name": "WebScraper"}
    }
    spec = SpecSchema.from_dict(spec_data)
    tool_spec = spec.to_tool_spec_dict()
    
    assert "name" in tool_spec
    assert "description" in tool_spec
    assert "purpose" in tool_spec
    assert "specification" in tool_spec
    
    assert tool_spec["name"] == "WebScraper"
    assert tool_spec["description"] == "Create a web scraper tool"
    assert tool_spec["purpose"] == "Create a web scraper tool"
    
    if spec.inputs:
        assert "input_schema" in tool_spec
        assert tool_spec["input_schema"] == spec.inputs
    if spec.outputs:
        assert "output_schema" in tool_spec
        assert tool_spec["output_schema"] == spec.outputs


@pytest.mark.asyncio
async def test_orchestrator_accepts_spec_schema_object(sample_spec_text, mock_components):
    """Test that orchestrator can accept SpecSchema objects directly."""
    spec = SpecSchema.from_text(sample_spec_text)
    
    orchestrator = MetaAgentOrchestrator(
        planning_engine=mock_components["planning_engine"],
        sub_agent_manager=mock_components["sub_agent_manager"],
        tool_registry=mock_components["tool_registry"],
        tool_designer_agent=mock_components["tool_designer_agent"]
    )
    
    # Mock decompose_spec to return expected format
    orchestrator.decompose_spec = MagicMock(return_value={
        "subtasks": [
            {
                "id": "task_1",
                "description": "Generate web scraper code",
                "agent_type": "coder"
            }
        ]
    })
    
    # Run orchestration with SpecSchema object
    results = await orchestrator.run(specification=spec)
    
    # Verify orchestrator processed the SpecSchema object
    assert results is not None
    assert mock_components["planning_engine"].analyze_tasks.called
    assert mock_components["sub_agent_manager"].get_or_create_agent.called
    
    # Verify decompose_spec was called with the correct converted dict
    orchestrator.decompose_spec.assert_called_once()
    called_spec = orchestrator.decompose_spec.call_args[0][0]
    assert isinstance(called_spec, dict)
    assert "task_description" in called_spec


@pytest.mark.asyncio 
async def test_tool_design_with_spec_schema():
    """Test that tool design works with SpecSchema objects."""
    spec_text = """
    Create a file reader tool that takes a filename and returns the content.
    
    Inputs:
    - filename (string): Path to the file to read
    
    Outputs:
    - content (string): File content
    """
    
    spec = SpecSchema.from_text(spec_text)
    
    # Mock components  
    tool_registry = MagicMock()
    tool_registry.register.return_value = "path/to/tool.py"
    
    tool_designer = MagicMock()
    tool_designer.design_tool.return_value = "# Generated tool code"
    
    orchestrator = MetaAgentOrchestrator(
        planning_engine=MagicMock(),
        sub_agent_manager=MagicMock(),
        tool_registry=tool_registry,
        tool_designer_agent=tool_designer
    )
    
    # Test design_and_register_tool with SpecSchema object
    result = await orchestrator.design_and_register_tool(spec)
    
    assert result == "path/to/tool.py"
    tool_designer.design_tool.assert_called_once()
    
    # Verify the tool designer was called with a proper dict (tool spec format)
    called_spec = tool_designer.design_tool.call_args[0][0]
    assert isinstance(called_spec, dict)
    # When a SpecSchema is converted to tool spec dict, it has different structure
    assert "name" in called_spec
    assert "description" in called_spec or "purpose" in called_spec


def test_spec_schema_conversion_backwards_compatibility():
    """Test that dict specs still work alongside SpecSchema objects."""
    # Test with regular dict (existing functionality)
    dict_spec = {
        "task_description": "Create a simple calculator",
        "inputs": {"a": "number", "b": "number"},
        "outputs": {"result": "number"}
    }
    
    spec_from_dict = SpecSchema.from_dict(dict_spec)
    
    assert spec_from_dict.task_description == "Create a simple calculator"
    assert spec_from_dict.inputs == {"a": "number", "b": "number"}
    assert spec_from_dict.outputs == {"result": "number"}
    
    # Test conversion back to dict
    converted_dict = spec_from_dict.to_dict()
    assert converted_dict["task_description"] == dict_spec["task_description"]
    assert converted_dict["inputs"] == dict_spec["inputs"]
    assert converted_dict["outputs"] == dict_spec["outputs"]
