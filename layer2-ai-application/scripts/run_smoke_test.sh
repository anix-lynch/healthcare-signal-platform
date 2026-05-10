#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pytest tests/test_smoke_esi.py tests/test_safety_overrides.py -v
