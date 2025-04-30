# tests/unit/test_sub_agent_manager.py
import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch, call, mock_open, ANY
import uuid

# --- Import Actual Classes ---
from meta_agent.sub_agent_manager import SubAgentManager, ToolDesignerAgent, CoderAgent, TesterAgent, BaseAgent, ReviewerAgent
from meta_agent.state_manager import StateManager
from meta_agent.template_engine import TemplateEngine
from agents import Agent, Runner                      # From OpenAI SDK (via memory)
from meta_agent.models.generated_tool import GeneratedTool

# --- Fixtures (Updated Specs) ---

@pytest.fixture
def mock_state_manager():
    """Fixture for a mocked StateManager."""
    manager = MagicMock(spec=StateManager)
    # Explicitly create the methods as mocks *before* setting return_value
    manager.get_agent_state = MagicMock(return_value=None) # Default: agent not found
    manager.get_all_agent_names = MagicMock(return_value=[]) # Default: no existing agents
    manager.save_agent_state = MagicMock()
    return manager

@pytest.fixture
def mock_template_engine():
    """Fixture for a mocked TemplateEngine."""
    engine = MagicMock(spec=TemplateEngine)
    # Explicitly create the render method as a mock
    engine.render = MagicMock(side_effect=lambda template_name, **kwargs: f"rendered_{template_name}_content")
    return engine

@pytest.fixture
def mock_tool_designer():
    """Fixture for a mocked ToolDesignerAgent."""
    # Use the actual ToolDesignerAgent class as the spec
    designer = MagicMock(spec=ToolDesignerAgent)
    async def mock_run(specification):
        # Simulate designing based on the 'tools', 'output_type', 'guardrails' keys
        return {
            "designed_tools": specification.get("tools", ["default_tool"]),
            "designed_output_type": specification.get("output_type", {"type": "default_string"}),
            "designed_guardrails": specification.get("guardrails", ["default_guardrail"])
        }
    designer.run = AsyncMock(side_effect=mock_run)
    # We need to mock model_dump if it exists on the actual class and is used
    if hasattr(ToolDesignerAgent, 'model_dump'):
         designer.model_dump = MagicMock(return_value={"config": "designer_config"}) # Needed for state saving
    return designer

@pytest.fixture
def sub_agent_manager(
    tmp_path
):
    """Fixture for SubAgentManager with mocked dependencies (patched later)."""
    # We might still need tmp_path if methods interact with filesystem directly
    # but base_agents_dir isn't set in __init__

    # Patch only Agent and Runner which are confirmed class imports
    with patch('meta_agent.sub_agent_manager.Agent', Agent), \
         patch('meta_agent.sub_agent_manager.Runner', Runner):

        # Instantiate without arguments
        manager = SubAgentManager()
        # Dependencies like state_manager, template_engine etc. are likely
        # instantiated within methods or are module level.
        # We will patch them directly in tests that need them.
        return manager

# --- Initialization Tests ---

def test_sub_agent_manager_initialization(sub_agent_manager): 
    """Test that SubAgentManager initializes correctly."""
    # Check the actual initialized attribute
    assert hasattr(sub_agent_manager, 'active_agents')
    assert sub_agent_manager.active_agents == {}

# --- get_or_create_agent Tests ---

def test_get_or_create_coder_agent(sub_agent_manager):
    """Test getting a CoderAgent using 'coder_tool'."""
    requirements = {"task_id": "task-1", "tools": ["coder_tool"], "description": "write code"}
    agent = sub_agent_manager.get_or_create_agent(requirements)
    assert isinstance(agent, CoderAgent)
    assert agent is sub_agent_manager.active_agents.get("CoderAgent") # Check cache with correct attribute

def test_get_or_create_tester_agent(sub_agent_manager):
    """Test getting a TesterAgent using 'tester_tool'."""
    requirements = {"task_id": "task-2", "tools": ["tester_tool"], "description": "write tests"}
    agent = sub_agent_manager.get_or_create_agent(requirements)
    assert isinstance(agent, TesterAgent)
    assert agent is sub_agent_manager.active_agents.get("TesterAgent") # Check cache with correct attribute

