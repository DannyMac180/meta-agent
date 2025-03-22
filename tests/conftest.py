"""
Pytest configuration file with fixtures for testing the meta-agent.
"""
import os
import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

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
                    "content": "Test response content"
                },
                "finish_reason": "stop"
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
