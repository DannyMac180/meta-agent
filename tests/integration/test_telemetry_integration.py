import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from meta_agent.cli.main import cli
from meta_agent.telemetry_db import TelemetryDB


@pytest.fixture
def valid_spec_dict():
    return {
        "task_description": "Test agent for CLI",
        "inputs": {"data": "string"},
        "outputs": {"status": "string"},
        "constraints": ["Must run quickly"],
        "technical_requirements": ["Python 3.10+"],
        "metadata": {"test_id": "cli-001"},
    }


@pytest.fixture
def sample_json_file(tmp_path, valid_spec_dict):
    file_path = tmp_path / "spec.json"
    with open(file_path, "w") as f:
        json.dump(valid_spec_dict, f)
    return file_path


def test_generate_records_telemetry(tmp_path, sample_json_file, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    result = runner.invoke(
        cli, ["--no-sensitive-logs", "generate", "--spec-file", str(sample_json_file)]
    )
    assert result.exit_code == 0
    assert "<redacted>" in result.output
    db_path = Path(tmp_path) / "meta_agent_telemetry.db"
    db = TelemetryDB(db_path)
    records = db.fetch_all()
    db.close()
    assert len(records) == 1
