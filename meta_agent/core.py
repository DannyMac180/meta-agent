"""
Proposed fixes for core.py to generate proper OpenAI Agents SDK implementations.

This implementation focuses on generating code that directly uses the OpenAI Agents SDK
classes and decorators, following the pattern shown in the simple_agent.py example.
"""

import asyncio
from typing import Dict, List, Any, Optional
import json
from agents import Runner
from pydantic import ValidationError

from meta_agent.models import (
    AgentSpecification,
    ToolDefinition,
    OutputTypeDefinition,
    AgentDesign,
    AgentCode,
    AgentImplementation
)
from meta_agent.config import load_config, check_api_key, print_api_key_warning

# Import the configured agent generator
from meta_agent.generation.agent_generator import agent_generator

async def generate_agent(specification: str, model_override: Optional[str] = None) -> AgentImplementation:
    """
    Generate an agent based on a natural language specification.

    Args:
        specification: A natural language description of the agent to create
        model_override: Optional model override for the generator

    Returns:
        Complete agent implementation

    Raises:
        ValueError: If the specification is empty.
        Exception: If any step of the generation process fails.
    """
    # Check for empty specification
    if not specification or not specification.strip():
        raise ValueError("Agent specification cannot be empty")

    # Load configuration and check API key
    load_config()
    if not check_api_key():
        print_api_key_warning()
        # Decide if execution should stop or continue with potential errors
        # For now, we'll let it continue, but it will likely fail.

    # Initialize the runner
    runner = Runner()

    print("Starting agent generation process...")

    # Step 1: Analyze the specification
    try:
        print("Step 1: Analyzing agent specification...")
        analysis_prompt = f"Analyze the following agent specification and return the structured result using the 'analyze_agent_specification' tool:\n\n```\n{specification}\n```"
        analysis_result = await runner.run(agent_generator, analysis_prompt)

        # Extract the structured result (JSON string) returned *by* the tool execution
        tool_output_json = None
        if hasattr(analysis_result, 'tool_outputs') and analysis_result.tool_outputs:
            # Assume the last tool output corresponds to the analysis tool's execution result
            tool_output = analysis_result.tool_outputs[-1]
            if isinstance(tool_output, str):
                tool_output_json = tool_output
            # Add handling if tool_output is already a dict (less likely based on error)
            elif isinstance(tool_output, dict):
                print("DEBUG: tool_output is already a dict, attempting to dump back to JSON.")
                tool_output_json = json.dumps(tool_output)

        if not tool_output_json:
            print(f"DEBUG: Failed to find tool output JSON in tool_outputs. Analysis Result: {analysis_result}")
            # As a fallback, check if final_output contains the JSON (less ideal)
            if hasattr(analysis_result, 'final_output') and isinstance(analysis_result.final_output, str) and analysis_result.final_output.strip().startswith('{'):
                print("DEBUG: Attempting to parse final_output as JSON fallback.")
                tool_output_json = analysis_result.final_output
            else:
                raise Exception("Could not find the JSON output from the 'analyze_agent_specification' tool in tool_outputs or final_output.")

        # Now, parse the confirmed JSON string
        agent_spec_dict = json.loads(tool_output_json)
        agent_specification = AgentSpecification.model_validate(agent_spec_dict)
        print(f"  -> Analyzed Specification: {agent_specification.name}")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 1 (Analysis): {e}")
        print(f"Analysis Result: {analysis_result if 'analysis_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to analyze agent specification: {e}") from e

    # Step 2: Design the tools
    try:
        print("Step 2: Designing agent tools...")
        design_tools_prompt = f"Based on this AgentSpecification JSON, design the necessary tools using the 'design_agent_tools' tool:\n\n```json\n{agent_specification.model_dump_json(indent=2)}\n```"
        tools_result = await runner.run(agent_generator, design_tools_prompt)

        # Extract the structured result (JSON string) returned *by* the tool execution
        tools_output_json = None
        if hasattr(tools_result, 'tool_outputs') and tools_result.tool_outputs:
            tool_output = tools_result.tool_outputs[-1]
            if isinstance(tool_output, str):
                tools_output_json = tool_output
        if not tools_output_json and hasattr(tools_result, 'final_output') and isinstance(tools_result.final_output, str) and tools_result.final_output.strip().startswith('{'):
            print("DEBUG: Using final_output for tools JSON fallback.")
            tools_output_json = tools_result.final_output
        if not tools_output_json:
             raise Exception("Could not find the JSON output from the 'design_agent_tools' tool.")

        tools_dict = json.loads(tools_output_json)
        tools_list = tools_dict.get('tools', [])  # Assuming tool returns {"tools": [...]}
        designed_tools = [ToolDefinition.model_validate(t) for t in tools_list]
        print(f"  -> Designed {len(designed_tools)} tools: {[t.name for t in designed_tools]}")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 2 (Tool Design): {e}")
        print(f"Tools Result: {tools_result if 'tools_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to design agent tools: {e}") from e

    # Step 3: Design the output type (if specified)
    designed_output_type: Optional[OutputTypeDefinition] = None
    output_type_code: Optional[str] = None
    try:
        print("Step 3: Designing output type (if specified)...")
        if agent_specification.output_type:  # Check if output type was mentioned
            design_output_prompt = f"The specification mentions an output type: '{agent_specification.output_type}'. Design a Pydantic model for this using the 'design_output_type' tool. Based on this AgentSpecification:\n\n```json\n{agent_specification.model_dump_json(indent=2)}\n```"
            output_type_result = await runner.run(agent_generator, design_output_prompt)

            # Extract the structured result (JSON string) returned *by* the tool execution
            output_type_json = None
            if hasattr(output_type_result, 'tool_outputs') and output_type_result.tool_outputs:
                tool_output = output_type_result.tool_outputs[-1]
                if isinstance(tool_output, str):
                    output_type_json = tool_output
            if not output_type_json and hasattr(output_type_result, 'final_output') and isinstance(output_type_result.final_output, str) and output_type_result.final_output.strip().startswith('{'):
                 print("DEBUG: Using final_output for output type JSON fallback.")
                 output_type_json = output_type_result.final_output

            if output_type_json: # Check if LLM returned a design JSON
                output_type_dict = json.loads(output_type_json)
                designed_output_type = OutputTypeDefinition.model_validate(output_type_dict)
                print(f"  -> Designed Output Type: {designed_output_type.name}")

                # Step 3b: Generate Output Type Code
                print("Step 3b: Generating output type code...")
                gen_output_code_prompt = f"Generate the Python code for this Pydantic OutputTypeDefinition using the 'generate_output_type_code' tool:\n\n```json\n{designed_output_type.model_dump_json(indent=2)}\n```"
                output_code_result = await runner.run(agent_generator, gen_output_code_prompt)

                # Extract the code string from the tool output
                output_code_json = None
                if hasattr(output_code_result, 'tool_outputs') and output_code_result.tool_outputs:
                    tool_output = output_code_result.tool_outputs[-1]
                    if isinstance(tool_output, str):
                        output_code_json = tool_output
                if not output_code_json and hasattr(output_code_result, 'final_output') and isinstance(output_code_result.final_output, str) and output_code_result.final_output.strip().startswith('{'):
                    print("DEBUG: Using final_output for output code JSON fallback.")
                    output_code_json = output_code_result.final_output
                else:
                    raise Exception("Could not find the JSON output from the 'generate_output_type_code' tool.")

                output_code_dict = json.loads(output_code_json)
                output_type_code = output_code_dict.get('code')
                if not output_type_code:
                    raise Exception("LLM failed to generate output type code.")
                print(f"  -> Generated code for {designed_output_type.name}")
            else:
                print("  -> No specific output type designed by LLM.")
        else:
            print("  -> No output type specified in the initial request.")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 3 (Output Type): {e}")
        print(f"Output Type Result: {output_type_result if 'output_type_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to design output type: {e}") from e

    # Step 4: Generate Tool Code
    try:
        print("Step 4: Generating tool code...")
        generated_tool_codes = []
        for tool in designed_tools:
            gen_tool_code_prompt = f"Generate the Python code for this ToolDefinition using the 'generate_tool_code' tool:\n\n```json\n{tool.model_dump_json(indent=2)}\n```"
            tool_code_result = await runner.run(agent_generator, gen_tool_code_prompt)

            # Extract the code string from the tool output
            tool_code_json = None
            if hasattr(tool_code_result, 'tool_outputs') and tool_code_result.tool_outputs:
                tool_output = tool_code_result.tool_outputs[-1]
                if isinstance(tool_output, str):
                    tool_code_json = tool_output
            if not tool_code_json and hasattr(tool_code_result, 'final_output') and isinstance(tool_code_result.final_output, str) and tool_code_result.final_output.strip().startswith('{'):
                print(f"DEBUG: Using final_output for {tool.name} code JSON fallback.")
                tool_code_json = tool_code_result.final_output
            else:
                raise Exception(f"Could not find the JSON output from the 'generate_tool_code' tool for {tool.name}.")

            tool_code_dict = json.loads(tool_code_json)
            tool_code = tool_code_dict.get('code')
            if not tool_code:
                raise Exception(f"LLM failed to generate code for tool {tool.name}")
            generated_tool_codes.append(tool_code)
            print(f"  -> Generated code for tool: {tool.name}")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 4 (Tool Code Generation): {e}")
        print(f"Tool Code Result: {tool_code_result if 'tool_code_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to generate tool code: {e}") from e

    # Step 5: Generate Agent Definition Code
    try:
        print("Step 5: Generating agent definition code...")
        agent_def_context = {
            "specification": agent_specification.model_dump(),
            "tool_names": [t.name for t in designed_tools],
            "output_type_name": designed_output_type.name if designed_output_type else None
        }
        gen_agent_code_prompt = f"Generate the Python code to define the Agent instance using the 'generate_agent_creation_code' tool, based on this context:\n\n```json\n{json.dumps(agent_def_context, indent=2)}\n```\nInclude the 'tools' list with the function names and 'output_type' if specified."
        agent_code_result = await runner.run(agent_generator, gen_agent_code_prompt)

        # Extract the code string from the tool output
        agent_code_json = None
        if hasattr(agent_code_result, 'tool_outputs') and agent_code_result.tool_outputs:
            tool_output = agent_code_result.tool_outputs[-1]
            if isinstance(tool_output, str):
                agent_code_json = tool_output
        if not agent_code_json and hasattr(agent_code_result, 'final_output') and isinstance(agent_code_result.final_output, str) and agent_code_result.final_output.strip().startswith('{'):
            print("DEBUG: Using final_output for agent code JSON fallback.")
            agent_code_json = agent_code_result.final_output
        else:
            raise Exception("Could not find the JSON output from the 'generate_agent_creation_code' tool.")

        agent_code_dict = json.loads(agent_code_json)
        agent_definition_code = agent_code_dict.get('code')
        if not agent_definition_code:
            raise Exception("LLM failed to generate agent definition code.")
        print(f"  -> Generated agent definition code for {agent_specification.name}")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 5 (Agent Definition Code): {e}")
        print(f"Agent Code Result: {agent_code_result if 'agent_code_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to generate agent definition code: {e}") from e

    # Step 6: Generate Runner Code
    try:
        print("Step 6: Generating runner code...")
        gen_runner_code_prompt = f"Generate a standard Python `async def main(): ...` runner block using the 'generate_runner_code' tool for the agent named '{agent_specification.name}'. It should initialize a Runner and run the agent in an interactive loop or with a sample query."
        runner_code_result = await runner.run(agent_generator, gen_runner_code_prompt)

        # Extract the code string from the tool output
        runner_code_json = None
        if hasattr(runner_code_result, 'tool_outputs') and runner_code_result.tool_outputs:
            tool_output = runner_code_result.tool_outputs[-1]
            if isinstance(tool_output, str):
                runner_code_json = tool_output
        if not runner_code_json and hasattr(runner_code_result, 'final_output') and isinstance(runner_code_result.final_output, str) and runner_code_result.final_output.strip().startswith('{'):
            print("DEBUG: Using final_output for runner code JSON fallback.")
            runner_code_json = runner_code_result.final_output
        else:
            raise Exception("Could not find the JSON output from the 'generate_runner_code' tool.")

        runner_code_dict = json.loads(runner_code_json)
        runner_code = runner_code_dict.get('code')
        if not runner_code:
            raise Exception("LLM failed to generate runner code.")
        print("  -> Generated runner code")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 6 (Runner Code Generation): {e}")
        print(f"Runner Code Result: {runner_code_result if 'runner_code_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to generate runner code: {e}") from e

    # Step 7: Assemble Implementation
    try:
        print("Step 7: Assembling final implementation...")
        assembly_input = {
            "agent_name": agent_specification.name,
            "tool_implementations": generated_tool_codes,
            "output_type_implementation": output_type_code,
            "agent_creation_code": agent_definition_code,
            "runner_code": runner_code,
        }
        assemble_prompt = f"Assemble the complete agent implementation using the 'assemble_agent_implementation' tool with the following generated code parts:\n\n```json\n{json.dumps(assembly_input, indent=2)}\n```"
        assembly_result = await runner.run(agent_generator, assemble_prompt)

        # Extract the AgentImplementation dict from the tool output
        implementation_json = None
        if hasattr(assembly_result, 'tool_outputs') and assembly_result.tool_outputs:
            tool_output = assembly_result.tool_outputs[-1]
            if isinstance(tool_output, str):
                implementation_json = tool_output
        if not implementation_json and hasattr(assembly_result, 'final_output') and isinstance(assembly_result.final_output, str) and assembly_result.final_output.strip().startswith('{'):
             print("DEBUG: Using final_output for assembly JSON fallback.")
             implementation_json = assembly_result.final_output
        else:
             raise Exception("Could not find the JSON output from the 'assemble_agent_implementation' tool.")

        agent_implementation = AgentImplementation.model_validate(json.loads(implementation_json))
        print("  -> Assembled final AgentImplementation")

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"Error during Step 7 (Assembly): {e}")
        print(f"Assembly Result: {assembly_result if 'assembly_result' in locals() else 'N/A'}")
        raise Exception(f"Failed to assemble agent implementation: {e}") from e

    print("Agent generation completed successfully.")
    return agent_implementation