def test_get_or_create_tool_designer_agent(sub_agent_manager):
    """Test getting a ToolDesignerAgent using 'tool_designer_tool'."""
    requirements = {"task_id": "task-3", "tools": ["tool_designer_tool"], "description": "design a tool"}
    agent = sub_agent_manager.get_or_create_agent(requirements)
    assert isinstance(agent, ToolDesignerAgent)
    assert agent is sub_agent_manager.active_agents.get("ToolDesignerAgent") # Check cache with correct attribute

def test_get_or_create_fallback_agent_unknown_tool(sub_agent_manager):
    """Test getting the BaseAgent when the tool is unknown."""
    requirements = {"task_id": "task-4", "tools": ["unknown_tool"], "description": "do something"}
    agent = sub_agent_manager.get_or_create_agent(requirements)
    assert isinstance(agent, BaseAgent)
    assert agent is sub_agent_manager.active_agents.get("BaseAgent") # Check cache with correct attribute

def test_get_or_create_fallback_agent_no_tool(sub_agent_manager):
    """Test getting the BaseAgent when no tools are provided."""
    requirements = {"task_id": "task-5", "tools": [], "description": "do something else"}
    agent = sub_agent_manager.get_or_create_agent(requirements)
    assert isinstance(agent, BaseAgent)
    assert agent is sub_agent_manager.active_agents.get("BaseAgent") # Check cache with correct attribute

def test_get_or_create_agent_caching(sub_agent_manager):
    """Test that agent instances are cached and reused."""
    requirements1 = {"task_id": "task-6", "tools": ["coder_tool"], "description": "code"}
    agent1 = sub_agent_manager.get_or_create_agent(requirements1)
    assert isinstance(agent1, CoderAgent)
    assert "CoderAgent" in sub_agent_manager.active_agents
    assert len(sub_agent_manager.active_agents) == 1

    requirements2 = {"task_id": "task-7", "tools": ["coder_tool"], "description": "code again"}
    agent2 = sub_agent_manager.get_or_create_agent(requirements2)
    assert agent2 is agent1
    assert len(sub_agent_manager.active_agents) == 1

    requirements3 = {"task_id": "task-8", "tools": ["tester_tool"], "description": "test"}
    agent3 = sub_agent_manager.get_or_create_agent(requirements3)
    assert isinstance(agent3, TesterAgent)
    assert agent3 is not agent1
    assert "TesterAgent" in sub_agent_manager.active_agents
    assert len(sub_agent_manager.active_agents) == 2

    requirements4 = {"task_id": "task-9", "tools": [], "description": "fallback"}
    agent4 = sub_agent_manager.get_or_create_agent(requirements4)
    assert isinstance(agent4, BaseAgent)
    assert "BaseAgent" in sub_agent_manager.active_agents
    assert len(sub_agent_manager.active_agents) == 3

    requirements5 = {"task_id": "task-10", "tools": ["unknown"], "description": "another fallback"}
    agent5 = sub_agent_manager.get_or_create_agent(requirements5)
    assert agent5 is agent4
    assert len(sub_agent_manager.active_agents) == 3

# Prepare mock for the failing agent instantiation test
mock_failing_coder = MagicMock(side_effect=Exception("Failed to initialize"))
mock_failing_coder.__name__ = "CoderAgent" # Need to mock the name for caching key

@patch.dict(
    'meta_agent.sub_agent_manager.SubAgentManager.AGENT_TOOL_MAP', # Target the class attribute dictionary
    {'coder_tool': mock_failing_coder} # Provide a mock that fails on call and has a name
)
def test_get_or_create_agent_instantiation_fails(sub_agent_manager): # No need to patch CoderAgent class directly anymore
    """Test that get_or_create_agent returns None if agent instantiation fails."""
    requirements = {"task_id": "task-error", "tools": ["coder_tool"], "description": "cause error"}
    agent = sub_agent_manager.get_or_create_agent(requirements)

    # Assert that None is returned and the agent wasn't cached
    assert agent is None
    assert "CoderAgent" not in sub_agent_manager.active_agents # Check correct attribute

# --- get_agent Tests ---

def test_get_agent_exists(sub_agent_manager):
    """Test retrieving an existing agent by its requirement key."""
    requirements = {"task_id": "task-exist", "tools": ["coder_tool"], "description": "get existing"}
    coder_agent = sub_agent_manager.get_or_create_agent(requirements)

    # Retrieve using the tool requirement key used for caching
    retrieved_agent = sub_agent_manager.get_agent("coder_tool")
    assert retrieved_agent is coder_agent

