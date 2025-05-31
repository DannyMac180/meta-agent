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
