"""Extract structured level-up manifests from BG3 PartyEditor LSX presets.

This turns a PartyEditor preset into JSON that can be used as a canonical
test-build manifest for choice-driven smoke tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional


def build_guid_map(class_descriptions_file: Path) -> dict[str, str]:
    """Load ClassDescriptions.lsx and build UUID → Name mapping for classes/subclasses."""
    guid_map: dict[str, str] = {}
    if not class_descriptions_file.exists():
        return guid_map

    try:
        root = ET.parse(class_descriptions_file).getroot()
        for class_node in root.findall(".//node[@id='ClassDescription']"):
            uuid_attr = get_attr(class_node, "UUID", "")
            name_attr = get_attr(class_node, "Name", "")
            if uuid_attr and name_attr:
                guid_map[uuid_attr] = name_attr
    except Exception:
        pass  # If parsing fails, return empty map; resolution will be skipped
    return guid_map


def resolve_guids_in_manifest(manifest: dict[str, object], guid_map: dict[str, str]) -> dict[str, object]:
    """Add human-readable names alongside GUID fields using the provided mapping."""
    # Resolve class/subclass names in each level-up
    if "level_ups" in manifest and isinstance(manifest["level_ups"], list):
        for level_up in manifest["level_ups"]:
            if isinstance(level_up, dict):
                if "class_guid" in level_up and isinstance(level_up["class_guid"], str):
                    guid = level_up["class_guid"]
                    if guid in guid_map:
                        level_up["class_name"] = guid_map[guid]
                if "subclass_guid" in level_up and isinstance(level_up["subclass_guid"], str):
                    guid = level_up["subclass_guid"]
                    if guid in guid_map:
                        level_up["subclass_name"] = guid_map[guid]

    # Resolve origin/background/race/subrace names in basics
    if "basics" in manifest and isinstance(manifest["basics"], dict):
        basics = manifest["basics"]
        for field in ["origin_guid", "background_guid", "race_guid", "subrace_guid"]:
            if field in basics and isinstance(basics[field], str):
                guid = basics[field]
                if guid in guid_map:
                    name_field = field.replace("_guid", "_name")
                    basics[name_field] = guid_map[guid]

    return manifest


def get_attr(node: ET.Element, attr_id: str, default=None):
    for attr in node.findall("attribute"):
        if attr.get("id") == attr_id:
            return attr.get("value", default)
    return default


def get_child(node: ET.Element, child_id: str) -> ET.Element | None:
    children = node.find("children")
    if children is None:
        return None
    for child in children.findall("node"):
        if child.get("id") == child_id:
            return child
    return None


def get_children(node: ET.Element, child_id: str | None = None) -> list[ET.Element]:
    children = node.find("children")
    if children is None:
        return []
    nodes = children.findall("node")
    if child_id is None:
        return nodes
    return [child for child in nodes if child.get("id") == child_id]


def parse_value_list(node: ET.Element, value_attr: str) -> list[str]:
    values = []
    for child in get_children(node):
        value = get_attr(child, value_attr)
        if value is not None:
            cleaned = value.strip()
            if cleaned:
                values.append(cleaned)
    return values


def parse_prepared_spells(level_up: ET.Element) -> list[dict[str, object]]:
    prepared_spells = []
    prepared = get_child(level_up, "PreparedSpells")
    prepared_slots = get_child(prepared, "PreparedSpellSlots") if prepared is not None else None
    for slot in get_children(prepared_slots, "PreparedSpellSlot"):
        prepared_spells.append(
            {
                "spell": get_attr(slot, "OriginatorPrototype", ""),
                "progression_source": get_attr(slot, "ProgressionSource", ""),
                "source_type": int(get_attr(slot, "SourceType", "0")),
            }
        )
    return prepared_spells


def parse_selector_node(selector: ET.Element) -> dict[str, object]:
    data: dict[str, object] = {
        "node_id": selector.get("id", ""),
        "definition_index": int(get_attr(selector, "DefinitionIndex", "0")),
        "list_uuid": get_attr(selector, "ListUUID", ""),
        "selector_id": get_attr(selector, "SelectorId", "").strip(),
    }

    level = get_attr(selector, "Level")
    if level is not None:
        data["level"] = int(level)

    owner_uuid = get_attr(selector, "OwnerUUID")
    if owner_uuid is not None:
        data["owner_uuid"] = owner_uuid

    parent_owner_uuid = get_attr(selector, "ParentOwnerUUID")
    if parent_owner_uuid is not None:
        data["parent_owner_uuid"] = parent_owner_uuid

    is_multiclass = get_attr(selector, "IsMulticlass")
    if is_multiclass is not None:
        data["is_multiclass"] = is_multiclass.lower() == "true"

    addition_slots = get_child(selector, "AdditionSlots")
    if addition_slots is not None:
        data["addition_slots"] = parse_value_list(addition_slots, "Value")

    replacement_slots = get_child(selector, "ReplacementSlots")
    if replacement_slots is not None:
        data["replacement_slots"] = parse_value_list(replacement_slots, "Value")

    prepared_spell_slots = get_child(selector, "PreparedSpellSlots")
    if prepared_spell_slots is not None:
        data["prepared_spell_slots"] = parse_value_list(prepared_spell_slots, "Value")

    slots = get_child(selector, "Slots")
    if slots is not None:
        data["slots"] = [int(value) for value in parse_value_list(slots, "Value")]

    slot_bonus_values = get_child(selector, "SlotBonusValues")
    if slot_bonus_values is not None:
        data["slot_bonus_values"] = [int(value) for value in parse_value_list(slot_bonus_values, "Object")]

    return data


def parse_selectors(level_up: ET.Element) -> dict[str, list[dict[str, object]]]:
    selectors = get_child(level_up, "Selectors")
    if selectors is None:
        return {}

    selector_groups: dict[str, list[dict[str, object]]] = {}
    for group in get_children(selectors):
        group_key = group.get("id", "")
        parsed = [parse_selector_node(selector) for selector in get_children(group)]
        if parsed:
            selector_groups[group_key] = parsed
    return selector_groups


def parse_ability_improvements(level_up: ET.Element) -> list[int]:
    improvements = get_child(level_up, "AbilityImprovements")
    if improvements is None:
        return []
    return [int(get_attr(child, "Object", "0")) for child in get_children(improvements, "AbilityImprovement")]


def parse_level_up(level_up: ET.Element, level_index: int) -> dict[str, object]:
    return {
        "level": level_index,
        "class_guid": get_attr(level_up, "Class", ""),
        "subclass_guid": get_attr(level_up, "SubClass", ""),
        "feat_guid": get_attr(level_up, "Feat", ""),
        "ability_improvements": parse_ability_improvements(level_up),
        "prepared_spells": parse_prepared_spells(level_up),
        "selectors": parse_selectors(level_up),
    }


def parse_preset(preset: ET.Element, source_file: Path, preset_index: int) -> dict[str, object]:
    full_definition = get_child(preset, "FullDefinition")
    basics = get_child(full_definition, "Basics") if full_definition is not None else None
    level_ups = get_child(full_definition, "LevelUps") if full_definition is not None else None

    level_up_entries = []
    for index, level_up in enumerate(get_children(level_ups, "LevelUp"), start=1):
        level_up_entries.append(parse_level_up(level_up, index))

    return {
        "source_file": str(source_file),
        "preset_index": preset_index,
        "character_name": get_attr(full_definition, "CustomName", ""),
        "character_uuid": get_attr(preset, "CharacterUUID", ""),
        "level_tag": get_attr(preset, "Level", ""),
        "total_experience": int(get_attr(preset, "TotalExperience", "0")),
        "basics": {
            "origin_guid": get_attr(basics, "Origin", "") if basics is not None else "",
            "background_guid": get_attr(basics, "Background", "") if basics is not None else "",
            "race_guid": get_attr(basics, "Race", "") if basics is not None else "",
            "subrace_guid": get_attr(basics, "SubRace", "") if basics is not None else "",
        },
        "level_ups": level_up_entries,
    }


def load_presets(source_file: Path) -> list[ET.Element]:
    root = ET.parse(source_file).getroot()
    party_preset = root.find("./region[@id='PartyPreset']/node[@id='root']")
    if party_preset is None:
        raise ValueError("Could not find PartyPreset root")

    presets_node = get_child(party_preset, "Presets")
    presets = get_children(presets_node, "Preset") if presets_node is not None else []
    if not presets:
        raise ValueError("No Preset nodes found")
    return presets


def select_preset(presets: list[ET.Element], character_name: str | None, preset_index: int | None) -> tuple[int, ET.Element]:
    if character_name:
        for index, preset in enumerate(presets, start=1):
            full_definition = get_child(preset, "FullDefinition")
            name = get_attr(full_definition, "CustomName", "") if full_definition is not None else ""
            if name.lower() == character_name.lower():
                return index, preset
        raise ValueError(f"Character '{character_name}' not found")

    if preset_index is None:
        return 1, presets[0]

    if preset_index < 1 or preset_index > len(presets):
        raise ValueError(f"Preset index {preset_index} out of range 1..{len(presets)}")
    return preset_index, presets[preset_index - 1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_file", type=Path, help="PartyEditor LSX file to extract from")
    parser.add_argument("--character-name", help="Preset character CustomName to extract")
    parser.add_argument("--preset-index", type=int, help="1-based preset index when a file contains multiple presets")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument(
        "--with-names",
        type=Path,
        metavar="CLASSDESCRIPTIONS_LSX",
        help="Resolve GUIDs to human-readable names using ClassDescriptions.lsx (enables readable diffs and error messages)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    presets = load_presets(args.source_file)
    preset_index, preset = select_preset(presets, args.character_name, args.preset_index)
    manifest = parse_preset(preset, args.source_file, preset_index)

    # Resolve GUIDs to names if requested
    if args.with_names:
        guid_map = build_guid_map(args.with_names)
        manifest = resolve_guids_in_manifest(manifest, guid_map)

    payload = json.dumps(manifest, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())