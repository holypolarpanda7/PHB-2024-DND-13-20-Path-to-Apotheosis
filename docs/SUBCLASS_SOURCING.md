# Subclasses without a 13-20 source (2026-10-03)

`Scripts/subclass_gap_audit.py` still lists these dnd55e subclasses with no features past level 12. Their 13-20
features aren't built because the rules text dnd55e follows isn't available here (VISION.md principle 1: follow the
source dnd55e uses; principle 4: no homebrew in its place). To finish one, add its source text to
`References/Subclasses/` (or The Oracle) and its features to `Scripts/gen_subclass_features.py`.

| Class | Subclass | Missing levels | dnd55e has (1-12) | Likely source (web search, unverified) |
| --- | --- | --- | --- | --- |
| Barbarian | Fractured | 14 | 3 Face of Rage / Mask of Civility, 6 Brains and Brawn, 10 Cunning and Brutal | GamingBrew Tomes Subclass Pack? (mentions "fractured") |
| Barbarian | Shadow Gnawer | 14 | 3 Shadow Smoke, 6 Creeping Fog, 10 Consume Darkness | 5esrd.com "Shadow Gnawer (Barbarian)" (third party) |
| Bard | College of Choreography | 14 | - | unknown (maybe dnd55e's own) |
| Cleric | Apocalypse Domain | 17 | 3 Visions of Annihilation, Doom Song; 6 All Will Be Dust | D&D Beyond promoted it (2025-07) - source book not found |
| Cleric | Astral Domain | 17 | 3 Create Void, Planar Reach; 6 Spatial Exchange | unknown |
| Cleric | Dragon Domain | 17 | 3 Chromatic Affinity, Draconic Majesty; 6 Wyrm's Blessing | unknown |
| Cleric | Mind Domain | 17 | 3 Psychic Feedback, Psychic Force; 6 Gestalt Anchor | unknown |
| Cleric | Shadow Domain | 17 | 3 Cover of Night, Lengthen Shadow, Shadow Grasp; 6 Fade to Black | unknown |
| Druid | Circle of Dragons | 14 | 3 Draconic Lore, Dragon Shape; 6 Improved Dragon Shape; 10 Draconic Magic | unknown |
| Druid | Circle of the Unbroken | 14 | 3 Improved Shillelagh, Wild Recovery; 6 Extra Attack; 10 War Magic | The Griffon's Saddlebag, Book 1 (14: Nature Armor?) |
| Fighter | Viking | 15, 18 | 10 Call of the Northlands | unknown |
| Rogue | Arachnoid Stalker | 13, 17 | 9 Paralytic Venom | Valda's Spire of Secrets (Mage Hand Press) |
| Rogue | Blade of Radiance | 13, 17 | 3 Sanctified Champion...; 9 Chains of Judgement, Divine Retaliation, Erupting Blades | Steinhardt's Guide to the Eldritch Hunt |
| Rogue | Highway Rider | 13, 17 | 3 Hair Trigger, Trusty Mount, Ride Them Down; 9 Horse Lord | Grim Hollow |
| Sorcerer | Frost Sorcery | 14, 18 | 3 Create Ice, Frozen Body; 6 Cold-Hearted | unknown |
| Sorcerer | Heroic Sorcery | 14, 18 | - | unknown |

If a subclass turns out to be dnd55e's own design (no published source), its 13-20 features would be new homebrew -
a decision for the project owner (VISION.md principle 4), not something to invent here.

Also open (documented, not gaps in sourcing): the half-caster 13/17 spells BG3 doesn't have (see
`Scripts/gen_subclass_spells.py` MISSING), Beast Master / Hunter have no subclass spells (audit false positives).
