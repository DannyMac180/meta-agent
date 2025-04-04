"""
Agent Generator - A tool for creating OpenAI Agents SDK agents

This script implements a generator that creates self-contained agents
using the OpenAI Agents SDK v0.0.7 based on specifications.
"""

import asyncio
import json
import re
import sys
import traceback
from typing import Any, Dict, List, Optional, Union
from ..models.agent import (
    AgentSpecification,
    GuardrailDefinition,
    OutputTypeDefinition,
    OutputTypeField,
    ToolDefinition,
    ToolParameter,
)


# ===================== SPECIFICATION PARSER =====================

def parse_specification(specification: str) -> AgentSpecification:
    """
    Parse a specification string (JSON or natural language) into an AgentSpecification.
    
    Args:
        specification: A specification string (JSON or natural language)
        
    Returns:
        An AgentSpecification object
    """
    # Try to parse as JSON first
    try:
        json_data = json.loads(specification)
        return parse_json_specification(json_data)
    except json.JSONDecodeError:
        # If not valid JSON, treat as natural language
        return parse_natural_language_specification(specification)
    except Exception as e:
        print(f"Error parsing specification: {e}")
        traceback.print_exc()
        raise


def parse_json_specification(json_data: Dict[str, Any]) -> AgentSpecification:
    """
    Parse a JSON specification into an AgentSpecification.
    
    Args:
        json_data: JSON data as a dictionary
        
    Returns:
        An AgentSpecification object
    """
    # Extract basic fields
    name = json_data.get("name", "DefaultAgent")
    description = json_data.get("description", "")
    instructions = json_data.get("instructions", "")
    
    # Parse tools
    tools = []
    for tool_data in json_data.get("tools", []):
        parameters = []
        for param_data in tool_data.get("parameters", []):
            parameters.append(ToolParameter(
                name=param_data.get("name", ""),
                type=param_data.get("type", "string"),
                description=param_data.get("description", ""),
                required=param_data.get("required", True)
            ))
        
        tools.append(ToolDefinition(
            name=tool_data.get("name", ""),
            description=tool_data.get("description", ""),
            parameters=parameters,
            return_type=tool_data.get("return_type", "string")
        ))
    
    # Parse output type if present
    output_type = None
    if "output_type" in json_data and isinstance(json_data["output_type"], dict):
        output_type_data = json_data["output_type"]
        fields = []
        for field_data in output_type_data.get("fields", []):
            fields.append(OutputTypeField(
                name=field_data.get("name", ""),
                type=field_data.get("type", "string"),
                description=field_data.get("description", ""),
                required=field_data.get("required", True)
            ))
        
        output_type = OutputTypeDefinition(
            name=output_type_data.get("name", "Output"),
            fields=fields
        )
    
    # Parse guardrails
    guardrails = []
    for guardrail_data in json_data.get("guardrails", []):
        guardrails.append(GuardrailDefinition(
            description=guardrail_data.get("description", ""),
            type=guardrail_data.get("type", "output")
        ))
    
    return AgentSpecification(
        name=name,
        description=description,
        instructions=instructions,
        tools=tools,
        output_type=output_type,
        guardrails=guardrails
    )


