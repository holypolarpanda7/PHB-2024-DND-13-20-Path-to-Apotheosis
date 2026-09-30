# Test plan: Wizard - Evoker, levels 3-20

Build `wiz-evoker`: Wizard / EvocationSchool, levels 3-20. Generated 2026-09-30 17:11 CDT (layers: base, dnd55e, apotheosis).

**Start:** load your save from build `wiz-base` ("Tavizard L2 base").

**Each level:** say **"level up"** -> make exactly the choices below -> say **"leveled"**. I run the level check and this level's automated tests. Save after each level (never while a test is staged).

## Level 3

Level-up screen:
- **Subclass: Evoker** (`EvocationSchool`)
- Spells (level 2 spells, pick 2): Aganazzar's Scorcher (filler), Arcane Lock (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 2): Darkbolt (filler), Darkness (filler)

## Level 4

Level-up screen:
- Spells (cantrips, pick 1): Bone Chill (filler)
- Spells (level 2 spells, pick 2): Arcane Vigor (filler), Blindness (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Enhance Leap (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 5

Level-up screen:
- Spells (level 3 spells, pick 2): Animate Dead (filler), Ashardalon's Stride (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Astral Flood (filler)

## Level 6

Level-up screen:
- Spells (level 3 spells, pick 2): Bestow Curse (filler), Blink (filler)

## Level 7

Level-up screen:
- Spells (level 4 spells, pick 2): Arcane Eye (filler), Banishment (filler)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Feather Fall (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Cacophonic Shield (filler)

## Level 8

Level-up screen:
- Spells (level 4 spells, pick 2): Blight (filler), Charm Monster (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 9

Level-up screen:
- Spells (level 5 spells, pick 2): Circle of Power (filler), Cloudkill (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Cone of Cold (filler)

## Level 10

Level-up screen:
- Spells (cantrips, pick 1): Booming Blade (filler)
- Spells (level 5 spells, pick 2): Conjure Elemental (filler), Danse Macabre (filler)

## Level 11

Level-up screen:
- Spells (level 6 spells, pick 2): Arcane Gate (filler), Chain Lightning (filler)
- Spells (level 1-6 spells, Wizard_3_Savant, pick 1): Dawn (filler)

## Level 12

Level-up screen:
- Spells (level 6 spells, pick 2): Circle of Death (filler), Create Undead (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 13

Level-up screen:
- Spells (level 7 spells, WizardSLevel7, pick 1): **Delayed Blast Fireball** (tested at L13)
- Spells (level 6 spells, WizardSpellList, pick 1): Disintegrate (filler)
- Spells (level 7 spells, Wizard_3_Savant, pick 1): Forcecage (filler)

Automated tests (`bg3_test_run_level(build="wiz-evoker", level=13)`), nothing for you to do:
- `spell-EvocationSchool-Projectile_Apo_DelayedBlastFireball` Delayed Blast Fireball damages a hostile wolf

## Level 14

Level-up screen:
- no choices

## Level 15

Level-up screen:
- Spells (level 6 spells, WizardSpellList, pick 1): Eyebite (filler)
- Spells (level 8 spells, WizardSLevel8, pick 1): Antimagic Field (filler)
- Spells (level 8 spells, Wizard_3_Savant, pick 1): Sunburst (filler)

## Level 16

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 17

Level-up screen:
- Spells (level 9 spells, WizardSLevel9, pick 1): Astral Projection (filler)
- Spells (level 6 spells, WizardSpellList, pick 1): Flesh to Stone (filler)
- Spells (level 9 spells, Wizard_3_Savant, pick 1): Meteor Swarm (filler)

## Level 18

Level-up screen:
- no choices

## Level 19

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 20

Level-up screen:
- no choices
