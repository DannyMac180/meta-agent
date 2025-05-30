import json
import yaml

try:
    from pydantic import BaseModel, Field, ValidationError, ConfigDict, field_validator

    _HAS_V2 = True
except ImportError:  # pragma: no cover - pydantic v1 fallback
    from pydantic import BaseModel, Field, ValidationError, validator as field_validator

    _HAS_V2 = False

    class ConfigDict(dict):
        pass


from typing import Any, Dict, List, Optional, Union


class ToolParameter(BaseModel):
    """
    Represents a single input parameter for a tool specification.

    Attributes:
        name (str): The name of the parameter.
        type_ (str): The type of the parameter (aliased as 'type' for compatibility).
        description (Optional[str]): A human-readable description of the parameter.
        required (bool): Whether the parameter is required (default: True).
    """

    if _HAS_V2:
        model_config = ConfigDict(populate_by_name=True)
    else:

        class Config:
            allow_population_by_field_name = True

    name: str
    type_: str = Field(alias="type")
    description: Optional[str] = None
    required: bool = True


class ToolSpecification(BaseModel):
    """
    Represents the specification for a tool, including its name, purpose, parameters, and output format.

    Attributes:
        name (str): The name of the tool.
        purpose (str): A description of what the tool does.
        input_parameters (List[ToolParameter]): The list of input parameters required by the tool.
        output_format (str): The expected output type or format.
    """

    name: str
    purpose: str
    input_parameters: List[ToolParameter] = Field(default_factory=list)
    output_format: str

    @field_validator("name")
    @classmethod
    def name_must_be_valid_identifier(cls, v: str) -> str:
        """Validate that the tool name is a valid Python identifier."""
        if not v.isidentifier():
            raise ValueError("Tool name must be a valid Python identifier")
        return v

    @field_validator("input_parameters")
    @classmethod
    def parameters_must_be_valid(cls, v: List[ToolParameter]) -> List[ToolParameter]:
        """Validate parameter names are valid identifiers and unique."""
        seen_names = set()
        for param in v:
            if not param.name.isidentifier():
                raise ValueError(
                    f'Parameter name "{param.name}" must be a valid Python identifier'
                )
            if param.name in seen_names:
                raise ValueError(f'Duplicate parameter name "{param.name}" found')
            seen_names.add(param.name)
        return v


class ToolSpecificationParser:
    def __init__(self, specification: Union[str, Dict[str, Any]]) -> None:
        """Initializes the parser with a specification.

        Args:
            specification: The tool specification, can be a raw string (JSON/YAML)
                           or a pre-parsed dictionary.
        """
        self.raw_specification = specification
        self.parsed_spec: Optional[ToolSpecification] = None
        self.errors: List[str] = []

    def parse(self) -> bool:
        """Parses and validates the specification.

        Returns:
            True if parsing and validation are successful, False otherwise.
        """
        data: Optional[Dict[str, Any]] = None
        try:
            if isinstance(self.raw_specification, dict):
                data = self.raw_specification
            elif isinstance(self.raw_specification, str):
                # Try parsing as JSON first
                try:
                    data = json.loads(self.raw_specification)
                except json.JSONDecodeError:
                    # If JSON fails, try parsing as YAML
                    try:
                        data = yaml.safe_load(self.raw_specification)
                        if data is None or not isinstance(data, dict):
                            self.errors.append(
                                "YAML specification did not parse into a dictionary."
                            )
                            return False
                    except yaml.YAMLError as e:
                        self.errors.append(
                            f"Failed to parse specification as JSON or YAML: {e}"
                        )
                        return False
            else:
                self.errors.append(
                    "Specification must be a string (JSON/YAML) or a dictionary."
                )
                return False

            if data is None:
                self.errors.append("Could not load specification data.")
                return False

            # Validate using Pydantic model
            self.parsed_spec = ToolSpecification(**data)
            return True

        except ValidationError as e:
            # Format validation errors to match the expected error messages in tests
            for err in e.errors():
                loc_parts = [str(part) for part in err["loc"]]
                field_name = loc_parts[0] if loc_parts else "unknown"
                error_msg = err["msg"]
                if error_msg.lower() == "field required":
                    error_msg = "Field required"

                # Special handling for specific validation errors to match test expectations
                if field_name == "name" and "valid Python identifier" in error_msg:
                    self.errors.append(
                        "name: Tool name must be a valid Python identifier"
                    )
                elif (
                    field_name == "input_parameters"
                    and "Duplicate parameter name" in error_msg
                ):
                    # Extract the parameter name from the error message
                    param_name = (
                        error_msg.split('"')[1] if '"' in error_msg else "unknown"
                    )
                    self.errors.append(
                        f'input_parameters: Duplicate parameter name "{param_name}" found'
                    )
                else:
                    # Default formatting for other errors
                    self.errors.append(f"{'.'.join(loc_parts)}: {error_msg}")

            return False
        except Exception as e:
            import logging

            logging.exception("Unexpected error during ToolSpecification parsing")
            self.errors.append(f"An unexpected error occurred during parsing: {e}")
            return False

    def get_specification(self) -> Optional[ToolSpecification]:
        """Returns the parsed and validated specification model."""
        return self.parsed_spec

    def get_errors(self) -> List[str]:
        """Returns any errors encountered during parsing or validation."""
        return self.errors
