#!/usr/bin/env bash
# Optional chat app on http://localhost:7860. The Neuro SAN server must already be running (scripts/run.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec .venv/bin/python app.py
