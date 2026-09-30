# Test plan: Wizard - Enchanter, levels 3-20

Build `wiz-enchanter`: Wizard / EnchantmentSchool, levels 3-20. Generated 2026-09-30 17:00 CDT (layers: base, dnd55e, apotheosis).

**Start:** load your save from build `wiz-base` ("Tavizard L2 base").

**Each level:** say **"level up"** -> make exactly the choices below -> say **"leveled"**. I run the level check and this level's automated tests. Save after each level (never while a test is staged).

## Level 3

Level-up screen:
- **Subclass: Enchanter** (`EnchantmentSchool`)
- Spells (level 2 spells, pick 2): Aganazzar's Scorcher (filler), Arcane Lock (filler)
- Choose 1 (Enchanter_3_EnchantingConversationalist): **Deception** (options: 4)
- Spells (level 6 spells, Wizard_3_Savant, pick 2): Charm Monster (filler), Charm Person (filler)

## Level 4

Level-up screen:
- Spells (cantrips, pick 1): Acid Splash (filler)
- Spells (level 2 spells, pick 2): Arcane Vigor (filler), Blindness (filler)
- Spells (level 1 spells, Wizard_2_RitualAdept, pick 1): Disguise Self (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 5

Level-up screen:
- Spells (level 3 spells, pick 2): Animate Dead (filler), Ashardalon's Stride (filler)
- Spells (level 6 spells, Wizard_3_Savant, pick 1): Confusion (filler)

## Level 6

Level-up screen:
- Spells (level 3 spells, pick 2): Astral Flood (filler), Bestow Curse (filler)

## Level 7

Level-up screen:
- Spells (level 4 spells, pick 2): Arcane Eye (filler), Banishment (filler)
- Spells (level 1 spells, Wizard_2_RitualAdept, pick 1): Enhance Leap (filler)
- Spells (level 6 spells, Wizard_3_Savant, pick 1): Crown of Madness (filler)

## Level 8

Level-up screen:
- Spells (level 4 spells, pick 2): Blight (filler), Conjure Minor Elemental (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 9

Level-up screen:
- Spells (level 5 spells, pick 2): Circle of Power (filler), Cloudkill (filler)
- Spells (level 6 spells, Wizard_3_Savant, pick 1): Dominate Person (filler)

## Level 10

Level-up screen:
- Spells (cantrips, pick 1): Blade Ward (filler)
- Spells (level 5 spells, pick 2): Cone of Cold (filler), Conjure Elemental (filler)

## Level 11

Level-up screen:
- Spells (level 6 spells, pick 2): Arcane Gate (filler), Chain Lightning (filler)
- Spells (level 6 spells, Wizard_3_Savant, pick 1): Hold Monster (filler)

## Level 12

Level-up screen:
- note: 2 Wizard progression nodes at this level (apotheosis, dnd55e); the level-up screen may ask twice
- Spells (level 6 spells, pick 2): Circle of Death (filler), Create Undead (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**
- Spells (level 6 spells, pick 2): Disintegrate (filler), Eyebite (filler)
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 13

Level-up screen:
- Spells (level 7 spells, WizardSLevel7, pick 1): Delayed Blast Fireball (filler)
- Spells (level 6 spells, WizardSpellList, pick 1): Flesh to Stone (filler)
- Spells (level ? spells, EnchantmentSavant, pick 1): 

## Level 14

Level-up screen:
- no choices

Automated tests (`bg3_test_run_level(build="wiz-enchanter", level=14)`), nothing for you to do:
- `feature-Enchanter_14_AlterMemories` Enchanter_14_AlterMemories: cast Modify Memory aura with 2 hostile living targets in range; both must gain MM_HOLD or MM_SLOW (cap=2)

## Level 15

Level-up screen:
- Spells (level 6 spells, WizardSpellList, pick 1): Globe of Invulnerability (filler)
- Spells (level 8 spells, WizardSLevel8, pick 1): **Befuddlement** (tested at L15)
- Spells (level ? spells, EnchantmentSavant, pick 1): 

Automated tests (`bg3_test_run_level(build="wiz-enchanter", level=15)`), nothing for you to do:
- `spell-EnchantmentSchool-Target_Apo_Befuddlement` Befuddlement applies FEEBLEMIND to a hostile wolf

## Level 16

Level-up screen:
- Feat: **Ability Score Improvement, +2 Intelligence**

## Level 17

Level-up screen:
- Spells (level 6 spells, WizardSpellList, pick 2): Otiluke's Freezing Sphere (filler), Otto's Irresistible Dance (filler)
- Spells (level ? spells, EnchantmentSavant, pick 1): 

## Level 18

Level-up screen:
- no choices

## Level 19

Level-up screen:
- Choose 1 (EpicBoons): 
- Feat: **Ability Score Improvement, +2 Intelligence**
- Spells (level ? spells, EnchantmentSavant, pick 1): 

## Level 20

Level-up screen:
- no choices
