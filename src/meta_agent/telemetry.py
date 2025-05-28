from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


from .telemetry_db import TelemetryDB


class TelemetryCollector:
    """Collect basic usage metrics for a generation run."""

    COST_TABLE: Dict[str, float] = {
        "o3": 0.01,
        "o4-mini-high": 0.02,
        "gpt-4o": 0.03,
        "default": 0.01,
    }

    class Severity(str, Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"

    class Category(str, Enum):
        COST_CONTROL = "cost_control"
        GUARDRAIL = "guardrail"
        EXECUTION = "execution"
        INTERNAL = "internal"

    @dataclass
    class Event:
        category: "TelemetryCollector.Category"
        severity: "TelemetryCollector.Severity"
        message: str

    def __init__(
        self,
        cost_cap: float = 0.5,
        *,
        db: TelemetryDB | None = None,
        include_sensitive: bool = True,
    ) -> None:
        self.cost_cap = cost_cap
        self.token_count = 0
        self.cost = 0.0
        self.guardrail_hits = 0
        self.latency = 0.0
        self._start: Optional[float] = None
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.include_sensitive = include_sensitive
        self.events: List[TelemetryCollector.Event] = []

    def record_event(
        self,
        category: "TelemetryCollector.Category",
        message: str,
        severity: "TelemetryCollector.Severity" = Severity.ERROR,
    ) -> None:
        """Record an informational or error event."""
        self.events.append(
            TelemetryCollector.Event(
                category=category,
                severity=severity,
                message=message,
            )
        )
        log = self.logger.info
        if severity in (self.Severity.ERROR, self.Severity.CRITICAL):
            log = self.logger.error
        elif severity is self.Severity.WARNING:
            log = self.logger.warning
        log(message)

    # --- Timing -----------------------------------------------------
    def start_timer(self) -> None:
        """Start the latency timer."""
        self._start = time.perf_counter()

    def stop_timer(self) -> None:
        """Stop the latency timer and accumulate duration."""
        if self._start is not None:
            self.latency += time.perf_counter() - self._start
            self._start = None
        if self.db:
            self.db.record(
                self.token_count,
                self.cost,
                self.latency,
                self.guardrail_hits,
            )

    # --- Usage ------------------------------------------------------
    def add_usage(
        self, prompt_tokens: int, response_tokens: int, model: str = "default"
    ) -> None:
        """Record token usage and update cost."""
        tokens = prompt_tokens + response_tokens
        self.token_count += tokens
        rate = self.COST_TABLE.get(model, self.COST_TABLE["default"])
        self.cost += rate * tokens / 1000.0
        ratio = self.cost / self.cost_cap if self.cost_cap > 0 else 0
        eps = 1e-6
        if ratio >= 1.0 - eps:
            self.record_event(
                self.Category.COST_CONTROL,
                f"Cost cap exceeded: ${self.cost:.2f} >= ${self.cost_cap:.2f}",
                severity=self.Severity.CRITICAL,
            )
            raise RuntimeError("cost cap exceeded")
        elif ratio >= 0.9 - eps:
            self.record_event(
                self.Category.COST_CONTROL,
                "90% of cost cap reached",
                severity=self.Severity.ERROR,
            )
        elif ratio >= 0.75 - eps:
            self.record_event(
                self.Category.COST_CONTROL,
                "75% of cost cap reached",
                severity=self.Severity.WARNING,
            )

    def increment_guardrail_hits(self) -> None:
        """Increment guardrail hit counter and record an event."""
        self.guardrail_hits += 1
        self.record_event(
            self.Category.GUARDRAIL,
            "guardrail violation",
            severity=self.Severity.WARNING,
        )

    # --- Summary ----------------------------------------------------
    def summary_line(self, metrics: Optional[List[str]] | None = None) -> str:
        """Return a one-line summary of selected metrics.

        Parameters
        ----------
        metrics:
            Iterable of metric names to include. Supported values are
            ``"cost"``, ``"tokens"``, ``"latency"`` and ``"guardrails"``.
            When ``None`` all metrics are displayed.
        """

        metrics = metrics or ["cost", "tokens", "latency", "guardrails"]
        parts: List[str] = []
        for m in metrics:
            if m == "cost":
                cost = f"${self.cost:.2f}" if self.include_sensitive else "<redacted>"
                parts.append(f"cost={cost}")
            elif m == "tokens":
                tokens = (
                    str(self.token_count) if self.include_sensitive else "<redacted>"
                )
                parts.append(f"tokens={tokens}")
            elif m == "latency":
                parts.append(f"latency={self.latency:.2f}s")
            elif m == "guardrails":
                parts.append(f"guardrails={self.guardrail_hits}")
        joined = " ".join(parts)
        return f"Telemetry: {joined}" if joined else "Telemetry:"
