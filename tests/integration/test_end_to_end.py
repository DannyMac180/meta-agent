"""
Integration tests for the meta-agent package.

These tests verify that the entire agent generation pipeline works correctly.
"""
import pytest
import os, sys
import asyncio
import json
from unittest.mock import patch, AsyncMock

# Import the function to test
from meta_agent.core import generate_agent
from meta_agent.models import AgentImplementation
# Import the actual Runner to mock its method
from agents import Runner


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key required")
async def test_simple_agent_generation():
    """
    Test generating a simple agent end-to-end.

    Note: This test requires an actual OPENAI_API_KEY to be set in the environment.
    Skip if no API key is available.
    """
    # This test now runs against the actual OpenAI API if the key is present.
    # It uses the real tools and the real meta-agent.

    specification = """
    Name: E2ESimpleAgent

    Description: A very simple agent for end-to-end testing.
    Instructions: You are a simple test agent that just responds with 'Hello, world!'
    """
    
    try:
        # No mocking here, call the actual function
        result = await generate_agent(specification)

        # Verify the result structure and basic content
        assert result is not None
        assert isinstance(result, AgentImplementation)
        assert result.main_file is not None
        assert "E2ESimpleAgent" in result.main_file  # Check name
        assert "Hello, world!" in result.main_file  # Check instructions made it
        assert "async def main():" in result.main_file  # Check runner code
        assert "requirements.txt" in result.additional_files
        assert "openai-agents>=0.0.7" in result.additional_files["requirements.txt"]

    except Exception as e:
        pytest.fail(f"End-to-end agent generation failed: {e}")


@pytest.mark.asyncio
@patch('meta_agent.core.Runner.run', new_callable=AsyncMock)  # Patch the actual Runner used in core.py
async def test_agent_generation_with_mocks(mock_run, mock_runner_results):
    """Test generating an agent with mocked OpenAI responses."""
    # This test uses the mocked runner results provided by the fixture

    # Configure the mock side effect using the fixture
    mock_run.side_effect = mock_runner_results

    specification = """
    Name: TestAgent
    Description: A test agent
    Instructions: You are a test agent
    Tools needed:
    1. test_tool: Does something
    Output type: TestOutput
    """

    try:
        result = await generate_agent(specification)

        # Verify the result
        assert result is not None
        assert isinstance(result, AgentImplementation)
        assert result.main_file is not None
        assert "TestAgent" in result.main_file

        # Verify all the mocks were called
        assert mock_run.call_count == len(mock_runner_results)

    except Exception as e:
        pytest.fail(f"Mocked agent generation failed: {e}")
