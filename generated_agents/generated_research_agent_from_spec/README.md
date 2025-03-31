# ResearchAgent

An advanced research agent that searches the web for information on complex topics,

## Installation

```bash
pip install openai-agents==0.0.7
```

## Usage

```python

# Basic usage
import asyncio
from agent_implementation import create_agent
from agents import Runner

async def run_agent():
    agent = create_agent()
    result = await Runner.run(agent, "Your query here")
    print(result.final_output)

asyncio.run(run_agent())

```
