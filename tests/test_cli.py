import pytest
import json
import yaml
from unittest.mock import patch, MagicMock
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
    assert "❌ Please provide either --spec-file or --spec-text." in result.output


def test_cli_create_no_input_non_interactive(runner):
    """Test create command exits with error in non-interactive environment."""
    # CliRunner by default simulates a non-interactive environment
    result = runner.invoke(cli, ["create"])
    assert result.exit_code != 0
    assert "❌ No specification provided." in result.output
    assert "In non-interactive environments, you must specify" in result.output
    assert "Use --spec-file path/to/spec.yaml" in result.output
    assert "Use --spec-text 'your specification here'" in result.output


def test_cli_create_with_spec_text_natural_language(runner):
    """Test create command works with natural language --spec-text."""
    spec_text = "Create an agent that processes data"
    result = runner.invoke(cli, ["create", "--spec-text", spec_text])
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output
    assert "Parsing as natural language" in result.output or "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output


def test_cli_create_with_spec_text_json(runner, valid_spec_dict):
    """Test create command works with JSON --spec-text."""
    spec_text = json.dumps(valid_spec_dict)
    result = runner.invoke(cli, ["create", "--spec-text", spec_text])
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output


def test_cli_create_with_spec_text_yaml(runner, valid_spec_dict):
    """Test create command works with YAML --spec-text."""
    spec_text = yaml.dump(valid_spec_dict)
    result = runner.invoke(cli, ["create", "--spec-text", spec_text])
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output


def test_cli_create_with_spec_file(runner, sample_json_file):
    """Test create command works with --spec-file option."""
    result = runner.invoke(cli, ["create", "--spec-file", str(sample_json_file)])
    assert result.exit_code == 0
    assert f"📄 Reading specification from {sample_json_file.name}" in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output


def test_cli_create_both_inputs(runner, sample_json_file):
    """Test create command exits with error if both inputs are provided."""
    result = runner.invoke(
        cli,
        ["create", "--spec-file", str(sample_json_file), "--spec-text", "some text"],
    )
    assert result.exit_code != 0
    assert "❌ Provide only one of --spec-file or --spec-text." in result.output


def test_cli_create_show_spec_flag(runner):
    """Test create command with --show-spec flag displays generated specification."""
    spec_text = "Create an agent that processes customer feedback"
    result = runner.invoke(cli, ["create", "--spec-text", spec_text, "--show-spec"])
    assert result.exit_code == 0
    assert "📋 Generated Specification:" in result.output
    assert "─" * 50 in result.output  # Separator line


def test_cli_create_show_spec_with_file(runner, sample_yaml_file):
    """Test create command with --show-spec flag using spec file."""
    result = runner.invoke(cli, ["create", "--spec-file", str(sample_yaml_file), "--show-spec"])
    assert result.exit_code == 0
    assert "📋 Generated Specification:" in result.output
    assert "task_description:" in result.output


def test_cli_generate_both_inputs(runner, sample_json_file):
    """Test CLI exits with error if both inputs are provided."""
    result = runner.invoke(
        cli,
        ["generate", "--spec-file", str(sample_json_file), "--spec-text", "some text"],
    )
    assert result.exit_code != 0
    assert "❌ Please provide only one of --spec-file or --spec-text." in result.output


def test_cli_generate_spec_file_json(runner, sample_json_file):
    """Test successful generation using a JSON spec file."""
    result = runner.invoke(cli, ["generate", "--spec-file", str(sample_json_file)])
    assert result.exit_code == 0
    assert "📄 Reading specification from" in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output
    assert "✅ Agent generation completed successfully!" in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_custom_metrics(runner, sample_json_file):
    result = runner.invoke(
        cli,
        ["generate", "--spec-file", str(sample_json_file), "--metric", "latency"],
    )
    assert result.exit_code == 0
    assert "Telemetry:" in result.output
    assert "latency=" in result.output
    assert "cost=" not in result.output


def test_cli_generate_spec_file_yaml(runner, sample_yaml_file):
    """Test successful generation using a YAML spec file."""
    result = runner.invoke(cli, ["generate", "--spec-file", str(sample_yaml_file)])
    assert result.exit_code == 0
    assert "📄 Reading specification from" in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output
    assert "✅ Agent generation completed successfully!" in result.output
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
    assert "❌ Unsupported file type: .txt" in result.output


