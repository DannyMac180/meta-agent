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


class Response:
    status = 200

    async def json(self):
        return {}

    async def text(self):
        return ""
