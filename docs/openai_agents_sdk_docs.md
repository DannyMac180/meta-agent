# OpenAI Agents SDK – Curated Documentation

> **Version reviewed:** commit corresponding to docs as of 18 Apr 2025  
> **Official site:** <https://openai.github.io/openai-agents-python/>

---

## 1. Introduction

The **OpenAI Agents SDK** is a lightweight framework for building *agentic* AI applications.
It exposes a minimal set of primitives—**Agents**, **Tools**, **Handoffs**, and **Guardrails**—
that can be composed into arbitrarily complex workflows.

---

## 2. Installation & Setup

```bash
# Create an isolated project
mkdir my_project && cd my_project
uv venv
source .venv/bin/activate

# Install the SDK
uv pip install openai-agents           # or: uv add openai-agents

# Configure credentials
export OPENAI_API_KEY="sk‑…"        # required for LLM calls & tracing
```

If you cannot set the environment variable at process start‑up, call:

```python
from agents import set_default_openai_key
set_default_openai_key("sk-…")
```

---

## 3. Core Concepts

### 3.1 Agents

An **`Agent`** wraps an LLM, **instructions** (system prompt), and optional
**tools**, **guardrails**, or **handoffs**.

```python
from agents import Agent

math_tutor = Agent(
    name="Math Tutor",
    instructions="Help with math problems. Show your reasoning step‑by‑step."
)
```

#### Configuration highlights

| attribute | purpose |
|-----------|---------|
| `instructions` | System prompt for the agent. |
| `tools` | List of tools (functions/other agents). |
| `handoffs` | Agents this agent can delegate to. |
| `input_guardrails`/`output_guardrails` | Validation routines. |
| `model` / `model_config` | Per‑agent model override. |
| `max_turns` | Safety limit for recursion/loops. |

---

### 3.2 Tools

Tools let agents *act* by calling Python functions, external APIs, or other
agents.

```python
from typing_extensions import TypedDict
from agents import function_tool, Agent

class Location(TypedDict):
    lat: float
    long: float

@function_tool
async def fetch_weather(location: Location) -> str:
    """Fetch the weather forecast for a given location."""
    return "sunny"

assistant = Agent(
    name="Assistant",
    tools=[fetch_weather],
)
```

Key points:

* Simple `@function_tool` decorator auto‑generates JSON schemas from type
  hints + docstrings.
* Functions may be *sync* or *async*.
* Custom tools can be built by instantiating `FunctionTool` directly.
* **Agents-as-tools**: `agent.as_tool(...)` converts an agent into a callable
  tool, useful for orchestration hierarchies.

---

### 3.3 Handoffs

Handoffs allow an agent to *transfer control* to another specialist agent:

```python
triage = Agent(
    name="Triage",
    instructions="Decide which specialist should answer.",
    handoffs=[math_tutor, history_tutor],
)
```

Internally each handoff appears to the LLM as a tool
(e.g. `transfer_to_history_tutor`). The runner automatically follows the
delegation chain.

---

### 3.4 Guardrails

Guardrails run side‑by‑side with business agents to enforce policies or
validate inputs/outputs.

```python
from pydantic import BaseModel
from agents import GuardrailFunctionOutput, InputGuardrail, Runner

class IsHomework(BaseModel):
    is_homework: bool
    reasoning: str

checker = Agent(
    name="Homework Guard",
    instructions="Determine if the user asks for homework help.",
    output_type=IsHomework,
)

async def homework_guard(ctx, agent, input_text):
    res = await Runner.run(checker, input_text, context=ctx.context)
    data = res.final_output_as(IsHomework)
    return GuardrailFunctionOutput(
        output_info=data,
        tripwire_triggered=not data.is_homework,
    )

triage.input_guardrails = [InputGuardrail(guardrail_function=homework_guard)]
```

---

## 4. Runner API

Use **`Runner`** to execute agents.

| method | description |
|--------|-------------|
| `await Runner.run(agent, input, *, context=None, …)` | Async, returns `RunResult`. |
| `Runner.run_sync(…)` | Synchronous wrapper around `run`. |
| `await Runner.run_streamed(…)` | Returns `RunResultStreaming` + live events. |

### Streaming

```python
result_stream = await Runner.run_streamed(agent, "Hello!")
async for event in result_stream.stream_events():
    handle(event)
print(result_stream.final_output)
```

`RunItemStreamEvent` objects cover messages, tool calls, handoffs, etc.

---

## 5. Tracing & Debugging

Tracing is **on by default**. Every run produces a rich graph of spans that can
be inspected in the *OpenAI Trace Viewer* on the dashboard.

Disable tracing globally:

```python
from agents import disable_default_tracing
disable_default_tracing()
```

Or per‑run via `run_config={"tracing": False}`.

---

## 6. Context Management

*Local context* (Python objects) can be attached via `RunContextWrapper`.
*LLM context* (structured data) can be appended via the `context` parameter of
`Runner.run`, and retrieved inside tools or guardrails.

---

## 7. Models

The SDK is provider‑agnostic:

* Set `Agent.model` for per‑agent overrides.
* Implement a custom `ModelProvider` and pass it to `Runner.run`.
* Use **LiteLLM** integration to access 100+ hosted models with the same agent
  code.

---

## 8. Quickstart – Full Workflow

```python
import asyncio
from agents import Agent, Runner

history_tutor = Agent(
    name="History Tutor",
    handoff_description="Answers history questions.",
    instructions="Explain historical events clearly.",
)

math_tutor = Agent(
    name="Math Tutor",
    handoff_description="Answers math questions.",
    instructions="Show reasoning step‑by‑step.",
)

triage = Agent(
    name="Triage",
    instructions="Route to the right tutor.",
    handoffs=[history_tutor, math_tutor],
)

async def main():
    res = await Runner.run(triage, "Who was the first president of the USA?")
    print(res.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. Advanced Features

* **Lifecycle hooks** – intercept events, customise retries, add logging.
* **Agent visualisation** – graph rendering of agent networks.
* **Voice agents** – full duplex speech pipelines (`voice.pipeline`).
* **MCP (Model Context Protocol)** – standardised inter‑process agent tooling.

---

## 10. Cheatsheet

| Item | Import | Notes |
|------|--------|-------|
| `Agent` | `from agents import Agent` | Core primitive. |
| `function_tool` | `from agents import function_tool` | Decorator for tools. |
| `Runner` | `from agents import Runner` | Execution engine. |
| `GuardrailFunctionOutput` | – | Compose guardrail results. |
| `RunResult` | – | Access `messages`, `tool_outputs`, `final_output`. |
| `RunItemStreamEvent` | – | Streaming event wrapper. |

---

## 11. Recommended Patterns

1. **Thin Orchestrator** → Specialist agents-as-tools for clear routing.
2. Keep guardrails *cheap*: fast model, simple schema.
3. Stream everything and surface partial progress to UX.
4. Prefer **typed tool args** (`TypedDict`/`BaseModel`) for robustness.
5. Limit recursion via `max_turns` on agents that can loop.

---

## 12. Further Reading

* **Examples** directory in the repo – reference implementations: chat, search,
  code‑execution, retrieval, voice, etc.
* **MCP spec** – protocol details & reference clients.

---

*Happy building!* 🚀