def parse_natural_language_specification(text: str) -> AgentSpecification:
    """
    Parse a natural language specification into an AgentSpecification.
    
    Args:
        text: Natural language specification text
        
    Returns:
        An AgentSpecification object
    """
    # Default values
    name = "DefaultAgent"
    description = ""
    instructions = text  # Use the entire text as instructions by default
    tools = []
    output_type = None
    guardrails = []
    
    # Extract name
    name_match = re.search(r"(?:^|\n)Name:\s*(.+?)(?:\n|$)", text)
    if name_match:
        name = name_match.group(1).strip()
    
    # Extract description
    desc_match = re.search(r"(?:^|\n)Description:\s*(.+?)(?:\n|$)", text)
    if desc_match:
        description = desc_match.group(1).strip()
    
    # Extract instructions
    instr_match = re.search(r"(?:^|\n)Instructions:\s*(.*?)(?:\n\s*\n|\n(?:Tools|Output type|Guardrails):|$)", text, re.DOTALL)
    if instr_match:
        instructions = instr_match.group(1).strip()
    
    # Extract tools
    tools_section = re.search(r"(?:^|\n)Tools:?\s*(.*?)(?:\n\s*\n|\n(?:Output type|Guardrails):|$)", text, re.DOTALL)
    if tools_section:
        tools_text = tools_section.group(1)
        # Look for numbered tools
        tool_matches = re.finditer(r"(?:^|\n)\s*(\d+)[\.:\)]\s*(\w+):\s*(.+?)(?:\n\s*Parameters:|\n\s*\d+[\.:\)]|\n\s*\n|$)", tools_text, re.DOTALL)
        
        for tool_match in tool_matches:
            tool_name = tool_match.group(2).strip()
            tool_desc = tool_match.group(3).strip()
            
            # Look for parameters
            params = []
            param_section = re.search(rf"{re.escape(tool_desc)}\s*(?:\n\s*Parameters:)?\s*(.*?)(?:\n\s*\d+[\.:\)]|\n\s*\n|$)", tools_text, re.DOTALL)
            if param_section:
                param_text = param_section.group(1)
                param_matches = re.finditer(r"(?:^|\n)\s*[-•*]\s*(\w+)(?:\s*\((\w+)(?:,\s*(\w+))?\))?\s*:\s*(.+?)(?:\n\s*[-•*]|\n\s*\n|$)", param_text, re.DOTALL)
                
                for param_match in param_matches:
                    param_name = param_match.group(1).strip()
                    param_type = param_match.group(2) if param_match.group(2) else "string"
                    param_required = "optional" not in param_match.group(4).lower() if param_match.group(4) else True
                    param_desc = param_match.group(4).strip() if param_match.group(4) else ""
                    
                    params.append(ToolParameter(
                        name=param_name,
                        type=param_type,
                        description=param_desc,
                        required=param_required
                    ))
            
            tools.append(ToolDefinition(
                name=tool_name,
                description=tool_desc,
                parameters=params,
                return_type="string"  # Default return type
            ))
    
    # Extract output type
    output_section = re.search(r"(?:^|\n)Output type:\s*(.*?)(?:\n\s*\n|\n(?:Guardrails):|$)", text, re.DOTALL)
    if output_section:
        output_text = output_section.group(1).strip()
        # Check if it's a structured output
        if "fields:" in output_text.lower() or "-" in output_text:
            output_name = "Output"
            name_match = re.search(r"(?:^|\n)Name:\s*(.+?)(?:\n|$)", output_text)
            if name_match:
                output_name = name_match.group(1).strip()
            
            fields = []
            field_matches = re.finditer(r"(?:^|\n)\s*[-•*]\s*(\w+)(?:\s*\((\w+)(?:,\s*(\w+))?\))?\s*:\s*(.+?)(?:\n\s*[-•*]|\n\s*\n|$)", output_text, re.DOTALL)
            
            for field_match in field_matches:
                field_name = field_match.group(1).strip()
                field_type = field_match.group(2) if field_match.group(2) else "string"
                field_required = "optional" not in field_match.group(4).lower() if field_match.group(4) else True
                field_desc = field_match.group(4).strip() if field_match.group(4) else ""
                
                fields.append(OutputTypeField(
                    name=field_name,
                    type=field_type,
                    description=field_desc,
                    required=field_required
                ))
            
            if fields:
                output_type = OutputTypeDefinition(
                    name=output_name,
                    fields=fields
                )
    
    # Extract guardrails
    guardrails_section = re.search(r"(?:^|\n)Guardrails:\s*(.*?)(?:\n\s*\n|$)", text, re.DOTALL)
    if guardrails_section:
        guardrails_text = guardrails_section.group(1)
        guardrail_matches = re.finditer(r"(?:^|\n)\s*[-•*]\s*(.+?)(?:\n\s*[-•*]|\n\s*\n|$)", guardrails_text, re.DOTALL)
        
        for guardrail_match in guardrail_matches:
            guardrail_desc = guardrail_match.group(1).strip()
            guardrail_type = "output"
            if "input" in guardrail_desc.lower():
                guardrail_type = "input"
            
            guardrails.append(GuardrailDefinition(
                description=guardrail_desc,
                type=guardrail_type
            ))
    
    return AgentSpecification(
        name=name,
        description=description,
        instructions=instructions,
        tools=tools,
        output_type=output_type,
        guardrails=guardrails
    )


