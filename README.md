# OpenAI Agents SDK Meta Agent

This repository contains a meta agent designed to create other agents using the OpenAI Agents SDK. The meta agent takes a natural language description of an agent design and generates a fully functional agent that conforms to the OpenAI Agents SDK specifications.

## Overview

The OpenAI Agents SDK Meta Agent (or Agent Generator) is a sophisticated tool that leverages the OpenAI Agents SDK to create a system capable of designing and implementing other agents. It follows a multi-step process to transform natural language specifications into executable agent code.

## Features

- **Natural Language Input**: Describe the agent you want in plain English
- **Structured Design Process**: Converts specifications into detailed agent blueprints
- **Code Generation**: Produces complete, runnable Python code
- **Multi-Agent Architecture**: Uses specialized sub-agents for different parts of the process
- **Validation**: Includes validation to ensure generated agents work correctly

## Architecture

The meta agent is built using a multi-agent architecture with specialized agents for different parts of the process:

1. **Specification Analyzer**: Parses natural language descriptions into structured specifications
2. **Tool Designer**: Designs tools based on the agent's requirements
3. **Output Type Designer**: Creates structured output types when needed
4. **Guardrail Designer**: Implements appropriate guardrails for input/output validation
5. **Code Generators**: Generate code for tools, output types, guardrails, and agent creation
6. **Implementation Assembler**: Combines all components into a complete implementation
7. **Implementation Validator**: Validates the generated code for correctness

## Installation

1. Ensure you have Python 3.8+ installed
2. Install the OpenAI Agents SDK:
   ```
   pip install openai-agents
   ```
3. Clone this repository or download the source files
4. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage

Run the agent generator with your agent specification:

```python
import asyncio
from agent_generator import generate_agent

async def main():
    specification = """
    Create a weather agent that can provide weather information for cities.
    
    Name: WeatherAgent
    
    Description: An agent that provides current weather information for cities worldwide.
    
    Instructions: You are a helpful weather assistant. When users ask about the weather
    in a specific city, use the get_weather tool to fetch that information.
    
    Tools needed:
    1. get_weather: Fetches current weather for a city
       - Parameters: city (string, required)
       - Returns: Weather data including temperature, conditions, humidity
    """
    
    implementation = await generate_agent(specification)
    
    # Save the implementation
    with open("weather_agent.py", "w") as f:
        f.write(implementation.main_file)
    
    # Save any additional files
    for filename, content in implementation.additional_files.items():
        with open(filename, "w") as f:
            f.write(content)

if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Test Script

You can also use the included test script to generate example agents:

```bash
python test_agent_generator.py
```

This will generate three example agents:
- A weather agent
- A research agent
- A customer service agent

## Agent Specification Format

When describing your agent, include the following information:

- **Name**: A name for your agent
- **Description**: A brief description of what the agent does
- **Instructions**: Detailed instructions for the agent
- **Tools needed**: Description of the tools the agent should use
- **Output type** (optional): If the agent should use structured output
- **Guardrails** (optional): Validation rules for input/output
- **Handoffs** (optional): Other agents this agent can hand off to

## Example Specifications

### Weather Agent

```
Create a weather agent that can provide weather information for cities.

Name: WeatherAgent

Description: An agent that provides current weather information for cities worldwide.

Instructions: You are a helpful weather assistant. When users ask about the weather
in a specific city, use the get_weather tool to fetch that information. If they ask
for a forecast, use the get_forecast tool. Always provide temperatures in both
Celsius and Fahrenheit. If a city cannot be found, politely inform the user.

Tools needed:
1. get_weather: Fetches current weather for a city
   - Parameters: city (string, required)
   - Returns: Weather data including temperature, conditions, humidity

2. get_forecast: Fetches 5-day forecast for a city
   - Parameters: city (string, required), days (integer, optional, default=5)
   - Returns: Forecast data for each day

Output type: A structured response with weather information

Guardrails:
- Validate that city names are non-empty strings
- Check if the weather data contains sensitive information
```

### Research Agent

```
Create a research agent that can search for information and summarize findings.

Name: ResearchAgent

Description: An agent that can search for information on various topics and provide
summarized findings with citations.

Instructions: You are a research assistant. When users ask for information on a topic,
use the search_web tool to find relevant information. Summarize the findings in a
concise manner, providing citations for the sources used. If the topic is ambiguous,
ask for clarification. Always prioritize reliable sources.

Tools needed:
1. search_web: Searches the web for information
   - Parameters: query (string, required), num_results (integer, optional, default=5)
   - Returns: List of search results with titles, snippets, and URLs

2. extract_content: Extracts the main content from a URL
   - Parameters: url (string, required)
   - Returns: The extracted text content

3. summarize_text: Summarizes a long text
   - Parameters: text (string, required), max_length (integer, optional, default=200)
   - Returns: Summarized text

Output type: A structured response with research findings and citations

Guardrails:
- Validate that search queries are appropriate
- Ensure citations are included for all information
- Check for balanced viewpoints on controversial topics
```

## Implementation Details

The meta agent is implemented using the OpenAI Agents SDK and follows these key patterns:

1. **Deterministic Workflow**: The agent follows a deterministic workflow similar to the pattern in the SDK examples
2. **Structured Output**: Uses structured output types for each phase of the process
3. **Agents as Tools**: Specialized agents handle different parts of the process
4. **Guardrails**: Ensures the generated agents meet quality standards

## Limitations

- The meta agent requires a well-structured specification to generate effective agents
- Generated agents may require additional refinement for complex use cases
- Tool implementations may need to be customized for specific APIs or services

## Future Improvements

- Support for more complex agent architectures
- Better handling of edge cases in specifications
- More sophisticated validation of generated agents
- UI for easier agent creation and testing

## License

MIT
