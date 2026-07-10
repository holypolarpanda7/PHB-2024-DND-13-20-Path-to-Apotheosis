#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./Scripts/run_smoke_and_kill_on_fail.sh EvocationSchool
#
# Preconditions:
# - BG3 is running and the SE console is open/accepting input
# - You can enter server context and run ! commands

SUBCLASS="${1:-EvocationSchool}"
SEND_TIMEOUT_SECONDS="${SMOKE_SEND_TIMEOUT_SECONDS:-15}"
OUTCOME_TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-25}"

ROOT='/c/Users/holyp/AppData/Local/Larian Studios/Baldur'"'"'s Gate 3/Script Extender Logs'
LATEST_LOG=$(ls -t "$ROOT"/Extender\ Runtime* | head -1)

echo "[smoke] latest log: $LATEST_LOG"
echo "[smoke] trigger: !apowizmanifest $SUBCLASS"

START_LINE=$(( $(wc -l < "$LATEST_LOG" 2>/dev/null || echo 0) + 1 ))

set +e
timeout "${SEND_TIMEOUT_SECONDS}s" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/se_console.sh" server "!apowizmanifest $SUBCLASS"
SEND_STATUS=$?
set -e

if [[ $SEND_STATUS -eq 124 ]]; then
  echo "[smoke] timeout after ${SEND_TIMEOUT_SECONDS}s while sending console command"
  echo "[smoke] check that BG3 Script Extender Console window is focused and responsive"
  exit 124
fi

if [[ $SEND_STATUS -ne 0 ]]; then
  echo "[smoke] failed to send console command (status $SEND_STATUS)"
  exit "$SEND_STATUS"
fi

# Wait for a definitive outcome line from this run.
PATTERN="RunManifest ${SUBCLASS}: ALL CHECKS PASSED|RunManifest ${SUBCLASS}: FAILED"
OUTCOME_LINE=""
DEADLINE=$((SECONDS + OUTCOME_TIMEOUT_SECONDS))
while (( SECONDS < DEADLINE )); do
  OUTCOME_LINE=$(sed -n "${START_LINE},\$p" "$LATEST_LOG" | grep -E -m1 "$PATTERN" || true)
  if [[ -n "$OUTCOME_LINE" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "$OUTCOME_LINE" ]]; then
  echo "[smoke] timeout after ${OUTCOME_TIMEOUT_SECONDS}s waiting for PASS/FAIL outcome"
  echo "[smoke] likely causes: console input not accepted, wrong context, or no command execution"
  echo "[smoke] quick check: ensure SE console is focused, enter server, then run !aposmokehelp"
  echo "[smoke] recent log tail:"
  tail -n 40 "$LATEST_LOG" || true
  exit 124
fi

echo "[smoke] outcome: $OUTCOME_LINE"

if [[ "$OUTCOME_LINE" == *"FAILED"* ]]; then
  if [[ "$OUTCOME_LINE" == *"[preflight] engine level remained"* ]]; then
    echo "[smoke] preflight blocker: host level did not advance via SetLevel/PROC_LevelUp*"
    echo "[smoke] keeping BG3 running so you can complete manual level-up choices first"
    echo "[smoke] after resolving the pending level-up UI, rerun this script"
    exit 3
  fi

  echo "[smoke] fail detected; killing BG3 for patch loop"
  powershell.exe -NoProfile -Command "Get-Process -Name bg3,bg3_dx11 -ErrorAction SilentlyContinue | Stop-Process -Force" || true
  echo "[smoke] BG3 terminated"
  exit 2
fi

echo "[smoke] pass"