def generate_sdk_implementation(agent_design: AgentDesign) -> str:
    """
    Generate a complete agent implementation following the OpenAI Agents SDK pattern.
    
    Args:
        agent_design: The agent design to implement
        
    Returns:
        Complete implementation code
    """
    # Generate imports
    imports = [
        "import asyncio",
        "import json",
        "import requests",
        "from typing import Optional, Dict, List, Any",
        "from agents import Agent, Runner, function_tool"
    ]
    
    # Generate tool implementations
    tool_implementations = []
    tool_names = []
    
    for tool in agent_design.tools:
        tool_name = tool.get("name", "unknown_tool")
        tool_names.append(tool_name)
        tool_description = tool.get("description", "")
        parameters = tool.get("parameters", [])
        returns = tool.get("returns", "Any")
        
        # Generate parameter string for function definition
        param_strings = []
        for param in parameters:
            param_name = param.get("name", "param")
            param_type = param.get("type", "str")
            param_required = param.get("required", True)
            
            if param_required:
                param_strings.append(f"{param_name}: {param_type}")
            else:
                default_value = param.get("default", "None")
                param_strings.append(f"{param_name}: Optional[{param_type}] = {default_value}")
        
        param_string = ", ".join(param_strings)
        
        # Generate docstring
        docstring = f'"""\n    {tool_description}\n    \n    Args:'
        for param in parameters:
            param_name = param.get("name", "param")
            param_description = param.get("description", "")
            docstring += f'\n        {param_name}: {param_description}'
        
        docstring += f'\n    \n    Returns:\n        {returns}\n    """'
        
        # Generate function body with more realistic placeholder implementation
        function_body = ""
        if tool_name == "search_web":
            function_body = """
    # This is a placeholder implementation - replace with actual functionality
    result = {
        "results": [
            {
                "title": f"Search result 1 for {query}",
                "snippet": "This is a snippet of the search result.",
                "url": "https://example.com/result1"
            },
            {
                "title": f"Search result 2 for {query}",
                "snippet": "This is another snippet of the search result.",
                "url": "https://example.com/result2"
            }
        ],
        "total_results": 2
    }
    return json.dumps(result)
"""
        elif tool_name == "extract_content":
            function_body = """
    # This is a placeholder implementation - replace with actual functionality
    content = f"Extracted content from {url}"
    return content
"""
        elif tool_name == "analyze_source":
            function_body = """
    # This is a placeholder implementation - replace with actual functionality
    analysis = {
        "credibility_score": 0.8,
        "analysis": f"Analysis of content from {url}"
    }
    return json.dumps(analysis)
"""
        elif tool_name == "summarize_content":
            function_body = """
    # This is a placeholder implementation - replace with actual functionality
    summary = "Summary of the provided texts."
    return summary
"""
        else:
            function_body = f"""
    # This is a placeholder implementation - replace with actual functionality
    result = {{"status": "success", "message": f"Executed {tool_name}"}}
    return json.dumps(result)
"""
        
        # Assemble the complete tool implementation
        tool_impl = f"""
@function_tool
def {tool_name}({param_string}) -> str:
    {docstring}{function_body}
"""
        tool_implementations.append(tool_impl)
    
    # Generate agent creation code
    agent_name = agent_design.specification.name
    agent_instructions = agent_design.specification.instructions
    
    # Ensure agent_name is a string
    if not isinstance(agent_name, str):
        agent_name = str(agent_name)
    
    # Create the agent creation code with proper tool references
    agent_creation = f"""
# Create the {agent_name} agent
{agent_name.lower()}_agent = Agent(
    name="{agent_name}",
    instructions=\"\"\"
    {agent_instructions}
    \"\"\",
    tools=[{', '.join(tool_names)}]
)

# Create a runner for the agent
runner = Runner()
"""
    
    # Generate main function
    main_function = f"""
async def main():
    \"\"\"Run the agent.\"\"\"
    print(f"Welcome to the {agent_name}!")
    print("Enter your query or 'exit' to quit.")
    
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break
        
        print("Processing your request...")
        result = await runner.run({agent_name.lower()}_agent, user_input)
        
        print("\\nResult:")
        print(result)
        print()

if __name__ == "__main__":
    asyncio.run(main())
"""
    
    # Assemble the complete implementation
    implementation_parts = [
        "\n".join(imports),
        "\n\n".join(tool_implementations),
        agent_creation,
        main_function
    ]
    
    return "\n\n".join(implementation_parts)

# Example usage (optional, for testing)
# async def main_test():
#     spec = """
#     Create a simple agent that responds to greetings.
#     Name: GreetingAgent
#     Description: A simple agent that responds to greetings in different languages.
#     Instructions: You are a friendly greeting agent...
#     Tools needed:
#     1. detect_language: Detects the language...
#     2. translate_greeting: Translates a greeting...
#     Output type: A simple text response
#     """
#     try:
#         impl = await generate_agent(spec)
#         print("\n--- Generated Main File ---")
#         print(impl.main_file)
#         print("\n--- Installation ---")
#         print(impl.installation_instructions)
#         print("\n--- Usage ---")
#         print(impl.usage_examples)
#     except Exception as e:
#         print(f"\nError generating agent: {e}")

# if __name__ == "__main__":
#     asyncio.run(main_test())
