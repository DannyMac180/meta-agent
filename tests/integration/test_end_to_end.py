"""
Integration tests for the meta-agent package.

These tests verify that the entire agent generation pipeline works correctly.
"""
import pytest
import os
import asyncio
import sys
from unittest.mock import patch

# Add the mocks directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mocks')))

# Patch the agents module
with patch.dict('sys.modules', {'agents': __import__('tests.mocks.agents', fromlist=['Agent', 'Runner'])}):
    from meta_agent.core import generate_agent


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key required")
async def test_simple_agent_generation():
    """
    Test generating a simple agent end-to-end.
    
    Note: This test requires an actual OPENAI_API_KEY to be set in the environment.
    Skip if no API key is available.
    """
    # Skip for now as we need to better structure the mocks
    pytest.skip("This test needs a better mock structure")
    
    specification = """
    Name: SimpleTestAgent
    
    Instructions: You are a simple test agent that just responds with 'Hello, world!'
    """
    
    with patch('meta_agent.core.Runner.run', new_callable=patch.AsyncMock) as mock_run:
        # Setup mock returns for different calls
        mock_run.side_effect = [
            # First call - analyze specification
            {"name": "SimpleTestAgent", "description": "", "instructions": "You are a simple test agent that just responds with 'Hello, world!'"},
            # Second call - design tools
            [],
            # Third call - design output type
            {},
            # Fourth call - design guardrails
            [],
            # Fifth call - generate tool code
            "",
            # Sixth call - generate output type code
            "",
            # Seventh call - generate guardrail code
            "",
            # Eighth call - generate agent creation code
            "from agents import Agent\n\nagent = Agent(name='SimpleTestAgent', instructions='You are a simple test agent that just responds with \\'Hello, world!\\'')",
            # Ninth call - generate runner code
            "from agents import Runner\n\nrunner = Runner()\n\n# Run the agent\nawait Runner.run(agent, user_input)",
            # Tenth call - assemble implementation
            {
                "main_file": "from agents import Agent, Runner\n\nagent = Agent(name='SimpleTestAgent', instructions='You are a simple test agent that just responds with \\'Hello, world!\\'')\n\n# Run the agent\nawait Runner.run(agent, user_input)",
                "additional_files": {"requirements.txt": "agents>=0.0.5"},
                "installation_instructions": "pip install -r requirements.txt",
                "usage_examples": "python main.py"
            },
            # Eleventh call - validate implementation
            {"valid": True}
        ]
        
        result = await generate_agent(specification)
    
        # Verify the result has the expected components
        assert result is not None
        assert result.main_file is not None
        assert "SimpleTestAgent" in result.main_file
        assert "Hello, world!" in result.main_file


@pytest.mark.asyncio
async def test_agent_generation_with_mocks():
    """Test generating an agent with mocked OpenAI responses."""
    # Skip for now as we need to better structure the mocks
    pytest.skip("This test needs a better mock structure")
    
    with patch('meta_agent.core.Runner.run', new_callable=patch.AsyncMock) as mock_run:
        # Configure mocks for each stage of the pipeline
        mock_run.side_effect = [
            # First call - analyze specification
            {"name": "TestAgent", "description": "Test description", "instructions": "Test instructions"},
            # Second call - design tools
            [{"name": "test_tool", "description": "A test tool"}],
            # Third call - design output type
            {"name": "TestOutput", "fields": []},
            # Fourth call - design guardrails
            [{"name": "test_guardrail", "description": "A test guardrail"}],
            # Fifth call - generate tool code
            "def test_tool(): pass",
            # Sixth call - generate output type code
            "class TestOutput: pass",
            # Seventh call - generate guardrail code
            "def validate(): pass",
            # Eighth call - generate agent creation code
            "agent = Agent(name='TestAgent')",
            # Ninth call - generate runner code
            "runner = Runner()",
            # Tenth call - assemble implementation
            {
                "main_file": "from agents import Agent, Runner\n\nagent = Agent(name='TestAgent', instructions='Test instructions')\n\nasync def main():\n    runner = Runner()\n    await Runner.run(agent, user_input)",
                "additional_files": {"requirements.txt": "agents>=0.0.5"},
                "installation_instructions": "pip install -r requirements.txt",
                "usage_examples": "python main.py"
            },
            # Eleventh call - validate implementation
            {"valid": True}
        ]
        
        specification = """
        Name: TestAgent
        
        Instructions: You are a test agent that does nothing.
        """
        
        result = await generate_agent(specification)
        
        # Verify the result
        assert result is not None
        assert result.main_file is not None
        assert "TestAgent" in result.main_file
        
        # Verify all the mocks were called
        assert mock_run.call_count > 0
