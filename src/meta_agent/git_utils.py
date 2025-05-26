"""Utilities for optional Git integration when generating bundles."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess


class GitManager:
    """Lightweight wrapper around Git commands."""

    def __init__(self, repo_dir: str | Path) -> None:
        self.repo_dir = Path(repo_dir)

    @staticmethod
    def git_available() -> bool:
        """Return True if the ``git`` executable can be found."""
        return shutil.which("git") is not None

    def _run(
        self, *args: str, env: dict | None = None
    ) -> subprocess.CompletedProcess[str]:
        if not self.git_available():
            raise RuntimeError("git executable not found")
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_dir,
            text=True,
            check=True,
            capture_output=True,
            env=env,
        )

    def init(self) -> None:
        """Initialize a new repository if one does not already exist."""
        if (self.repo_dir / ".git").exists():
            return
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self._run("init")
        self._run("config", "user.name", "meta-agent")
        self._run("config", "user.email", "meta-agent@example.com")
        self._run("branch", "-M", "main")

    def commit_all(self, message: str = "Initial commit") -> str:
        """Add all files and create a commit.

        Returns the commit SHA.
        """
        env = os.environ.copy()
        # Deterministic commit timestamp
        env.setdefault("GIT_AUTHOR_DATE", "1970-01-01T00:00:00+0000")
        env.setdefault("GIT_COMMITTER_DATE", "1970-01-01T00:00:00+0000")
        self._run("add", "-A", env=env)
        self._run("commit", "-m", message, env=env)
        result = self._run("rev-parse", "HEAD", env=env)
        return result.stdout.strip()

    def add_remote(self, name: str, url: str) -> None:
        self._run("remote", "add", name, url)

    def push(self, remote: str = "origin", branch: str = "main") -> None:
        self._run("push", remote, f"HEAD:{branch}")
        # If the remote is a local path, set its HEAD to the pushed branch so
        # commands like ``git log`` default to the new branch.
        remote_url = self._run("remote", "get-url", remote).stdout.strip()
        remote_path = Path(remote_url)
        if remote_path.exists():
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(remote_path),
                    "symbolic-ref",
                    "HEAD",
                    f"refs/heads/{branch}",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
