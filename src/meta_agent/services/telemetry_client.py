"""Telemetry API client and tracing integration utilities."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class EndpointConfig:
    """Configuration for a telemetry API endpoint."""

    url: str
    auth_token: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.auth_token:
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
        self.headers.setdefault("Content-Type", "application/json")


class TelemetryAPIClient:
    """Simple async client for posting telemetry data to multiple endpoints.

    Parameters
    ----------
    endpoints:
        Mapping of endpoint names to :class:`EndpointConfig` objects. Each
        endpoint must specify the full URL for posting telemetry data.
    rate_limit:
        Maximum number of concurrent requests allowed. This acts as a basic
        rate limiter when sending many events quickly.
    timeout:
        Request timeout in seconds.
    """

    def __init__(
        self,
        endpoints: Dict[str, EndpointConfig],
        *,
        rate_limit: int = 5,
        timeout: int = 10,
    ) -> None:
        if not endpoints:
            raise ValueError("At least one endpoint must be configured")
        self.endpoints = endpoints
        self.timeout = timeout
        self._sem = asyncio.Semaphore(rate_limit)
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=None)
        )

    async def send(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Post ``payload`` to the endpoint identified by ``name``."""
        if name not in self.endpoints:
            raise ValueError(f"Unknown endpoint '{name}'")
        cfg = self.endpoints[name]
        async with self._sem:
            async with self._session.post(
                cfg.url,
                json=payload,
                headers=cfg.headers,
                timeout=self.timeout,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(f"API error: {resp.status} - {text}")
                return await resp.json()

    async def close(self) -> None:
        """Close the underlying HTTP session."""
      
        await self._session.close()


    # --- Runner integration -------------------------------------------------

    def attach_runner(self, runner_cls: Any, endpoint: str = "traces") -> None:
        """Patch ``runner_cls.run`` to send span data to ``endpoint``.

        The patched ``run`` method forwards all arguments to the original
        implementation, awaits the result, and if the result object exposes a
        ``span_graph``/``spans``/``trace`` attribute, it will be posted to the
        configured telemetry endpoint using :meth:`send`.
        """

        orig_run = getattr(runner_cls, "run")

        async def wrapped_run(*args: Any, **kwargs: Any) -> Any:
            result = await orig_run(*args, **kwargs)
            span_data = (
                getattr(result, "span_graph", None)
                or getattr(result, "spans", None)
                or getattr(result, "trace", None)
            )
            if span_data is not None:
                try:
                    await self.send(endpoint, span_data)  # type: ignore[arg-type]
                except Exception as exc:  # pragma: no cover - log only
                    logger.error("Failed to send telemetry: %s", exc)
            return result

        setattr(runner_cls, "run", wrapped_run)
        runner_cls._meta_agent_orig_run = orig_run  # type: ignore[attr-defined]

    def detach_runner(self, runner_cls: Any) -> None:
        """Restore ``runner_cls.run`` if it was patched by :meth:`attach_runner`."""
        orig = getattr(runner_cls, "_meta_agent_orig_run", None)
        if orig:
            setattr(runner_cls, "run", orig)
            delattr(runner_cls, "_meta_agent_orig_run")