def test_cli_generate_spec_file_invalid_content(runner, invalid_content_json_file):
    """Test CLI exits with error for invalid JSON/YAML content in file."""
    result = runner.invoke(
        cli, ["generate", "--spec-file", str(invalid_content_json_file)]
    )
    assert result.exit_code != 0
    assert "❌" in result.output  # Should show error message
    assert "parse" in result.output.lower()  # Should mention parsing error


def test_cli_generate_spec_file_invalid_schema(runner, invalid_schema_json_file):
    """Test CLI exits with error for valid JSON but invalid schema in file."""
    result = runner.invoke(
        cli, ["generate", "--spec-file", str(invalid_schema_json_file)]
    )
    assert result.exit_code != 0
    assert "❌" in result.output
    assert "task_description" in result.output.lower()  # Pydantic validation error message


def test_cli_generate_spec_text_plain(runner):
    """Test successful generation using plain text spec."""
    # Assuming SpecSchema.from_text can handle plain text adequately
    plain_text = "Create a tool to add two numbers."
    result = runner.invoke(cli, ["generate", "--spec-text", plain_text])
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output
    assert "✅ Agent generation completed successfully!" in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_text_json(runner, valid_spec_dict):
    """Test successful generation using JSON spec text."""
    sample_json_spec_text = json.dumps(valid_spec_dict)
    result = runner.invoke(cli, ["generate", "--spec-text", sample_json_spec_text])
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output
    assert "✅ Agent generation completed successfully!" in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_text_yaml(runner, valid_spec_dict):
    """Test successful generation using YAML spec text."""
    sample_yaml_spec_text = yaml.dump(valid_spec_dict)
    result = runner.invoke(cli, ["generate", "--spec-text", sample_yaml_spec_text])
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output
    assert "✅ Specification parsed successfully:" in result.output
    assert "🚀 Starting agent generation..." in result.output
    assert "✅ Agent generation completed successfully!" in result.output
    assert '"status": "simulated_success"' in result.output


def test_cli_generate_spec_text_invalid_schema(runner):
    """Test CLI exits with error for valid JSON but invalid schema in text."""
    invalid_spec_text = json.dumps(
        {"inputs": {"data": "string"}}
    )  # Missing task_description
    result = runner.invoke(cli, ["generate", "--spec-text", invalid_spec_text])
    assert result.exit_code != 0
    assert "📝 Processing specification from text..." in result.output
    assert "❌" in result.output  # Error indicator
    assert "task_description" in result.output.lower()  # Pydantic validation error


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


