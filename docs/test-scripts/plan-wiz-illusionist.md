# Test plan: Wizard - Illusionist, levels 3-20

Build `wiz-illusionist`: Wizard / IllusionSchool, levels 3-20. Generated 2026-09-30 17:11 CDT (layers: base, dnd55e, apotheosis).

**Start:** load your save from build `wiz-base` ("Tavizard L2 base").

**Each level:** say **"level up"** -> make exactly the choices below -> say **"leveled"**. I run the level check and this level's automated tests. Save after each level (never while a test is staged).

## Level 3

Level-up screen:
- **Subclass: Illusionist** (`IllusionSchool`)
- Spells (level 2 spells, pick 2): Aganazzar's Scorcher (filler), Arcane Lock (filler)
- Spells (level 1-5 spells, Wizard_3_Savant, pick 2): Blur (filler), Cloak of Shadow (filler)

## Level 4

Level-up screen:
- Spells (cantrips, pick 1): Bone Chill (filler)
- Spells (level 2 spells, pick 2): Arcane Vigor (filler), Blindness (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Enhance Leap (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 5

Level-up screen:
- Spells (level 3 spells, pick 2): Animate Dead (filler), Ashardalon's Stride (filler)
- Spells (level 1-5 spells, Wizard_3_Savant, pick 1): Colour Spray (filler)

## Level 6

Level-up screen:
- Spells (level 3 spells, pick 2): Astral Flood (filler), Bestow Curse (filler)

## Level 7

Level-up screen:
- Spells (level 4 spells, pick 2): Arcane Eye (filler), Banishment (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Feather Fall (filler)
- Spells (level 2-5 spells, Wizard_3_Savant, pick 1): Fear (filler)

## Level 8

Level-up screen:
- Spells (level 4 spells, pick 2): Blight (filler), Charm Monster (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 9

Level-up screen:
- Spells (level 5 spells, pick 2): Circle of Power (filler), Cloudkill (filler)
- Spells (level 2-5 spells, Wizard_3_Savant, pick 1): Dream (filler)

## Level 10

Level-up screen:
- Spells (cantrips, pick 1): Booming Blade (filler)
- Spells (level 5 spells, pick 2): Cone of Cold (filler), Conjure Elemental (filler)

## Level 11

Level-up screen:
- Spells (level 6 spells, pick 2): Arcane Gate (filler), Chain Lightning (filler)
- Spells (level 2-5 spells, Wizard_3_Savant, pick 1): Fire Dance (filler)

## Level 12

Level-up screen:
- Spells (level 6 spells, pick 2): Circle of Death (filler), Create Undead (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 13

Level-up screen:
- Spells (level 7 spells, WizardSLevel7, pick 1): Delayed Blast Fireball (filler)
- Spells (level 6 spells, WizardSpellList, pick 1): Disintegrate (filler)
- Spells (level 7 spells, Wizard_3_Savant, pick 1): Mirage Arcane (filler)

## Level 14

Level-up screen:
- no choices

## Level 15

Level-up screen:
- Spells (level 6 spells, WizardSpellList, pick 1): Eyebite (filler)
- Spells (level 8 spells, WizardSLevel8, pick 1): Antimagic Field (filler)

## Level 16

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 17

Level-up screen:
- Spells (level 9 spells, WizardSLevel9, pick 1): **Weird** (tested at L17)
- Spells (level 6 spells, WizardSpellList, pick 1): Flesh to Stone (filler)
- Spells (level ? spells, Wizard_3_Savant, pick 1): 

Automated tests (`bg3_test_run_level(build="wiz-illusionist", level=17)`), nothing for you to do:
- `spell-IllusionSchool-Target_Apo_Weird` Weird applies FRIGHTENED to a hostile wolf

## Level 18

Level-up screen:
- no choices

## Level 19

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 20

Level-up screen:
- no choices
