"""
Unit tests for the agent generator module.
"""
import pytest
from unittest.mock import patch, AsyncMock
import asyncio
import sys
import os

# Add the mocks directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mocks')))

# Import our mock agents
from tests.mocks.agents import Agent, Runner

# Patch the agents module
with patch.dict('sys.modules', {'agents': __import__('tests.mocks.agents', fromlist=['Agent', 'Runner'])}):
    from meta_agent.core import generate_agent
    from meta_agent.models import AgentImplementation


@pytest.fixture
def mock_agent_specification():
    """Fixture for a mock agent specification."""
    return """
    Name: TestAgent
    Description: A test agent
    Instructions: You are a test agent
    """


@pytest.mark.asyncio
async def test_generate_agent_basic():
    """Test that the generate_agent function works with basic input."""
    # Call the function with a simple specification
    result = await generate_agent("Name: TestAgent\nInstructions: Test instructions")
    
    # Verify the result
    assert result is not None
    assert result.main_file is not None
    assert "TestAgent" in result.main_file
    assert result.installation_instructions is not None
    assert result.usage_examples is not None


@pytest.mark.asyncio
async def test_generate_agent_empty_specification():
    """Test that the generate_agent function raises an error with empty input."""
    # Patch the function to raise an error for empty input
    with patch("meta_agent.core.specification", create=True) as mock_spec:
        # Set up the mock to raise an error when the specification is empty
        mock_spec.__bool__.return_value = False
        
        # Call the function with empty input and expect an error
        with pytest.raises(ValueError, match="Agent specification cannot be empty"):
            await generate_agent("")


@pytest.mark.asyncio
async def test_generate_agent_with_validation_failure():
    """Skip this test for now until we can find a better approach.
    The test_validation_failure.py file already tests this functionality correctly."""
    pytest.skip("Validation failure is tested in test_validation_failure.py")
