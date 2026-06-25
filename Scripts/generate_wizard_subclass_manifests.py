"""Generate canonical wizard-subclass manifests from PartyEditor presets.

This script scans PartyEditor LSX files, finds presets that contain wizard
level-up decisions with explicit subclass picks, and exports one canonical
manifest per wizard subclass.
"""

from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from extract_partyeditor_levelups import (
    get_attr,
    get_child,
    get_children,
    load_presets,
    parse_preset,
    resolve_guids_in_manifest,
)

WIZARD_GUID = "a865965f-501b-46e9-9eaa-7748e8c04d09"
ZERO_GUID = "00000000-0000-0000-0000-000000000000"


@dataclass
class ClassDescriptionEntry:
    uuid: str
    name: str
    parent_guid: str


@dataclass
class PresetCandidate:
    source_file: Path
    preset_index: int
    character_name: str
    character_uuid: str
    total_levels: int
    wizard_level_count: int
    wizard_subclasses: set[str]


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "unknown"


def load_class_descriptions(files: Iterable[Path]) -> dict[str, ClassDescriptionEntry]:
    import xml.etree.ElementTree as ET

    entries: dict[str, ClassDescriptionEntry] = {}
    for file_path in files:
        if not file_path.exists():
            continue

        root = ET.parse(file_path).getroot()
        for node in root.findall(".//node[@id='ClassDescription']"):
            uuid = get_attr(node, "UUID", "")
            name = get_attr(node, "Name", "")
            parent = get_attr(node, "ParentGuid", "")
            if uuid and name and uuid not in entries:
                entries[uuid] = ClassDescriptionEntry(uuid=uuid, name=name, parent_guid=parent)

    return entries


def collect_candidates(partyeditor_dir: Path) -> list[PresetCandidate]:
    candidates: list[PresetCandidate] = []

    for source_file in sorted(partyeditor_dir.glob("*.lsx")):
        try:
            presets = load_presets(source_file)
        except Exception:
            continue

        for preset_index, preset in enumerate(presets, start=1):
            full_definition = get_child(preset, "FullDefinition")
            level_ups = get_child(full_definition, "LevelUps") if full_definition is not None else None
            if level_ups is None:
                continue

            wizard_level_count = 0
            wizard_subclasses: set[str] = set()
            total_levels = 0
            for level_up in get_children(level_ups, "LevelUp"):
                total_levels += 1
                class_guid = get_attr(level_up, "Class", "")
                subclass_guid = get_attr(level_up, "SubClass", "")
                if class_guid == WIZARD_GUID:
                    wizard_level_count += 1
                    if subclass_guid and subclass_guid != ZERO_GUID:
                        wizard_subclasses.add(subclass_guid)

            if wizard_level_count == 0 or not wizard_subclasses:
                continue

            candidates.append(
                PresetCandidate(
                    source_file=source_file,
                    preset_index=preset_index,
                    character_name=get_attr(full_definition, "CustomName", "") if full_definition is not None else "",
                    character_uuid=get_attr(preset, "CharacterUUID", ""),
                    total_levels=total_levels,
                    wizard_level_count=wizard_level_count,
                    wizard_subclasses=wizard_subclasses,
                )
            )

    return candidates


def candidate_score(candidate: PresetCandidate) -> tuple[int, int, int, int]:
    name = candidate.character_name.lower()
    gale_bonus = 1 if name == "gale" else 0
    named_bonus = 1 if bool(name) else 0
    return (
        candidate.wizard_level_count,
        candidate.total_levels,
        gale_bonus,
        named_bonus,
    )


def choose_best_candidates(candidates: list[PresetCandidate]) -> dict[str, PresetCandidate]:
    by_subclass: dict[str, list[PresetCandidate]] = {}
    for candidate in candidates:
        for subclass_guid in candidate.wizard_subclasses:
            by_subclass.setdefault(subclass_guid, []).append(candidate)

    selected: dict[str, PresetCandidate] = {}
    for subclass_guid, group in by_subclass.items():
        best = max(group, key=candidate_score)
        selected[subclass_guid] = best
    return selected


def build_guid_name_map(entries: dict[str, ClassDescriptionEntry]) -> dict[str, str]:
    return {entry.uuid: entry.name for entry in entries.values()}


def write_manifest(candidate: PresetCandidate, subclass_name: str, output_dir: Path, guid_name_map: dict[str, str]) -> str:
    presets = load_presets(candidate.source_file)
    preset = presets[candidate.preset_index - 1]
    manifest = parse_preset(preset, candidate.source_file, candidate.preset_index)
    manifest = resolve_guids_in_manifest(manifest, guid_name_map)

    file_name = f"wizard_{safe_name(subclass_name).lower()}_canonical.json"
    out_path = output_dir / file_name
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return file_name