# ===================== CODE GENERATION =====================

def generate_tool_code(tool: ToolDefinition) -> str:
    """
    Generate Python code for a tool based on its definition.
    
    Args:
        tool: Tool definition
        
    Returns:
        Python code implementing the tool
    """
    params = []
    for param in tool.parameters:
        param_type = _convert_type(param.type)
        if param.required:
            params.append(f"{param.name}: {param_type}")
        else:
            params.append(f"{param.name}: {param_type} = None")
    
    params_str = ", ".join(params)
    return_type = _convert_type(tool.return_type)
    
    docstring = f'"""\n{tool.description}\n\n'
    if tool.parameters:
        docstring += "Args:\n"
        for param in tool.parameters:
            docstring += f"    {param.name}: {param.description}\n"
    docstring += f'\nReturns:\n    {return_type}: {tool.description} result\n"""'
    
    code = [
        f"@function_tool",
        f"def {tool.name}({params_str}) -> {return_type}:",
        f"    {docstring}",
        f"    # TODO: Implement the tool functionality",
        f"    # This is a placeholder implementation",
        f"    return f\"Result for {tool.name} with parameters: {{{', '.join([p.name + '=' + p.name for p in tool.parameters])}}}\""
    ]
    
    return "\n".join(code)


def generate_output_type_code(output_type: OutputTypeDefinition) -> str:
    """
    Generate Python code for an output type based on its definition.
    
    Args:
        output_type: Output type definition
        
    Returns:
        Python code defining the output type
    """
    # Generate class definition
    code = [
        f"class {output_type.name}(BaseModel):",
        f'    """Output type for {output_type.name}."""'
    ]
    
    # Generate fields
    for field in output_type.fields:
        field_type = _convert_type(field.type)
        if field.required:
            code.append(f"    {field.name}: {field_type} = Field(description=\"{field.description}\")")
        else:
            code.append(f"    {field.name}: Optional[{field_type}] = Field(default=None, description=\"{field.description}\")")
    
    # Add an empty line if there are no fields
    if not output_type.fields:
        code.append("    pass")
    
    return "\n".join(code)


def generate_guardrail_code(guardrail: GuardrailDefinition) -> str:
    """
    Generate Python code for a guardrail based on its definition.
    
    Args:
        guardrail: Guardrail definition
        
    Returns:
        Python code implementing the guardrail
    """
    guardrail_name = "validate_" + re.sub(r'[^a-zA-Z0-9]', '_', guardrail.description.lower())[:30]
    
    if guardrail.type.lower() == "input":
        code = [
            f"@input_guardrail",
            f"def {guardrail_name}(input_text: str) -> GuardrailFunctionOutput:",
            f'    """',
            f'    {guardrail.description}',
            f'    ',
            f'    Args:',
            f'        input_text: The input text to validate',
            f'    ',
            f'    Returns:',
            f'        GuardrailFunctionOutput indicating whether the input is valid',
            f'    """',
            f"    # TODO: Implement the guardrail validation logic",
            f"    # This is a placeholder implementation",
            f"    return GuardrailFunctionOutput(is_valid=True)"
        ]
    else:  # output guardrail
        code = [
            f"@output_guardrail",
            f"def {guardrail_name}(output_text: str) -> GuardrailFunctionOutput:",
            f'    """',
            f'    {guardrail.description}',
            f'    ',
            f'    Args:',
            f'        output_text: The output text to validate',
            f'    ',
            f'    Returns:',
            f'        GuardrailFunctionOutput indicating whether the output is valid',
            f'    """',
            f"    # TODO: Implement the guardrail validation logic",
            f"    # This is a placeholder implementation",
            f"    return GuardrailFunctionOutput(is_valid=True)"
        ]
    
    return "\n".join(code)


