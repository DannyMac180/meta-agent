"""
Mock implementation of the OpenAI Agents SDK for testing.
"""

import json # Ensure json is imported
# Import the actual tool to simulate its execution
from meta_agent.design.analyzer import analyze_agent_specification as actual_analyzer_tool
from tests.mocks.decorators import function_tool

class Agent:
    """Mock Agent class for testing."""
    
    def __init__(self, name=None, instructions=None, tools=None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
    
    def tool(self, func=None):
        """Mock tool decorator."""
        def decorator(f):
            self.tools.append(f)
            return f
        
        if func is None:
            return decorator
        return decorator(func)


# Mock RunResult class
class RunResult:
    """Mock RunResult class for testing."""
    def __init__(self, final_output=None, tool_outputs=None):
        self.final_output = final_output
        self.tool_outputs = tool_outputs if tool_outputs is not None else [] # Ensure it's a list


class Runner:
    """Mock Runner class for testing."""
    
    def __init__(self):
        pass
    
    @staticmethod
    async def run(agent, specification_or_prompt): # Rename input param for clarity
        """Mock run method that returns different results based on the prompt."""
        # Check if input is empty
        if not specification_or_prompt or not specification_or_prompt.strip():
            raise ValueError("Agent specification cannot be empty")
            
        prompt = specification_or_prompt # Assume input is the prompt string

        # Check if this is an analyze_agent_specification call
        if "analyze_agent_specification" in prompt:
            print("DEBUG Mock: Simulating analyze_agent_specification tool call")
            # Simulate LLM deciding to call the tool.
            # The tool itself expects the raw specification string.

            # Simulate extracting the original spec from the prompt
            # (This is crude, real LLM does this based on context)
            spec_marker = "```\n"
            start_index = prompt.find(spec_marker)
            end_index = prompt.rfind("```")
            original_spec = ""
            if start_index != -1 and end_index != -1:
                 original_spec = prompt[start_index + len(spec_marker):end_index].strip()
            else: # Fallback if markers not found
                 print("WARN Mock: Could not find spec markers in prompt, using full prompt as spec.")
                 original_spec = specification_or_prompt # Less accurate simulation

            # Simulate executing the *actual* tool function
            try:
                 # Call the actual tool function from analyzer.py
                 tool_output_json = actual_analyzer_tool(specification=original_spec)
                 print(f"DEBUG Mock: Tool execution returned: {tool_output_json!r}")
                 
                 # Return a RunResult containing this output in tool_outputs
                 return RunResult(
                     final_output="Analysis complete.", # Simulate agent's final text
                     tool_outputs=[tool_output_json]  # The analyzer returns a JSON string
                 )
            except Exception as e:
                 print(f"DEBUG Mock: Error executing actual tool: {e}")
                 # Return an error or empty result to simulate failure
                 return RunResult(final_output=f"Error during analysis: {e}", tool_outputs=[])

        # --- Simulate other tool calls similarly ---
        # These need to return JSON *strings* in tool_outputs

        # Check if this is a design_agent_tools call
        elif "design_agent_tools" in prompt:
            print("DEBUG Mock: Simulating design_agent_tools call")
            # Simulate the tool returning a JSON string containing a list of tool definitions
            tool_output_json_str = json.dumps({
                "tools": [
                    # Example tool definition structure
                    {
                        "name": "search_web",
                        "description": "Searches the web for information",
                        "parameters": [
                            {"name": "query", "type": "string", "required": True},
                            {"name": "num_results", "type": "integer", "required": False, "default": 8}
                        ],
                        "return_type": "str", # Often JSON string
                        "implementation": "# Placeholder" # Mock doesn't need full impl
                    },
                     {
                        "name": "extract_content",
                        "description": "Extracts the main content from a URL",
                        "parameters": [{"name": "url", "type": "string", "required": True}],
                        "return_type": "str",
                        "implementation": "# Placeholder"
                    }
                    # Add other tools based on expected spec if needed for testing
                ]
            })
            return RunResult(
                final_output="Tools designed.",
                tool_outputs=[tool_output_json_str]
            )

        # Check if this is a design_output_type call
        elif "design_output_type" in prompt:
            print("DEBUG Mock: Simulating design_output_type call")
            # Simulate tool returning JSON string for output type def, or empty if none
            tool_output_json_str = json.dumps({
                 "name": "ResearchReport",
                 "fields": [
                    {"name": "summary", "type": "string", "description": "Executive summary"},
                    {"name": "references", "type": "List[str]", "description": "Cited sources"}
                 ],
                 "code": "# Placeholder code" # Mock doesn't need full code here
            })
            # Or return an empty dict/null if no output type is needed:
            # tool_output_json_str = json.dumps({})
            return RunResult(
                final_output="Output type designed (or not needed).",
                tool_outputs=[tool_output_json_str]
            )

        # Check if this is a generate_tool_code call
        elif "generate_tool_code" in prompt:
            print("DEBUG Mock: Simulating generate_tool_code call")
            # Simulate returning JSON string with the code
            # Extract tool name from prompt crudely for mock response
            tool_name = "some_tool"
            if "search_web" in prompt: tool_name = "search_web"
            if "extract_content" in prompt: tool_name = "extract_content"

            tool_code = f"""
@function_tool()
def {tool_name}(...): # Add args based on tool_name if needed
    \"\"\"Docstring for {tool_name}.\"\"\"
    # TODO: Implement {tool_name} logic here
    print(f"Executing mock {tool_name}")
    return "Mock result from {tool_name}"
"""
            tool_output_json_str = json.dumps({"code": tool_code})
            return RunResult(
                final_output=f"Code generated for {tool_name}.",
                tool_outputs=[tool_output_json_str]
            )

        # Check if this is a generate_output_type_code call
        elif "generate_output_type_code" in prompt:
            print("DEBUG Mock: Simulating generate_output_type_code call")
            # Simulate returning JSON string with the pydantic code
            output_code = """
from pydantic import BaseModel, Field
from typing import List

class ResearchReport(BaseModel):
    \"\"\"Generated output type.\"\"\"
    summary: str = Field(..., description="Executive summary")
    references: List[str] = Field(default_factory=list, description="Cited sources")
"""
            tool_output_json_str = json.dumps({"code": output_code})
            return RunResult(
                final_output="Output type code generated.",
                tool_outputs=[tool_output_json_str]
            )

        # Check if this is a generate_agent_creation_code call
        elif "generate_agent_creation_code" in prompt:
            print("DEBUG Mock: Simulating generate_agent_creation_code call")
            # Simulate returning JSON string with agent definition code
            agent_creation_code = """
research_agent = Agent(
    name="ResearchAgent",
    instructions=\"\"\"<Agent instructions here>\"\"\",
    tools=[search_web, extract_content], # Use function names
    output_type=ResearchReport # Use class name
)
"""
            tool_output_json_str = json.dumps({"code": agent_creation_code})
            return RunResult(
                final_output="Agent creation code generated.",
                tool_outputs=[tool_output_json_str]
            )

        # Check if this is a generate_runner_code call
        elif "generate_runner_code" in prompt:
            print("DEBUG Mock: Simulating generate_runner_code call")
            # Simulate returning JSON string with runner code
            runner_code = """
async def main():
    runner = Runner()
    print("Starting ResearchAgent...")
    # Example run
    result = await runner.run(research_agent, "What are the effects of climate change?")
    print("Result:", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""
            tool_output_json_str = json.dumps({"code": runner_code})
            return RunResult(
                final_output="Runner code generated.",
                tool_outputs=[tool_output_json_str]
            )

        # Check if this is an assemble_agent_implementation call
        elif "assemble_agent_implementation" in prompt:
            print("DEBUG Mock: Simulating assemble_agent_implementation call")
            # Simulate returning the final AgentImplementation structure as a JSON string
            # In a real scenario, the assembler tool would construct this
            implementation_dict = {
                "main_file": """
# Agent implementation for TestAgent
from agents import Agent, Runner

def main():
    agent = Agent(name="TestAgent")
    user_input = input("Enter your request: ")
    await Runner.run(agent, user_input)
""",
                "additional_files": {
                    "requirements.txt": "openai-agents>=0.0.7\npydantic>=2.0\npython-dotenv>=1.0.0"
                },
                "installation_instructions": "pip install -r requirements.txt",
                "usage_examples": "python main.py"
            }
            tool_output_json_str = json.dumps(implementation_dict)
            return RunResult(
                final_output="Assembly complete.",
                tool_outputs=[tool_output_json_str]
            )

        # Default response if no specific tool trigger matched
        print(f"DEBUG Mock: No specific tool trigger matched for prompt: {prompt[:100]}...")
        return RunResult(
            final_output=f"Mock response for: {specification_or_prompt[:50]}...",
            tool_outputs=[]
        )
