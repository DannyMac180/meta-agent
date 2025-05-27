import pytest
import aiohttp
from unittest.mock import AsyncMock, patch

from meta_agent.services.telemetry_client import TelemetryAPIClient, EndpointConfig


@pytest.mark.asyncio
async def test_send_success():
    with patch("aiohttp.ClientSession") as mock_session:
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={"ok": True})
        cm = AsyncMock()
        cm.__aenter__.return_value = response
        mock_session.return_value.post.return_value = cm
        mock_session.return_value.close = AsyncMock()
        client = TelemetryAPIClient({"trace": EndpointConfig("http://example.com")})
        result = await client.send("trace", {"data": 1})
        assert result == {"ok": True}
        await client.close()


@pytest.mark.asyncio
async def test_send_http_error():
    with patch("aiohttp.ClientSession") as mock_session:
        resp = AsyncMock()
        resp.status = 500
        resp.text = AsyncMock(return_value="bad")
        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        mock_session.return_value.post.return_value = cm
        mock_session.return_value.close = AsyncMock()
        client = TelemetryAPIClient({"trace": EndpointConfig("http://example.com")})
        with pytest.raises(aiohttp.ClientResponseError):
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


@pytest.mark.asyncio
async def test_send_retry_success():
    with patch("aiohttp.ClientSession") as mock_session:
        resp1 = AsyncMock()
        resp1.status = 500
        resp1.text = AsyncMock(return_value="bad")
        cm1 = AsyncMock()
        cm1.__aenter__.return_value = resp1

        resp2 = AsyncMock()
        resp2.status = 200
        resp2.json = AsyncMock(return_value={"ok": True})
        cm2 = AsyncMock()
        cm2.__aenter__.return_value = resp2

        mock_session.return_value.post.side_effect = [cm1, cm2]
        mock_session.return_value.close = AsyncMock()

        client = TelemetryAPIClient(
            {"trace": EndpointConfig("http://example.com")}, retries=1, backoff=0
        )
        result = await client.send("trace", {"d": 1})
        assert result == {"ok": True}
        assert mock_session.return_value.post.call_count == 2
        await client.close()


@pytest.mark.asyncio
async def test_send_retry_failure():
    with patch("aiohttp.ClientSession") as mock_session:
        resp = AsyncMock()
        resp.status = 500
        resp.text = AsyncMock(return_value="bad")
        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        mock_session.return_value.post.return_value = cm
        mock_session.return_value.close = AsyncMock()

        client = TelemetryAPIClient(
            {"trace": EndpointConfig("http://example.com")}, retries=1, backoff=0
        )
        with pytest.raises(Exception):
            await client.send("trace", {"d": 1})
        assert mock_session.return_value.post.call_count == 2
        await client.close()
