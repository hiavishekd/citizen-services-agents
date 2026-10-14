#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../neuro-san-studio"
../.venv/bin/ns check-llm-keys
../.venv/bin/ns check-config
