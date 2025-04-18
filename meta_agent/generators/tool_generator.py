"""
Tool generator module.

This module contains functions for generating tool code based on tool definitions.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple

from meta_agent.models import ToolDefinition

# Strategy constants for tool generation
STRATEGY_STANDARD = "standard"
STRATEGY_SIMPLE = "simple"
STRATEGY_EXTERNAL = "external"
STRATEGY_FALLBACK = "fallback"

# Map of standard agent tools to their Responses API import path and async flag
_STANDARD_TOOL_MAP: dict[str, tuple[str, bool, list[str]]] = {
    "web_search": ("agents.tools.web_search", True, ["query", "num_results"]),
    "web_browse": ("agents.tools.web_browse", True, ["url"]),
    "python":     ("agents.tools.python",     True, ["code"]),
    # add more standard tools here as needed
}

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
    
    strategy = _pick_strategy(tool)
    if strategy == STRATEGY_STANDARD:
        implementation = _build_standard_wrapper(tool)
    elif strategy == STRATEGY_SIMPLE:
        implementation = _build_simple_impl(tool)
    elif strategy == STRATEGY_EXTERNAL:
        api_meta = await _discover_external_api(tool)
        implementation = await _build_external_api_impl(tool, api_meta)
    else:
        implementation = _build_fallback_stub(tool)

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
    Handles already-running event loops gracefully (e.g., in interactive environments).
    Args:
        tools: List of tool definitions
    Returns:
        Python code implementing all tools
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(generate_tools_code(tools))
            except ImportError:
                # Fallback: run as a coroutine (will only work if called from async context)
                coro = generate_tools_code(tools)
                import warnings
                warnings.warn("nest_asyncio not installed, returning coroutine. Install nest_asyncio for full sync support.")
                return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(generate_tools_code(tools))
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


async def _discover_external_api(tool: ToolDefinition) -> Optional[Dict[str, Any]]:
    """
    Discover an external public API matching the tool definition via web_search.
    
    Args:
        tool: The tool definition
        
    Returns:
        A dict with API metadata (endpoint, method, params) or None if not found
    """
    try:
        try:
            from agents import Agent, Runner, function_tool
            from agents.tools import web_search
        except ImportError:
            return None
            
        query = f"python implementation for {tool.name} function"
        if tool.description:
            query += f" that {tool.description.lower()}"
            
        if tool.parameters:
            param_names = [p.name for p in tool.parameters]
            query += f" with parameters {', '.join(param_names)}"
            
        search_results = await web_search(query, num_results=3)
        
        if not search_results or isinstance(search_results, str) and "error" in search_results.lower():
            return None
            
        return search_results
    except Exception as e:
        return None


def _build_fallback_stub(tool: ToolDefinition) -> str:
    """
    Build a fallback stub implementation for the generated tool.
    Returns a runnable default implementation based on tool.return_type.
    """
    implementation_lines: list[str] = []
    implementation_lines.append("    import json")
    implementation_lines.append("    try:")
    
    # ------- build the params dictionary -------
    if tool.parameters:
        param_entries = ", ".join(
            [f'\"{p.name}\": {p.name}' for p in tool.parameters]
        )
        implementation_lines.append(f"        params = {{{param_entries}}}")
    else:
        implementation_lines.append("        params = {}")
    
    # ------- choose return strategy -------
    rt = (tool.return_type or "any").lower()
    if rt in {"string", "str"}:
        implementation_lines.append("        return json.dumps(params)")
    elif rt in {"integer", "int", "number", "float"}:
        implementation_lines.append(
            "        if params and all(isinstance(v, (int, float)) for v in params.values()):"
        )
        implementation_lines.append("            return sum(params.values())")
        implementation_lines.append("        return len(params)")
    elif rt in {"boolean", "bool"}:
        implementation_lines.append("        return all(bool(v) for v in params.values())")
    elif rt in {"object", "dict"}:
        implementation_lines.append("        return params")
    elif rt in {"array", "list"}:
        implementation_lines.append("        return list(params.values())")
    else:
        implementation_lines.append("        return params")
    
    # ------- error handling -------
    implementation_lines.append("    except Exception as e:")
    implementation_lines.append("        return f\"Error in generated tool: {str(e)}\"")
    
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


def _is_standard_tool(tool: ToolDefinition) -> bool:
    return tool.name.lower() in _STANDARD_TOOL_MAP

def _can_simple_impl(tool: ToolDefinition) -> bool:
    """
    Determine if the tool is simple enough for an inline standard Python implementation.
    """
    SIMPLE_KEYWORDS = {
        "reverse": "string",
        "uppercase": "string",
        "lowercase": "string",
        "length": "string",
        "sum": "number",
        "average": "number",
        "count": "array",
    }
    desc = tool.description.lower()
    rt = (tool.return_type or "").lower()
    for kw, expected_rt in SIMPLE_KEYWORDS.items():
        if kw in desc and expected_rt in rt:
            return True
    return False

def _pick_strategy(tool: ToolDefinition) -> str:
    if _is_standard_tool(tool):
        return STRATEGY_STANDARD
    if _can_simple_impl(tool):
        return STRATEGY_SIMPLE
    # external if an API is found
    # note: call _discover_external_api at usage time
    return STRATEGY_EXTERNAL

def _build_standard_wrapper(tool: ToolDefinition) -> str:
    """
    Generate a thin wrapper using standard Responses API tool.
    """
    import_path, is_async, params = _STANDARD_TOOL_MAP[tool.name.lower()]
    # Build import statement (will be included once by generate_tools_code)
    wrapper_name = tool.name
    sig_params = []
    for p in tool.parameters:
        default = "" if p.required else " = None"
        sig_params.append(f"{p.name}: {_convert_type(p.type)}{default}")
    sig = ", ".join(sig_params)
    call_args = ", ".join([f"{n}={n}" for n in params])
    lines = []
    decorator = "@function_tool"
    async_kw = "async " if is_async else ""
    lines.append(f"{decorator}")
    lines.append(f"{async_kw}def {wrapper_name}({sig}) -> {_convert_type(tool.return_type)}:")
    lines.append(f'    """Thin wrapper around `{import_path}`."""')
    if is_async:
        lines.append(f"    return await {import_path}({call_args})")
    else:
        lines.append(f"    return {import_path}({call_args})")
    return "\n".join(lines)

def _build_simple_impl(tool: ToolDefinition) -> str:
    """
    Inline implementation for simple tools (e.g., uppercase, lowercase).
    """
    name = tool.name
    rt = tool.return_type.lower()
    if "uppercase" in tool.description.lower():
        return f"""    return {tool.parameters[0].name}.upper()"""
    if "lowercase" in tool.description.lower():
        return f"""    return {tool.parameters[0].name}.lower()"""
    if "reverse" in tool.description.lower():
        return f"""    return {tool.parameters[0].name}[::-1]"""
    if "length" in tool.description.lower():
        return f"""    return len({tool.parameters[0].name})"""
    # default fallback to params stub
    return _build_fallback_stub(tool)

async def _build_external_api_impl(tool: ToolDefinition, api_meta: Dict[str, Any]) -> str:
    """
    Generate code calling an external REST API based on discovered api_meta.
    """
    if api_meta is None:
        return _build_fallback_stub(tool)
    endpoint = api_meta.get("endpoint")
    method = api_meta.get("method", "GET").upper()
    params = api_meta.get("params", [])
    # choose sync requests by default
    code = [
        "    import requests, json",
        "    try:",
        f"        resp = requests.{method.lower()}(",
        f"            \"{endpoint}\",",
        f"            params={{ {', '.join([f'\"{p}\": {p}' for p in tool.parameters])} }}",
        "        )",
        "        data = resp.json()",
        "        return json.dumps(data)",
        "    except Exception as e:",
        "        return f\"Error calling external API: {str(e)}\""
    ]
    return "\n".join(code)
