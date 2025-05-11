# OpenAI Responses API Usage Guide

## 1. Overview

The OpenAI Responses API is a new, stateful API designed to simplify building AI-powered applications. It unifies the best capabilities from the Chat Completions API (ease of use for multi-turn conversations) and the Assistants API (tool use and state management) into a single, more flexible interface.

Key benefits of the Responses API include:
- **Simplified agent development** with built-in state management
- **Multiple tools and multiple turns** in a single API call
- **Unified item-based design** for clearer response handling
- **Intuitive streaming events** and SDK helpers

The API is designed to support increasingly complex tasks as model capabilities evolve, making it ideal for developers building agentic applications that need to connect models to real-world data and actions.

## 2. Key Concepts

### Stateful Interactions

Unlike the Chat Completions API (which requires sending the entire conversation history with each request), the Responses API is inherently stateful. It maintains conversation history server-side, allowing you to:

- Reference previous interactions using a `previous_response_id`
- Retrieve full conversation history at any time
- Fork conversations from any point to explore different paths

### Input Structure

The Responses API uses an `input` parameter instead of the `messages` array from Chat Completions:

- Can be a simple string for user queries
- Can be a structured list of message objects with roles (similar to Chat Completions)
- Supports a new `developer` role in addition to `system` and `user` roles
- When using `previous_response_id`, you only need to provide the new input

### Output Structure

The response object has a different structure than Chat Completions:

- Main content is accessed via `response.output[0].content[0].text` (or similar path)
- Some SDKs may provide helper methods like `response.output_text`
- Supports multiple output items for different types of content (text, tool calls)
- Includes metadata about the response and the conversation state

### Integrated Tools

The Responses API supports built-in tools that can be used directly:

- **Web Search**: Enhance responses with up-to-date information from the internet
- **File Search**: Query uploaded documents for relevant information
- **Code Interpreter**: Execute code to solve problems or generate visualizations
- **Computer Use**: Control a computer interface for more complex tasks
- **Function Calling**: Define custom functions the model can use

## 3. How to Use (Python Client - Conceptual Examples)

### Client Initialization

```python
# For OpenAI
from openai import OpenAI
client = OpenAI(api_key="YOUR_API_KEY")

# For Azure OpenAI
from openai import AzureOpenAI
client = AzureOpenAI(
    api_version="2025-03-01-preview",  # Or newer
    azure_endpoint="YOUR_AZURE_ENDPOINT",
    api_key="YOUR_AZURE_API_KEY"
)
```

### Creating a Response (New Conversation)

```python
# Simple input as a string
response = client.responses.create(
    model="gpt-4o",
    input="What is the capital of France?"
)

# Or with structured messages (similar to Chat Completions)
response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

# Accessing the output text
assistant_reply = response.output[0].content[0].text
print(assistant_reply)

# Or using the helper method if available
# print(response.output_text)

# Store the response ID for continuing the conversation later
response_id = response.id
```

### Continuing a Conversation

```python
# Continue the conversation using previous_response_id
follow_up_response = client.responses.create(
    model="gpt-4o",
    input="What about Germany?",  # Only the new user message is needed
    previous_response_id=response_id  # From the previous response
)

# Access the new response
assistant_reply = follow_up_response.output[0].content[0].text
print(assistant_reply)

# Update the response ID for future interactions
response_id = follow_up_response.id
```

### Retrieving a Past Response

```python
# Fetch a complete response by its ID
fetched_response = client.responses.retrieve(response_id)

# This gives you the full state of that response, including conversation history
```

### Using Tools

```python
# Define tools the model can use
tools = [
    {
        "type": "web_search"
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string", 
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Create a response with tools
response_with_tools = client.responses.create(
    model="gpt-4o",
    input="What's the weather like in Boston and what's in the news today?",
    tools=tools
)

# The response might include tool calls that need to be executed
# For example, if the model decides to call the get_weather function:
if hasattr(response_with_tools.output[0], 'tool_calls'):
    for tool_call in response_with_tools.output[0].tool_calls:
        if tool_call.function.name == "get_weather":
            location = json.loads(tool_call.function.arguments).get("location")
            # Call your actual weather API here
            weather_result = get_real_weather(location)
            
            # Submit the tool results back to continue
            response_with_tool_results = client.responses.create(
                model="gpt-4o",
                input=[{"role": "tool", "content": json.dumps(weather_result)}],
                previous_response_id=response_with_tools.id
            )
```

## 4. Key Parameters for `responses.create()`

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | **Required**. ID of the model to use (e.g., "gpt-4o") |
| `input` | string or array | **Required**. The input for the model. Can be a simple string or array of message objects |
| `previous_response_id` | string | ID of a previous response to continue the conversation |
| `temperature` | number | Controls randomness (0-2, default varies by model) |
| `max_output_tokens` | integer | Maximum number of tokens to generate |
| `tools` | array | List of tools the model can call |
| `tool_choice` | string or object | Controls how the model uses tools ("auto", "none", or specific tool) |
| `response_format` | object | Specifies the format of the response (e.g., JSON) |
| `seed` | integer | Seed for deterministic results |
| `stream` | boolean | Whether to stream the response |

## 5. Response Object Structure (Inferred)

The response object from `client.responses.create()` or `client.responses.retrieve()` likely contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the response (e.g., "resp_abc123") |
| `object` | string | Type of object (e.g., "response") |
| `created` | integer | Unix timestamp when the response was created |
| `model` | string | The model used for the response |
| `output` | array | List of output items (text, tool calls, etc.) |
| `usage` | object | Token usage statistics (prompt_tokens, completion_tokens, total_tokens) |
| `status` | string | Status of the response (e.g., "completed", "requires_action") |
| `system_fingerprint` | string | Fingerprint representing the model's configuration |

For text responses, the content is typically accessed via:
```python
response.output[0].content[0].text
```

For tool calls, they might be accessed via:
```python
response.output[0].tool_calls
```

## 6. Differences from Chat Completions API

| Feature | Responses API | Chat Completions API |
|---------|--------------|----------------------|
| **State Management** | Stateful with `previous_response_id` | Stateless (requires sending full history) |
| **API Endpoint** | `/v1/responses` | `/v1/chat/completions` |
| **Client Method** | `client.responses.create()` | `client.chat.completions.create()` |
| **Input Structure** | `input` parameter (string or array) | `messages` array |
| **Output Structure** | `output[0].content[0].text` | `choices[0].message.content` |
| **Built-in Tools** | Web search, file search, code interpreter | Limited to function calling |
| **Developer Role** | Supports `developer` role | Not supported |

## 7. Migration Considerations

When migrating from the Chat Completions API to the Responses API:

- **Conversation History**: Instead of maintaining and sending the full conversation history with each request, use `previous_response_id` to reference previous interactions.
- **Response Parsing**: Update your code to extract content from the new response structure.
- **Tool Integration**: Leverage built-in tools instead of implementing them separately.
- **Stateful Design**: Take advantage of the stateful nature to simplify your application architecture.
- **Role Management**: Consider using the new `developer` role for instructions that should override the system role.

## 8. Disclaimer

This guide is based on available information about the OpenAI Responses API as of its initial release. The actual implementation details, parameter names, and response structures may vary. Always consult the [official OpenAI API documentation](https://platform.openai.com/docs/api-reference/responses) for the most accurate and up-to-date information.

As the Responses API evolves, new features and capabilities may be added, and some details in this guide may become outdated. The OpenAI Python client library documentation should be your primary reference for implementation details.
