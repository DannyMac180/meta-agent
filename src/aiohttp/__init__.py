class ClientSession:
    def __init__(self, *args, **kwargs):
        pass

    async def close(self) -> None:
        pass

    def post(self, *args, **kwargs):
        class _RespCtx:
            async def __aenter__(self_inner):
                return Response()

            async def __aexit__(self_inner, exc_type, exc, tb):
                pass

        return _RespCtx()


class TCPConnector:
    def __init__(self, *args, **kwargs):
        pass


class ClientError(Exception):
    """Base error class matching aiohttp's API."""


class ClientResponseError(ClientError):
    """Error raised for 5xx responses."""

    def __init__(self, *args, **kwargs):
        self.request_info = kwargs.get("request_info")
        self.history = kwargs.get("history")
        self.status = kwargs.get("status")
        self.message = kwargs.get("message")
        self.headers = kwargs.get("headers")
        super().__init__(self.message)


class Response:
    status = 200

    async def json(self):
        return {}

    async def text(self):
        return ""


class ClientError(Exception):
    """Placeholder for aiohttp.ClientError used in tests."""

    pass
