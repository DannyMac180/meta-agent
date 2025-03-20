import json
from meta_agent.agent_generator import agent

# Print the agent's name and instructions
print(f"Agent name: {agent.name}")

# Print information about the tools
for i, tool in enumerate(agent.tools):
    print(f"\nTool {i+1}: {tool.name}")
    print(f"Description: {tool.description}")
    if hasattr(tool, "get_openai_tool"):
        openai_tool = tool.get_openai_tool()
        print(f"OpenAI tool schema:\n{json.dumps(openai_tool, indent=2)}")
    elif hasattr(tool, "_openai_schema"):
        schema = tool._openai_schema()
        print(f"Schema:\n{json.dumps(schema, indent=2)}")
    else:
        print("No schema available")
