from __future__ import annotations

from pathlib import Path
from typing import Optional

import logging

from .execution import ExecutionModule
from .result_collection import ResultCollectionModule, CollectionResult
from .reporting import ReportingModule


class EvaluationHarness:
    """Coordinate execution, collection and reporting of tests."""

    def __init__(
        self,
        result_collector: Optional[ResultCollectionModule] = None,
        reporter: Optional[ReportingModule] = None,
    ) -> None:
        self.result_collector = result_collector or ResultCollectionModule()
        self.reporter = reporter or ReportingModule()
        self.logger = logging.getLogger(__name__)

    def evaluate(
        self,
        path: Path,
        timeout: int = 60,
        output_format: str = "text",
    ) -> str:
        """Run tests at ``path`` and return a formatted report."""
        self.logger.info("Starting evaluation for %s", path)
        result: CollectionResult = self.result_collector.execute_and_collect(
            path, timeout=timeout
        )
        return self.reporter.generate_report(result, output_format=output_format)
