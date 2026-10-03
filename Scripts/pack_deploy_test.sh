#!/usr/bin/env bash
set -euo pipefail

# One-command local test loop (works from WSL and Git Bash):
# 1) Stage Mods/<mod> + Public/<mod> and package them into a .pak with LSLib's Divine
# 2) Verify the pak layout (meta.lsx, stats, SE scripts at the right paths) BEFORE deploying
# 3) Deploy to the BG3 user Mods folder (refuses while the game is running; backs up the old pak)
# 4) Print quick sanity info (modsettings + this run's Script Extender log)
#
# History: until 2026-09-30 this packed only Mods/<mod> as the package ROOT, so paks had no Mods/<mod>/
# prefix and no Public/ content at all - the game never loaded Apotheosis stats from them.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MOD_FOLDER="dnd55e_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
MOD_UUID="1467c26f-e7bb-49d1-d980-6e033aea04fa"

if [[ -d /mnt/c ]]; then C=/mnt/c; D=/mnt/d; to_win() { wslpath -w "$1"; }
else C=/c; D=/d; to_win() { cygpath -w "$1"; }; fi

BG3_USERDATA="$C/Users/holyp/AppData/Local/Larian Studios/Baldur's Gate 3"
BG3_MODS_DIR="$BG3_USERDATA/Mods"
BG3_MODSETTINGS="$BG3_USERDATA/PlayerProfiles/Public/modsettings.lsx"
SE_LOG_DIR="$BG3_USERDATA/Script Extender Logs"

# Keep generated artifacts OUTSIDE the source repo.
OUT_DIR="$C/Users/holyp/AppData/Local/Temp/ApotheosisBuild"
STAGE="$OUT_DIR/stage"
OUT_PAK="$OUT_DIR/${MOD_FOLDER}.pak"
DEPLOY_PAK="$BG3_MODS_DIR/${MOD_FOLDER}.pak"

find_divine() {
    local candidates=(
        "${DIVINE:-}"
        "$D/BG3Modding/Tools/LSLib/Packed/Tools/Divine.exe"
    )
    local p
    for p in "${candidates[@]}"; do
        [[ -n "$p" && -f "$p" ]] && { echo "$p"; return 0; }
    done
    command -v divine.exe >/dev/null 2>&1 && { command -v divine.exe; return 0; }
    # Vortex's bundled copy is too old to read current LSF files; last resort only
    p="$C/Program Files/Black Tree Gaming Ltd/Vortex/resources/app.asar.unpacked/bundledPlugins/game-baldursgate3/tools/divine.exe"
    [[ -f "$p" ]] && { echo "$p"; return 0; }
    return 1
}

game_running() {
    # capture first: with `set -o pipefail`, `tasklist | grep -q` reports failure when grep exits early (SIGPIPE)
    local procs
    procs="$(tasklist.exe 2>/dev/null | tr -d '\r' || true)"
    grep -qiE '^bg3(_dx11)?\.exe' <<<"$procs"
}

