#!/usr/bin/env bash
set -euo pipefail

# 1️⃣ Install Hatch – pipx is preinstalled in the image
pipx install hatch           # ~1-2 s download

# 2️⃣ Install your project (and runtime deps) into the *system* interpreter
pip install -e .

# That’s it – the network will be disabled right after this script exits
