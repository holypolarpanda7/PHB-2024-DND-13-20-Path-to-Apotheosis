# Test plan: Wizard - Abjurer, levels 3-20

Build `wiz-abjurer`: Wizard / AbjurationSchool, levels 3-20. Generated 2026-09-30 17:11 CDT (layers: base, dnd55e, apotheosis).

**Start:** load your save from build `wiz-base` ("Tavizard L2 base").

**Each level:** say **"level up"** -> make exactly the choices below -> say **"leveled"**. I run the level check and this level's automated tests. Save after each level (never while a test is staged).

## Level 3

Level-up screen:
- **Subclass: Abjurer** (`AbjurationSchool`)
- Spells (level 2 spells, pick 2): Aganazzar's Scorcher (filler), Arcane Lock (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 2): Arcane Vigor (filler), Elminster's Elusion (filler)

## Level 4

Level-up screen:
- Spells (cantrips, pick 1): Bone Chill (filler)
- Spells (level 2 spells, pick 2): Blindness (filler), Blur (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Enhance Leap (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 5

Level-up screen:
- Spells (level 3 spells, pick 2): Animate Dead (filler), Ashardalon's Stride (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Counterspell (filler)

## Level 6

Level-up screen:
- Spells (level 3 spells, pick 2): Astral Flood (filler), Bestow Curse (filler)

## Level 7

Level-up screen:
- Spells (level 4 spells, pick 2): Arcane Eye (filler), Banishment (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Feather Fall (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Glyph of Warding (filler)

## Level 8

Level-up screen:
- Spells (level 4 spells, pick 2): Blight (filler), Charm Monster (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 9

Level-up screen:
- Spells (level 5 spells, pick 2): Circle of Power (filler), Cloudkill (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Otiluke's Resilient Sphere (filler)

## Level 10

Level-up screen:
- Spells (cantrips, pick 1): Booming Blade (filler)
- Spells (level 5 spells, pick 2): Cone of Cold (filler), Conjure Elemental (filler)

## Level 11

Level-up screen:
- Spells (level 6 spells, pick 2): Arcane Gate (filler), Chain Lightning (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Globe of Invulnerability (filler)

## Level 12

Level-up screen:
- Spells (level 6 spells, pick 2): Circle of Death (filler), Create Undead (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 13

Level-up screen:
- Spells (level 7 spells, WizardSLevel7, pick 1): Delayed Blast Fireball (filler)
- Spells (level 6 spells, WizardSpellList, pick 1): Disintegrate (filler)
- Spells (level 7 spells, Wizard_3_Savant, pick 1): Symbol (filler)

## Level 14

Level-up screen:
- no choices

## Level 15

Level-up screen:
- Spells (level 6 spells, WizardSpellList, pick 1): Eyebite (filler)
- Spells (level 8 spells, WizardSLevel8, pick 1): **Antimagic Field** (tested at L15)
- Spells (level 8 spells, Wizard_3_Savant, pick 1): **Mind Blank** (tested at L15)

Automated tests (`bg3_test_run_level(build="wiz-abjurer", level=15)`), nothing for you to do:
- `spell-AbjurationSchool-Shout_Apo_AntimagicField` Antimagic Field applies APO_ANTIMAGIC_AURA to you
- `spell-AbjurationSchool-Target_Apo_MindBlank` Mind Blank applies APO_MIND_BLANK to you

## Level 16

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 17

Level-up screen:
- Spells (level 9 spells, WizardSLevel9, pick 1): Astral Projection (filler)
- Spells (level 6 spells, WizardSpellList, pick 1): Flesh to Stone (filler)
- Spells (level 9 spells, Wizard_3_Savant, pick 1): Imprisonment (filler)

## Level 18

Level-up screen:
- no choices

## Level 19

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 20

Level-up screen:
- no choices
