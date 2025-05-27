import pytest
import json
import yaml
from click.testing import CliRunner

from meta_agent.cli.main import cli
from meta_agent.telemetry_db import TelemetryDB

# --- Fixtures ---


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def valid_spec_dict():
    """Provides a dictionary representing a valid specification."""
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
    """Creates a temporary JSON file with a valid specification."""
    file_path = tmp_path / "spec.json"
    with open(file_path, "w") as f:
        json.dump(valid_spec_dict, f)
    return file_path


@pytest.fixture
def sample_yaml_file(tmp_path, valid_spec_dict):
    """Creates a temporary YAML file with a valid specification."""
    file_path = tmp_path / "spec.yaml"
    with open(file_path, "w") as f:
        yaml.dump(valid_spec_dict, f)
    return file_path


@pytest.fixture
def invalid_format_file(tmp_path):
    """Creates a temporary file with an unsupported extension."""
    file_path = tmp_path / "spec.txt"
    file_path.write_text("This is just text.")
    return file_path


@pytest.fixture
def invalid_content_json_file(tmp_path):
    """Creates a temporary JSON file with invalid JSON syntax."""
    file_path = tmp_path / "invalid.json"
    file_path.write_text('{"task_description": "incomplete json",')
    return file_path


@pytest.fixture
def invalid_schema_json_file(tmp_path):
    """Creates a temporary JSON file with valid JSON but invalid schema."""
    file_path = tmp_path / "invalid_schema.json"
    # Missing 'task_description'
    invalid_data = {"inputs": {"data": "string"}}
    with open(file_path, "w") as f:
        json.dump(invalid_data, f)
    return file_path


# --- Test Cases ---


def test_cli_generate_no_input(runner):
    """Test CLI exits with error if no input is provided."""
    result = runner.invoke(cli, ["generate"])
    assert result.exit_code != 0
    assert "Error: Please provide either --spec-file or --spec-text." in result.output


def test_cli_generate_both_inputs(runner, sample_json_file):
    """Test CLI exits with error if both inputs are provided."""
    result = runner.invoke(
        cli,
        ["generate", "--spec-file", str(sample_json_file), "--spec-text", "some text"],
    )
    assert result.exit_code != 0
    assert (
        "Error: Please provide only one of --spec-file or --spec-text." in result.output
    )


def test_cli_generate_spec_file_json(runner, sample_json_file):
    """Test successful generation using a JSON spec file."""
    result = runner.invoke(cli, ["generate", "--spec-file", str(sample_json_file)])
    assert result.exit_code == 0
    assert "Reading specification from file:" in result.output
    assert "Specification parsed successfully:" in result.output
    # assert "Task Description: Test agent for CLI" in result.output # Description might change
    assert "Starting agent generation orchestration..." in result.output
    assert "Orchestration finished." in result.output
    # Optionally, check for status: success in the final JSON output
    assert '"status": "simulated_success"' in result.output
    assert "Telemetry:" in result.output
    assert "Telemetry:" in result.output


def test_cli_generate_spec_file_yaml(runner, sample_yaml_file):
    """Test successful generation using a YAML spec file."""
    result = runner.invoke(cli, ["generate", "--spec-file", str(sample_yaml_file)])
    assert result.exit_code == 0
    assert "Reading specification from file:" in result.output
    assert "Specification parsed successfully:" in result.output
    # assert "Task Description: Test agent for CLI" in result.output # Description might change
    assert "Starting agent generation orchestration..." in result.output
    assert "Orchestration finished." in result.output
    # Optionally, check for status: success in the final JSON output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_file_not_found(runner):
    """Test CLI exits with error if spec file doesn't exist."""
    result = runner.invoke(cli, ["generate", "--spec-file", "nonexistent.json"])
    assert result.exit_code != 0
    # Click's error message for missing file
    assert "Invalid value for '--spec-file'" in result.output
    assert "File 'nonexistent.json' does not exist." in result.output


