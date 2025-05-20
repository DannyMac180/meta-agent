#!/usr/bin/env bash
set -euxo pipefail

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate

# setup.sh (runs inside Codex container)
uv pip install --upgrade "hatchling>=1.24" wheel

# Install the package in development mode with test extras
uv pip install -e ".[test]"