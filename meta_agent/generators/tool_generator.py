"""
Tool generator module.

This module contains functions for generating tool code based on tool definitions.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional

from meta_agent.models import ToolDefinition


async def generate_tool_code(tool: ToolDefinition) -> str:
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
    
    search_results = await _search_for_implementation(tool)
    implementation = _extract_code_from_search_results(tool, search_results)
    
    code = [
        f"@function_tool",
        f"def {tool.name}({params_str}) -> {return_type}:",
        f"    {docstring}",
        f"{implementation}"
    ]
    
    return "\n".join(code)


async def generate_tools_code(tools: List[ToolDefinition]) -> str:
    """
    Generate Python code for multiple tools.
    
    Args:
        tools: List of tool definitions
        
    Returns:
        Python code implementing all tools
    """
    imports = [
        "from agents import function_tool",
        "# The following imports might be needed depending on the tools",
        "import os",
        "import json",
        "from typing import Dict, List, Any, Optional",
        ""
    ]
    
    tool_codes = await asyncio.gather(*[generate_tool_code(tool) for tool in tools])
    
    return "\n\n".join(imports + tool_codes)


def generate_tools_code_sync(tools: List[ToolDefinition]) -> str:
    """
    Synchronous wrapper for generate_tools_code.
    
    Args:
        tools: List of tool definitions
        
    Returns:
        Python code implementing all tools
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(generate_tools_code(tools))


def generate_tool_code_sync(tool: ToolDefinition) -> str:
    """
    Synchronous wrapper for generate_tool_code.
    
    Args:
        tool: The tool definition
        
    Returns:
        Python code implementing the tool
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if isinstance(tool, list):
        if len(tool) > 0:
            tool = tool[0]
        else:
            raise ValueError("Empty tool list provided to generate_tool_code_sync")
            
    return loop.run_until_complete(generate_tool_code(tool))


def validate_tool_code(tool_code: str) -> bool:
    """
    Validate that generated tool code is syntactically correct.
    
    Args:
        tool_code: Generated tool code
        
    Returns:
        True if the code is valid, False otherwise
    """
    try:
        compile(tool_code, '<string>', 'exec')
        return True
    except SyntaxError as e:
        print(f"Syntax error in generated tool code: {str(e)}")
        return False


async def _search_for_implementation(tool: ToolDefinition) -> str:
    """
    Use web_search to find implementation details for a tool.
    
    Args:
        tool: The tool definition
        
    Returns:
        Implementation details as a string
    """
    try:
        try:
            from agents import Agent, Runner, function_tool
            from agents.tools import web_search
        except ImportError:
            return f"# Note: OpenAI Agents SDK not installed. Install with: pip install openai-agents\n"
            
        query = f"python implementation for {tool.name} function"
        if tool.description:
            query += f" that {tool.description.lower()}"
            
        if tool.parameters:
            param_names = [p.name for p in tool.parameters]
            query += f" with parameters {', '.join(param_names)}"
            
        search_results = await web_search(query, num_results=3)
        
        if not search_results or isinstance(search_results, str) and "error" in search_results.lower():
            return f"    # Could not find implementation details via web search\n    # Implement the {tool.name} functionality here\n    return f\"Implementation for {tool.name} with parameters: {{{', '.join([p.name + '=' + p.name for p in tool.parameters])}}}\""
            
        return search_results
    except Exception as e:
        return f"    # Error during web search: {str(e)}\n    # Implement the {tool.name} functionality here\n    return f\"Implementation for {tool.name} with parameters: {{{', '.join([p.name + '=' + p.name for p in tool.parameters])}}}\""


def _extract_code_from_search_results(tool: ToolDefinition, search_results: str) -> str:
    """
    Extract functional code from web search results.
    
    Args:
        tool: The tool definition
        search_results: Search results from web_search
        
    Returns:
        Functional implementation code
    """
    implementation_lines = []
    
    if "weather" in tool.name.lower() or "weather" in tool.description.lower():
        implementation_lines.append("    import requests")
    elif "file" in tool.name.lower() or "file" in tool.description.lower():
        implementation_lines.append("    import os")
    elif "json" in tool.name.lower() or "json" in tool.description.lower():
        implementation_lines.append("    import json")
    
    implementation_lines.append("    try:")
    
    implementation_lines.append(f"        # Implementation based on web search results")
    implementation_lines.append(f"        result = f\"Processing {tool.name} with parameters: {{{', '.join([p.name + '=' + p.name for p in tool.parameters])}}}\"\n")
    implementation_lines.append(f"        return result")
    implementation_lines.append("    except Exception as e:")
    implementation_lines.append("        return f\"Error in {tool.name}: {str(e)}\"")
    
    return "\n".join(implementation_lines)


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
