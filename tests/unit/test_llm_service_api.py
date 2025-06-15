"""
Unit tests for the LLMService _call_llm_api method.
"""

import pytest
from unittest.mock import patch, MagicMock
from meta_agent.services.llm_service import LLMService
import openai


class TestLLMServiceAPI:
    """Tests for the LLMService _call_llm_api method."""

    @pytest.fixture
    def service(self):
        """Fixture for an LLMService instance."""
        return LLMService(api_key="test_key", model="test_model")

    @pytest.fixture
    def mock_openai_response(self):
        """Fixture for a mock OpenAI API response."""
        mock = MagicMock()
        mock.model_dump.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "```python\ndef test_function():\n    return 'Hello, World!'\n```"
                    }
                }
            ]
        }
        return mock

    @pytest.mark.asyncio
    async def test_call_llm_api_success(self, service, mock_openai_response):
        """Test successful API call."""
        # Mock the OpenAI client's chat.completions.create method
        with patch.object(service.client.chat.completions, 'create', return_value=mock_openai_response):
            # Call the method
            result = await service._call_llm_api("Generate a test function", {})

            # Check that the OpenAI client was called correctly
            service.client.chat.completions.create.assert_called_once()
            call_args = service.client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'test_model'
            assert call_args[1]['max_completion_tokens'] == 2000
            assert len(call_args[1]['messages']) >= 2  # System and user messages
            
            # Check the result
            assert result == mock_openai_response.model_dump.return_value

    @pytest.mark.asyncio
    async def test_call_llm_api_with_context(self, service, mock_openai_response):
        """Test API call with context."""
        # Mock the OpenAI client's chat.completions.create method
        with patch.object(service.client.chat.completions, 'create', return_value=mock_openai_response):
            # Call the method with context
            context = {
                "tool_purpose": "Test function",
                "constraints": ["No side effects"],
            }
            result = await service._call_llm_api("Generate a test function", context)

            # Check that the OpenAI client was called correctly
            service.client.chat.completions.create.assert_called_once()
            call_args = service.client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # Check that context was included (should be at least 3 messages: system, context, user)
            assert len(messages) >= 3
            
            # Check that user message is present
            user_message = None
            for msg in messages:
                if msg["role"] == "user":
                    user_message = msg
                    break
            assert user_message is not None
            assert user_message["content"] == "Generate a test function"
            
            # Check the result
            assert result == mock_openai_response.model_dump.return_value

    @pytest.mark.asyncio
    async def test_call_llm_api_error_response(self, service):
        """Test API call with error response."""
        # Mock the OpenAI client to raise an authentication error
        with patch.object(service.client.chat.completions, 'create', side_effect=openai.AuthenticationError("Invalid API key", response=MagicMock(), body=None)):
            # Call the method and expect an exception
            with pytest.raises(openai.AuthenticationError):
                await service._call_llm_api("Generate a test function", {})

    @pytest.mark.asyncio
    async def test_call_llm_api_network_error(self, service):
        """Test API call with network error."""
        # Mock the OpenAI client to raise a connection error
        with patch.object(service.client.chat.completions, 'create', side_effect=openai.APIConnectionError(request=MagicMock())):
            # Call the method and expect an exception
            with pytest.raises(openai.APIConnectionError):
                await service._call_llm_api("Generate a test function", {})

    @pytest.mark.asyncio
    async def test_call_llm_api_timeout(self, service):
        """Test API call with timeout."""
        # Mock the OpenAI client to raise a timeout error
        with patch.object(service.client.chat.completions, 'create', side_effect=openai.APITimeoutError(request=MagicMock())):
            # Call the method and expect an exception
            with pytest.raises(openai.APITimeoutError):
                await service._call_llm_api("Generate a test function", {})