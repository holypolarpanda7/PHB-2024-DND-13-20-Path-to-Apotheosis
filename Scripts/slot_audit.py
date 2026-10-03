"""Spell-slot curve audit (2026-10-03): sums ActionResource(SpellSlot,n,level) boosts from progressions (class table +
caster subclass tables, base -> dnd55e -> Apotheosis, last layer wins per node UUID, passives' Boosts included) and
compares levels 1-20 with the 2024 full / half / third caster tables. Reads the bg3-data MCP index.
Run: python3 Scripts/slot_audit.py"""
import json
import os
import re
import sqlite3

DB = os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite")
FULL = {1: [2], 2: [3], 3: [4, 2], 4: [4, 3], 5: [4, 3, 2], 6: [4, 3, 3], 7: [4, 3, 3, 1], 8: [4, 3, 3, 2], 9: [4, 3, 3, 3, 1],
        10: [4, 3, 3, 3, 2], 11: [4, 3, 3, 3, 2, 1], 12: [4, 3, 3, 3, 2, 1], 13: [4, 3, 3, 3, 2, 1, 1], 14: [4, 3, 3, 3, 2, 1, 1],
        15: [4, 3, 3, 3, 2, 1, 1, 1], 16: [4, 3, 3, 3, 2, 1, 1, 1], 17: [4, 3, 3, 3, 2, 1, 1, 1, 1], 18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
        19: [4, 3, 3, 3, 3, 2, 1, 1, 1], 20: [4, 3, 3, 3, 3, 2, 2, 1, 1]}
HALF = {1: [2], 2: [2], 3: [3], 4: [3], 5: [4, 2], 6: [4, 2], 7: [4, 3], 8: [4, 3], 9: [4, 3, 2], 10: [4, 3, 2], 11: [4, 3, 3],
        12: [4, 3, 3], 13: [4, 3, 3, 1], 14: [4, 3, 3, 1], 15: [4, 3, 3, 2], 16: [4, 3, 3, 2], 17: [4, 3, 3, 3, 1], 18: [4, 3, 3, 3, 1],
        19: [4, 3, 3, 3, 2], 20: [4, 3, 3, 3, 2]}
THIRD = {3: [2], 4: [3], 5: [3], 6: [3], 7: [4, 2], 8: [4, 2], 9: [4, 2], 10: [4, 3], 11: [4, 3], 12: [4, 3], 13: [4, 3, 2],
         14: [4, 3, 2], 15: [4, 3, 2], 16: [4, 3, 3], 17: [4, 3, 3], 18: [4, 3, 3], 19: [4, 3, 3, 1], 20: [4, 3, 3, 1]}
CASTERS = {"Bard": FULL, "Cleric": FULL, "Druid": FULL, "Sorcerer": FULL, "Wizard": FULL, "Paladin": HALF, "Ranger": HALF,
           "Artificer": HALF, "EldritchKnight": THIRD, "ArcaneTrickster": THIRD, "MysticArts": THIRD}
# dnd55e features implemented as extra slots (not part of the curve): Divine Intervention's free 5th-level cast,
# Spell-Storing Item's stored spells; half casters get their first slots at 2 in dnd55e (its 1-12 design)
FEATURE_SLOTS = {"Cleric_10_DivineIntervention", "Artificer_11_SpellStoringItem"}
SKIP_LEVEL_1 = {"Paladin", "Ranger", "Artificer"}
SLOT = re.compile(r"ActionResource\(SpellSlot,\s*(\d+)\s*,\s*(\d+)\)")
RANK = {"base": 0, "dnd55e": 1, "apotheosis": 2}

con = sqlite3.connect(DB)
passive_boosts = {}
for name, layer, data in con.execute("SELECT name, layer, data FROM stats WHERE type='PassiveData' ORDER BY rank"):
    b = json.loads(data).get("Boosts")
    if b is not None:
        passive_boosts[name] = b


def curve(name):
    nodes = {}
    for layer, uuid, level, attrs in con.execute("SELECT layer, uuid, level, attrs FROM prog WHERE name=? ORDER BY rank", (name,)):
        a = json.loads(attrs)
        if str(a.get("IsMulticlass", "")).lower() == "true":
            continue
        nodes[uuid] = (int(level), a)  # last layer wins
    per = {}
    for level, a in nodes.values():
        text = a.get("Boosts") or ""
        passives = [x for x in (a.get("PassivesAdded") or "").split(";") if x]
        for p in passives:
            if p not in FEATURE_SLOTS:
                text += ";" + passive_boosts.get(p, "")
        for n, lvl in SLOT.findall(text):
            per.setdefault(level, {}).setdefault(int(lvl), 0)
            per[level][int(lvl)] += int(n)
    out, total = {}, {}
    for L in range(1, 21):
        for sl, n in per.get(L, {}).items():
            total[sl] = total.get(sl, 0) + n
        out[L] = [total.get(i, 0) for i in range(1, 10)]
    return out


bad = 0
for name, table in CASTERS.items():
    c = curve(name)
    for L in range(1, 21):
        if L == 1 and name in SKIP_LEVEL_1:
            continue
        want = (table.get(L, []) + [0] * 9)[:9]
        if c[L] != want:
            bad += 1
            print(f"{name:16s} L{L:2d}: has {c[L][:9]} want {want}")
print(f"{bad} level rows differ")
