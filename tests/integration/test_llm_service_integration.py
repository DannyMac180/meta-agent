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
    
    # Store the original OpenAI mock and replace it with the real one
    original_openai = sys.modules.get('openai')
    
    # Remove the OpenAI mock and force reload the real openai package
    if 'openai' in sys.modules:
        del sys.modules['openai']
    
    # Try to import the real openai package
    real_openai = None
    try:
        import openai as real_openai
        sys.modules['openai'] = real_openai
        # Also need to reload the llm_service module to pick up the real openai
        if 'meta_agent.services.llm_service' in sys.modules:
            del sys.modules['meta_agent.services.llm_service']
    except ImportError:
        # If real openai is not available, restore the mock
        if original_openai:
            sys.modules['openai'] = original_openai
    
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
    
    # Restore the original OpenAI module (mock)
    if original_openai:
        sys.modules['openai'] = original_openai
    
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
    # Import the real OpenAI client directly and patch it into LLMService
    try:
        # Remove mock if it exists and import real openai
        if 'openai' in sys.modules:
            mock_openai = sys.modules['openai']
            del sys.modules['openai']
        
        # Import real OpenAI
        import openai as real_openai
        
        # Create a fresh instance of LLMService for this test
        # This ensures we're not affected by any mocking or state changes from other tests
        try:
            # LLMService will attempt to load the API key from .env or environment
            service = LLMService()
            
            # Replace the client with a real OpenAI client
            service.client = real_openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            logger.info("Successfully created LLMService instance")
        except ValueError as e:
            pytest.fail(
                f"Failed to initialize LLMService, API key likely missing or invalid: {e}"
            )
        
    except ImportError as e:
        pytest.skip(f"Real OpenAI package not available: {e}")
    finally:
        # Restore mock for other tests
        if 'mock_openai' in locals():
            sys.modules['openai'] = mock_openai

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
