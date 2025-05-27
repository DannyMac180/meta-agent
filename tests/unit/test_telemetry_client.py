import pytest
from unittest.mock import AsyncMock, patch

from meta_agent.services.telemetry_client import TelemetryAPIClient, EndpointConfig


@pytest.fixture
async def telemetry_client():
    with patch("aiohttp.ClientSession") as mock_session:
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={"ok": True})
        cm = AsyncMock()
        cm.__aenter__.return_value = response
        mock_session.return_value.post.return_value = cm
        client = TelemetryAPIClient({"trace": EndpointConfig("http://example.com")})
        try:
            yield client
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_send_success(telemetry_client):
    result = await telemetry_client.send("trace", {"data": 1})
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_send_http_error():
    with patch("aiohttp.ClientSession") as mock_session:
        resp = AsyncMock()
        resp.status = 500
        resp.text = AsyncMock(return_value="bad")
        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        mock_session.return_value.post.return_value = cm
        client = TelemetryAPIClient({"trace": EndpointConfig("http://example.com")})
        with pytest.raises(ValueError):
            await client.send("trace", {"d": 1})
        await client.close()


@pytest.mark.asyncio
async def test_attach_runner(monkeypatch):
    # Fake runner class
    class FakeRunner:
        async def run(self, *_, **__):
            class Res:
                span_graph = {"span": 1}

            return Res()

    client = TelemetryAPIClient({"trace": EndpointConfig("http://example.com")})
    send_mock = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(client, "send", send_mock)

    client.attach_runner(FakeRunner, "trace")
    res = await FakeRunner().run(None)
    assert hasattr(res, "span_graph")
    send_mock.assert_awaited_once_with("trace", {"span": 1})
    await client.close()
