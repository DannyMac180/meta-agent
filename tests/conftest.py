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


# Always provide a lightweight OpenAI stub to avoid dependency issues during collection.
class _OpenAIError(Exception):
    """Base class for OpenAI error stubs."""


class AuthenticationError(_OpenAIError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args)


class APIConnectionError(_OpenAIError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args)


class APITimeoutError(_OpenAIError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args)


openai_stub = SimpleNamespace(
    OpenAI=MagicMock(),
    AuthenticationError=AuthenticationError,
    APIConnectionError=APIConnectionError,
    APITimeoutError=APITimeoutError,
)
sys.modules.setdefault("openai", openai_stub)
