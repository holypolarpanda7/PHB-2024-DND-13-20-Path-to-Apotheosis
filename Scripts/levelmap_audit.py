"""Level maps that stats use but that stop before level 13 in every layer (2026-10-03): candidates for
gen_levelmaps.py (each needs its 2024 high-level steps checked; some stop on purpose). Reads the bg3-data MCP index.
Run: python3 Scripts/levelmap_audit.py"""
import json
import os
import re
import sqlite3

con = sqlite3.connect(os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite"))
maps = {}
for layer, name, attrs in con.execute("SELECT layer, name, attrs FROM staticdata WHERE kind LIKE 'LevelMap%' ORDER BY rank"):
    a = json.loads(attrs)
    m = maps.setdefault(name, {"levels": {}, "layers": ""})
    m["levels"].update({int(k[5:]): v for k, v in a.items() if k.startswith("Level") and k[5:].isdigit()})
    m["layers"] += layer[0]
used = set()
for (data,) in con.execute("SELECT data FROM stats"):
    used.update(re.findall(r"LevelMapValue\((\w+)\)", data))
n = 0
for name in sorted(maps):
    lv = maps[name]["levels"]
    if lv and max(lv) < 13 and name in used:
        n += 1
        print(f"{name:28s} [{maps[name]['layers']}] last level {max(lv)} = {lv[max(lv)]}")
print(f"{n} level maps stop before 13")
