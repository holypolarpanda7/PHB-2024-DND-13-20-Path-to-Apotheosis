# Sources for dnd55e's third-party subclasses (researched 2026-10-03)

`Scripts/subclass_gap_audit.py` lists dnd55e subclasses with no features past level 12. dnd55e's wiki
(`github.com/Yoonmoonsik/bg3dnd/wiki`, cloned from `bg3dnd.wiki.git`) describes what it built but names no sources, so the
sources below were found by web search on feature names (VISION principle 1: follow the source dnd55e uses; principle 4:
no homebrew). dnd55e often rewrites its subclasses for the 2024 rules (features moved, merged or reworked), so a source's
13+ feature is only "missing" if dnd55e didn't already fold it into levels 1-12.

Status: BUILT = in `Scripts/gen_subclass_features.py` and tested in game; TEXT = source text found, not built yet; NO TEXT =
source identified but its rules text isn't reachable (paid book, site blocks automated fetches); UNKNOWN = no source found.

| Class | Subclass | Source (confidence) | Source's 13+ features | Status |
| --- | --- | --- | --- | --- |
| Barbarian | Shadow Gnawer | Book of Ebon Tides, Open Design 2022 (OGL, 5esrd) - certain | 14 Corrosive Haze | BUILT |
| Cleric | Shadow Domain | Book of Ebon Tides, Open Design 2022 (OGL, 5esrd) - certain | 17 Army of Shadow | BUILT |
| Cleric | Mind Domain | Exploring Eberron, Keith Baker (dnd5e.wikidot "Mind Domain (HB)") - certain | 17 Bend Reality | BUILT (interrupt is a manual check) |
| Rogue | Highway Rider | Grim Hollow Player's Guide (Nieb's Critical Collection mirror) - certain | 13 True Grit, 17 Desperado | 13 BUILT (Constitution proficiency only); 17 BUILT (free weapon attack option only) |
| Rogue | Arachnoid Stalker | Valda's Spire of Secrets, Mage Hand Press, 2024 version (magehandpress.com/2024/10/arachnoid-stalker) - certain | 13 Web Walker, 17 Paralytic Venom | 13 BUILT; 17 TEXT (dnd55e already has a Cunning Strike Paralytic Venom at 9) |
| Druid | Circle of Dragons | The Griffon's Saddlebag: Book Two - certain | 14 Heart of a Dragon (breath weapon outside dragon form, better AC and Fly speed, three attacks) | NO TEXT (summary only, no numbers) |
| Druid | Circle of the Unbroken | The Griffon's Saddlebag: Book One (Bell of Lost Souls) - certain | 14: Shillelagh Mastery d12 | NO TEXT |
| Bard | College of Choreography | The Griffon's Saddlebag: Book One - certain | 14: ? | NO TEXT |
| Cleric | Astral Domain | The Griffon's Saddlebag: Book One - certain | 17 Supreme Switching (upgrades Spatial Exchange / Misty Step) | NO TEXT |
| Cleric | Dragon Domain | Valda's Spire of Secrets (D&D Beyond lists "Cleric - Dragon Domain") - likely | 17: ? | NO TEXT |
| Sorcerer | Heroic Sorcery | Valda's Spire of Secrets "Heroic Bloodline" (capstone: Haste without Concentration) - likely; dnd55e's version (Heroic Spells, Martial Sorcery, Extra Attack, War Magic) is a rework | 14 / 18: ? | NO TEXT (Mage Hand Press's 2017 "Reincarnated Hero" is a different, older subclass) |
| Fighter | Viking | Kobold Press, Northlands Worldbook (Seaborne, Savage Charge, Call of the Northlands) - certain | 15 Marauder's Reprisal, 18 Unstoppable Assault (levels per the dnd55e gap) | NO TEXT |
| Rogue | Blade of Radiance | Steinhardt's Guide to the Eldritch Hunt (World Anvil homebrew, masongarth2000) - certain | 13 / 17: ? (Chains of Judgement, Divine Retaliation are 9) | NO TEXT (World Anvil returns 403) |
| Barbarian | Fractured | Grim Hollow, "Barbarian: Path of the Fractured" (grimhollow.fandom.com, Scribd copy) - certain | 14: ? (3 Face of Rage / Mask of Civility, 6 Brains and Brawn, 10 Cunning and Brutal) | NO TEXT (fandom returns 402) |
| Cleric | Apocalypse Domain | not Midgard Heroes Handbook (features differ: Ranting Ruin, Damnation, Weight of Guilt, Herald of the Apocalypse) | ? | UNKNOWN (dnd55e's Visions of Annihilation / Doom Song / All Will Be Dust aren't in any version found) |
| Sorcerer | Frost Sorcery | dandwiki "Frost Sorcery" is a different design | ? | UNKNOWN |

Built with a known gap:
- **Highway Rider 17 Desperado** ("reduced to 0 HP: use your Reaction for one Hair Trigger action before you fall"): a stand-in
  `DownedStatus` plus a Lua hook fires a free Hair Trigger attack (Advantage) at the nearest hostile, then the character
  falls. Only the attack option of Hair Trigger is offered (no move / Dodge / use object choice).
- **True Grit's Evasion-style half**: the engine's Evasion is Dexterity-only, so only the Constitution proficiency is built.

To finish a NO TEXT row, add the book's text under `References/Subclasses/` (or The Oracle's `owned_books`) and its features to
`Scripts/gen_subclass_features.py`. `Scripts/regen_all.sh` then regenerates everything.

Also open (not sourcing gaps): the half-caster 13/17 spells BG3 doesn't have (`Scripts/gen_subclass_spells.py` MISSING).
