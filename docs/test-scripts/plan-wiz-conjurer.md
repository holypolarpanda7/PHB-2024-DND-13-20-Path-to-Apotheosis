# Test plan: Wizard - Conjurer, levels 3-20

Build `wiz-conjurer`: Wizard / ConjurationSchool, levels 3-20. Generated 2026-09-30 17:11 CDT (layers: base, dnd55e, apotheosis).

**Start:** load your save from build `wiz-base` ("Tavizard L2 base").

**Each level:** say **"level up"** -> make exactly the choices below -> say **"leveled"**. I run the level check and this level's automated tests. Save after each level (never while a test is staged).

## Level 3

Level-up screen:
- **Subclass: Conjurer** (`ConjurationSchool`)
- Spells (level 2 spells, pick 2): Aganazzar's Scorcher (filler), Arcane Lock (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 2): Cloud of Daggers (filler), Find Familiar (filler)

## Level 4

Level-up screen:
- Spells (cantrips, pick 1): Bone Chill (filler)
- Spells (level 2 spells, pick 2): Arcane Vigor (filler), Blindness (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Enhance Leap (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 5

Level-up screen:
- Spells (level 3 spells, pick 2): Animate Dead (filler), Ashardalon's Stride (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Flaming Sphere (filler)

## Level 6

Level-up screen:
- Spells (level 3 spells, pick 2): Astral Flood (filler), Bestow Curse (filler)

## Level 7

Level-up screen:
- Spells (level 4 spells, pick 2): Arcane Eye (filler), Banishment (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Feather Fall (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Conjure Minor Elemental (filler)

## Level 8

Level-up screen:
- Spells (level 4 spells, pick 2): Blight (filler), Charm Monster (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 9

Level-up screen:
- Spells (level 5 spells, pick 2): Circle of Power (filler), Cloudkill (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Conjure Elemental (filler)

## Level 10

Level-up screen:
- Spells (cantrips, pick 1): Booming Blade (filler)
- Spells (level 5 spells, pick 2): Cone of Cold (filler), Danse Macabre (filler)

## Level 11

Level-up screen:
- Spells (level 6 spells, pick 2): Arcane Gate (filler), Chain Lightning (filler)
- Spells (level 1-5 spells, Wizard_3_Savant, pick 1): Dimension Door (filler)

## Level 12

Level-up screen:
- Spells (level 6 spells, pick 2): Circle of Death (filler), Create Undead (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 13

Level-up screen:
- Spells (level 7 spells, WizardSLevel7, pick 1): **Simulacrum** (tested at L13)
- Spells (level 6 spells, WizardSpellList, pick 1): Disintegrate (filler)
- Spells (level 7 spells, Wizard_3_Savant, pick 1): Mordenkainen's Magnificent Mansion (filler)

Automated tests (`bg3_test_run_level(build="wiz-conjurer", level=13)`), nothing for you to do:
- `spell-ConjurationSchool-Target_Apo_Simulacrum` Simulacrum applies APO_SIMULACRUM to you

## Level 14

Level-up screen:
- no choices

## Level 15

Level-up screen:
- Spells (level 6 spells, WizardSpellList, pick 1): Eyebite (filler)
- Spells (level 8 spells, WizardSLevel8, pick 1): **Maze** (tested at L15)
- Spells (level 8 spells, Wizard_3_Savant, pick 1): Demiplane (filler)

Automated tests (`bg3_test_run_level(build="wiz-conjurer", level=15)`), nothing for you to do:
- `spell-ConjurationSchool-Target_Apo_Maze` Maze applies BANISHED to a hostile wolf

## Level 16

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 17

Level-up screen:
- Spells (level 9 spells, WizardSLevel9, pick 1): Astral Projection (filler)
- Spells (level 6 spells, WizardSpellList, pick 1): Flesh to Stone (filler)
- Spells (level 9 spells, Wizard_3_Savant, pick 1): Gate (filler)

## Level 18

Level-up screen:
- no choices

## Level 19

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 20

Level-up screen:
- no choices
