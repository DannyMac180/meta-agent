#!/usr/bin/env bash
set -euo pipefail

: "${BUILDER_BUCKET:=metaagent-artifacts}"

# Requires mc (MinIO client) installed in the environment where this is run
mc alias set local http://localhost:9000 minioadmin minioadmin >/dev/null 2>&1 || true
mc mb -q local/${BUILDER_BUCKET} || true
