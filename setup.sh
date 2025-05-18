#!/usr/bin/env bash
set -euxo pipefail

# Create a virtual environment and install dependencies
uv venv
uv pip install -r uv.lock --extra test

