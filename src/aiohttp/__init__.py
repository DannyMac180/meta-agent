class ClientError(Exception):
    pass


class TCPConnector:
    def __init__(self, *_, **__):
        pass


class ClientSession:
    def __init__(self, *_, **__):
        pass

    async def post(self, *_args, **_kwargs):
        raise NotImplementedError("aiohttp is required for network access")

    async def close(self) -> None:
        pass
