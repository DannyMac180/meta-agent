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

### System Flow Diagram

```mermaid
graph TD
    %% Main Components
    User[User Input - Natural Language Spec] --> GenerateAgent[generate_agent]
    GenerateAgent --> Result[Agent Code]
    
    %% Data Models
    subgraph Data Models
        AS[AgentSpecification]
        TD[ToolDefinition]
        OTD[OutputTypeDefinition]
        GD[GuardrailDefinition]
        AD[AgentDesign]
        AC[AgentCode]
        AI[AgentImplementation]
    end
    
    %% Process Flow
    subgraph Process Flow
        GenerateAgent --> AnalyzeSpec[analyze_agent_specification]
        AnalyzeSpec --> DesignTools[design_agent_tools]
        AnalyzeSpec --> DesignOutputType[design_output_type]
        AnalyzeSpec --> DesignGuardrails[design_guardrails]
        
        DesignTools --> GenToolCode[generate_tool_code]
        DesignOutputType --> GenOutputTypeCode[generate_output_type_code]
        DesignGuardrails --> GenGuardrailCode[generate_guardrail_code]
        
        GenToolCode --> GenAgentCode[generate_agent_creation_code]
        GenOutputTypeCode --> GenAgentCode
        GenGuardrailCode --> GenAgentCode
        
        GenAgentCode --> GenRunnerCode[generate_runner_code]
        GenRunnerCode --> AssembleImpl[assemble_agent_implementation]
        
        AssembleImpl --> ValidateImpl[validate_agent_implementation]
        ValidateImpl --> Result
    end
    
    %% Data Flow
    User -. "Creates" .-> AS
    AS -. "Used to create" .-> TD
    AS -. "Used to create" .-> OTD
    AS -. "Used to create" .-> GD
    TD -. "Part of" .-> AD
    OTD -. "Part of" .-> AD
    GD -. "Part of" .-> AD
    AD -. "Used to generate" .-> AC
    AC -. "Assembled into" .-> AI
    
    %% Styling
    classDef process fill:#f9f,stroke:#333,stroke-width:2px,color:#000;
    classDef dataModel fill:#bbf,stroke:#333,stroke-width:1px,color:#000;
    classDef input fill:#bfb,stroke:#333,stroke-width:1px,color:#000;
    classDef output fill:#fbb,stroke:#333,stroke-width:1px,color:#000;
    
    class GenerateAgent,AnalyzeSpec,DesignTools,DesignOutputType,DesignGuardrails,GenToolCode,GenOutputTypeCode,GenGuardrailCode,GenAgentCode,GenRunnerCode,AssembleImpl,ValidateImpl process;
    class AS,TD,OTD,GD,AD,AC,AI dataModel;
    class User input;
    class Result output;
```

## Installation

### From PyPI (Recommended)

Install the package directly from PyPI:

```bash
pip install danmac-meta-agent
```

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/DannyMac180/meta-agent.git
   cd meta-agent
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```
   Or create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your-api-key
   ```

## Usage

### Using the Command Line Interface (CLI)

After installation, you can use the meta-agent from the command line:

```bash
# Display help
danmac-meta-agent --help

# Generate an agent from a specification in a file
danmac-meta-agent --file path/to/specification.txt --output ./my_agent

# Generate an agent from a specification provided directly
danmac-meta-agent --spec "Create a weather agent that can fetch and report weather data..."
```

CLI Options:
- `--spec`, `-s`: Natural language specification for the agent to generate
- `--file`, `-f`: Path to a file containing the agent specification
- `--output`, `-o`: Output directory for the generated agent code (default: current directory)

### Using as a Python Library

```python
import asyncio
from meta_agent import generate_agent

async def main():
    specification = """
    Create a simple agent that responds to greetings.
    
    Name: GreetingAgent
    
    Description: A simple agent that responds to greetings in different languages.
    
    Instructions: You are a friendly greeting agent. When users greet you in any language,
    respond with an appropriate greeting in the same language. If you're not sure what
    language is being used, respond in English. Be warm and welcoming in your responses.
    
    Tools needed:
    1. detect_language: Detects the language of the input text
       - Parameters: text (string, required)
       - Returns: Language code (e.g., "en", "es", "fr")
    
    2. translate_greeting: Translates a greeting to the specified language
       - Parameters: greeting (string, required), language_code (string, required)
       - Returns: Translated greeting
    
    Output type: A simple text response
    
    Guardrails:
    - Ensure responses are appropriate and respectful
    - Validate that language codes are valid ISO codes
    """
    
    # Generate the agent
    implementation = await generate_agent(specification)
    
    # Print the implementation
    print("Agent implementation generated successfully!")
    print("\nMain file:")
    print(implementation.main_file[:500] + "..." if len(implementation.main_file) > 500 else implementation.main_file)

if __name__ == "__main__":
    asyncio.run(main())
```

