import json
import re
import yaml
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError
from typing import cast

try:
    from pydantic import field_validator  # type: ignore
except ImportError:  # Pydantic v1
    from pydantic import validator as field_validator
from typing import Optional, Dict, List, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol

    class _ModelDumpProtocol(Protocol):
        def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
            ...


class SpecSchema(BaseModel):
    """Data model for agent specifications."""

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Return model data as a dictionary across Pydantic versions."""
        base = getattr(super(), "model_dump", None)
        if callable(base):
            # Pyright: `model_dump` return type is `Any`; we narrow it.
            return cast(Dict[str, Any], base(*args, **kwargs))
        return self.dict(*args, **kwargs)

    task_description: str = Field(
        ..., description="Detailed description of the agent's task and requirements."
    )
    inputs: Optional[Dict[str, str]] = Field(
        default=None,
        description="Specification of expected inputs, e.g., {'input_name': 'type'}.",
    )
    outputs: Optional[Dict[str, str]] = Field(
        default=None,
        description="Specification of expected outputs, e.g., {'output_name': 'type'}.",
    )
    constraints: Optional[List[str]] = Field(
        default=None, description="List of constraints or assumptions."
    )
    technical_requirements: Optional[List[str]] = Field(
        default=None,
        description="Specific technical requirements, e.g., libraries, frameworks.",
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Optional metadata fields."
    )

    @field_validator("task_description")
    @classmethod
    def task_description_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Task description must not be empty")
        return v

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpecSchema":
        """Creates a SpecSchema instance from a dictionary."""
        try:
            return cls(**data)
        except ValidationError as e:
            # Re-raise or handle specific validation errors
            print(f"Error validating spec data from dict: {e}")
            raise

    @classmethod
    def from_json(cls, json_input: Union[str, Path]) -> "SpecSchema":
        """Creates a SpecSchema instance from a JSON string or file path."""
        data: Dict[str, Any]
        try:
            file_path: Path | None = None
            if isinstance(json_input, Path):
                file_path = json_input
            elif isinstance(json_input, str):
                try:
                    possible_path = Path(json_input)
                    if possible_path.is_file() or possible_path.exists():
                        file_path = possible_path
                except OSError:
                    file_path = None

            if file_path is not None:
                if not file_path.exists():
                    raise FileNotFoundError(f"JSON file not found: {file_path}")
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                # Assume it's a JSON string
                data = json.loads(str(json_input))
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            raise
        except (FileNotFoundError, ValidationError) as e:
            print(f"Error processing JSON input: {e}")
            raise

    @classmethod
    def from_yaml(cls, yaml_input: Union[str, Path]) -> "SpecSchema":
        """Creates a SpecSchema instance from a YAML string or file path."""
        data: Dict[str, Any]
        try:
            file_path: Path | None = None
            if isinstance(yaml_input, Path):
                file_path = yaml_input
            elif isinstance(yaml_input, str):
                try:
                    possible_path = Path(yaml_input)
                    if possible_path.is_file() or possible_path.exists():
                        file_path = possible_path
                except OSError:
                    file_path = None

            if file_path is not None:
                if not file_path.exists():
                    raise FileNotFoundError(f"YAML file not found: {file_path}")
                with file_path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                # Assume it's a YAML string
                data = yaml.safe_load(str(yaml_input))

            if not isinstance(data, dict):
                raise TypeError("YAML content did not parse into a dictionary.")

            if isinstance(data.get("metadata"), dict):
                data["metadata"] = {
                    k: str(v) if not isinstance(v, str) else v
                    for k, v in data["metadata"].items()
                }

            return cls.from_dict(data)
        except yaml.YAMLError as e:
            print(f"Error decoding YAML: {e}")
            raise
        except (FileNotFoundError, ValidationError, TypeError) as e:
            print(f"Error processing YAML input: {e}")
            raise

    @classmethod
    def from_text(cls, text_input: str) -> "SpecSchema":
        """Creates a SpecSchema instance from free-form text with intelligent parsing."""
        text = text_input.strip()
        
        # Initialize parsed data
        parsed_data = {
            "task_description": text,
            "inputs": None,
            "outputs": None,
            "constraints": None,
            "technical_requirements": None,
            "metadata": None
        }
        
        # Parse inputs - look for patterns like "takes X as input", "inputs:", "input: X (type)"
        inputs = cls._parse_inputs(text)
        if inputs:
            parsed_data["inputs"] = inputs
        
        # Parse outputs - look for patterns like "returns X", "outputs:", "output: X (type)"
        outputs = cls._parse_outputs(text)
        if outputs:
            parsed_data["outputs"] = outputs
        
        # Parse constraints - look for patterns like "must", "should", "constraint:", "requirements:"
        constraints = cls._parse_constraints(text)
        if constraints:
            parsed_data["constraints"] = constraints
        
        # Parse technical requirements
        tech_reqs = cls._parse_technical_requirements(text)
        if tech_reqs:
            parsed_data["technical_requirements"] = tech_reqs
        
        # Clean up task description by removing parsed sections
        parsed_data["task_description"] = cls._clean_task_description(text)
        
        return cls(**parsed_data)
    
    @classmethod
    def _parse_inputs(cls, text: str) -> Optional[Dict[str, str]]:
        """Parse inputs from natural language text."""
        inputs = {}
        
        # Pattern 1: "takes X as input", "input is X", "input: X"
        patterns = [
            r"takes?\s+(\w+)\s+(?:\(([^)]+)\))?\s+as\s+input",
            r"input\s+is\s+(\w+)\s+(?:\(([^)]+)\))?",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1)
                type_hint = match.group(2) if match.group(2) else "string"
                inputs[name] = type_hint.strip()
        
        # Pattern 2: Multi-line inputs section  
        inputs_section = re.search(r"^\s*inputs?:\s*$\n((?:\s*-\s*\w+.*\n?)*)", text, re.IGNORECASE | re.MULTILINE)
        if not inputs_section:
            # Try alternative format with space after colon
            inputs_section = re.search(r"^\s*inputs?:\s*\n((?:\s*-\s*\w+.*\n?)*)", text, re.IGNORECASE | re.MULTILINE)
        
        if inputs_section:
            lines = inputs_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().lstrip('- ')
                if line and not line.lower().startswith(('output', 'constraint', 'requirement', 'technical')):
                    match = re.match(r"(\w+)\s*(?:\(([^)]+)\)|:\s*([^,\n]+))?", line)
                    if match:
                        name = match.group(1)
                        type_hint = match.group(2) or match.group(3) or "string"
                        inputs[name] = type_hint.strip()
        
        # Pattern 3: Inline comma-separated inputs
        inline_match = re.search(r"^inputs?:\s*([^\n]+)", text, re.IGNORECASE | re.MULTILINE)
        if inline_match and not inputs:  # Only if we haven't found multi-line inputs
            input_text = inline_match.group(1)
            # Split by comma and parse each
            for item in input_text.split(','):
                item = item.strip()
                match = re.match(r"(\w+)\s*(?:\(([^)]+)\))?", item)
                if match:
                    name = match.group(1)
                    type_hint = match.group(2) if match.group(2) else "string"
                    inputs[name] = type_hint.strip()
        
        return inputs if inputs else None
    
    @classmethod
    def _parse_outputs(cls, text: str) -> Optional[Dict[str, str]]:
        """Parse outputs from natural language text."""
        outputs = {}
        
        # Pattern 1: "returns X", "output is X"
        patterns = [
            r"returns?\s+(\w+)\s+(?:\(([^)]+)\))?",
            r"output\s+is\s+(\w+)\s+(?:\(([^)]+)\))?",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1)
                type_hint = match.group(2) if match.group(2) else "string"
                outputs[name] = type_hint.strip()
        
        # Pattern 2: Multi-line outputs section
        outputs_section = re.search(r"^\s*outputs?:\s*$\n((?:\s*-\s*\w+.*\n?)*)", text, re.IGNORECASE | re.MULTILINE)
        if not outputs_section:
            # Try alternative format with space after colon
            outputs_section = re.search(r"^\s*outputs?:\s*\n((?:\s*-\s*\w+.*\n?)*)", text, re.IGNORECASE | re.MULTILINE)
            
        if outputs_section:
            lines = outputs_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().lstrip('- ')
                if line and not line.lower().startswith(('input', 'constraint', 'requirement', 'technical')):
                    match = re.match(r"(\w+)\s*(?:\(([^)]+)\)|:\s*([^,\n]+))?", line)
                    if match:
                        name = match.group(1)
                        type_hint = match.group(2) or match.group(3) or "string"
                        outputs[name] = type_hint.strip()
        
        # Pattern 3: Inline comma-separated outputs
        inline_match = re.search(r"^outputs?:\s*([^\n]+)", text, re.IGNORECASE | re.MULTILINE)
        if inline_match and not outputs:  # Only if we haven't found multi-line outputs
            output_text = inline_match.group(1)
            for item in output_text.split(','):
                item = item.strip()
                match = re.match(r"(\w+)\s*(?:\(([^)]+)\))?", item)
                if match:
                    name = match.group(1)
                    type_hint = match.group(2) if match.group(2) else "string"
                    outputs[name] = type_hint.strip()
        
        return outputs if outputs else None
    
    @classmethod
    def _parse_constraints(cls, text: str) -> Optional[List[str]]:
        """Parse constraints from natural language text."""
        constraints = []
        
        # Pattern 1: Explicit constraints section
        constraints_section = re.search(r"^\s*constraints?:\s*$\n((?:\s*-\s*.+?\n?)*)", text, re.IGNORECASE | re.MULTILINE)
        if not constraints_section:
            # Try alternative format with space after colon
            constraints_section = re.search(r"^\s*constraints?:\s*\n((?:\s*-\s*.+?\n?)*)", text, re.IGNORECASE | re.MULTILINE)
            
        if constraints_section:
            lines = constraints_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().lstrip('- ')
                if line and not line.lower().startswith(('technical', 'requirement')):
                    constraints.append(line)
        
        # Pattern 2: Inline constraints
        inline_match = re.search(r"^constraints?:\s*([^\n]+)", text, re.IGNORECASE | re.MULTILINE)
        if inline_match and not constraints:  # Only if we haven't found multi-line constraints
            constraint_text = inline_match.group(1).strip()
            if constraint_text:
                constraints.append(constraint_text)
        
        # Pattern 3: "must" statements (standalone sentences)
        must_patterns = [
            r"\bmust\s+([^.]+?)(?=\.|$)",
            r"\bshould\s+([^.]+?)(?=\.|$)",
            r"\bneeds?\s+to\s+([^.]+?)(?=\.|$)",
            r"\brequired?\s+to\s+([^.]+?)(?=\.|$)",
        ]
        
        for pattern in must_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                constraint = match.group(1).strip()
                if constraint and len(constraint) > 3:  # Avoid very short matches
                    formatted_constraint = f"must {constraint}"
                    if formatted_constraint not in constraints:
                        constraints.append(formatted_constraint)
        
        return constraints if constraints else None
    
    @classmethod
    def _parse_technical_requirements(cls, text: str) -> Optional[List[str]]:
        """Parse technical requirements from natural language text."""
        tech_reqs = []
        
        # Pattern 1: Explicit technical requirements section
        tech_section = re.search(r"^\s*(?:technical\s+)?requirements?:\s*$\n((?:\s*-\s*.+?\n?)*)", text, re.IGNORECASE | re.MULTILINE)
        if not tech_section:
            # Try alternative format with space after colon
            tech_section = re.search(r"^\s*(?:technical\s+)?requirements?:\s*\n((?:\s*-\s*.+?\n?)*)", text, re.IGNORECASE | re.MULTILINE)
            
        if tech_section:
            lines = tech_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().lstrip('- ')
                if line:
                    tech_reqs.append(line)
        
        # Pattern 2: Inline technical requirements
        inline_match = re.search(r"^(?:technical\s+)?requirements?:\s*([^\n]+)", text, re.IGNORECASE | re.MULTILINE)
        if inline_match and not tech_reqs:  # Only if we haven't found multi-line requirements
            req_text = inline_match.group(1).strip()
            if req_text:
                tech_reqs.append(req_text)
        
        # Pattern 3: Technology mentions
        tech_patterns = [
            r"using\s+([A-Z][a-zA-Z]+)",
            r"with\s+([A-Z][a-zA-Z]+)",
            r"framework:\s*([A-Za-z][A-Za-z0-9_-]+)",
            r"library:\s*([A-Za-z][A-Za-z0-9_-]+)",
        ]
        
        for pattern in tech_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tech = match.group(1).strip()
                if tech and tech not in tech_reqs and len(tech) > 2:
                    tech_reqs.append(tech)
        
        return tech_reqs if tech_reqs else None
    
    @classmethod
    def _clean_task_description(cls, text: str) -> str:
        """Clean the task description by removing parsed sections."""
        # Remove explicit sections that were parsed
        sections_to_remove = [
            r"^\s*inputs?:\s*$\n(?:\s*-\s*.+\n?)*",
            r"^\s*inputs?:\s*\n(?:\s*-\s*.+\n?)*", 
            r"^\s*outputs?:\s*$\n(?:\s*-\s*.+\n?)*",
            r"^\s*outputs?:\s*\n(?:\s*-\s*.+\n?)*",
            r"^\s*constraints?:\s*$\n(?:\s*-\s*.+?\n?)*",
            r"^\s*constraints?:\s*\n(?:\s*-\s*.+?\n?)*",
            r"^\s*(?:technical\s+)?requirements?:\s*$\n(?:\s*-\s*.+?\n?)*",
            r"^\s*(?:technical\s+)?requirements?:\s*\n(?:\s*-\s*.+?\n?)*",
            r"^inputs?:\s*[^\n]+",
            r"^outputs?:\s*[^\n]+",
            r"^constraints?:\s*[^\n]+",
            r"^(?:technical\s+)?requirements?:\s*[^\n]+",
        ]
        
        cleaned = text
        for pattern in sections_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up extra whitespace and newlines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else text

    def to_dict(self) -> Dict[str, Any]:
        """Convert SpecSchema to dictionary, handling different Pydantic versions."""
        return self.model_dump(exclude_unset=True)

    def to_tool_spec_dict(self) -> Dict[str, Any]:
        """Convert SpecSchema to tool specification dictionary format."""
        spec_dict = self.to_dict()
        
        # Convert SpecSchema format to tool spec format if needed
        metadata = spec_dict.get("metadata") or {}
        tool_spec = {
            "name": metadata.get("name", "Generated Tool"),
            "description": spec_dict.get("task_description", ""),
            "purpose": spec_dict.get("task_description", ""),
            "specification": spec_dict
        }
        
        # Add input/output schemas if available
        if spec_dict.get("inputs"):
            tool_spec["input_schema"] = spec_dict["inputs"]
        if spec_dict.get("outputs"):
            tool_spec["output_schema"] = spec_dict["outputs"]
        
        return tool_spec

    # TODO: Add more specific validation methods as needed
    # TODO: Add helper methods (e.g., for merging specs)
    # TODO: Add serialization/deserialization methods (if needed beyond Pydantic defaults)
