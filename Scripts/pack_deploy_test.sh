#!/usr/bin/env bash
set -euo pipefail

# One-command local test loop:
# 1) Package mod folder into .pak using divine
# 2) Deploy .pak to BG3 user Mods folder
# 3) Print quick sanity info (modsettings + latest SE log)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MOD_FOLDER="PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
MOD_UUID="1467c26f-e7bb-49d1-d980-6e033aea04fa"
MOD_SOURCE="$REPO_ROOT/Mods/$MOD_FOLDER"

BG3_USERDATA="/c/Users/holyp/AppData/Local/Larian Studios/Baldur's Gate 3"
BG3_MODS_DIR="$BG3_USERDATA/Mods"
BG3_MODSETTINGS="$BG3_USERDATA/PlayerProfiles/Public/modsettings.lsx"
SE_LOG_DIR="$BG3_USERDATA/Extender Logs"

# Keep generated package artifacts OUTSIDE the source repo.
# Use a simple AppData temp path to avoid URI parsing edge-cases in divine.
OUT_DIR="/c/Users/holyp/AppData/Local/Temp/ApotheosisBuild"
OUT_PAK="$OUT_DIR/${MOD_FOLDER}.pak"
DEPLOY_PAK="$BG3_MODS_DIR/${MOD_FOLDER}.pak"

find_divine() {
    if command -v divine.exe >/dev/null 2>&1; then
        command -v divine.exe
        return 0
    fi
    if command -v divine >/dev/null 2>&1; then
        command -v divine
        return 0
    fi

    local candidates=(
        "/c/Program Files/Black Tree Gaming Ltd/Vortex/resources/app.asar.unpacked/bundledPlugins/game-baldursgate3/tools/divine.exe"
        "/c/Program Files (x86)/Black Tree Gaming Ltd/Vortex/resources/app.asar.unpacked/bundledPlugins/game-baldursgate3/tools/divine.exe"
    )

    local p
    for p in "${candidates[@]}"; do
        if [[ -f "$p" ]]; then
            echo "$p"
            return 0
        fi
    done

    return 1
}

main() {
    if [[ ! -d "$MOD_SOURCE" ]]; then
        echo "[ERR] Mod source folder missing: $MOD_SOURCE"
        exit 1
    fi

    mkdir -p "$OUT_DIR" "$BG3_MODS_DIR"

    local divine
    if ! divine="$(find_divine)"; then
        echo "[ERR] Could not find divine.exe (Vortex LSlib packer)."
        echo "      Install/enable BG3 extension in Vortex or add divine to PATH."
        exit 1
    fi

    echo "[1/4] Packaging with divine"
    echo "      $divine"
    "$divine" -g bg3 -a create-package -s "$MOD_SOURCE" -d "$OUT_PAK"

    if [[ ! -f "$OUT_PAK" ]]; then
        echo "[ERR] Packaging reported success but no pak was produced: $OUT_PAK"
        exit 1
    fi

    echo "[2/4] Deploying pak to BG3 Mods"
    cp -f "$OUT_PAK" "$DEPLOY_PAK"

    echo "[3/4] Sanity checks"
    ls -lh "$DEPLOY_PAK"
    if [[ -f "$BG3_MODSETTINGS" ]]; then
        if grep -qi "$MOD_UUID" "$BG3_MODSETTINGS"; then
            echo "      modsettings.lsx contains Apotheosis UUID ($MOD_UUID)."
        else
            echo "      [WARN] modsettings.lsx does NOT contain Apotheosis UUID ($MOD_UUID)."
            echo "             Enable the mod in your current profile/load order before launch."
        fi
    else
        echo "      [WARN] modsettings.lsx not found: $BG3_MODSETTINGS"
    fi

    echo "[4/4] Latest Script Extender log"
    if [[ -d "$SE_LOG_DIR" ]]; then
        local latest_log
        latest_log="$(find "$SE_LOG_DIR" -maxdepth 1 -type f -name '*.log' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
        if [[ -n "${latest_log:-}" && -f "$latest_log" ]]; then
            echo "      $latest_log"
            echo "      --- tail (Apotheosis-tagged) ---"
            grep -F "[Apotheosis]" "$latest_log" | tail -n 30 || echo "      (no [Apotheosis] lines yet)"
        else
            echo "      (no Extender log files yet; launch game once with SE logging enabled)"
        fi
    else
        echo "      (Extender log folder not present yet: $SE_LOG_DIR)"
    fi

    echo ""
    echo "Done. Next: launch BG3 normally and watch the SE console for:"
    echo "  [Apotheosis] BootstrapServer.lua loading - server context"
    echo "  [Apotheosis] SessionLoaded - Apotheosis server scripts active"
}

main "$@"
