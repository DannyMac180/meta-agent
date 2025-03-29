"""
Unit tests for the core module.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import asyncio
import json  # Import json

# Add the mocks directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mocks')))

# Import our mock agents
from tests.mocks.agents import Agent, Runner

# Patch the agents module
with patch.dict('sys.modules', {'agents': __import__('tests.mocks.agents', fromlist=['Agent', 'Runner'])}):
    from meta_agent.core import generate_agent

# Import the actual Runner to mock its method
from agents import Runner

# Import the function to test
from meta_agent.models import AgentImplementation  # Add this import


def test_generate_agent_basic():
    """Test that the generate_agent function exists."""
    assert callable(generate_agent)


@pytest.mark.asyncio
async def test_generate_agent_empty_input():
    """Test that the generate_agent function raises an error with empty input."""
    # The check is now at the beginning of the function
    with pytest.raises(ValueError, match="Agent specification cannot be empty"):
        await generate_agent("")

    with pytest.raises(ValueError, match="Agent specification cannot be empty"):
        await generate_agent("   ")


@pytest.mark.asyncio
@patch.object(Runner, 'run')
async def test_generate_agent_with_mocks(mock_run, mock_runner_results):
    """Test generate_agent with mocked dependencies."""
    # Setup the mock to return values from mock_runner_results
    mock_run.side_effect = mock_runner_results

    # Call the function with a simple specification
    result = await generate_agent("Name: TestAgent\nInstructions: Test instructions")

    # Verify the result
    assert result is not None
    assert isinstance(result, AgentImplementation)
    assert isinstance(result.main_file, str)
    assert "TestAgent" in result.main_file  # Check if agent name appears in assembled code
    assert result.installation_instructions is not None
    assert result.usage_examples is not None

    # Check that the mock runner was called multiple times (once per step)
    mock_run.assert_called()
    assert mock_run.call_count == len(mock_runner_results)  # Should match number of steps