def test_cli_generate_spec_file_invalid_format(runner, invalid_format_file):
    """Test CLI exits with error for unsupported file format."""
    result = runner.invoke(cli, ["generate", "--spec-file", str(invalid_format_file)])
    assert result.exit_code != 0
    assert "Error: Unsupported file type: .txt" in result.output


def test_cli_generate_spec_file_invalid_content(runner, invalid_content_json_file):
    """Test CLI exits with error for invalid JSON/YAML content in file."""
    result = runner.invoke(
        cli, ["generate", "--spec-file", str(invalid_content_json_file)]
    )
    assert result.exit_code != 0
    assert (
        "Error processing specification:" in result.output
    )  # Generic error from SpecSchema parser
    assert "Error decoding JSON" in result.output  # More specific error from SpecSchema


def test_cli_generate_spec_file_invalid_schema(runner, invalid_schema_json_file):
    """Test CLI exits with error for valid JSON but invalid schema in file."""
    result = runner.invoke(
        cli, ["generate", "--spec-file", str(invalid_schema_json_file)]
    )
    assert result.exit_code != 0
    assert "Error processing specification:" in result.output
    assert "task_description" in result.output  # Pydantic validation error message


def test_cli_generate_spec_text_plain(runner):
    """Test successful generation using plain text spec."""
    # Assuming SpecSchema.from_text can handle plain text adequately
    plain_text = "Create a tool to add two numbers."
    result = runner.invoke(cli, ["generate", "--spec-text", plain_text])
    assert result.exit_code == 0
    assert "Processing specification from text input..." in result.output
    assert "Parsing spec-text as free-form text." in result.output
    assert "Specification parsed successfully:" in result.output
    assert "Starting agent generation orchestration..." in result.output
    assert "Orchestration finished." in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_text_json(runner, valid_spec_dict):
    """Test successful generation using JSON spec text."""
    sample_json_spec_text = json.dumps(valid_spec_dict)
    result = runner.invoke(cli, ["generate", "--spec-text", sample_json_spec_text])
    assert result.exit_code == 0
    assert "Processing specification from text input..." in result.output
    assert "Parsed spec-text as JSON." in result.output
    assert "Specification parsed successfully:" in result.output
    assert "Starting agent generation orchestration..." in result.output
    assert "Orchestration finished." in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_text_yaml(runner, valid_spec_dict):
    """Test successful generation using YAML spec text."""
    sample_yaml_spec_text = yaml.dump(valid_spec_dict)
    result = runner.invoke(cli, ["generate", "--spec-text", sample_yaml_spec_text])
    assert result.exit_code == 0
    assert "Processing specification from text input..." in result.output
    assert "Parsed spec-text as YAML." in result.output
    assert "Specification parsed successfully:" in result.output
    assert "Starting agent generation orchestration..." in result.output
    assert "Orchestration finished." in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_text_invalid_schema(runner):
    """Test CLI exits with error for valid JSON but invalid schema in text."""
    invalid_spec_text = json.dumps(
        {"inputs": {"data": "string"}}
    )  # Missing task_description
    result = runner.invoke(cli, ["generate", "--spec-text", invalid_spec_text])
    assert result.exit_code != 0
    assert "Processing specification from text input..." in result.output
    assert (
        "Error validating structured text input:" in result.output
    )  # Error from main.py handler
    assert "task_description" in result.output  # Pydantic validation error


def test_cli_dashboard_no_data(runner, tmp_path):
    db_path = tmp_path / "tele.db"
    TelemetryDB(db_path).close()
    result = runner.invoke(cli, ["dashboard", "--db-path", str(db_path)])
    assert result.exit_code == 0
    assert "No telemetry data found." in result.output


def test_cli_dashboard_with_data(runner, tmp_path):
    db_path = tmp_path / "tele.db"
    db = TelemetryDB(db_path)
    db.record(5, 0.1, 0.2, 1)
    db.close()
    result = runner.invoke(cli, ["dashboard", "--db-path", str(db_path)])
    assert result.exit_code == 0
    assert "Telemetry Dashboard:" in result.output
    assert "5" in result.output
    assert "$0.10" in result.output
