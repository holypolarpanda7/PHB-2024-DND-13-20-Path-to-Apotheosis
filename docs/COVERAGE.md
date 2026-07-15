# Coverage & Gap Audit

Last full audit: 2026-07-14 (`Scripts/completeness_audit.py` + `Scripts/compat_audit.py`
+ TableUUID diff against dnd55e).

## Complete

- All 16 base classes have progression rows for every level 13–20.
- 80 subclasses have 13–20 feature nodes; TableUUID cross-check against dnd55e
  reports **0 missing / 0 unresolved** remaps.
- 157 of 175 passives are REAL (mechanical boosts/functors); the rest are
  classified below.

## Stub passives that are intentional (do not "fix")

- `Barbarian_BrutalStrike_Improved`, `Barbarian_BrutalStrike_17` — markers read
  by `HasPassive()` conditions in `Spell_Target.txt`.
- `Warlock_MysticArcanum_7/8/9` — display markers; the arcanum spells are
  granted via `SelectSpells` in Progressions.lsx.
- `Druid_BeastSpells`, `Diviner_14_GreaterPortent`,
  `NobleGenies_15_ElementalRebuke` — implemented in Lua
  (`BootstrapServer.lua`), the passive is the visible anchor.

## Real gaps — features that do nothing yet

None as of 2026-07-14. The four previously flagged:

| Passive | Resolution |
| --- | --- |
| `Berserker_10_Retaliation` | false positive — implemented in dnd55e (`UnlockInterrupt(Interrupt_Berserker_10_Retaliation)`) |
| `ControlledChaos` | false positive — implemented in base game (`UnlockInterrupt(Interrupt_ControlledChaos)`) |
| `DeadThree_UnholyInfiltration` | implemented 2026-07-14: Advantage on Stealth/Deception + 18m darkvision |
| `WinterWalker_15_FrozenHaunt` | implemented 2026-07-14: Cold resistance + CHILLED (2 turns) on dealing cold damage |

`completeness_audit.py` now reads base-game and dnd55e Passive.txt too, labeling
upstream-implemented passives `REAL-UPSTREAM` instead of `STUB`.

## Missing subclass extensions (exist in dnd55e, no 13–20 rows here)

24 subclasses (by dnd55e progression TableUUID):

- **Cleric domains:** Apocalypse, Astral, Mind, Nature, Shadow, Tempest
- **Druid circles:** Dragons, Dreams, Spores, Unbroken
- **Sorcerer:** Frost Sorcery, Shadow Magic, Storm Sorcery
- **Warlock:** Hexblade, Undead Patron
- **Paladin:** Blade of Radiance, Crown
- **Fighter:** Cavalier
- **Monk:** Kensei
- **Bard:** Spirits College
- **Barbarian:** Fractured, Hollow Warden
- **Rogue/Gunslinger-family:** Highway Rider, Shadow Gnawer

These are the largest outstanding content work. Each needs: 13–20 progression
rows (features typically at 14/15/17/18/20 depending on class), passives with
real boosts, localization handles, and expectations regeneration.

## Regenerating this audit

```bash
python Scripts/completeness_audit.py
python Scripts/compat_audit.py
python Scripts/build_all_class_expectations.py
```
