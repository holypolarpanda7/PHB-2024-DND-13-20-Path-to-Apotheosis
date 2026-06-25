"""Build wizard 13-20 expectation matrix from manifests + Progressions.lsx.

This script combines the wizard subclass manifest index with Apotheosis
Progressions.lsx to generate a per-subclass expectation artifact used by smoke
validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def get_attr(node: ET.Element, attr_id: str, default: str = "") -> str:
    for attr in node.findall("attribute"):
        if attr.get("id") == attr_id:
            return attr.get("value", default)
    return default


def parse_progressions(progressions_file: Path) -> list[dict[str, object]]:
    root = ET.parse(progressions_file).getroot()
    nodes = root.findall(".//node[@id='Progression']")

    progressions: list[dict[str, object]] = []
    for node in nodes:
        name = get_attr(node, "Name", "")
        if not name:
            continue

        level_raw = get_attr(node, "Level", "0")
        try:
            level = int(level_raw)
        except ValueError:
            level = 0

        progressions.append(
            {
                "name": name,
                "level": level,
                "uuid": get_attr(node, "UUID", ""),
                "table_uuid": get_attr(node, "TableUUID", ""),
                "passives_added": get_attr(node, "PassivesAdded", ""),
                "passives_removed": get_attr(node, "PassivesRemoved", ""),
                "boosts": get_attr(node, "Boosts", ""),
                "selectors": get_attr(node, "Selectors", ""),
            }
        )

    return progressions


def levels_13_20(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted([item for item in items if 13 <= int(item.get("level", 0)) <= 20], key=lambda x: int(x["level"]))


def summarize_entry(entry: dict[str, object]) -> dict[str, object]:
    return {
        "level": entry["level"],
        "uuid": entry["uuid"],
        "passives_added": entry["passives_added"],
        "passives_removed": entry["passives_removed"],
        "boosts": entry["boosts"],
        "selectors": entry["selectors"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-index",
        type=Path,
        default=Path("Scripts/test_build_manifests/wizard_subclasses/wizard_subclass_manifest_index.json"),
        help="Path to wizard subclass manifest index JSON",
    )
    parser.add_argument(
        "--progressions",
        type=Path,
        default=Path(
            "Public/PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa/Progressions/Progressions.lsx"
        ),
        help="Path to Apotheosis Progressions.lsx",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Scripts/test_build_manifests/wizard_13_20_expectations.json"),
        help="Output JSON containing per-subclass expected 13-20 grants",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    index = json.loads(args.manifest_index.read_text(encoding="utf-8"))
    progressions = parse_progressions(args.progressions)

    wizard_base = levels_13_20([p for p in progressions if p["name"] == "Wizard"])

    manifests = list(index.get("generated_manifests", [])) + list(index.get("inferred_manifests", []))
    by_subclass: dict[str, dict[str, object]] = {}
    for item in manifests:
        by_subclass[str(item.get("subclass_name", ""))] = item

    subclasses: list[dict[str, object]] = []
    for subclass_name, manifest_meta in sorted(by_subclass.items(), key=lambda kv: kv[0].lower()):
        subclass_entries = levels_13_20([p for p in progressions if p["name"] == subclass_name])

        subclasses.append(
            {
                "subclass_name": subclass_name,
                "subclass_guid": manifest_meta.get("subclass_guid", ""),
                "manifest_file": manifest_meta.get("manifest_file", ""),
                "manifest_kind": "inferred" if "donor_subclass_guid" in manifest_meta else "canonical",
                "expected_wizard_base_13_20": [summarize_entry(x) for x in wizard_base],
                "expected_subclass_13_20": [summarize_entry(x) for x in subclass_entries],
                "has_subclass_entries": len(subclass_entries) > 0,
            }
        )

    payload = {
        "wizard_class_guid": index.get("wizard_class_guid", ""),
        "progressions_file": str(args.progressions),
        "subclass_count": len(subclasses),
        "subclasses": subclasses,
    }

    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote expectation matrix: {args.output}")
    print(f"Wizard base progression entries (13-20): {len(wizard_base)}")
    for sub in subclasses:
        print(
            f"- {sub['subclass_name']}: subclass entries={len(sub['expected_subclass_13_20'])}, manifest={sub['manifest_kind']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
