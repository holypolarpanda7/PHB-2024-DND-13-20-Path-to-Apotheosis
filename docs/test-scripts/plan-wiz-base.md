# Test plan: Wizard base, levels 1-2 (shared by every subclass run)

Build `wiz-base`: Wizard, levels 1-2. Generated 2026-09-30 17:11 CDT (layers: base, dnd55e, apotheosis).

**Each level:** say **"level up"** -> make exactly the choices below -> say **"leveled"**. I run the level check and this level's automated tests. Save after each level (never while a test is staged).

## Level 1

Character creation:
- Spells (cantrips, pick 3): Acid Splash (filler), Blade Ward (filler), Blood Bolt (filler)
- Spells (level 1 spells, pick 6): **Magic Missile** (tested at L1), **Mage Armour** (tested at L1), Absorb Elements (filler), Body Warping of Gorgoroth (filler), Burning Hands (filler), Catapult (filler)
- Skills: any (doesn't affect tests)
- AbilityBonus: any (doesn't affect tests)

Automated tests (`bg3_test_run_level(build="wiz-base", level=1)`), nothing for you to do:
- `wiz-01-magic-missile` Magic Missile: 3 darts hit a hostile wolf and spend a 1st-level slot
- `wiz-01-mage-armor` Mage Armour on yourself (out of combat) applies MAGE_ARMOR and spends a 1st-level slot

Your spot check `wiz-01-slot-spotcheck`: Spot check: a hotbar Magic Missile really spends a 1st-level slot
1. Say **"stage wiz-01-slot-spotcheck"**; I set it up (you act first).
2. Cast **Magic Missile** from the class spell bar at the Wolf (A, 40 HP). Click the wolf three times so all three darts go to it.
3. Say **"verify"**.

## Level 2

Level-up screen:
- Spells (level 1 spells, pick 2): Charm Person (filler), Chromatic Orb (filler)
- SkillsExpertise: any (doesn't affect tests)
- Spells (level 1-3 spells, Wizard_2_RitualAdept, pick 1): Disguise Self (filler)

**Save now as "Tavizard L2 base"**: other builds start from it.