def test_get_agent_not_exists(sub_agent_manager):
    """Test retrieving a non-existent agent returns None."""
    retrieved_agent = sub_agent_manager.get_agent("NonExistentAgent")
    assert retrieved_agent is None

# --- list_agents Tests ---

def test_list_agents_empty(sub_agent_manager):
    """Test listing agents when the cache is empty."""
    assert sub_agent_manager.list_agents() == {}

def test_list_agents_populated(sub_agent_manager):
    """Test listing agents after populating the cache."""
    # Create a couple of agents
    req1 = {"task_id": "task-12", "tools": ["coder_tool"], "description": "code"}
    coder = sub_agent_manager.get_or_create_agent(req1)
    req2 = {"task_id": "task-13", "tools": [], "description": "fallback"}
    base = sub_agent_manager.get_or_create_agent(req2)

    expected_agents = {
        "CoderAgent": coder,
        "BaseAgent": base
    }
    assert sub_agent_manager.list_agents() == expected_agents

# --- Placeholder Agent Tests ---

@pytest.mark.asyncio
async def test_base_agent_run():
    """Test the run method of the placeholder BaseAgent."""
    agent = BaseAgent()
    spec = {"task_id": "task-base", "description": "Do basic stuff"}
    result = await agent.run(spec)
    assert result["status"] == "simulated_success"
    assert "Result from BaseAgent for task-base" in result["output"]

@pytest.mark.asyncio
async def test_coder_agent_run():
    """Test the run method of the placeholder CoderAgent."""
    agent = CoderAgent()
    spec = {"task_id": "task-coder", "description": "Write code"}
    result = await agent.run(spec)
    assert result["status"] == "simulated_success"
    assert "Generated code by CoderAgent for task-coder" in result["output"]

@pytest.mark.asyncio
async def test_tester_agent_run():
    """Test the run method of the placeholder TesterAgent."""
    agent = TesterAgent()
    spec = {"task_id": "task-tester", "description": "Test code"}
    result = await agent.run(spec)
    assert result["status"] == "simulated_success"
    assert "Test results from TesterAgent for task-tester" in result["output"]

@pytest.mark.asyncio
async def test_reviewer_agent_run():
    """Test the run method of the placeholder ReviewerAgent."""
    agent = ReviewerAgent()
    spec = {"task_id": "task-reviewer", "description": "Review code"}
    result = await agent.run(spec)
    assert result["status"] == "simulated_success"
    assert "Review comments from ReviewerAgent for task-reviewer" in result["output"]

# --- ToolDesignerAgent Tests ---

@pytest.mark.asyncio
async def test_tool_designer_generate_tool_websearch():
    """Test ToolDesignerAgent.generate_tool for WebSearchTool trigger keywords."""
    agent = ToolDesignerAgent()
    # Specification containing a keyword that should trigger WebSearchTool
    spec_search = {"description": "Search the web for documentation"}

    generated_tool = await agent.generate_tool(spec_search)

    assert isinstance(generated_tool, GeneratedTool)
    # Check if the generated code contains expected elements of the WebSearchTool stub
    assert "class WebSearchTool:" in generated_tool.code
    assert "def search_web(query: str, tool_instance: WebSearchTool)" in generated_tool.code
    assert "tool_instance.run(query)" in generated_tool.code
    # Check tests and docs
    assert "test_search_web" in generated_tool.tests
    assert "Searches the web for a query" in generated_tool.docs

@pytest.mark.asyncio
async def test_tool_designer_generate_tool_filesearch():
    """Test ToolDesignerAgent.generate_tool for FileSearchTool trigger keywords."""
    agent = ToolDesignerAgent()
    # Specification containing a keyword that should trigger FileSearchTool
    # Use a keyword absolutely unique to FileSearchTool keywords
    spec_filesearch = {"description": "embedding lookup"}

    generated_tool = await agent.generate_tool(spec_filesearch)

    assert isinstance(generated_tool, GeneratedTool)
    # Check if the generated code contains expected elements of the FileSearchTool stub
    assert "class FileSearchTool:" in generated_tool.code # Stub class
    assert "def search_files(query: str)" in generated_tool.code
    assert "return FileSearchTool()(query)" in generated_tool.code # Usage of the stub
    # Check tests and docs
    assert "test_search_files" in generated_tool.tests
    assert "Searches indexed files/vectors" in generated_tool.docs

