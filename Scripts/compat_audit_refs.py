"""Extended compatibility audit for non-table references.

Checks Passives, Boosts (ActionResource names), and Selector UUIDs referenced by
Apotheosis progressions against what dnd55e defines AND what Apotheosis defines itself.
"""
import re
import os
from collections import defaultdict

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APO = os.path.join(WS, "PHB-2024-DND-13-20-Path-to-Apotheosis", "Public",
                   "PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa")
DND = os.path.join(WS, "dnd55e", "Public", "DnD2024_897914ef-5c96-053c-44af-0be823f895fe")


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def walk_text(root, exts):
    buf = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in exts:
                buf.append(read(os.path.join(dp, fn)))
    return "\n".join(buf)


def main():
    apo_prog = read(os.path.join(APO, "Progressions", "Progressions.lsx"))

    # All text we can resolve names/uuids against
    dnd_all = walk_text(DND, {".lsx", ".txt"})
    apo_all = walk_text(APO, {".lsx", ".txt"})
    known = dnd_all + "\n" + apo_all

    # --- Passives referenced (PassivesAdded / PassivesRemoved, semicolon lists) ---
    passives = set()
    for m in re.finditer(r'id="Passives(?:Added|Removed)"[^>]*value="([^"]*)"', apo_prog):
        for p in m.group(1).split(";"):
            p = p.strip()
            if p:
                passives.add(p)

    # --- ActionResource(...) names inside Boosts ---
    resources = set()
    for m in re.finditer(r'ActionResource\(([^,()]+),', apo_prog):
        resources.add(m.group(1).strip())

    # --- Selector referenced UUIDs (SelectPassives / SelectSpells / AddSpells etc.) ---
    sel_uuids = set()
    for m in re.finditer(r'id="Selectors"[^>]*value="([^"]*)"', apo_prog):
        for u in re.findall(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', m.group(1)):
            sel_uuids.add(u)

    def report(title, items, as_uuid=False):
        miss = []
        for it in sorted(items):
            # name-based: look for value="name" or name token; uuid-based: raw search
            if as_uuid:
                ok = it in known
            else:
                ok = (f'"{it}"' in known) or (f'value="{it}"' in known) or \
                     (re.search(r'\b' + re.escape(it) + r'\b', known) is not None)
            if not ok:
                miss.append(it)
        print(f"\n=== {title}: {len(items)} referenced, {len(miss)} unresolved ===")
        for m in miss:
            print("  MISS:", m)
        return miss

    report("PASSIVES", passives)
    report("ACTION RESOURCES (Boosts)", resources)
    report("SELECTOR UUIDs", sel_uuids, as_uuid=True)


if __name__ == "__main__":
    main()
