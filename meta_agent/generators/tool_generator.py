"""
Tool generator module.

This module contains functions for generating tool code based on tool definitions.
"""

from typing import List
from meta_agent.models import ToolDefinition


def generate_tool_code(tool: ToolDefinition) -> str:
    """
    Generate Python code for a tool based on its definition.
    
    Args:
        tool: The tool definition
        
    Returns:
        Python code implementing the tool using the function_tool decorator
    """
    # Generate function signature
    params_code = []
    for param in tool.parameters:
        param_type = _convert_type(param.type)
        if param.required:
            params_code.append(f"{param.name}: {param_type}")
        else:
            params_code.append(f"{param.name}: {param_type} = None")
    
    params_str = ", ".join(params_code)
    return_type = _convert_type(tool.return_type)
    
    # Generate docstring
    docstring = f'"""\n{tool.description}\n\n'
    if tool.parameters:
        docstring += "Args:\n"
        for param in tool.parameters:
            docstring += f"    {param.name}: {param.description}\n"
    docstring += f'\nReturns:\n    {return_type}: {tool.return_type} result\n"""'
    
    # Generate function implementation
    code = [
        f"@function_tool",
        f"def {tool.name}({params_str}) -> {return_type}:",
        f"    {docstring}",
        f"    # TODO: Implement the tool functionality",
        f"    # This is a placeholder implementation",
        f"    return f\"Result for {tool.name} with parameters: {{{', '.join([p.name + '=' + p.name for p in tool.parameters])}}}\""
    ]
    
    return "\n".join(code)


def generate_tools_code(tools: List[ToolDefinition]) -> str:
    """
    Generate Python code for multiple tools.
    
    Args:
        tools: List of tool definitions
        
    Returns:
        Python code implementing all tools
    """
    imports = [
        "from agents import function_tool",
        "from typing import Dict, List, Any, Optional",
        ""
    ]
    
    tool_codes = [generate_tool_code(tool) for tool in tools]
    
    return "\n\n".join(imports + tool_codes)


def _convert_type(type_str: str) -> str:
    """
    Convert a type string to a Python type annotation.
    
    Args:
        type_str: Type string from the specification
        
    Returns:
        Python type annotation
    """
    type_mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "Dict[str, Any]",
        "array": "List[Any]"
    }
    
    return type_mapping.get(type_str.lower(), "Any")
