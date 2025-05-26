import subprocess
from pathlib import Path

from meta_agent.git_utils import GitManager


def test_git_manager_init_and_commit(tmp_path: Path) -> None:
    gm = GitManager(tmp_path)
    gm.init()
    (tmp_path / "foo.txt").write_text("hi")
    sha = gm.commit_all("init")

    assert (tmp_path / ".git").exists()
    out = subprocess.check_output(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True
    ).strip()
    assert out == sha


def test_git_manager_push(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True)

    repo = tmp_path / "repo"
    gm = GitManager(repo)
    gm.init()
    (repo / "bar.txt").write_text("bar")
    gm.commit_all("first")
    gm.add_remote("origin", str(remote))
    gm.push("origin", "main")

    log = subprocess.check_output(
        ["git", "-C", str(remote), "log", "--oneline"], text=True
    )
    assert "first" in log
