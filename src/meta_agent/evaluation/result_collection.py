from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time

import logging

from meta_agent.evaluation.execution import ExecutionModule
from meta_agent.sandbox.sandbox_manager import SandboxExecutionError  # noqa: F401


@dataclass
class CollectionResult:
    """Execution results with timing metadata."""

    exit_code: int
    stdout: str
    stderr: str
    duration: float


class ResultCollectionModule:
    """Collect results from the :class:`ExecutionModule`."""

    def __init__(self, execution_module: Optional[ExecutionModule] = None) -> None:
        self.execution_module = execution_module or ExecutionModule()
        self.logger = logging.getLogger(__name__)

    def execute_and_collect(self, path: Path, timeout: int = 60) -> CollectionResult:
        """Run tests via the execution module and gather outputs."""
        self.logger.info("Executing and collecting results for %s", path)
        start = time.perf_counter()
        result = self.execution_module.run_tests(path, timeout=timeout)
        end = time.perf_counter()
        self.logger.debug(
            "Execution finished in %.2fs with exit code %s",
            end - start,
            result.exit_code,
        )
        return CollectionResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration=end - start,
        )
