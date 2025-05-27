from __future__ import annotations

import time
import logging
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
        if self.cost >= self.cost_cap:
            self.logger.warning(
                "Cost cap exceeded: $%.2f >= $%.2f", self.cost, self.cost_cap

            )
            raise RuntimeError("cost cap exceeded")
        elif ratio >= 0.9 - eps and self.cost_cap > 0:
            self.record_event(
                self.Category.COST_CONTROL,
                "90% of cost cap reached",
                severity=self.Severity.ERROR,
            )
        elif ratio >= 0.75 - eps and self.cost_cap > 0:
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
    def summary_line(self) -> str:
        """Return a one-line summary of collected metrics."""
        cost = f"${self.cost:.2f}" if self.include_sensitive else "<redacted>"
        tokens = str(self.token_count) if self.include_sensitive else "<redacted>"
        return (
            "Telemetry: "
            f"cost={cost} "
            f"tokens={tokens} "
            f"latency={self.latency:.2f}s "
            f"guardrails={self.guardrail_hits}"
        )
