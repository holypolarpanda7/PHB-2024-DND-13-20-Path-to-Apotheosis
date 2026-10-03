# dnd55e findings (candidates for upstream reports) - 2026-10-03

Found by `bg3_lint_progressions` on the dnd55e layer (dnd55e 2026-10-02 14:08 CDT). Not verified in game yet; each
needs a character of that subclass levelled through the listed level before reporting (dnd55e-fork workflow).

- **Stacked subclass choice nodes.** For these tables a base-game node and a dnd55e node with *different* UUIDs sit
  at the same level and both carry Selectors, so both load: the choices (e.g. Nature Domain's skill pick, the domain
  spell lists) may be offered/granted twice. NatureDomain L3/5/7/9, TempestDomain L3/5/7/9, EnchantmentSchool L3/5
  (UUIDs swapped between base and dnd55e), BattleMaster L3 (two dnd55e nodes).
- **Lay on Hands** is a charge pool (3 at 1, +1 at 4 and 10) rather than the 2024 5 x Paladin level Hit Points; not
  extended past 12 here because it's dnd55e's own model.
- **Compressed level maps** (Apotheosis principle 2 would move these back; left as-is pending a decision): Sneak
  Attack 7d6 at 11 (2024: 13), cantrip and True Strike / Booming Blade tier 3 at 10 (2024: 11), Breath Weapon 3d10
  at 10 (2024: 11), Land's Aid 3d6 at 5 / 4d6 at 10 (2024: 10 / 14).

Found while generating 7th-9th level upcasts (`Scripts/gen_upcasts.py`, dnd55e 2026-10-03 04:07 +0900), checked with
`bg3_lint_stats` / the MCP resolver, not yet in game:

- **Danse Macabre can't resolve.** dnd55e `Spell_Target.txt` redefines `Target_AnimateDead_Ghoul_6` as an empty entry
  (only `SpellType`, no `using`), which replaces the base spell. Base `Target_CursedTome_WakeTheDead` uses it, and
  dnd55e `Target_DanseMacabre` (and `_6`) use Wake the Dead, so the whole chain has no SpellAnimation: a normal cast
  never resolves. Apotheosis' generated `Target_DanseMacabre_7`..`_9` inherit the same gap (lint flags them).
- **Awaken at 6th level spends a 5th level slot.** dnd55e `Target_Awaken_6` sets no UseCosts, so it inherits the
  root's `SpellSlotsGroup:1:1:5`. (Base-game quirks of the same kind: `Shout_SeeInvisibility_6` costs a 2nd level
  slot, `Projectile_Smite_Banishing_6` a 5th.) Apotheosis' 7th-9th variants set the right slot level explicitly.
