#!/usr/bin/env bash
set -euxo pipefail

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install the package in development mode with test extras
uv pip install -e ".[test]"