@pytest.mark.asyncio
async def test_tool_designer_generate_tool_openweathermap():
    """Test ToolDesignerAgent.generate_tool for OpenWeatherMap trigger keywords."""
    agent = ToolDesignerAgent()
    spec_weather = {"description": "Get the weather using openweathermap"}

    generated_tool = await agent.generate_tool(spec_weather)

    assert isinstance(generated_tool, GeneratedTool)
    # Check for specific elements of the OpenWeatherMap tool code
    assert "import requests" in generated_tool.code
    assert "def get_weather(city: str, api_key: str)" in generated_tool.code
    assert "requests.get(url)" in generated_tool.code
    assert "response.raise_for_status()" in generated_tool.code
    # Check tests and docs
    assert "test_get_weather_success" in generated_tool.tests
    expected_docs = (
        '# get_weather\n\n'
        'Fetches current weather for a city using the OpenWeatherMap API.\n'
        'Returns parsed JSON on success or raises HTTPError on failure.\n'
    )
    assert generated_tool.docs == expected_docs

@pytest.mark.asyncio
async def test_tool_designer_generate_tool_fallback_llm(monkeypatch):
    """
    When Runner returns something that is **not** valid JSON, the agent should
    surface an error stub in the `code` field rather than crash.
    """
    from agents import Runner

    # Force Runner.run to emit a clearly-invalid JSON string.
    async def fake_run(*_a, **_kw):
        class FakeRes:
            final_output = "definitely not-json"
        return FakeRes()

    monkeypatch.setattr(Runner, "run", fake_run)

    agent = ToolDesignerAgent()
    spec  = {"task_id": "badjson", "description": "some generic task"}

    result = await agent.generate_tool(spec)

    assert isinstance(result, GeneratedTool)
    # Fallback branch should prefix the code with '# Error' to signal the problem.
    assert result.code.startswith("# Error"), "Expected an error stub when JSON parsing fails"

# --- SubAgentManager Tests ---

def test_tool_designer_generate_tool_websearch(sub_agent_manager, mock_tool_designer):
    """Test tool generation dispatch for web search (placeholder)."""
    # This test might need more mocking if it directly interacts with ToolDesignerAgent methods
    # Assuming get_agent is the primary interaction point for now
    requirements = {"task_id": "task-web", "tools": ["tool_designer_tool"], "description": "design web search"}
    # Patch the AGENT_TOOL_MAP temporarily for this test
    with patch.dict(sub_agent_manager.AGENT_TOOL_MAP, {'tool_designer_tool': lambda **kwargs: mock_tool_designer}):
        agent = sub_agent_manager.get_agent(tool_requirement="tool_designer_tool", **requirements) # Use get_agent
        assert agent is mock_tool_designer

def test_tool_designer_generate_tool_filesearch(sub_agent_manager, mock_tool_designer):
    """Test tool generation dispatch for file search (placeholder)."""
    requirements = {"task_id": "task-file", "tools": ["tool_designer_tool"], "description": "design file search"}
    with patch.dict(sub_agent_manager.AGENT_TOOL_MAP, {'tool_designer_tool': lambda **kwargs: mock_tool_designer}):
        agent = sub_agent_manager.get_agent(tool_requirement="tool_designer_tool", **requirements)
        assert agent is mock_tool_designer

def test_tool_designer_generate_tool_openweathermap(sub_agent_manager, mock_tool_designer):
    """Test tool generation dispatch for OpenWeatherMap (placeholder)."""
    requirements = {"task_id": "task-weather", "tools": ["tool_designer_tool"], "description": "design weather tool"}
    with patch.dict(sub_agent_manager.AGENT_TOOL_MAP, {'tool_designer_tool': lambda **kwargs: mock_tool_designer}):
        agent = sub_agent_manager.get_agent(tool_requirement="tool_designer_tool", **requirements)
        assert agent is mock_tool_designer

def test_tool_designer_generate_tool_fallback_llm(sub_agent_manager, mock_tool_designer):
    """Test tool generation dispatch using LLM fallback (placeholder)."""
    requirements = {"task_id": "task-llm", "tools": ["tool_designer_tool"], "description": "design fallback tool"}
    with patch.dict(sub_agent_manager.AGENT_TOOL_MAP, {'tool_designer_tool': lambda **kwargs: mock_tool_designer}):
        agent = sub_agent_manager.get_agent(tool_requirement="tool_designer_tool", **requirements)
        assert agent is mock_tool_designer
