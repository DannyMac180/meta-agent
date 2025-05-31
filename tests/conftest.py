import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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
