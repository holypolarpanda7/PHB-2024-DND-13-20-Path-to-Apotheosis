"""Build per-level grant expectations for EVERY class and subclass in Apotheosis.

Generalizes the wizard-only expectation pipeline:
  - reads Apotheosis Progressions.lsx (all ProgressionType 0/1 nodes)
  - maps subclass progression tables to their parent class via dnd55e
    ClassDescriptions.lsx (ParentGuid -> class UUID -> class name)
  - emits:
      Scripts/test_build_manifests/all_class_expectations.json
      Mods/<guid>/ScriptExtender/Lua/ClassExpectations.lua

Run after any Progressions.lsx change:
    python Scripts/build_all_class_expectations.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

APO_PUBLIC = Path(
    "Public/PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
)
PROGRESSIONS = APO_PUBLIC / "Progressions" / "Progressions.lsx"
# later sources override earlier ones (dnd55e wins over base game)
CLASSDESC_SOURCES = [
    Path("../BaseGame/Shared/Public/Shared/ClassDescriptions/ClassDescriptions.lsx"),
    Path("../BaseGame/Shared/Public/SharedDev/ClassDescriptions/ClassDescriptions.lsx"),
    Path("../BaseGame/GustavX/Public/GustavX/ClassDescriptions/ClassDescriptions.lsx"),
    Path(
        "../dnd55e/Public/DnD2024_897914ef-5c96-053c-44af-0be823f895fe"
        "/ClassDescriptions/ClassDescriptions.lsx"
    ),
]
OUT_JSON = Path("Scripts/test_build_manifests/all_class_expectations.json")
OUT_LUA = Path(
    "Mods/PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
    "/ScriptExtender/Lua/ClassExpectations.lua"
)

NODE_RE = re.compile(r'<node id="(?:Progression|ClassDescription)">.*?</node>', re.S)
ATTR_RE = re.compile(r'<attribute id="([^"]+)"[^/]*?value="([^"]*)"')


def parse_nodes(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [dict(ATTR_RE.findall(node)) for node in NODE_RE.findall(text)]


def passives_list(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    parts = [p.strip() for p in value.replace(";", ",").split(",")]
    return [p for p in parts if p]


def build_class_map() -> dict[str, dict]:
    """table UUID -> {name, parent_name or None} from base game + dnd55e ClassDescriptions."""
    nodes: list[dict] = []
    for src in CLASSDESC_SOURCES:
        if src.exists():
            nodes.extend(parse_nodes(src))
        else:
            print(f"WARNING: ClassDescriptions source missing: {src}")
    by_uuid = {n["UUID"]: n for n in nodes if "UUID" in n and "Name" in n}
    table_map: dict[str, dict] = {}
    table_desc_uuids: dict[str, list[str]] = {}
    for n in nodes:
        table = n.get("ProgressionTableUUID")
        if not table or "Name" not in n:
            continue
        parent_name = None
        parent = n.get("ParentGuid")
        if parent and parent in by_uuid:
            parent_name = by_uuid[parent]["Name"]
        # later sources override earlier ones (dnd55e wins over base game)
        table_map[table] = {"name": n["Name"], "parent": parent_name}
        if n.get("UUID"):
            uuids = table_desc_uuids.setdefault(table, [])
            if n["UUID"] not in uuids:
                uuids.append(n["UUID"])
    return table_map, table_desc_uuids


def main() -> int:
    table_map, table_desc_uuids = build_class_map()
    prog_nodes = parse_nodes(PROGRESSIONS)

    classes: dict[str, dict] = {}
    subclasses: dict[str, dict] = {}
    unmapped: set[str] = set()

    for n in prog_nodes:
        name = n.get("Name")
        level = n.get("Level")
        if not name or not level:
            continue
        table = n.get("TableUUID", "")
        ptype = n.get("ProgressionType", "")
        mapped = table_map.get(table)
        is_subclass = (mapped and mapped["parent"]) or ptype == "1"
        parent = mapped["parent"] if (mapped and mapped["parent"]) else None
        if is_subclass and not parent:
            unmapped.add(name)

        entry = {
            "passives": passives_list(n.get("PassivesAdded", "")),
            "boosts": n.get("Boosts", ""),
            "selectors": n.get("Selectors", ""),
        }

        bucket = subclasses if is_subclass else classes
        rec = bucket.setdefault(
            name,
            {"table_uuid": table, "parent": parent, "levels": {}},
        )
        lvl = int(level)
        if lvl in rec["levels"]:
            # merge multiclass/duplicate rows for the same level
            rec["levels"][lvl]["passives"].extend(
                p for p in entry["passives"] if p not in rec["levels"][lvl]["passives"]
            )
        else:
            rec["levels"][lvl] = entry

    # resolve subclass parents that came from ProgressionType only:
    # match dnd55e name shared with an Apotheosis class we know about
    for name, rec in subclasses.items():
        if not rec["parent"]:
            mapped = table_map.get(rec["table_uuid"])
            if mapped and mapped["parent"]:
                rec["parent"] = mapped["parent"]

    # ClassDescription UUID -> expectation-table name, so the SE runtime can
    # resolve a live character's class/subclass from its Classes component
    class_uuid_map: dict[str, str] = {}
    subclass_uuid_map: dict[str, str] = {}
    for name, rec in classes.items():
        for u in table_desc_uuids.get(rec["table_uuid"], []):
            class_uuid_map[u] = name
    for name, rec in subclasses.items():
        for u in table_desc_uuids.get(rec["table_uuid"], []):
            subclass_uuid_map[u] = name

    data = {
        "source": str(PROGRESSIONS),
        "classes": classes,
        "subclasses": subclasses,
        "class_uuids": class_uuid_map,
        "subclass_uuids": subclass_uuid_map,
        "unmapped_subclass_parents": sorted(unmapped),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    OUT_LUA.write_text(emit_lua(classes, subclasses, class_uuid_map, subclass_uuid_map), encoding="utf-8")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_LUA}")
    print(f"Classes: {len(classes)}  Subclasses: {len(subclasses)}")
    if unmapped:
        print(f"Subclasses with unresolved parent class: {', '.join(sorted(unmapped))}")
    return 0


def lua_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def lua_str_list(items: list[str]) -> str:
    if not items:
        return "{}"
    return "{ " + ", ".join(lua_str(i) for i in items) + " }"


def emit_levels(levels: dict[int, dict], pad: str) -> list[str]:
    lines = []
    for lvl in sorted(levels):
        e = levels[lvl]
        lines.append(f"{pad}[{lvl}] = {{")
        lines.append(f"{pad}    passives  = {lua_str_list(e['passives'])},")
        if e["boosts"]:
            lines.append(f"{pad}    boosts    = {lua_str(e['boosts'])},")
        if e["selectors"]:
            lines.append(f"{pad}    selectors = {lua_str(e['selectors'])},")
        lines.append(f"{pad}}},")
    return lines


def emit_lua(classes: dict, subclasses: dict, class_uuid_map: dict, subclass_uuid_map: dict) -> str:
    lines = [
        "-- AUTO-GENERATED by Scripts/build_all_class_expectations.py",
        "-- DO NOT EDIT BY HAND.  Re-run the generator after Progressions.lsx changes.",
        "-- Loaded by BootstrapServer.lua and exposed as _G.ApotheosisClassExpectations.",
        "",
        "local M = { classes = {}, subclasses = {}, class_uuids = {}, subclass_uuids = {} }",
        "",
    ]
    for u in sorted(class_uuid_map):
        lines.append(f"M.class_uuids[{lua_str(u)}] = {lua_str(class_uuid_map[u])}")
    for u in sorted(subclass_uuid_map):
        lines.append(f"M.subclass_uuids[{lua_str(u)}] = {lua_str(subclass_uuid_map[u])}")
    lines.append("")
    for name in sorted(classes):
        rec = classes[name]
        lines.append(f"M.classes[{lua_str(name)}] = {{")
        lines.append("    levels = {")
        lines.extend(emit_levels(rec["levels"], " " * 8))
        lines.append("    },")
        lines.append("}")
        lines.append("")
    for name in sorted(subclasses):
        rec = subclasses[name]
        parent = lua_str(rec["parent"]) if rec["parent"] else "nil"
        lines.append(f"M.subclasses[{lua_str(name)}] = {{")
        lines.append(f"    parent = {parent},")
        lines.append("    levels = {")
        lines.extend(emit_levels(rec["levels"], " " * 8))
        lines.append("    },")
        lines.append("}")
        lines.append("")
    lines.append("_G.ApotheosisClassExpectations = M")
    lines.append("return M")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
