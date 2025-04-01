# Installing OpenAI Agents SDK

## Basic Installation

Install the OpenAI Agents SDK using pip:

```bash
pip install openai-agents
```

## Setting up an OpenAI API Key

Before using the SDK, you need to set up an OpenAI API key:

1. If you don't have an API key, follow [these instructions](https://platform.openai.com/docs/quickstart) to create an OpenAI API key.

2. Set the environment variable:

```bash
export OPENAI_API_KEY=sk-...
```

## Project Setup Example

Here's a complete example of setting up a new project with the OpenAI Agents SDK:

```bash
# Create a new project directory
mkdir my_project
cd my_project

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the Agents SDK
pip install openai-agents

# Set your OpenAI API key
export OPENAI_API_KEY=sk-...
```

## Hello World Example

Create a simple script to test your installation:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)
```

Save this to a file (e.g., `hello_agent.py`) and run it to verify your installation is working correctly.

## Dependencies

The OpenAI Agents SDK uses:
- Pydantic for data validation and schema generation
- Griffe for parsing docstrings
- Python's inspect module for function signature extraction

These dependencies are automatically installed when you install the SDK.