main() {
    local src
    for src in "$REPO_ROOT/Mods/$MOD_FOLDER" "$REPO_ROOT/Public/$MOD_FOLDER"; do
        [[ -d "$src" ]] || { echo "[ERR] Mod source folder missing: $src"; exit 1; }
    done

    local divine
    divine="$(find_divine)" || { echo "[ERR] Divine.exe not found (set DIVINE=... or install LSLib to $D/BG3Modding/Tools/LSLib)"; exit 1; }

    echo "[1/5] Staging Mods/ + Public/ ($(date '+%Y-%m-%d %H:%M %Z'))"
    rm -rf "$STAGE"; mkdir -p "$STAGE/Mods" "$STAGE/Public" "$BG3_MODS_DIR"
    cp -r "$REPO_ROOT/Mods/$MOD_FOLDER" "$STAGE/Mods/"
    cp -r "$REPO_ROOT/Public/$MOD_FOLDER" "$STAGE/Public/"

    echo "[2/5] Packaging with $divine"
    rm -f "$OUT_PAK"
    "$divine" -g bg3 -a create-package -s "$(to_win "$STAGE")" -d "$(to_win "$OUT_PAK")" | tail -n 1
    [[ -f "$OUT_PAK" ]] || { echo "[ERR] Packaging reported success but no pak was produced: $OUT_PAK"; exit 1; }

    echo "[3/5] Verifying pak layout"
    local listing
    listing="$("$divine" -g bg3 -a list-package -s "$(to_win "$OUT_PAK")" | tr -d '\r' | cut -f1)"
    local required=(
        "Mods/$MOD_FOLDER/meta.lsx"
        "Mods/$MOD_FOLDER/ScriptExtender/Lua/BootstrapServer.lua"
        "Public/$MOD_FOLDER/Stats/Generated/Data/Passive.txt"
        "Public/$MOD_FOLDER/Progressions/Progressions.lsx"
    )
    local r missing=0
    for r in "${required[@]}"; do
        grep -qxF "$r" <<<"$listing" || { echo "      [ERR] missing in pak: $r"; missing=1; }
    done
    [[ $missing -eq 0 ]] || { echo "[ERR] Refusing to deploy a malformed pak."; exit 1; }
    echo "      $(wc -l <<<"$listing") files; required paths present."

    echo "[4/5] Deploying"
    if game_running; then
        echo "      [ERR] BG3 is running and has the pak open. Close the game and re-run (built pak kept at $OUT_PAK)."
        exit 2
    fi
    if [[ -f "$DEPLOY_PAK" ]]; then
        cp -f "$DEPLOY_PAK" "$OUT_DIR/previous_$(date -r "$DEPLOY_PAK" '+%Y%m%d_%H%M').pak"
    fi
    cp -f "$OUT_PAK" "$DEPLOY_PAK"
    ls -l "$DEPLOY_PAK"

    echo "[5/5] Sanity checks"
    if [[ -f "$BG3_MODSETTINGS" ]] && grep -qi "$MOD_UUID" "$BG3_MODSETTINGS"; then
        echo "      modsettings.lsx contains Apotheosis UUID ($MOD_UUID)."
    elif [[ -f "$BG3_MODSETTINGS" ]]; then
        # Vortex / the game rewrite modsettings.lsx and drop our manually-deployed pak; re-enable it last
        # (after its dnd55e dependency) by inserting before the first </children>, which closes the Mods node.
        cp -f "$BG3_MODSETTINGS" "$OUT_DIR/modsettings_$(date '+%Y%m%d_%H%M%S').lsx.bak"
        awk -v folder="$MOD_FOLDER" -v uuid="$MOD_UUID" '
            !done && /<\/children>/ {
                i = "                            "
                print "                        <node id=\"ModuleShortDesc\">"
                print i "<attribute id=\"Folder\" type=\"LSString\" value=\"" folder "\"/>"
                print i "<attribute id=\"MD5\" type=\"LSString\" value=\"\"/>"
                print i "<attribute id=\"Name\" type=\"LSString\" value=\"dnd55e_13-20_PathtoApotheosis\"/>"
                print i "<attribute id=\"PublishHandle\" type=\"uint64\" value=\"0\"/>"
                print i "<attribute id=\"UUID\" type=\"guid\" value=\"" uuid "\"/>"
                print i "<attribute id=\"Version64\" type=\"int64\" value=\"36028797018963968\"/>"
                print "                        </node>"
                done = 1
            }
            { print }' "$BG3_MODSETTINGS" > "$OUT_DIR/modsettings.new"
        cp -f "$OUT_DIR/modsettings.new" "$BG3_MODSETTINGS"
        echo "      [FIX] Apotheosis UUID was missing from modsettings.lsx - enabled it (backup in $OUT_DIR)."
    else
        echo "      [WARN] $BG3_MODSETTINGS not found - enable the mod before launch."
    fi
    if [[ -d "$SE_LOG_DIR" ]]; then
        local latest_log
        latest_log="$(ls -t "$SE_LOG_DIR"/Extender\ Runtime*.log 2>/dev/null | head -1 || true)"
        if [[ -n "$latest_log" ]]; then
            echo "      latest SE log: $(basename "$latest_log") (names are UTC; written $(date -r "$latest_log" '+%Y-%m-%d %H:%M %Z'))"
            grep -F "[Apotheosis]" "$latest_log" | tail -n 5 || echo "      (no [Apotheosis] lines in that log)"
        fi
    fi
    echo ""
    echo "Done. Launch BG3 and look for: [Apotheosis] BootstrapServer.lua loading / SessionLoaded - Apotheosis server scripts active"
}

main "$@"
