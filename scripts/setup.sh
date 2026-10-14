#!/usr/bin/env bash
# One-time setup: Python 3.12 venv, upstream studio clone, install, link our files in.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

command -v uv >/dev/null || { echo "Install uv first: https://docs.astral.sh/uv/"; exit 1; }
[ -d neuro-san-studio ] || git clone https://github.com/cognizant-ai-lab/neuro-san-studio neuro-san-studio
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ./neuro-san-studio openpyxl
"$ROOT/scripts/sync.sh"
echo "Setup done. Export ANTHROPIC_API_KEY, then run scripts/check.sh and scripts/run.sh"
