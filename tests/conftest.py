import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# Ensure src directory is on path so local plugins can load
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

pytest_plugins = ["pytest_mock"]

docker_mock = MagicMock()
docker_mock.errors = SimpleNamespace(
    DockerException=Exception,
    APIError=Exception,
    ImageNotFound=Exception,
    NotFound=Exception,
)
# Provide from_env to be patched later in tests
docker_mock.from_env = MagicMock()

sys.modules.setdefault("docker", docker_mock)

# ---------------------------
# Mock the OpenAI SDK if it is not installed
# ---------------------------

# Create proper exception classes that inherit from their respective base exceptions
class MockOpenAIError(Exception):
    pass

class MockAPIError(MockOpenAIError):
    def __init__(self, message="API Error", response=None, body=None):
        super().__init__(message)
        self.response = response
        self.body = body

class MockAuthenticationError(MockAPIError):
    def __init__(self, message="Authentication Error", response=None, body=None):
        super().__init__(message)
        self.response = response
        self.body = body

class MockAPIConnectionError(MockOpenAIError):
    def __init__(self, request=None):
        super().__init__("Connection Error")
        self.request = request

class MockAPITimeoutError(MockOpenAIError):
    def __init__(self, request=None):
        super().__init__("Timeout Error")
        self.request = request

class MockRateLimitError(MockAPIError):
    def __init__(self, message="Rate Limit Error", response=None, body=None):
        super().__init__(message)
        self.response = response
        self.body = body

openai_mock = MagicMock()
openai_mock.OpenAIError = MockOpenAIError
openai_mock.APIError = MockAPIError
openai_mock.AuthenticationError = MockAuthenticationError
openai_mock.APIConnectionError = MockAPIConnectionError
openai_mock.APITimeoutError = MockAPITimeoutError
openai_mock.RateLimitError = MockRateLimitError

# Register mock so that `import openai` works anywhere in the codebase
# Use mock by default, but allow integration tests to override it
sys.modules.setdefault("openai", openai_mock)

# (Nothing else changes below)