"""
Specification analyzer for the meta-agent package.

This module contains functions for analyzing natural language descriptions
to extract agent specifications.
"""

from typing import Optional, Dict, Any, List
import json
import re
from agents import function_tool
from meta_agent.models.agent import AgentSpecification


@function_tool()
def analyze_agent_specification(specification: str) -> str:
    """
    Analyze a natural language description to extract agent specifications.
    
    Args:
        specification: Natural language description of the agent to create

    Returns:
        JSON string containing the structured agent specification
    """
    print(f"DEBUG: Received specification:\n{specification!r}")
    
    # Initialize default values
    name = "DefaultAgent"
    description = ""
    instructions = ""
    tools: List[Dict[str, Any]] = []
    output_type = None
    guardrails: List[Dict[str, Any]] = []

    # Extract name
    name_match = re.search(r'Name:\s*(\w+)', specification)
    if name_match:
        name = name_match.group(1)
    print(f"DEBUG: Extracted name: {name!r}")

    # Extract description
    desc_match = re.search(r'Description:\s*([^\n]+(?:\n(?!\n)[^\n]+)*)', specification)
    if desc_match:
        description = desc_match.group(1).strip()
    print(f"DEBUG: Extracted description: {description!r}")

    # Extract instructions
    instr_match = re.search(r'Instructions:\s*([^\n]+(?:\n(?!\n)[^\n]+)*)', specification)
    if instr_match:
        instructions = instr_match.group(1).strip()
    print(f"DEBUG: Extracted instructions: {instructions!r}")

    # Extract tools
    tools_section = re.search(r'Tools needed:(.*?)(?=\n\s*\n|Output type:|Guardrails:|$)', specification, re.DOTALL)
    if tools_section:
        tool_blocks = re.finditer(r'(\d+\.\s*[\w_]+):\s*([^\n]+)(?:\s*-\s*Parameters:\s*((?:\s*-[^\n]+\n?)*))?\s*-\s*Returns:\s*([^\n]+)', tools_section.group(1))
        for tool_block in tool_blocks:
            tool_name = tool_block.group(1).split('.')[-1].strip()
            tool_desc = tool_block.group(2).strip()
            parameters = []
            
            if tool_block.group(3):  # If parameters exist
                param_matches = re.finditer(r'-\s*([\w_]+)\s*\(([\w\s,]+)(?:,\s*(?:required|optional))?(?:,\s*default=([^)]+))?\)', tool_block.group(3))
                for param in param_matches:
                    param_name = param.group(1).strip()
                    param_type = param.group(2).strip().lower()
                    param_default = param.group(3)
                    required = "optional" not in param.group(0).lower()
                    
                    param_dict = {
                        "name": param_name,
                        "type": param_type,
                        "required": required
                    }
                    if param_default:
                        param_dict["default"] = param_default
                    parameters.append(param_dict)

            tool = {
                "name": tool_name,
                "description": tool_desc,
                "parameters": parameters,
                "returns": tool_block.group(4).strip()
            }
            tools.append(tool)
    print(f"DEBUG: Extracted tools: {tools!r}")

    # Extract output type
    output_match = re.search(r'Output type:\s*([^\n]+)', specification)
    if output_match:
        output_type = output_match.group(1).strip()
    print(f"DEBUG: Extracted output type: {output_type!r}")

    # Extract guardrails
    guardrails_section = re.search(r'Guardrails:(.*?)(?=\n\s*\n|$)', specification, re.DOTALL)
    if guardrails_section:
        guardrail_items = re.finditer(r'-\s*([^\n]+)', guardrails_section.group(1))
        for item in guardrail_items:
            guardrails.append({
                "description": item.group(1).strip()
            })
    print(f"DEBUG: Extracted guardrails: {guardrails!r}")

    # Create the specification object
    spec = AgentSpecification(
        name=name,
        description=description,
        instructions=instructions,
        tools=tools,
        output_type=output_type,
        guardrails=guardrails
    )
    
    result = json.dumps(spec.model_dump())
    print(f"DEBUG: Generated JSON: {result!r}")
    return result