def generate_agent_code(spec: AgentSpecification) -> str:
    """
    Generate Python code for creating an agent based on its specification.
    
    Args:
        spec: Agent specification
        
    Returns:
        Python code creating the agent
    """
    code = [
        f"def create_agent():",
        f'    """',
        f'    Create a {spec.name} agent.',
        f'    ',
        f'    Returns:',
        f'        An initialized Agent instance',
        f'    """'
    ]
    
    # Generate agent initialization
    code.append(f"    # Create the agent")
    code.append(f"    agent = Agent(")
    code.append(f'        name="{spec.name}",')
    
    # Add instructions with proper indentation
    instructions = spec.instructions.replace('\n', '\n        ')
    code.append(f'        instructions="""{instructions}""",')
    
    # Add tools if present
    if spec.tools:
        code.append(f"        tools=[")
        for tool in spec.tools:
            code.append(f"            {tool.name},")
        code.append(f"        ],")
    
    # Add output type if present
    if spec.output_type:
        code.append(f"        output_type={spec.output_type.name},")
    
    # Add guardrails if present
    if spec.guardrails:
        input_guardrails = [g for g in spec.guardrails if g.type.lower() == "input"]
        output_guardrails = [g for g in spec.guardrails if g.type.lower() == "output"]
        
        if input_guardrails:
            code.append(f"        input_guardrails=[")
            for guardrail in input_guardrails:
                guardrail_name = "validate_" + re.sub(r'[^a-zA-Z0-9]', '_', guardrail.description.lower())[:30]
                code.append(f"            {guardrail_name},")
            code.append(f"        ],")
        
        if output_guardrails:
            code.append(f"        output_guardrails=[")
            for guardrail in output_guardrails:
                guardrail_name = "validate_" + re.sub(r'[^a-zA-Z0-9]', '_', guardrail.description.lower())[:30]
                code.append(f"            {guardrail_name},")
            code.append(f"        ],")
    
    # Close agent initialization
    code.append(f"    )")
    code.append(f"    return agent")
    
    return "\n".join(code)


def generate_runner_code() -> str:
    """
    Generate Python code for running an agent.
    
    Returns:
        Python code for running the agent
    """
    code = [
        f"async def run_agent(input_text: str):",
        f'    """',
        f'    Run the agent with the given input text.',
        f'    ',
        f'    Args:',
        f'        input_text: The input text to send to the agent',
        f'    ',
        f'    Returns:',
        f'        The agent\'s response',
        f'    """',
        f"    agent = create_agent()",
        f"    result = await Runner.run(agent, input_text)",
        f"    return result.final_output",
        f"",
        f"",
        f"async def main():",
        f'    """',
        f'    Main function to run the agent interactively.',
        f'    """',
        f"    print(\"Agent is ready. Type 'exit' to quit.\")",
        f"    while True:",
        f"        user_input = input(\"> \")",
        f"        if user_input.lower() == 'exit':",
        f"            break",
        f"        ",
        f"        try:",
        f"            agent_result = await run_agent(user_input)",
        f"            print(f\"\\nAgent: {{agent_result}}\\n\")",
        f"        except Exception as e:",
        f"            print(f\"Error: {{e}}\")",
        f"",
        f"",
        f"if __name__ == \"__main__\":",
        f"    asyncio.run(main())"
    ]
    
    return "\n".join(code)


