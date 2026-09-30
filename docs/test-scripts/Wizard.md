# Wizard test script

Generated 2026-09-30 16:48 CDT from `/mnt/d/BG3Modding/Mod_Projects/PHB-2024-DND-13-20-Path-to-Apotheosis/tests/bg3` (layers: base, dnd55e, apotheosis).
Say the words in **bold quotes** to me; I run the tools. Never save while a test is staged.

## Level 1

Say **"level check"** first: I confirm your level 1 features and spells (`bg3_level_check`).

### 1.1 Magic Missile: 3 darts hit a hostile wolf and spend a 1st-level slot

Case `wiz-01-magic-missile` - automated: I set up, cast and check it; costs checked against the loaded data.

1. Say **"run wiz-01-magic-missile"** (or **"run level 1"** for all of them). I set up:
   - a hostile Wolf (A, 40 HP) about 8 m away
   - combat starts; a temporary Initiative +50 makes you act first
2. Watch: I cast it for you, check the results and clean up.

What you should see:
- you act first in initiative
- the Wolf (A, 40 HP) loses 6-15 HP
- the Wolf (A, 40 HP) takes Force damage
- one SpellSlot (level 1) is spent

Notes: 3 darts x (1d4+1) Force = 6-15 damage; the wolf has 40 HP so it survives.

### 1.2 Mage Armour on yourself (out of combat) applies MAGE_ARMOR and spends a 1st-level slot

Case `wiz-01-mage-armor` - automated: I set up, cast and check it; costs checked against the loaded data.

1. Say **"run wiz-01-mage-armor"** (or **"run level 1"** for all of them). I set up:
   - nothing extra
2. Watch: I cast it for you, check the results and clean up.

What you should see:
- you gain Mage Armour
- one SpellSlot (level 1) is spent

### 1.3 Spot check: a hotbar Magic Missile really spends a 1st-level slot

Case `wiz-01-slot-spotcheck` - you cast it from the hotbar (verifies the engine charging costs).

1. Say **"stage wiz-01-slot-spotcheck"**. I set up:
   - a hostile Wolf (A, 40 HP) about 8 m away
   - combat starts; a temporary Initiative +50 makes you act first
2. On your turn, cast **Magic Missile** from your class spell bar at **the Wolf (A, 40 HP)**. Use the hotbar, not the console.
3. Click the wolf three times so all three darts go to it.
4. Wait for the spell to resolve. Don't end your turn.
5. Say **"verify"**. I check the results, then remove every spawn and test boost.

What you should see:
- you act first in initiative
- one SpellSlot (level 1) is spent

Notes: Only needed once per resource type: auto cases check costs against the data.
