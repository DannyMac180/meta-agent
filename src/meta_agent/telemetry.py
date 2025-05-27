import time
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


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

    def __init__(self, cost_cap: float = 0.5) -> None:
        self.cost_cap = cost_cap
        self.token_count = 0
        self.cost = 0.0
        self.guardrail_hits = 0
        self.latency = 0.0
        self._start: Optional[float] = None
        self.logger = logging.getLogger(__name__)
        self.events: List[TelemetryCollector.Event] = []

    def record_event(
        self,
        category: "TelemetryCollector.Category",
        message: str,
        severity: "TelemetryCollector.Severity" = Severity.ERROR,
    ) -> None:
        """Record an error or informational event."""
        self.events.append(
            TelemetryCollector.Event(category=category, severity=severity, message=message)
        )
        log_method = self.logger.info
        if severity in (self.Severity.ERROR, self.Severity.CRITICAL):
            log_method = self.logger.error
        elif severity is self.Severity.WARNING:
            log_method = self.logger.warning
        log_method(message)

    # --- Timing -----------------------------------------------------
    def start_timer(self) -> None:
        """Start the latency timer."""
        self._start = time.perf_counter()

    def stop_timer(self) -> None:
        """Stop the latency timer and accumulate duration."""
        if self._start is not None:
            self.latency += time.perf_counter() - self._start
            self._start = None

    # --- Usage ------------------------------------------------------
    def add_usage(self, prompt_tokens: int, response_tokens: int, model: str = "default") -> None:
        """Record token usage and update cost."""
        tokens = prompt_tokens + response_tokens
        self.token_count += tokens
        rate = self.COST_TABLE.get(model, self.COST_TABLE["default"])
        self.cost += rate * tokens / 1000.0
        ratio = self.cost / self.cost_cap if self.cost_cap > 0 else 0
        if ratio >= 1.0:
            self.record_event(
                self.Category.COST_CONTROL,
                f"Cost cap exceeded: ${self.cost:.2f} >= ${self.cost_cap:.2f}",
                severity=self.Severity.CRITICAL,
            )
            raise RuntimeError("cost cap exceeded")
        elif ratio >= 0.9:
            self.record_event(
                self.Category.COST_CONTROL,
                "90% of cost cap reached",
                severity=self.Severity.ERROR,
            )
        elif ratio >= 0.75:
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
        return (
            f"Telemetry: cost=${self.cost:.2f} "
            f"tokens={self.token_count} "
            f"latency={self.latency:.2f}s "
            f"guardrails={self.guardrail_hits}"
        )