def test_cli_export_json(runner, tmp_path):
    db_path = tmp_path / "tele.db"
    db = TelemetryDB(db_path)
    db.record(5, 0.1, 0.2, 1)
    db.close()
    out = tmp_path / "export.json"
    result = runner.invoke(
        cli,
        [
            "export",
            "--db-path",
            str(db_path),
            "--output",
            str(out),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_cli_export_csv(runner, tmp_path):
    db_path = tmp_path / "tele.db"
    db = TelemetryDB(db_path)
    db.record(5, 0.1, 0.2, 1)
    db.close()
    out = tmp_path / "export.csv"
    result = runner.invoke(
        cli,
        [
            "export",
            "--db-path",
            str(db_path),
            "--output",
            str(out),
            "--format",
            "csv",
            "--metric",
            "tokens",
        ],
    )
    assert result.exit_code == 0
    assert out.exists()


# --- Enhanced Create Command Tests ---


def test_cli_create_interactive_prompting_scenarios(runner):
    """Test create command interactive prompting - simplified test for non-interactive detection."""
    # Since CliRunner is non-interactive by design, we test that it correctly detects this
    # and provides helpful error messages
    result = runner.invoke(cli, ["create"])
    assert result.exit_code != 0
    assert "❌ No specification provided." in result.output
    assert "In non-interactive environments, you must specify" in result.output
    assert "Use --spec-file path/to/spec.yaml" in result.output
    assert "Use --spec-text 'your specification here'" in result.output
    assert "Example: meta-agent create --spec-text" in result.output


def test_cli_create_interactive_help_message_quality(runner):
    """Test that the interactive help message provides clear guidance."""
    result = runner.invoke(cli, ["create"])
    assert result.exit_code != 0
    output = result.output
    
    # Check that the message is comprehensive and helpful
    assert "❌ No specification provided." in output
    assert "In non-interactive environments" in output
    assert "--spec-file" in output
    assert "--spec-text" in output
    assert "Example:" in output
    assert "Analyze customer feedback sentiment" in output  # Concrete example


def test_cli_create_privacy_flag_integration(runner, sample_json_file):
    """Test create command works with --no-sensitive-logs flag."""
    result = runner.invoke(
        cli, 
        ["--no-sensitive-logs", "create", "--spec-file", str(sample_json_file)]
    )
    assert result.exit_code == 0
    assert "📄 Reading specification from" in result.output
    # In test environment, sensitive data should be sanitized


def test_cli_create_debug_flag_integration(runner, sample_json_file):
    """Test create command works with --debug flag."""
    result = runner.invoke(
        cli, 
        ["--debug", "create", "--spec-file", str(sample_json_file)]
    )
    assert result.exit_code == 0
    # Debug flag should enable more verbose logging


def test_cli_create_spec_text_invalid_json(runner):
    """Test create command handles invalid JSON in spec-text."""
    invalid_json = '{"task_description": "incomplete json",'
    result = runner.invoke(cli, ["create", "--spec-text", invalid_json])
    # Invalid JSON should be parsed as natural language, so this should succeed
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output


def test_cli_create_spec_text_invalid_yaml(runner):
    """Test create command handles invalid YAML in spec-text."""
    invalid_yaml = """
task_description: "Valid start"
    invalid_indentation: "This will fail"
- not_proper_list
"""
    result = runner.invoke(cli, ["create", "--spec-text", invalid_yaml])
    # Invalid YAML should be parsed as natural language, so this should succeed
    assert result.exit_code == 0
    assert "📝 Processing specification from text..." in result.output


def test_cli_create_spec_text_invalid_schema(runner):
    """Test create command handles valid JSON/YAML but invalid schema."""
    invalid_spec = json.dumps({"inputs": {"data": "string"}})  # Missing task_description
    result = runner.invoke(cli, ["create", "--spec-text", invalid_spec])
    assert result.exit_code != 0
    assert "❌" in result.output
    assert "task_description" in result.output.lower()


def test_cli_create_natural_language_various_formats(runner):
    """Test create command handles various natural language formats."""
    test_cases = [
        "Create a sentiment analysis agent",
        "I need an agent to process customer feedback and categorize it by urgency",
        "Build me a tool that takes CSV files and outputs summary statistics",
        "Process documents, extract key information, and generate reports",
    ]
    
    for spec_text in test_cases:
        result = runner.invoke(cli, ["create", "--spec-text", spec_text])
        assert result.exit_code == 0, f"Failed for spec: {spec_text}"
        assert "📝 Processing specification from text..." in result.output


def test_cli_create_custom_metrics(runner, sample_json_file):
    """Test create command with custom metrics."""
    result = runner.invoke(
        cli,
        ["create", "--spec-file", str(sample_json_file), "--metric", "latency", "--metric", "cost"],
    )
    assert result.exit_code == 0
    # Should include metrics in telemetry output


def test_cli_create_file_parsing_errors(runner, tmp_path):
    """Test create command handles various file parsing errors."""
    # Test with non-existent file (handled by click)
    result = runner.invoke(cli, ["create", "--spec-file", "nonexistent.json"])
    assert result.exit_code != 0
    assert "does not exist" in result.output
    
    # Test with invalid file extension
    invalid_file = tmp_path / "spec.txt"
    invalid_file.write_text("some content")
    result = runner.invoke(cli, ["create", "--spec-file", str(invalid_file)])
    assert result.exit_code != 0
    assert "❌ Unsupported file type: .txt" in result.output


def test_cli_create_enhanced_error_messages(runner):
    """Test create command provides helpful error messages."""
    # Test validation error
    invalid_spec = json.dumps({"invalid": "spec"})
    result = runner.invoke(cli, ["create", "--spec-text", invalid_spec])
    assert result.exit_code != 0
    assert "❌" in result.output
    assert "💡" in result.output  # Should include helpful suggestions


def test_cli_create_backward_compatibility_with_generate(runner, sample_json_file):
    """Test that generate command still works (backward compatibility)."""
    result = runner.invoke(cli, ["generate", "--spec-file", str(sample_json_file)])
    assert result.exit_code == 0
    # generate command should still function for existing users


def test_cli_create_specification_preview(runner, valid_spec_dict):
    """Test create command shows specification preview."""
    spec_text = json.dumps(valid_spec_dict)
    result = runner.invoke(cli, ["create", "--spec-text", spec_text])
    assert result.exit_code == 0
    assert "✅ Specification parsed successfully:" in result.output
    assert "Task:" in result.output
    assert valid_spec_dict["task_description"][:50] in result.output  # Task preview
