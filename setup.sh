#!/usr/bin/env bash
set -euxo pipefail

# Install project + test extras into the system interpreter
python -m pip install -e ".[test]"
