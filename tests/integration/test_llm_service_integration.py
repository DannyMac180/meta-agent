import os
import socket
import logging
import pytest
import sys

from meta_agent.services.llm_service import LLMService

# Configure logging for this test module
logger = logging.getLogger(__name__)

# Module-level setup and teardown to ensure clean state
@pytest.fixture(scope="module", autouse=True)
def ensure_clean_state():
    """Ensure clean state before and after running tests in this module.
    
    This fixture runs automatically for all tests in this module and ensures
    that any global state or mocks that might affect LLMService are reset.
    """
    # Store original sys.modules entries that we care about
    original_modules = {}
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('meta_agent.services'):
            original_modules[module_name] = sys.modules.get(module_name)
    
    # Store original environment variables
    original_env = os.environ.copy()
    
    # Yield control to the tests
    yield
    
    # Restore original modules to undo any monkey patching
    for module_name, module in original_modules.items():
        if module is None:
            if module_name in sys.modules:
                del sys.modules[module_name]
        else:
            sys.modules[module_name] = module
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)


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
    # Create a fresh instance of LLMService for this test
    # This ensures we're not affected by any mocking or state changes from other tests
    try:
        # LLMService will attempt to load the API key from .env or environment
        service = LLMService()
        logger.info("Successfully created LLMService instance")
    except ValueError as e:
        pytest.fail(
            f"Failed to initialize LLMService, API key likely missing or invalid: {e}"
        )

    simple_prompt = "Say hello in one sentence."
    context = {}

    try:
        # Add debug logging to see what's happening
        logger.info(f"Sending prompt to LLM: {simple_prompt}")
        code_response = await service.generate_code(simple_prompt, context)

        # Log the response for debugging
        logger.info(f"Received response from LLM: {code_response[:100]}...")

        assert isinstance(code_response, str), "Response should be a string"
        assert len(code_response.strip()) > 0, "Response string should not be empty"
        # We are not asserting the *content* of the response, just that we got one.
        print(
            f"Successfully received response from LLMService: {code_response[:100]}..."
        )

    except Exception as e:
        # Get more detailed error information
        error_type = type(e).__name__
        error_message = str(e)
        
        # Log the error details
        logger.error(f"Error type: {error_type}")
        logger.error(f"Error message: {error_message}")
        
        # Include the exception traceback in the failure message
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Traceback: {tb}")
        
        pytest.fail(
            f"LLMService.generate_code failed with an unexpected exception ({error_type}): {error_message}"
        )


# To run this test specifically (ensure .env or OPENAI_API_KEY is set):
# uv pip install -r uv.lock --extra test && pytest tests/integration/test_llm_service_integration.py
