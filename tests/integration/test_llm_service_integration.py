import os
import socket

import pytest
from meta_agent.services.llm_service import LLMService


def internet_available() -> bool:
    try:
        socket.create_connection(("api.openai.com", 443), timeout=1).close()
        return True
    except OSError:
        return False


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set in environment for integration test",
)
@pytest.mark.skipif(
    not internet_available(),
    reason="Network not available for integration test",
)
@pytest.mark.asyncio
async def test_llm_service_live_api_call():
    """Tests that LLMService can make a successful live API call.

    This test relies on the OPENAI_API_KEY environment variable being set.
    It uses the default model and API base configured in LLMService.
    """
    try:
        # LLMService will attempt to load the API key from .env or environment
        service = LLMService()
    except ValueError as e:
        pytest.fail(
            f"Failed to initialize LLMService, API key likely missing or invalid: {e}"
        )

    simple_prompt = "Say hello in one sentence."
    context = {}

    try:
        code_response = await service.generate_code(simple_prompt, context)

        assert isinstance(code_response, str), "Response should be a string"
        assert len(code_response.strip()) > 0, "Response string should not be empty"
        # We are not asserting the *content* of the response, just that we got one.
        print(
            f"Successfully received response from LLMService: {code_response[:100]}..."
        )

    except Exception as e:
        pytest.fail(
            f"LLMService.generate_code failed with an unexpected exception: {e}"
        )


# To run this test specifically (ensure .env or OPENAI_API_KEY is set):
# uv pip install -r uv.lock --extra test && pytest tests/integration/test_llm_service_integration.py
