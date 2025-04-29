import json
import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic import ConfigDict
from typing import Any, Dict, List, Optional, Union


from pydantic import Field

class ToolParameter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    type_: str = Field(alias="type")
    description: Optional[str] = None
    required: bool = True


class ToolSpecification(BaseModel):
    name: str
    purpose: str
    input_parameters: List[ToolParameter] = Field(default_factory=list)
    output_format: str


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
                            self.errors.append("YAML specification did not parse into a dictionary.")
                            return False
                    except yaml.YAMLError as e:
                        self.errors.append(f"Failed to parse specification as JSON or YAML: {e}")
                        return False
            else:
                self.errors.append("Specification must be a string (JSON/YAML) or a dictionary.")
                return False

            if data is None:
                 self.errors.append("Could not load specification data.")
                 return False

            # Validate using Pydantic model
            self.parsed_spec = ToolSpecification(**data)
            return True

        except ValidationError as e:
            self.errors.extend([
                f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}" for err in e.errors()
            ])
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

