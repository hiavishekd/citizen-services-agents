#!/usr/bin/env bash
# Link our tracked folders into the studio clone. Safe to re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STUDIO="$ROOT/neuro-san-studio"
[ -d "$STUDIO" ] || { echo "Run scripts/setup.sh first"; exit 1; }

link() { rm -rf "$2"; mkdir -p "$(dirname "$2")"; ln -s "$1" "$2"; }

link "$ROOT/networks"             "$STUDIO/registries/citizen_services"
link "$ROOT/coded_tools"          "$STUDIO/coded_tools/citizen_services"
link "$ROOT/data"                 "$STUDIO/data"
link "$ROOT/config/llm_config.hocon" "$STUDIO/config/llm_config.hocon"

INCLUDE='include "registries/citizen_services/manifest.hocon",'
grep -qF "$INCLUDE" "$STUDIO/registries/manifest.hocon" || \
  sed -i.bak "s|^    include \"registries/generated/manifest.hocon\",|&\n\n    # Citizen Services Agents\n    $INCLUDE|" "$STUDIO/registries/manifest.hocon"
rm -f "$STUDIO/registries/manifest.hocon.bak"
echo "Linked networks, coded_tools, data and config into the studio."
