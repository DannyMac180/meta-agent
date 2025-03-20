import inspect
from agents import function_tool
from meta_agent.agent_generator import design_agent_tools
import json

# Inspect the function signature
print(f"Function signature: {inspect.signature(design_agent_tools)}")

# Get the function tool schema
original_design_agent_tools = design_agent_tools.__wrapped__  # Get the original function
print(f"Original function: {original_design_agent_tools}")

# Debug the generated schema
tool = design_agent_tools
if hasattr(tool, "_openai_schema"):
    schema = tool._openai_schema()
    print("Tool schema:")
    print(json.dumps(schema, indent=2))
else:
    print("Tool does not have _openai_schema")
