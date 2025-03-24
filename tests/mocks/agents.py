"""
Mock implementation of the OpenAI Agents SDK for testing.
"""

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


class Runner:
    """Mock Runner class for testing."""
    
    def __init__(self):
        pass
    
    @staticmethod
    async def run(agent, specification):
        """Mock run method that returns different results based on the specification."""
        # Check if specification is empty
        if not specification or not specification.strip():
            raise ValueError("Agent specification cannot be empty")
            
        # Check if this is an analyze_agent_specification call
        if "Analyze this agent specification" in specification:
            return {
                "name": "TestAgent",
                "description": "Test description",
                "instructions": "Test instructions"
            }
        # Check if this is a design_agent_tools call
        elif "Design tools for this agent" in specification:
            return [{
                "name": "test_tool", 
                "description": "A test tool",
                "parameters": [{"name": "param1", "type": "string", "required": True}],
                "return_type": "string",
                "implementation": "def test_tool(param1):\n    return f'Result: {param1}'"
            }]
        # Check if this is a design_output_type call
        elif "Design an output type" in specification:
            return {
                "name": "TestOutput",
                "fields": [{"name": "result", "type": "string", "description": "Result of the tool execution"}],
                "code": "class TestOutput(BaseModel):\n    result: str = Field(description='Result of the tool execution')"
            }
        # Check if this is a design_guardrails call
        elif "Design guardrails" in specification:
            return [{
                "name": "test_guardrail", 
                "description": "A test guardrail",
                "type": "input",
                "validation_logic": "Check if input contains sensitive information",
                "implementation": "def validate_input(input_text):\n    return 'password' not in input_text.lower()"
            }]
        # Check if this is a generate_tool_code call
        elif "Generate code for this tool" in specification:
            return "def test_tool(param1):\n    return f'Result: {param1}'"
        # Check if this is a generate_output_type_code call
        elif "Generate code for this output type" in specification:
            return "class TestOutput(BaseModel):\n    result: str = Field(description='Result of the tool execution')"
        # Check if this is a generate_guardrail_code call
        elif "Generate code for this guardrail" in specification:
            return "def validate_input(input_text):\n    return 'password' not in input_text.lower()"
        # Check if this is a generate_agent_creation_code call
        elif "Generate code that creates an agent instance" in specification:
            return "from agents import Agent\n\nagent = Agent(name='TestAgent', instructions='Test instructions')"
        # Check if this is a generate_runner_code call
        elif "Generate code that runs the agent" in specification:
            return "from agents import Runner\n\nrunner = Runner()\n\n# Run the agent\nawait Runner.run(agent, user_input)"
        # Check if this is an assemble_agent_implementation call
        elif "Assemble the complete agent implementation" in specification:
            return {
                "main_file": """
# Agent implementation for TestAgent
from agents import Agent, Runner

def test_tool(param1):
    return f'Result: {param1}'

# Create the agent
agent = Agent(name='TestAgent', instructions='Test instructions')

async def main():
    runner = Runner()
    await Runner.run(agent, user_input)
""",
                "additional_files": {
                    "requirements.txt": "agents>=0.0.6\npython-dotenv>=1.0.0"
                },
                "installation_instructions": "pip install -r requirements.txt",
                "usage_examples": "python main.py"
            }
        # Check if this is a validate_agent_implementation call
        elif "Validate this agent implementation" in specification:
            return {"valid": True, "message": "Agent implementation is valid"}
        # Default response
        return "Mock response for: " + specification[:50] + "..."


def function_tool(func=None, *, name=None, description=None):
    """Mock function_tool decorator."""
    def decorator(f):
        f._function_tool = True
        f._name = name or f.__name__
        f._description = description or f.__doc__
        return f
    
    if func is None:
        return decorator
    return decorator(func)
