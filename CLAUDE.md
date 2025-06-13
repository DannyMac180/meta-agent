# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup
**IMPORTANT: Always use the project's .venv virtual environment**
- Activate with: `source .venv/bin/activate`
- All package installations should be done within this venv using `uv pip install`

## Development Commands

This project uses **uv** for Python dependency management (not Hatch). Key commands:

```bash
# Environment setup
uv venv
uv pip install -e ".[test]"

# Testing
make test                    # Run all tests
make unit                    # Run unit tests only
make integration            # Run integration tests only
pytest tests/unit -q --asyncio-mode=strict
pytest -m integration --asyncio-mode=strict

# Code quality
make lint                   # Run ruff linting (with auto-fix)
make types                  # Run pyright type checking
ruff check . --fix
pyright

# Utility
make clean                  # Clean build artifacts (preserves .venv)
```

## Architecture Overview

Meta Agent is a Python application that generates fully-functional OpenAI Agents SDK agents from natural-language specifications. The architecture consists of:

### Core Components
- **Meta Agent Orchestrator** (`src/meta_agent/orchestrator.py`): Central planning and coordination
- **Tool Designer Agent** (`src/meta_agent/agents/tool_designer_agent.py`): Generates Python tool code and tests
- **Guardrail Designer Agent** (`src/meta_agent/agents/guardrail_designer_agent.py`): Creates validation logic and safety checks
- **Evaluation Harness** (`src/meta_agent/evaluation/`): Compiles, executes, and reports on generated code

### Key Modules
- **CLI Interface** (`src/meta_agent/cli/main.py`): Primary user interaction point
- **Template System** (`src/meta_agent/templates/`, `src/meta_agent/template_library/`): Agent code generation templates
- **Sandbox Environment** (`src/meta_agent/sandbox/`): Isolated execution for generated code
- **LLM Service** (`src/meta_agent/services/llm_service.py`): Handles OpenAI API interactions
- **Bundle System** (`src/meta_agent/bundle.py`, `src/meta_agent/bundle_generator.py`): Packages final agent artifacts

### Sub-Agent Pattern
The system uses a sub-agent architecture where specialized agents handle specific tasks:
- Tool Designer: Code generation with unit tests
- Guardrail Designer: Safety validation and policy checks
- Meta Agent coordinates between sub-agents and assembles final output

## Project Structure Notes

- `src/meta_agent/` - Main application code
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - End-to-end integration tests
- `docs/` - Technical architecture documentation
- `src/meta_agent/generated_tools/` - Registry for generated tool artifacts
- `temp_sandbox_test_code/` - Temporary sandbox execution area

## Testing Approach

- Async tests use `pytest-asyncio` with strict mode
- Integration tests marked with `@pytest.mark.integration`
- Sandbox execution isolated with Docker (see `Dockerfile`, `seccomp.json`)
- Coverage tracking enabled for `meta_agent` and `tests` packages

## Dependencies

- Uses `uv.lock` for exact version pinning
- Main frameworks: OpenAI Agents SDK, Pydantic, Jinja2, Docker
- Testing: pytest with asyncio, coverage, and mocking support
- Type checking: pyright (not mypy)
- Linting: ruff (not black/flake8)