"""Compatibility audit: cross-check Apotheosis references against the rebuilt dnd55e.

Run from workspace root: python <this>.py
Prints a remap of broken progression TableUUIDs (old -> new) matched by subclass/class Name.
"""
import re
import os
from collections import defaultdict

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APO = os.path.join(WS, "PHB-2024-DND-13-20-Path-to-Apotheosis", "Public",
                   "PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa")
DND = os.path.join(WS, "dnd55e", "Public", "DnD2024_897914ef-5c96-053c-44af-0be823f895fe")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def parse_progressions(text):
    nodes = []
    for m in re.finditer(r'<node id="Progression">(.*?)</node>', text, re.S):
        body = m.group(1)

        def attr(n):
            mm = re.search(r'id="%s"[^>]*value="([^"]*)"' % n, body)
            return mm.group(1) if mm else None
        nodes.append({"Name": attr("Name"), "Table": attr("TableUUID"),
                      "Level": attr("Level"), "UUID": attr("UUID")})
    return nodes


def main():
    apo = read(os.path.join(APO, "Progressions", "Progressions.lsx"))
    dnd = read(os.path.join(DND, "Progressions", "Progressions.lsx"))
    apon = parse_progressions(apo)
    dndn = parse_progressions(dnd)

    dnd_name2tbl = defaultdict(set)
    for n in dndn:
        if n["Name"] and n["Table"]:
            dnd_name2tbl[n["Name"]].add(n["Table"])
    dnd_tables = set(n["Table"] for n in dndn if n["Table"])

    apo_tables = set(n["Table"] for n in apon if n["Table"])
    miss = [t for t in apo_tables if t not in dnd_tables]

    tbl2name = defaultdict(set)
    for n in apon:
        if n["Table"]:
            tbl2name[n["Table"]].add(n["Name"])

    print("OLD_TABLE | APO_NAME | NEW_DND_TABLE")
    remap = {}
    unresolved = []
    for t in sorted(miss):
        for nm in tbl2name[t]:
            cur = dnd_name2tbl.get(nm)
            if cur and len(cur) == 1:
                new = next(iter(cur))
                print(f"{t} | {nm} | {new}")
                remap[t] = new
            elif cur and len(cur) > 1:
                print(f"{t} | {nm} | MULTIPLE:{sorted(cur)}")
                unresolved.append((t, nm, cur))
            else:
                print(f"{t} | {nm} | *** NO DND TABLE FOR NAME ***")
                unresolved.append((t, nm, None))

    print(f"\nTotal miss: {len(miss)}  auto-remap: {len(remap)}  unresolved: {len(unresolved)}")

    # Manual rename map: Apotheosis name -> current dnd55e name (rebuild renamed these)
    RENAMES = {
        "AberrantSorcery": "Aberrant",
        "ArchitectsOfRuin": "ArchitectOfRuin",
        "ClockworkSorcery": "Clockwork",
        "NobleGenies": "NobleGenie",
        "SpellfireSorcery": "Spellfire",
        "WildMagicPath": "WildMagic",
        "PurpleDragonKnight": "Banneret",
        "ScionThree": "DeadThree",
    }
    print("\n=== MANUAL RENAME RESOLUTION (old apo table -> new dnd table) ===")
    for t in sorted(miss):
        for nm in tbl2name[t]:
            if nm in RENAMES:
                tgt = RENAMES[nm]
                cur = dnd_name2tbl.get(tgt)
                if cur and len(cur) == 1:
                    new = next(iter(cur))
                    print(f"{t} | {nm}->{tgt} | {new}")
                    remap[t] = new
                else:
                    print(f"{t} | {nm}->{tgt} | UNRESOLVED dnd tables={cur}")

    # Orphaned: still unresolved after renames (no dnd55e equivalent)
    orphan_names = {"ArcanaDomain", "SecretAgent", "Deadeye", "TrickShot",
                    "Psion", "Telepath", "Psykinetic", "Metamorph", "PsiWarper"}
    print("\n=== ORPHANED CONTENT (no dnd55e base; per-name progression node count) ===")
    name_levels = defaultdict(list)
    for n in apon:
        if n["Name"] in orphan_names:
            name_levels[n["Name"]].append(n["Level"])
    for nm in sorted(orphan_names):
        lv = sorted(name_levels.get(nm, []), key=lambda x: int(x) if x else 0)
        print(f"  {nm}: {len(lv)} nodes, levels {lv}")

    print(f"\nFINAL remap entries: {len(remap)}")
    return remap, unresolved


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
