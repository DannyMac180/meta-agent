from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import json
from typing import Iterable, List

from meta_agent.evaluation.result_collection import CollectionResult


@dataclass
class SummaryReport:
    """Summarised information about a collection result."""

    exit_code: int
    passed: bool
    duration: float
    stdout: str
    stderr: str


class ReportingModule:
    """Format :class:`CollectionResult` objects for display."""

    def summarize(self, result: CollectionResult) -> SummaryReport:
        """Create a :class:`SummaryReport` from a collection result."""
        return SummaryReport(
            exit_code=result.exit_code,
            passed=result.exit_code == 0,
            duration=result.duration,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def aggregate(self, results: Iterable[CollectionResult]) -> List[SummaryReport]:
        """Summarize multiple results."""
        return [self.summarize(r) for r in results]

    def to_text(self, report: SummaryReport) -> str:
        """Return a human‑readable text report."""
        lines = [
            f"Status: {'PASSED' if report.passed else 'FAILED'}",
            f"Exit Code: {report.exit_code}",
            f"Duration: {report.duration:.2f}s",
            "stdout:\n" + report.stdout,
            "stderr:\n" + report.stderr,
        ]
        return "\n".join(lines)

    def to_json(self, report: SummaryReport) -> str:
        """Return a JSON representation of the report."""
        return json.dumps(asdict(report), indent=2)

    def to_html(self, report: SummaryReport) -> str:
        """Return a simple HTML representation of the report."""
        return (
            "<html><body>"
            "<h2>Evaluation Report</h2>"
            f"<p>Status: {'PASSED' if report.passed else 'FAILED'}</p>"
            f"<p>Exit Code: {report.exit_code}</p>"
            f"<p>Duration: {report.duration:.2f}s</p>"
            f"<h3>stdout</h3><pre>{html.escape(report.stdout)}</pre>"
            f"<h3>stderr</h3><pre>{html.escape(report.stderr)}</pre>"
            "</body></html>"
        )

    def generate_report(self, result: CollectionResult, output_format: str = "text") -> str:
        """Generate a formatted report for a result."""
        summary = self.summarize(result)
        if output_format == "json":
            return self.to_json(summary)
        if output_format == "html":
            return self.to_html(summary)
        return self.to_text(summary)
