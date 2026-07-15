#!/usr/bin/env bash
set -euo pipefail

# Arm level-up watch mode and stream test results live.
#
# Usage:
#   ./Scripts/watch_levelups.sh          # enable watch + follow results
#   ./Scripts/watch_levelups.sh off      # disable watch mode
#
# Flow: run this once, then level up in-game with real UI choices.
# Every level with expected grants (13-20 AND moved sub-13 features)
# validates automatically; functional feature tests for newly granted
# passives run right after. Ctrl-C stops following (watch stays on).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CDRIVE="/c"
[[ ! -d "$CDRIVE/Users" && -d /mnt/c/Users ]] && CDRIVE="/mnt/c"
ROOT="$CDRIVE/Users/holyp/AppData/Local/Larian Studios/Baldur's Gate 3/Extender Logs"
[[ -d "$ROOT" ]] || ROOT="$CDRIVE/Users/holyp/AppData/Local/Larian Studios/Baldur's Gate 3/Script Extender Logs"

if [[ "${1:-}" == "off" ]]; then
  "$SCRIPT_DIR/se_console.sh" server "!apowatch off"
  echo "[watch] disabled"
  exit 0
fi

"$SCRIPT_DIR/se_console.sh" server "!apowatch on"
echo "[watch] enabled - level up in-game; streaming results (Ctrl-C to stop following)"

LATEST_LOG=$(ls -t "$ROOT"/Extender\ Runtime* | head -1)
echo "[watch] following: $LATEST_LOG"
tail -n 0 -f "$LATEST_LOG" | grep --line-buffered -E '\[Apotheosis\].*(Watch|FeatureTest|PASS|FAIL)'
