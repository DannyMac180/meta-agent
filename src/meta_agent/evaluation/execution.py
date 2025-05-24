from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logging

from meta_agent.sandbox.sandbox_manager import (
    SandboxExecutionError,
    SandboxManager,
)


@dataclass
class ExecutionResult:
    """Result of running tests inside the sandbox."""

    exit_code: int
    stdout: str
    stderr: str


class ExecutionModule:
    """Run pytest for generated code inside a Docker sandbox."""

    def __init__(self, sandbox_manager: Optional[SandboxManager] = None) -> None:
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.logger = logging.getLogger(__name__)

    def run_tests(self, path: Path, timeout: int = 60) -> ExecutionResult:
        """Execute tests located at ``path`` inside the sandbox."""
        self.logger.info("Running tests in %s", path)
        try:
            exit_code, stdout, stderr = self.sandbox_manager.run_code_in_sandbox(
                code_directory=path,
                command=["pytest", "-vv"],
                timeout=timeout,
            )
            self.logger.debug("Sandbox returned exit code %s", exit_code)
        except SandboxExecutionError:
            self.logger.error("Sandbox execution failed", exc_info=True)
            raise
        return ExecutionResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
