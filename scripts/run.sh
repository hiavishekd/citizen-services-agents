#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../neuro-san-studio"
exec ../.venv/bin/ns run "$@"
