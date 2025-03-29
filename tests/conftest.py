"""
Pytest configuration file with fixtures for testing the meta-agent.
"""
import os
import pytest
import asyncio
import sys
import json
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

from meta_agent.models import AgentSpecification, ToolDefinition, OutputTypeDefinition, AgentImplementation

# Load environment variables for tests
load_dotenv()

# Add the mocks directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'mocks')))

# Make sure our mock agents module is available
pytest.importorskip("tests.mocks.agents")


@pytest.fixture
def mock_openai_response():
    """Fixture to mock OpenAI API responses."""
    return {
        "id": "test-id",
        "model": "gpt-4",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "analyze_agent_specification",
                                "arguments": json.dumps({
                                    "name": "ResearchAgent",
                                    "description": "An advanced research agent that searches the web for information on complex topics, analyzes multiple sources, and generates comprehensive, well-structured research reports with citations.",
                                    "instructions": "You are an expert research assistant specialized in web-based research. When given a research question or topic, use your tools to search for relevant information across multiple sources. Analyze the information for accuracy, relevance, and credibility. Synthesize findings into a comprehensive report that includes: 1. An executive summary of key findings 2. A detailed analysis of the topic with supporting evidence 3. Different perspectives or viewpoints when applicable 4. Citations for all sources used 5. Recommendations for further research if relevant",
                                    "tools": [
                                        {
                                            "name": "search_web",
                                            "description": "Searches the web for information",
                                            "parameters": [
                                                {"name": "query", "type": "string", "required": True},
                                                {"name": "num_results", "type": "integer", "required": False, "default": 8}
                                            ],
                                            "return_type": "list"
                                        },
                                        {
                                            "name": "extract_content",
                                            "description": "Extracts the main content from a URL",
                                            "parameters": [
                                                {"name": "url", "type": "string", "required": True}
                                            ],
                                            "return_type": "string"
                                        },
                                        {
                                            "name": "analyze_source",
                                            "description": "Analyzes the credibility of a source",
                                            "parameters": [
                                                {"name": "url", "type": "string", "required": True},
                                                {"name": "content", "type": "string", "required": True}
                                            ],
                                            "return_type": "dict"
                                        },
                                        {
                                            "name": "summarize_content",
                                            "description": "Summarizes content from multiple sources",
                                            "parameters": [
                                                {"name": "texts", "type": "list", "required": True},
                                                {"name": "max_length", "type": "integer", "required": False, "default": 500}
                                            ],
                                            "return_type": "string"
                                        }
                                    ],
                                    "output_type": "A structured research report with sections for summary, analysis, findings, and references",
                                    "guardrails": [
                                        {"name": "source_citation", "description": "Ensure all claims are supported by cited sources", "type": "output"},
                                        {"name": "balanced_viewpoints", "description": "Check for balanced representation of different viewpoints on controversial topics", "type": "output"},
                                        {"name": "source_credibility", "description": "Verify that sources are credible and relevant to the research question", "type": "input"}
                                    ]
                                })
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ]
    }


@pytest.fixture
def mock_agent_specification():
    """Fixture for a test agent specification."""
    return """
    Name: TestAgent
    
    Description: A test agent for unit testing
    
    Instructions: You are a test agent used for unit testing the meta-agent framework.
    
    Tools needed:
    1. test_tool: A tool for testing
       - Parameters: param1 (string, required)
       - Returns: Test result
    
    Output type: A test result
    
    Guardrails:
    - Validate input parameters
    """


@pytest.fixture
def event_loop():
    """Create and provide an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def environment_setup():
    """Setup environment variables for tests and restore after tests."""
    original_env = os.environ.copy()
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    yield
    os.environ.clear()
    os.environ.update(original_env)


# --- New Fixture for Mock Runner Results ---

@pytest.fixture
def mock_runner_results():
    """Provides a sequence of mock RunResult objects for the generator steps."""
    # Import here to avoid issues if mocks aren't available
    from tests.mocks.agents import RunResult

    # 1. Analyze Specification Result (JSON String)
    spec_output = AgentSpecification(
        name="TestAgent",
        description="A test agent",
        instructions="Test instructions",
        tools=[{"name": "test_tool", "description": "A test tool", "parameters": [{"name":"arg1", "type":"str"}], "returns": "str"}],
        output_type="TestOutput",
        guardrails=[],
        handoffs=[]
    ).model_dump_json()

    # 2. Design Tools Result (JSON String containing {"tools": [...]})
    tools_output = json.dumps({
        "tools": [
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters=[{"name": "arg1", "type": "str", "required": True}],
                return_type="str",
                implementation="# Placeholder"
            ).model_dump()
        ]
    })

    # 3. Design Output Type Result (JSON String of OutputTypeDefinition)
    output_design_output = OutputTypeDefinition(
        name="TestOutput",
        fields=[{"name": "result", "type": "str", "description": "The final result"}],
        code="# Placeholder"
    ).model_dump_json()

    # 4. Generate Output Type Code Result (JSON String {"code": "..."})
    output_code_output = json.dumps({
        "code": """from pydantic import BaseModel, Field

class TestOutput(BaseModel):
    result: str = Field(description="The final result")"""
    })

    # 5. Generate Tool Code Result (JSON String {"code": "..."})
    tool_code_output = json.dumps({
        "code": """from agents import function_tool

@function_tool
def test_tool(arg1: str) -> str:
    \"\"\"A test tool.\"\"\"
    # TODO: Implement
    return 'Not implemented'"""
    })

    # 6. Generate Agent Definition Code Result (JSON String {"code": "..."})
    agent_def_code_output = json.dumps({
        "code": """from agents import Agent
from .tools import test_tool
from .output_types import TestOutput

agent = Agent(
    name="TestAgent",
    description="A test agent",
    instructions=\"\"\"Test instructions\"\"\",
    tools=[test_tool],
    output_type=TestOutput
)"""
    })

    # 7. Generate Runner Code Result (JSON String {"code": "..."})
    runner_code_output = json.dumps({
        "code": """import asyncio
from agents import Runner
from .agent import agent

async def main():
    runner = Runner()
    result = await runner.run(agent, "Your input here")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())"""
    })

    # 8. Assembly Result (JSON String with complete implementation)
    assembly_output = json.dumps({
        "main_file": "main.py",
        "additional_files": {
            "requirements.txt": "agents>=0.0.5",
            "README.md": "# TestAgent\n\nA test agent implementation."
        },
        "installation_instructions": "pip install -r requirements.txt",
        "usage_examples": "python main.py"
    })

    # Create RunResult objects with both final_output and tool_outputs
    return [
        RunResult(final_output=spec_output, tool_outputs=[spec_output]),  # Analysis
        RunResult(final_output=tools_output, tool_outputs=[tools_output]),  # Tools
        RunResult(final_output=output_design_output, tool_outputs=[output_design_output]),  # Output Type Design
        RunResult(final_output=output_code_output, tool_outputs=[output_code_output]),  # Output Type Code
        RunResult(final_output=tool_code_output, tool_outputs=[tool_code_output]),  # Tool Code
        RunResult(final_output=agent_def_code_output, tool_outputs=[agent_def_code_output]),  # Agent Definition
        RunResult(final_output=runner_code_output, tool_outputs=[runner_code_output]),  # Runner Code
        RunResult(final_output=assembly_output, tool_outputs=[assembly_output])  # Assembly
    ]
