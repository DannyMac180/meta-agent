class DockerException(Exception):
    pass

class ImageNotFound(DockerException):
    pass

class APIError(DockerException):
    pass

class NotFound(DockerException):
    pass

class _Errors:
    DockerException = DockerException
    ImageNotFound = ImageNotFound
    APIError = APIError
    NotFound = NotFound

errors = _Errors()

def from_env():
    raise DockerException("Docker not available in test environment")