def infer_manifest_from_donor(
    donor_candidate: PresetCandidate,
    donor_subclass_guid: str,
    target_subclass_guid: str,
    target_subclass_name: str,
    output_dir: Path,
    guid_name_map: dict[str, str],
) -> str:
    presets = load_presets(donor_candidate.source_file)
    preset = presets[donor_candidate.preset_index - 1]
    manifest = parse_preset(preset, donor_candidate.source_file, donor_candidate.preset_index)
    manifest = copy.deepcopy(manifest)

    replaced = 0
    for level_up in manifest.get("level_ups", []):
        if not isinstance(level_up, dict):
            continue
        if level_up.get("class_guid") != WIZARD_GUID:
            continue

        subclass_guid = level_up.get("subclass_guid", "")
        if subclass_guid == donor_subclass_guid:
            level_up["subclass_guid"] = target_subclass_guid
            replaced += 1

    if replaced == 0:
        for level_up in manifest.get("level_ups", []):
            if not isinstance(level_up, dict):
                continue
            if level_up.get("class_guid") != WIZARD_GUID:
                continue
            if int(level_up.get("level", 0)) >= 2:
                level_up["subclass_guid"] = target_subclass_guid
                replaced += 1
                break

    manifest["inference"] = {
        "inferred": True,
        "method": "subclass_guid_substitution",
        "confidence": "medium",
        "target_subclass_guid": target_subclass_guid,
        "target_subclass_name": target_subclass_name,
        "donor_subclass_guid": donor_subclass_guid,
        "donor_subclass_name": guid_name_map.get(donor_subclass_guid, ""),
        "donor_source_file": str(donor_candidate.source_file),
        "donor_preset_index": donor_candidate.preset_index,
        "replaced_level_entries": replaced,
    }

    manifest = resolve_guids_in_manifest(manifest, guid_name_map)

    file_name = f"wizard_{safe_name(target_subclass_name).lower()}_inferred.json"
    out_path = output_dir / file_name
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return file_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--partyeditor-dir",
        type=Path,
        default=Path(r"D:\BG3Modding\Mod_Projects\BaseGame\Gustav\Mods\GustavDev\Story\PartyEditor"),
        help="Directory containing PartyEditor .lsx files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("Scripts/test_build_manifests/wizard_subclasses"),
        help="Output directory for generated canonical manifests",
    )
    parser.add_argument(
        "--class-descriptions",
        type=Path,
        nargs="+",
        default=[
            Path(r"D:\BG3Modding\Mod_Projects\dnd55e\Public\DnD2024_897914ef-5c96-053c-44af-0be823f895fe\ClassDescriptions\ClassDescriptions.lsx"),
            Path(r"D:\BG3Modding\Mod_Projects\BaseGame\Shared\Public\Shared\ClassDescriptions\ClassDescriptions.lsx"),
        ],
        help="ClassDescriptions.lsx files used for GUID-to-name resolution and subclass inventory",
    )
    parser.add_argument(
        "--infer-missing",
        action="store_true",
        help="Infer missing subclass manifests by substituting subclass GUIDs from a donor canonical manifest",
    )
    parser.add_argument(
        "--infer-source-subclass",
        default="EvocationSchool",
        help="Donor subclass name used for inference when --infer-missing is enabled (default: EvocationSchool)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    class_entries = load_class_descriptions(args.class_descriptions)
    guid_name_map = build_guid_name_map(class_entries)

    wizard_subclasses = {
        entry.uuid: entry.name
        for entry in class_entries.values()
        if entry.parent_guid == WIZARD_GUID
    }

    candidates = collect_candidates(args.partyeditor_dir)
    selected = choose_best_candidates(candidates)

    generated: list[dict[str, object]] = []
    for subclass_guid, subclass_name in sorted(wizard_subclasses.items(), key=lambda item: item[1].lower()):
        best = selected.get(subclass_guid)
        if best is None:
            continue

        file_name = write_manifest(best, subclass_name, output_dir, guid_name_map)
        generated.append(
            {
                "subclass_guid": subclass_guid,
                "subclass_name": subclass_name,
                "manifest_file": file_name,
                "source_file": str(best.source_file),
                "preset_index": best.preset_index,
                "character_name": best.character_name,
                "wizard_level_count": best.wizard_level_count,
                "total_levels": best.total_levels,
            }
        )

    by_name = {name.lower(): guid for guid, name in wizard_subclasses.items()}
    inferred: list[dict[str, object]] = []

    if args.infer_missing:
        donor_guid = by_name.get(str(args.infer_source_subclass).lower())
        donor_candidate = selected.get(donor_guid) if donor_guid else None

        if donor_candidate is not None and donor_guid is not None:
            for subclass_guid, subclass_name in sorted(wizard_subclasses.items(), key=lambda item: item[1].lower()):
                if subclass_guid in selected:
                    continue

                file_name = infer_manifest_from_donor(
                    donor_candidate=donor_candidate,
                    donor_subclass_guid=donor_guid,
                    target_subclass_guid=subclass_guid,
                    target_subclass_name=subclass_name,
                    output_dir=output_dir,
                    guid_name_map=guid_name_map,
                )
                inferred.append(
                    {
                        "subclass_guid": subclass_guid,
                        "subclass_name": subclass_name,
                        "manifest_file": file_name,
                        "donor_subclass_guid": donor_guid,
                        "donor_subclass_name": wizard_subclasses.get(donor_guid, ""),
                        "donor_source_file": str(donor_candidate.source_file),
                        "donor_preset_index": donor_candidate.preset_index,
                    }
                )

    missing = [
        {"subclass_guid": guid, "subclass_name": name}
        for guid, name in sorted(wizard_subclasses.items(), key=lambda item: item[1].lower())
        if guid not in selected and guid not in {item["subclass_guid"] for item in inferred}
    ]

    index = {
        "wizard_class_guid": WIZARD_GUID,
        "partyeditor_dir": str(args.partyeditor_dir),
        "total_candidates": len(candidates),
        "generated_manifests": generated,
        "inferred_manifests": inferred,
        "missing_subclasses": missing,
    }

    index_path = output_dir / "wizard_subclass_manifest_index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(generated)} canonical wizard manifests")
    if inferred:
        print(f"Generated {len(inferred)} inferred wizard manifests")
    if missing:
        print("Missing subclasses:")
        for item in missing:
            print(f"  - {item['subclass_name']} ({item['subclass_guid']})")

    print(f"Index written to: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
