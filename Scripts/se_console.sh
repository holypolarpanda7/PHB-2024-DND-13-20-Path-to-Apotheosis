#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <command1> [command2 ...]"
    echo "Example: $0 server 'Apotheosis.Smoke.Wizard.RunManifest(\"EvocationSchool\")'"
    exit 1
fi

powershell.exe -ExecutionPolicy Bypass -File "$SCRIPT_DIR/send_se_console_command.ps1" "$@"