## Package Structure

```
meta-agent/
├── meta_agent/                  # Main package
│   ├── __init__.py              # Package initialization
│   ├── core.py                  # Core agent generator functionality
│   ├── agent_generator.py       # Legacy module (deprecated)
│   ├── cli.py                   # Command-line interface
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── agent.py             # Agent specification model
│   │   ├── tool.py              # Tool definition model
│   │   ├── output.py            # Output type definition model
│   │   ├── guardrail.py         # Guardrail definition model
│   │   ├── design.py            # Agent design model
│   │   ├── code.py              # Agent code model
│   │   └── implementation.py    # Agent implementation model
│   ├── design/                  # Design-related functions
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Agent specification analyzer
│   │   ├── tool_designer.py     # Tool designer
│   │   ├── output_designer.py   # Output type designer
│   │   └── guardrail_designer.py # Guardrail designer
│   ├── generation/              # Code generation functions
│   │   ├── __init__.py
│   │   ├── tool_generator.py    # Tool code generator
│   │   ├── output_generator.py  # Output type code generator
│   │   ├── guardrail_generator.py # Guardrail code generator
│   │   ├── agent_generator.py   # Agent creation code generator
│   │   ├── runner_generator.py  # Runner code generator
│   │   └── assembler.py         # Implementation assembler
│   ├── validation/              # Validation functions
│   │   ├── __init__.py
│   │   └── validator.py         # Implementation validator
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── config.py            # Configuration utilities
│       ├── file_utils.py        # File operation utilities
│       └── string_utils.py      # String manipulation utilities
├── tests/                       # Test directory
│   ├── __init__.py
│   └── test_agent_generator.py
├── agents/                      # Example agents (not included in package)
├── pyproject.toml               # Package configuration
├── setup.py                     # Setup script for backward compatibility
├── MANIFEST.in                  # Package manifest
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Running Tests

```bash
python -m tests.test_agent_generator
```

## Agent Specification Format

When describing your agent, include the following information:

- **Name**: A name for your agent
- **Description**: A brief description of what the agent does
- **Instructions**: Detailed instructions for the agent
- **Tools needed**: Description of the tools the agent should use
- **Output type**: The format of the agent's response (text or structured)
- **Guardrails**: Any validation or safety measures to implement

### Example Specification

Here's a complete example of a specification for a research agent:

```
Create a research agent that can search for information and summarize findings.

Name: ResearchAgent

Description: An agent that can search for information on various topics and provide summarized findings with citations.

Instructions: You are a research assistant. When given a topic or question, search for relevant information, analyze the results, and provide a concise summary with proper citations. Focus on providing accurate, up-to-date information from reliable sources. If you don't have enough information, acknowledge the limitations of your findings.

Tools needed:
1. search_web: Searches the web for information
   - Parameters: query (string, required), max_results (integer, optional, default=5)
   - Returns: List of search results with title, URL, and snippet

2. fetch_content: Fetches the full content of a webpage
   - Parameters: url (string, required)
   - Returns: Full text content of the webpage

3. summarize_text: Summarizes a long text
   - Parameters: text (string, required), max_length (integer, optional, default=200)
   - Returns: Summarized text

Output type: A structured response with research findings and citations

Guardrails:
- Validate URLs before fetching content
- Ensure citations are properly formatted
- Check that summaries accurately represent the source material
- Limit the length of responses to a reasonable size
```

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

## Development

### Dependency Management

This project uses precise version constraints to ensure consistent behavior across different environments. We maintain lock files for each supported Python version to guarantee reproducible builds.

#### Generating Lock Files

To generate lock files for all supported Python versions:

```bash
# Make the script executable if needed
chmod +x scripts/generate_lock_files.sh

# Run the script
./scripts/generate_lock_files.sh
```

This creates version-specific lock files in the `lock_files` directory:
- `requirements-py39-lock.txt` for Python 3.9
- `requirements-py310-lock.txt` for Python 3.10
- `requirements-py311-lock.txt` for Python 3.11

These lock files are used by the CI/CD pipeline to ensure consistent testing across all supported Python versions.

## Limitations

- The meta agent requires a well-structured specification to generate effective agents
- Generated agents may require additional refinement for complex use cases
- Tool implementations may need to be customized for specific APIs or services

## Future Improvements

- Support for more complex agent architectures
- Better handling of edge cases in specifications
- More sophisticated validation of generated agents
- UI for easier agent creation and testing

## Updating the Package

If you've made changes to the package and want to release a new version:

1. Update the version number in `pyproject.toml`
2. Rebuild the distribution packages:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   python -m build
   ```
3. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
