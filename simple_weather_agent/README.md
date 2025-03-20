# Simple Weather Agent

This is a simple example of an OpenAI Agents SDK agent that provides weather information.

## Features

- Get current weather for any location
- Uses the OpenAI Agents SDK
- Simple interactive CLI interface

## Usage

Run the agent:

```bash
python weather_agent.py
```

Then interact with it by asking about the weather:

```
> What's the weather in San Francisco?
> How's the weather in New York?
> What should I wear in London today?
```

Type `exit` to quit.

## Implementation

This agent demonstrates:
- Creating function tools
- Initializing an Agent with the OpenAI Agents SDK 0.0.5
- Setting up a Runner
- Building an interactive CLI loop
