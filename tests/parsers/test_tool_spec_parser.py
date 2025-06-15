from meta_agent.parsers.tool_spec_parser import (
    ToolSpecificationParser,
    ToolSpecification,
    ToolParameter,
)

# --- Test Data ---
VALID_JSON_SPEC = '''
{
    "name": "get_weather",
    "purpose": "Fetches the current weather for a given location.",
    "input_parameters": [
        {"name": "location", "type": "string", "description": "City and state, e.g., San Francisco, CA", "required": true},
        {"name": "unit", "type": "string", "description": "Temperature unit (celsius or fahrenheit)", "required": false}
    ],
    "output_format": "JSON string containing temperature, conditions, and humidity."
}
'''

VALID_YAML_SPEC = '''
name: search_web
purpose: Searches the web for a given query.
input_parameters:
  - name: query
    type: string
    description: The search query.
    required: true
  - name: num_results
    type: integer
    description: Number of results to return.
    required: false
output_format: List of search result objects.
'''

VALID_DICT_SPEC = {
    "name": "calculate_sum",
    "purpose": "Calculates the sum of a list of numbers.",
    "input_parameters": [
        {"name": "numbers", "type": "list[float]", "description": "List of numbers to sum.", "required": True}
    ],
    "output_format": "A single float representing the sum."
}

INVALID_JSON_MALFORMED = '''
{
    "name": "malformed",
    "purpose": "Missing closing brace"
'''

INVALID_YAML_MALFORMED = '''
name: malformed
purpose: Bad indentation
  input_parameters:
  - name: param1
 type: string
'''

INVALID_SPEC_MISSING_FIELDS = '''
{
    "name": "incomplete_tool",
    "purpose": "This spec is missing output_format."
}
'''

# --- Test Cases ---

def test_parse_valid_json():
    """Tests parsing a valid JSON specification."""
    parser = ToolSpecificationParser(VALID_JSON_SPEC)
    assert parser.parse() is True
    assert parser.get_errors() == []
    spec = parser.get_specification()
    assert isinstance(spec, ToolSpecification)
    assert spec.name == "get_weather"
    assert spec.purpose == "Fetches the current weather for a given location."
    assert len(spec.input_parameters) == 2
    assert spec.input_parameters[0] == ToolParameter(name="location", type="string", description="City and state, e.g., San Francisco, CA", required=True)
    assert spec.input_parameters[1] == ToolParameter(name="unit", type="string", description="Temperature unit (celsius or fahrenheit)", required=False)
    assert spec.output_format == "JSON string containing temperature, conditions, and humidity."

def test_parse_valid_yaml():
    """Tests parsing a valid YAML specification."""
    parser = ToolSpecificationParser(VALID_YAML_SPEC)
    assert parser.parse() is True
    assert parser.get_errors() == []
    spec = parser.get_specification()
    assert isinstance(spec, ToolSpecification)
    assert spec.name == "search_web"
    assert len(spec.input_parameters) == 2
    assert spec.input_parameters[0].name == "query"
    assert spec.input_parameters[1].required is False
    assert spec.output_format == "List of search result objects."

def test_parse_valid_dict():
    """Tests parsing a valid dictionary specification."""
    parser = ToolSpecificationParser(VALID_DICT_SPEC)
    assert parser.parse() is True
    assert parser.get_errors() == []
    spec = parser.get_specification()
    assert isinstance(spec, ToolSpecification)
    assert spec.name == "calculate_sum"
    assert len(spec.input_parameters) == 1
    assert spec.input_parameters[0].type_ == "list[float]"
    assert spec.output_format == "A single float representing the sum."

def test_parse_invalid_json_malformed():
    """Tests parsing malformed JSON."""
    parser = ToolSpecificationParser(INVALID_JSON_MALFORMED)
    assert parser.parse() is False
    assert parser.get_specification() is None
    errors = parser.get_errors()
    assert len(errors) == 1
    assert "Failed to parse specification as JSON or YAML" in errors[0]

def test_parse_invalid_yaml_malformed():
    """Tests parsing malformed YAML."""
    # Note: Depending on the YAML parser's strictness, this might parse partially
    # or throw a specific YAMLError. We check that parsing fails.
    parser = ToolSpecificationParser(INVALID_YAML_MALFORMED)
    assert parser.parse() is False
    assert parser.get_specification() is None
    errors = parser.get_errors()
    assert len(errors) > 0 # Expect at least one error
    # More specific error check could be added if needed, e.g., checking for YAMLError message

def test_parse_invalid_spec_missing_fields():
    """Tests parsing a spec missing required Pydantic fields."""
    parser = ToolSpecificationParser(INVALID_SPEC_MISSING_FIELDS)
    assert parser.parse() is False
    assert parser.get_specification() is None
    errors = parser.get_errors()
    assert len(errors) > 0
    assert any("output_format: Field required" in err for err in errors)

def test_parse_invalid_input_type():
    """Tests parsing with an invalid input type (neither str nor dict)."""
    parser = ToolSpecificationParser({"name": "test", "input_schema": {}, "output_schema": {}})
    assert parser.parse() is False
    assert parser.get_specification() is None
    errors = parser.get_errors()
    assert len(errors) == 1
    assert errors[0] == "Specification must be a string (JSON/YAML) or a dictionary."

def test_parse_yaml_not_dict():
    """Tests parsing YAML that doesn't result in a dictionary."""
    yaml_list = '''
    - item1
    - item2
    '''
    parser = ToolSpecificationParser(yaml_list)
    assert parser.parse() is False
    assert parser.get_specification() is None
    errors = parser.get_errors()
    assert len(errors) == 1
    assert errors[0] == "YAML specification did not parse into a dictionary."

def test_parse_invalid_name_identifier():
    """Tests parsing a spec with invalid tool name identifier."""
    bad_spec = {
        "name": "123invalid",
        "purpose": "Invalid name",
        "input_parameters": [],
        "output_format": "int"
    }
    parser = ToolSpecificationParser(bad_spec)
    assert parser.parse() is False
    errors = parser.get_errors()
    # Expect the field validator error for name
    assert any("name: Tool name must be a valid Python identifier" in err for err in errors)

def test_parse_duplicate_param_names():
    """Tests parsing a spec with duplicate parameter names."""
    bad_spec = {
        "name": "dup_tool",
        "purpose": "Duplicate params",
        "input_parameters": [
            {"name": "a", "type": "int", "required": True},
            {"name": "a", "type": "int", "required": True}
        ],
        "output_format": "int"
    }
    parser = ToolSpecificationParser(bad_spec)
    assert parser.parse() is False
    errors = parser.get_errors()
    # Expect duplicate param name error
    assert any("input_parameters: Duplicate parameter name \"a\" found" in err for err in errors)
