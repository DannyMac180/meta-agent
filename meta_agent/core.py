"""
Core functionality for the Meta Agent.

This module contains the main entry point for generating agents from specifications.
"""

import json
from typing import Dict, Any, Optional, Union

from meta_agent.models import AgentSpecification, AgentImplementation
from meta_agent.generators.agent_generator import generate_agent as generate_agent_file_content
from meta_agent.utils import parse_json_string


def generate_agent(specification: str, output_dir: Optional[str] = None) -> AgentImplementation:
    """
    Generate an agent based on a natural language or JSON specification.
    
    Args:
        specification: A specification string describing the agent to create.
                      Can be either a JSON string or a natural language description.
        output_dir: Optional directory to write the generated agent files to.
                   If provided, the agent files will be written to this directory.
    
    Returns:
        Complete agent implementation
        
    Raises:
        ValueError: If the specification is empty or invalid
        Exception: If any step of the generation process fails
    """
    # Check for empty specification
    if not specification or not specification.strip():
        raise ValueError("Agent specification cannot be empty")
    
    # Parse the specification (needed for README)
    agent_spec = _parse_specification(specification)
    
    # Generate the agent implementation code string
    main_file_content = generate_agent_file_content(specification)

    # Construct the implementation object (assuming no extra files for now)
    # TODO: Potentially parse generated code for dependencies to improve instructions
    installation_instructions = f"pip install openai agents\n# Add other dependencies from agent_implementation.py if needed"
    usage_examples = f"# Save the generated code as agent_implementation.py\n\n# Run the agent:\npython agent_implementation.py --spec '...' # Replace ... with your spec or path to spec file"

    implementation = AgentImplementation(
        main_file=main_file_content,
        additional_files={},
        installation_instructions=installation_instructions,
        usage_examples=usage_examples,
    )
    
    # Write files if output directory is provided
    if output_dir:
        from meta_agent.utils import ensure_directory, write_file
        ensure_directory(output_dir)
        
        # Write main file
        main_file_path = f"{output_dir}/agent_implementation.py"
        write_file(main_file_path, implementation.main_file)
        
        # Write additional files
        for filename, content in implementation.additional_files.items():
            file_path = f"{output_dir}/{filename}"
            write_file(file_path, content)
        
        # Write README with usage instructions
        readme_content = f"""# {agent_spec.name}

{agent_spec.description}

## Installation

```bash
{implementation.installation_instructions}
```

## Usage

```python
{implementation.usage_examples}
```
"""
        write_file(f"{output_dir}/README.md", readme_content)
    
    return implementation


def _parse_specification(specification: str) -> AgentSpecification:
    """
    Parse a specification string into an AgentSpecification.
    
    This function attempts to parse the specification as JSON first.
    If that fails, it treats it as a natural language description and
    uses a simplified parsing approach.
    
    Args:
        specification: The specification string
        
    Returns:
        An AgentSpecification object
        
    Raises:
        ValueError: If the specification cannot be parsed
    """
    # Try to parse as JSON first
    try:
        spec_dict = parse_json_string(specification)
        return AgentSpecification(**spec_dict)
    except json.JSONDecodeError:
        # Not valid JSON, treat as natural language
        # For now, use a simplified approach
        return _parse_natural_language(specification)


def _parse_natural_language(specification: str) -> AgentSpecification:
    """
    Parse a natural language specification into an AgentSpecification.
    
    This is a simplified implementation that extracts basic information
    from the natural language description.
    
    Args:
        specification: The natural language specification
        
    Returns:
        An AgentSpecification object
    """
    lines = specification.strip().split('\n')
    
    # Extract name (first line or default)
    name = "DefaultAgent"
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
            break
    
    # Extract description
    description = ""
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.lower().startswith("description:"):
            description = line.split(":", 1)[1].strip()
            break
    
    # Extract instructions
    instructions = specification
    
    # Extract tools (simplified)
    tools = []
    tool_section = False
    current_tool = None
    
    for line in lines:
        line = line.strip()
        if line.lower().startswith("tools needed:") or line.lower() == "tools:":
            tool_section = True
            continue
        
        if tool_section and line:
            if line[0].isdigit() and ":" in line:
                # New tool
                if current_tool:
                    tools.append(current_tool)
                
                # Parse tool name and description
                parts = line.split(":", 1)
                tool_name = parts[0].strip().split(".", 1)[-1].strip()
                tool_desc = parts[1].strip() if len(parts) > 1 else ""
                
                from meta_agent.models import ToolDefinition, ToolParameter
                current_tool = ToolDefinition(
                    name=tool_name,
                    description=tool_desc,
                    parameters=[],
                    return_type="string"
                )
            
            # Check for parameters section
            elif current_tool and "parameters:" in line.lower():
                continue
            
            # Parse parameters
            elif current_tool and "-" in line and ":" in line:
                param_parts = line.split(":", 1)
                param_name = param_parts[0].strip("-").strip()
                param_desc = param_parts[1].strip()
                
                # Try to extract type information
                param_type = "string"  # default
                if "(" in param_name and ")" in param_name:
                    type_start = param_name.find("(")
                    type_end = param_name.find(")")
                    param_type = param_name[type_start+1:type_end].strip()
                    param_name = param_name[:type_start].strip()
                
                # Check if required
                required = True
                if "optional" in param_desc.lower():
                    required = False
                
                from meta_agent.models import ToolParameter
                current_tool.parameters.append(ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=param_desc,
                    required=required
                ))
    
    # Add the last tool if exists
    if current_tool:
        tools.append(current_tool)
    
    # Extract guardrails
    guardrails = []
    guardrail_section = False
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.lower().startswith("guardrails:"):
            guardrail_section = True
            continue
        
        if guardrail_section and line.strip() and line.strip().startswith("-"):
            guardrail_desc = line.strip("-").strip()
            
            from meta_agent.models import GuardrailDefinition
            guardrails.append(GuardrailDefinition(
                description=guardrail_desc,
                implementation=""
            ))
    
    return AgentSpecification(
        name=name,
        description=description,
        instructions=instructions,
        tools=tools,
        output_type=None,
        guardrails=guardrails
    )
