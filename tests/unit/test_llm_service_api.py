"""
Unit tests for the LLMService _call_llm_api method.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock

import aiohttp
import asyncio
from meta_agent.services.llm_service import LLMService


class TestLLMServiceAPI:
    """Tests for the LLMService _call_llm_api method."""

    @pytest.fixture
    def service(self):
        """Fixture for an LLMService instance."""
        return LLMService(api_key="test_key", model="test_model")

    @pytest.fixture
    def mock_response(self):
        """Fixture for a mock aiohttp response."""
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(
            return_value={
                "output": {
                    "content": "```python\ndef test_function():\n    return 'Hello, World!'\n```"
                }
            }
        )
        mock.text = AsyncMock(return_value="")
        return mock

    @pytest.fixture
    def mock_session(self):
        """Fixture for a mock aiohttp.ClientSession."""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_call_llm_api_success(self, service, mock_response, mock_session):
        """Test successful API call."""
        # Configure the mock session
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_session.post.return_value = mock_context_manager

        # Patch aiohttp.ClientSession to return our mock
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Call the method
            result = await service._call_llm_api("Generate a test function", {})

            # Check that the session was used correctly
            mock_session.post.assert_called_once()
            args, kwargs = mock_session.post.call_args
            assert args[0] == service.api_base
            assert "headers" in kwargs
            assert "json" in kwargs
            assert "timeout" in kwargs
            assert kwargs["timeout"] == service.timeout

            # Check the payload
            payload = kwargs["json"]
            assert payload["model"] == service.model
            assert isinstance(payload["input"], list)
            assert len(payload["input"]) >= 1
            assert payload["input"][-1]["role"] == "user"
            assert payload["input"][-1]["content"] == "Generate a test function"

            # Check the result
            assert result == mock_response.json.return_value

    @pytest.mark.asyncio
    async def test_call_llm_api_with_context(
        self, service, mock_response, mock_session
    ):
        """Test API call with context."""
        # Configure the mock session
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_session.post.return_value = mock_context_manager

        # Patch aiohttp.ClientSession to return our mock
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Call the method with context
            context = {
                "tool_purpose": "Test function",
                "constraints": ["No side effects"],
            }
            result = await service._call_llm_api("Generate a test function", context)

            # Check the payload
            args, kwargs = mock_session.post.call_args
            payload = kwargs["json"]

            # Check that the context was included in the messages
            messages = payload["input"]
            assert len(messages) >= 2  # At least system + user message

            # Find the context message
            context_message = None
            for msg in messages:
                if msg["role"] == "system" and "context" in msg["content"].lower():
                    context_message = msg
                    break

            assert context_message is not None
            assert "tool_purpose" in context_message["content"]
            assert "constraints" in context_message["content"]

    @pytest.mark.asyncio
    async def test_call_llm_api_error_response(self, service, mock_session):
        """Test API call with error response."""
        # Configure the mock response for an error
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")

        # Configure the mock session
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_session.post.return_value = mock_context_manager

        # Patch aiohttp.ClientSession to return our mock
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Call the method and expect an exception
            with pytest.raises(ValueError) as excinfo:
                await service._call_llm_api("Generate a test function", {})

            # Check the exception message
            assert "API error: 400" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_call_llm_api_network_error(self, service):
        """Test API call with network error."""
        # Patch aiohttp.ClientSession to raise an exception
        with patch(
            "aiohttp.ClientSession", side_effect=aiohttp.ClientError("Connection error")
        ):
            # Call the method and expect an exception
            with pytest.raises(aiohttp.ClientError) as excinfo:
                await service._call_llm_api("Generate a test function", {})

            # Check the exception message
            assert "Connection error" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_call_llm_api_timeout(self, service, mock_session):
        """Test API call with timeout."""
        # Configure the mock session to raise a timeout
        mock_session.post.side_effect = asyncio.TimeoutError("Request timed out")

        # Patch aiohttp.ClientSession to return our mock
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Call the method and expect an exception
            with pytest.raises(asyncio.TimeoutError) as excinfo:
                await service._call_llm_api("Generate a test function", {})

            # Check the exception message
            assert "Request timed out" in str(excinfo.value)
