# ruff: skip-file
# Meta Agent Contributor Guide

## Repository Overview
This project orchestrates the creation of OpenAI Agents from natural language specifications. The
`meta_agent` package contains the orchestrator and utilities to parse specs, plan tasks, generate tool
code and manage sub-agents.

Key packages under `src/meta_agent`:
- `cli/` – entry points for the `meta-agent` command line tool.
- `orchestrator.py` – coordinates planning and agent execution.
- `planning_engine.py` – analyses tasks and produces execution plans.
- `sub_agent_manager.py` – manages specialised sub-agents.
- `tool_designer.py` – generates new tools from specifications.
- `generators/` – LLM-driven code builders and prompt helpers.
- `models/` – Pydantic models such as `SpecSchema` and tool metadata.
- `parsers/` – utilities for parsing specifications.
- `services/` – wrappers around LLM calls.
- `templates/` & `template_engine.py` – Jinja templates used by generators.
- `utils/` – config and logging helpers.
- `generated_tools/` – auto-generated tools (do not edit manually).

## Directory Guide
- `src/meta_agent/` – production Python code. Most contributions belong here.
- `tests/` – unit and integration tests. Add tests for every new feature.
- `docs/` – longer form documentation and design notes.
- `scripts/` – Node.js helpers for task management and PRD parsing.
- `tasks/` – generated task files. Update via `task-master` commands only.
- `temp_sandbox_test_code/` – temporary sandbox used in tests.

## Environment Setup
The universal Docker image provides:
- **Python:** 3.10, 3.11.12, 3.12, 3.13 via **pyenv** (default 3.11.12).
- **uv** and **poetry** installed globally.
- **Node:** versions 18, 20 and 22 via **nvm** with corepack enabled.
- Additional tools: bun, rust, go, swift, gradle and more.

Create a virtual environment and install dev dependencies:
```bash
uv venv
uv pip install -e ".[test]"
```

## Lint, Type-Check and Test
Run all checks locally before opening a PR:
```bash
ruff check .
black --check .
pytest
mypy
pyright
```
CI expects all of these to pass.

## Contribution Rules
- Modules and variables use `snake_case`; classes use `CamelCase`.
- Tests live under `tests/` and files start with `test_`.
- Commit messages: `type: short summary` (e.g. `feat: add tool registry`).
- PR titles follow the same `type: summary` style. Keep changes small and focused.

## Agent Guidance
Codex should work primarily inside `src/meta_agent/` and `tests/`.
Avoid modifying `generated_tools/`, `tasks/`, or `temp_sandbox_test_code/` unless explicitly asked.
Run the full suite (`ruff`, `black`, `mypy`, `pyright`, `pytest`) before presenting a diff.

## Testing Instructions
Run the full suite with coverage:
```bash
pytest -v --cov=src/meta_agent tests
```
Run a single test:
```bash
pytest tests/test_agent.py::test_agent
```
Run a single test with coverage:
```bash
pytest -v --cov=src/meta_agent tests/test_agent.py::test_agent
```
When writing or running tests that require a call over the network, stub/mock the network call because
Codex does not have access to the network.

## Repo Rules
Check the `.windsurfrules` file for more information on how to use this repo, especially when working
with task-master tasks.

## Task management specific instructions
This project is using task-master to manage tasks. The tasks are stored in the `tasks/` directory and
are parsed using the `scripts/` directory. When I ask you to work on a task, check the task directory for the one to work on.

For example, if I ask you to work on task 11, check the `tasks/task_011.txt` file for the task details.

Subtask would be in the `tasks/task_011.txt` file like: ## 9. Implement Code Generation and Testing Capabilities [pending]