def assemble_agent_implementation(
    spec: AgentSpecification,
    tool_code: List[str],
    output_type_code: Optional[str],
    guardrail_code: List[str],
    agent_code: str,
    runner_code: str
) -> str:
    """
    Assemble all code components into a single Python file.
    
    Args:
        spec: Agent specification
        tool_code: List of tool code strings
        output_type_code: Output type code string (if any)
        guardrail_code: List of guardrail code strings
        agent_code: Agent creation code string
        runner_code: Runner code string
        
    Returns:
        Complete Python code as a string
    """
    # Generate file header
    header = [
        f'"""',
        f'{spec.name} - {spec.description}',
        f'',
        f'This is a self-contained agent implementation using the OpenAI Agents SDK v0.0.7.',
        f'"""',
        f'',
        f'import asyncio',
        f'import os',
        f'from typing import Dict, List, Any, Optional',
        f'',
        f'from pydantic import BaseModel, Field',
        f'from agents import Agent, Runner, function_tool, input_guardrail, output_guardrail, GuardrailFunctionOutput',
        f'',
        f'# Check for OpenAI API key',
        f'if not os.environ.get("OPENAI_API_KEY"):',
        f'    print("Warning: OPENAI_API_KEY environment variable not set.")',
        f'    print("Please set it with: export OPENAI_API_KEY=your_api_key")',
        f''
    ]
    
    # Combine all code components
    components = []
    
    # Add output type if present
    if output_type_code:
        components.append("# Output Type Definition")
        components.append(output_type_code)
        components.append("")
    
    # Add tools
    if tool_code:
        components.append("# Tool Definitions")
        components.append("\n\n".join(tool_code))
        components.append("")
    
    # Add guardrails
    if guardrail_code:
        components.append("# Guardrail Definitions")
        components.append("\n\n".join(guardrail_code))
        components.append("")
    
    # Add agent creation code
    components.append("# Agent Creation")
    components.append(agent_code)
    components.append("")
    
    # Add runner code
    components.append("# Agent Runner")
    components.append(runner_code)
    
    # Assemble the complete file
    return "\n".join(header + components)


# ===================== HELPER FUNCTIONS =====================

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


# ===================== MAIN GENERATOR FUNCTION =====================

def generate_agent(specification: str, output_file: Optional[str] = None) -> str:
    """
    Generate an agent based on a specification.
    
    Args:
        specification: A specification string (JSON or natural language)
        output_file: Optional file path to write the generated code
        
    Returns:
        The generated Python code as a string
    """
    try:
        # Parse the specification
        spec = parse_specification(specification)
        
        # Generate code for tools
        from meta_agent.generators.tool_generator import generate_tools_code_sync
        tool_code = generate_tools_code_sync(spec.tools).split("\n\n")[1:]  # Skip imports
        
        # Generate code for output type if specified
        output_type_code = None
        if spec.output_type:
            output_type_code = generate_output_type_code(spec.output_type)
        
        # Generate code for guardrails
        guardrail_code = [generate_guardrail_code(guardrail) for guardrail in spec.guardrails]
        
        # Generate code for agent creation
        agent_code = generate_agent_code(spec)
        
        # Generate code for running the agent
        runner_code = generate_runner_code()
        
        # Assemble the complete implementation
        implementation = assemble_agent_implementation(
            spec=spec,
            tool_code=tool_code,
            output_type_code=output_type_code,
            guardrail_code=guardrail_code,
            agent_code=agent_code,
            runner_code=runner_code
        )
        
        # Write to file if specified
        if output_file:
            with open(output_file, "w") as f:
                f.write(implementation)
            print(f"Agent code written to {output_file}")
        
        return implementation
    except Exception as e:
        print(f"Error in generate_agent: {str(e)}")
        traceback.print_exc()
        # Re-raise the exception for proper error handling
        raise


# ===================== COMMAND LINE INTERFACE =====================

async def main():
    """Main function to run the agent generator."""
    print("Welcome to the OpenAI Agents SDK Agent Generator!")
    
    # Check if a specification file was provided
    if len(sys.argv) > 1:
        spec_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "generated_agent.py"
        
        try:
            with open(spec_file, "r") as f:
                specification = f.read()
            
            print(f"Generating agent from specification file: {spec_file}")
            generate_agent(specification, output_file)
            print(f"Agent generated successfully and saved to {output_file}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            traceback.print_exc()
    else:
        # Interactive mode
        print("Please describe the agent you want to create:")
        print("(Type or paste your specification, then press Ctrl+D (Unix) or Ctrl+Z (Windows) to finish)")
        
        specification_lines = []
        try:
            while True:
                line = input()
                specification_lines.append(line)
        except EOFError:
            specification = "\n".join(specification_lines)
        
        if not specification.strip():
            print("Error: Empty specification")
            return
        
        print("\nGenerating agent based on your specification...")
        try:
            generate_agent(specification, "generated_agent.py")
            print("Agent generated successfully and saved to generated_agent.py")
        except Exception as e:
            print(f"Error generating agent: {str(e)}")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
