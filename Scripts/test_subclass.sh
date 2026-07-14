#!/usr/bin/env bash
set -euo pipefail

# One-command subclass validation against the running game.
#
# Usage:
#   ./Scripts/test_subclass.sh EvocationSchool             # sweep 13-20
#   ./Scripts/test_subclass.sh ZealotPath --check 14       # single-level check
#   ./Scripts/test_subclass.sh EvocationSchool --pack      # pack+deploy first
#   ./Scripts/test_subclass.sh EvocationSchool --no-kill   # keep BG3 alive on FAIL
#
# Preconditions:
# - BG3 is running with the SE console open (launch from Steam, not Vortex)
# - The loaded save's host character IS the class/subclass under test
#   (the sweep levels the host 13->20 and verifies each level's grants)
#
# Exit codes: 0 pass, 2 fail (game killed unless --no-kill), 3 preflight
# blocker, 124 timeout.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

NAME=""
MODE="sweep"
CHECK_LEVEL=""
DO_PACK=0
KILL_ON_FAIL=1
SEND_TIMEOUT_SECONDS="${SMOKE_SEND_TIMEOUT_SECONDS:-15}"
OUTCOME_TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-90}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)   MODE="check"; CHECK_LEVEL="${2:-}"; [[ -n "$CHECK_LEVEL" ]] && shift ;;
    --pack)    DO_PACK=1 ;;
    --no-kill) KILL_ON_FAIL=0 ;;
    *)         NAME="$1" ;;
  esac
  shift
done

if [[ -z "$NAME" ]]; then
  echo "Usage: $0 <ClassOrSubclassName> [--check [level]] [--pack] [--no-kill]"
  echo "Run '!apolist' in the SE console (server context) for all valid names."
  exit 1
fi

if [[ $DO_PACK -eq 1 ]]; then
  echo "[test] pack+deploy first (game must NOT be running during deploy)"
  "$SCRIPT_DIR/pack_deploy_test.sh"
  echo "[test] pack+deploy done - launch BG3 from Steam, load the test save, then rerun without --pack"
  exit 0
fi

ROOT='/c/Users/holyp/AppData/Local/Larian Studios/Baldur'"'"'s Gate 3/Script Extender Logs'
LATEST_LOG=$(ls -t "$ROOT"/Extender\ Runtime* | head -1)
echo "[test] latest log: $LATEST_LOG"

if [[ "$MODE" == "check" ]]; then
  COMMAND="!aposub $NAME${CHECK_LEVEL:+ $CHECK_LEVEL}"
  PATTERN="SubclassCheck ${NAME}: PASS|SubclassCheck ${NAME}: FAILED|SubclassCheck error"
else
  COMMAND="!aposubsweep $NAME"
  PATTERN="SubclassSweep ${NAME}: ALL CHECKS PASSED|SubclassSweep ${NAME}: FAILED|SubclassSweep error"
fi

echo "[test] trigger: $COMMAND"
START_LINE=$(( $(wc -l < "$LATEST_LOG" 2>/dev/null || echo 0) + 1 ))

set +e
timeout "${SEND_TIMEOUT_SECONDS}s" "$SCRIPT_DIR/se_console.sh" server "$COMMAND"
SEND_STATUS=$?
set -e

if [[ $SEND_STATUS -eq 124 ]]; then
  echo "[test] timeout sending console command - is the SE console window open and responsive?"
  exit 124
elif [[ $SEND_STATUS -ne 0 ]]; then
  echo "[test] failed to send console command (status $SEND_STATUS)"
  exit "$SEND_STATUS"
fi

OUTCOME_LINE=""
DEADLINE=$((SECONDS + OUTCOME_TIMEOUT_SECONDS))
while (( SECONDS < DEADLINE )); do
  OUTCOME_LINE=$(sed -n "${START_LINE},\$p" "$LATEST_LOG" | grep -E -m1 "$PATTERN" || true)
  [[ -n "$OUTCOME_LINE" ]] && break
  sleep 1
done

if [[ -z "$OUTCOME_LINE" ]]; then
  echo "[test] timeout after ${OUTCOME_TIMEOUT_SECONDS}s waiting for outcome"
  echo "[test] quick check: SE console focused? 'server' context? try !aposmokehelp"
  echo "[test] recent log tail:"
  tail -n 40 "$LATEST_LOG" || true
  exit 124
fi

echo "[test] outcome: $OUTCOME_LINE"

# show the per-level detail from this run
sed -n "${START_LINE},\$p" "$LATEST_LOG" | grep -E '\[Apotheosis\].*(PASS|FAIL|INFO L)' | tail -n 30 || true

if [[ "$OUTCOME_LINE" == *"FAILED"* || "$OUTCOME_LINE" == *"error"* ]]; then
  if [[ $KILL_ON_FAIL -eq 1 ]]; then
    echo "[test] FAIL detected; killing BG3 for the patch loop"
    powershell.exe -NoProfile -Command "Get-Process -Name bg3,bg3_dx11 -ErrorAction SilentlyContinue | Stop-Process -Force" || true
  else
    echo "[test] FAIL detected (--no-kill: leaving BG3 running)"
  fi
  exit 2
fi

echo "[test] PASS"
