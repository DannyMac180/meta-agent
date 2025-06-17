import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import builtins

# Store original import function
_original_import = builtins.__import__

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

# Create comprehensive mock structure that mimics OpenAI SDK
import typing

class MockGeneric:
    """Mock for typing.Generic that handles parametrization"""
    def __class_getitem__(cls, item):
        return cls
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
    
    def __getattr__(self, name):
        return MagicMock()

# Create type variables for generic mock classes
T = typing.TypeVar('T')

# Create mock classes that properly handle parametrization
class MockParsedChatCompletionMessage(typing.Generic[T]):
    """Mock for ParsedChatCompletionMessage that handles parametrization"""
    
    def __class_getitem__(cls, item):
        # Return the same class for any parametrization
        return cls
    
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return MagicMock()
    
    @classmethod
    def __instancecheck__(cls, instance):
        return True
    
    @classmethod 
    def __subclasscheck__(cls, subclass):
        return True

class MockChatCompletionMessage(typing.Generic[T]):
    """Mock for ChatCompletionMessage that handles parametrization"""
    
    def __class_getitem__(cls, item):
        # Return the same class for any parametrization
        return cls
    
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return MagicMock()
    
    @classmethod
    def __instancecheck__(cls, instance):
        return True
    
    @classmethod 
    def __subclasscheck__(cls, subclass):
        return True

# Create the complete module hierarchy
mock_parsed_chat_completion = MagicMock()
mock_parsed_chat_completion.ParsedChatCompletionMessage = MockParsedChatCompletionMessage

mock_chat_completion = MagicMock()
mock_chat_completion.ChatCompletionMessage = MockChatCompletionMessage

mock_chat = MagicMock()
mock_chat.parsed_chat_completion = mock_parsed_chat_completion
mock_chat.chat_completion = mock_chat_completion
mock_chat.chat_completion_message = mock_chat_completion

mock_types = MagicMock()
mock_types.chat = mock_chat

# Mock the OpenAI client and related classes
class MockOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = MagicMock()

openai_mock = MagicMock()
openai_mock.OpenAI = MockOpenAI
openai_mock.OpenAIError = MockOpenAIError
openai_mock.APIError = MockAPIError
openai_mock.AuthenticationError = MockAuthenticationError
openai_mock.APIConnectionError = MockAPIConnectionError
openai_mock.APITimeoutError = MockAPITimeoutError
openai_mock.RateLimitError = MockRateLimitError
openai_mock.types = mock_types

# Mock the submodules to prevent real imports
openai_types_mock = MagicMock()
openai_types_mock.chat = mock_chat
sys.modules.setdefault("openai.types", openai_types_mock)
sys.modules.setdefault("openai.types.chat", mock_chat)
sys.modules.setdefault("openai.types.chat.parsed_chat_completion", mock_parsed_chat_completion)
sys.modules.setdefault("openai.types.chat.chat_completion", mock_chat_completion)
sys.modules.setdefault("openai.types.chat.chat_completion_message", mock_chat_completion)

# Don't install the import hook by default - let pytest handle it
# The comprehensive sys.modules registration should be sufficient

# Register mock so that `import openai` works anywhere in the codebase
# Use mock by default, but allow integration tests to override it
sys.modules.setdefault("openai", openai_mock)

# Aggressively register all possible OpenAI module paths
sys.modules.setdefault("openai.types", openai_types_mock)
sys.modules.setdefault("openai.types.chat", mock_chat)
sys.modules.setdefault("openai.types.chat.parsed_chat_completion", mock_parsed_chat_completion)
sys.modules.setdefault("openai.types.chat.chat_completion", mock_chat_completion)
sys.modules.setdefault("openai.types.chat.chat_completion_message", mock_chat_completion)

# Also register common import variations
sys.modules.setdefault("openai._models", MagicMock())
sys.modules.setdefault("openai._compat", MagicMock())
sys.modules.setdefault("openai.BaseModel", MagicMock())

# (Nothing else changes below)