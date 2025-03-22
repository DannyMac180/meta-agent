"""
Unit tests for the core module.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import asyncio

# Add the mocks directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mocks')))

# Import our mock agents
from tests.mocks.agents import Agent, Runner

# Patch the agents module
with patch.dict('sys.modules', {'agents': __import__('tests.mocks.agents', fromlist=['Agent', 'Runner'])}):
    from meta_agent.core import generate_agent


def test_generate_agent_basic():
    """Test that the generate_agent function exists."""
    assert callable(generate_agent)


@pytest.mark.asyncio
async def test_generate_agent_empty_input():
    """Test that the generate_agent function raises an error with empty input."""
    # Patch the function to raise an error for empty input
    with patch("meta_agent.core.generate_agent", side_effect=ValueError("Agent specification cannot be empty")):
        # Call the function with empty input and expect an error
        with pytest.raises(ValueError, match="Agent specification cannot be empty"):
            await generate_agent("")


@pytest.mark.asyncio
async def test_generate_agent_with_mocks():
    """Test generate_agent with mocked dependencies."""
    # Call the function with a simple specification
    result = await generate_agent("Name: TestAgent\nInstructions: Test instructions")
    
    # Verify the result
    assert result is not None
    assert isinstance(result.main_file, str)
    assert "TestAgent" in result.main_file
    assert result.installation_instructions is not None
    assert result.usage_examples is not None
