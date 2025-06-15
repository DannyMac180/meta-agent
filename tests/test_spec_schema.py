import pytest
import json
import yaml
from pydantic import ValidationError

from meta_agent.models.spec_schema import SpecSchema

# --- Fixtures ---


@pytest.fixture
def valid_spec_dict():
    return {
        "task_description": "Create a calculator agent",
        "inputs": {"num1": "float", "num2": "float"},
        "outputs": {"result": "float"},
        "constraints": ["Must handle division by zero"],
        "technical_requirements": ["Use Python 3.9+"],
        "metadata": {"version": "1.0"},
    }


@pytest.fixture
def sample_spec_json_file(tmp_path, valid_spec_dict):
    file_path = tmp_path / "spec.json"
    with open(file_path, "w") as f:
        json.dump(valid_spec_dict, f)
    return file_path


@pytest.fixture
def sample_spec_yaml_file(tmp_path, valid_spec_dict):
    file_path = tmp_path / "spec.yaml"
    with open(file_path, "w") as f:
        yaml.dump(valid_spec_dict, f)
    return file_path


# --- Test Cases ---


def test_spec_schema_instantiation(valid_spec_dict):
    """Test basic instantiation with valid data."""
    spec = SpecSchema(**valid_spec_dict)
    assert spec.task_description == valid_spec_dict["task_description"]
    assert spec.inputs == valid_spec_dict["inputs"]
    assert spec.outputs == valid_spec_dict["outputs"]
    assert spec.constraints == valid_spec_dict["constraints"]
    assert spec.technical_requirements == valid_spec_dict["technical_requirements"]
    assert spec.metadata == valid_spec_dict["metadata"]


def test_spec_schema_missing_required_field():
    """Test validation error for missing required field (task_description)."""
    with pytest.raises(ValidationError, match="task_description"):
        SpecSchema()  # type: ignore[call-arg]


def test_spec_schema_empty_task_description(valid_spec_dict):
    """Test validation error for empty task_description."""
    invalid_dict = valid_spec_dict.copy()
    invalid_dict["task_description"] = "  "  # Whitespace only
    with pytest.raises(ValueError, match="Task description must not be empty"):
        SpecSchema(**invalid_dict)


def test_from_dict(valid_spec_dict):
    """Test creating SpecSchema from a dictionary."""
    spec = SpecSchema.from_dict(valid_spec_dict)
    assert spec.task_description == valid_spec_dict["task_description"]


def test_from_dict_invalid():
    """Test from_dict raises validation error for invalid data."""
    with pytest.raises(ValidationError):
        SpecSchema.from_dict({"inputs": {}})


def test_from_json_string(valid_spec_dict):
    """Test creating SpecSchema from a JSON string."""
    json_str = json.dumps(valid_spec_dict)
    spec = SpecSchema.from_json(json_str)
    assert spec.task_description == valid_spec_dict["task_description"]


def test_from_json_file(sample_spec_json_file, valid_spec_dict):
    """Test creating SpecSchema from a JSON file path."""
    spec = SpecSchema.from_json(sample_spec_json_file)
    assert spec.task_description == valid_spec_dict["task_description"]


def test_from_json_invalid_string():
    """Test from_json raises error for invalid JSON string."""
    invalid_json_str = '{"task_description": "test"'
    with pytest.raises(json.JSONDecodeError):
        SpecSchema.from_json(invalid_json_str)


def test_from_json_file_not_found(tmp_path):
    """Test from_json raises error for non-existent file."""
    non_existent_file = tmp_path / "not_real.json"
    with pytest.raises(FileNotFoundError):
        SpecSchema.from_json(non_existent_file)


def test_from_yaml_string(valid_spec_dict):
    """Test creating SpecSchema from a YAML string."""
    yaml_str = yaml.dump(valid_spec_dict)
    spec = SpecSchema.from_yaml(yaml_str)
    assert spec.task_description == valid_spec_dict["task_description"]


def test_from_yaml_file(sample_spec_yaml_file, valid_spec_dict):
    """Test creating SpecSchema from a YAML file path."""
    spec = SpecSchema.from_yaml(sample_spec_yaml_file)
    assert spec.task_description == valid_spec_dict["task_description"]


def test_from_yaml_invalid_string():
    """Test from_yaml raises error for invalid YAML string."""
    invalid_yaml_str = "task_description: test\n  inputs: invalid: yaml"
    with pytest.raises(yaml.YAMLError):
        SpecSchema.from_yaml(invalid_yaml_str)


def test_from_yaml_file_not_found(tmp_path):
    """Test from_yaml raises error for non-existent file."""
    non_existent_file = tmp_path / "not_real.yaml"
    with pytest.raises(FileNotFoundError):
        SpecSchema.from_yaml(non_existent_file)


def test_from_yaml_not_dict(tmp_path):
    """Test from_yaml raises TypeError if content is not a dict."""
    file_path = tmp_path / "list.yaml"
    with open(file_path, "w") as f:
        yaml.dump([1, 2, 3], f)
    with pytest.raises(
        TypeError, match="YAML content did not parse into a dictionary."
    ):
        SpecSchema.from_yaml(file_path)


def test_from_text():
    """Test the placeholder from_text method."""
    text_input = "  Just a simple task description.  "
    spec = SpecSchema.from_text(text_input)
    assert spec.task_description == "Just a simple task description."
    # Check that other fields are None or default
    assert spec.inputs is None
    assert spec.outputs is None
    assert spec.constraints is None
    assert spec.technical_requirements is None
    assert spec.metadata is None
