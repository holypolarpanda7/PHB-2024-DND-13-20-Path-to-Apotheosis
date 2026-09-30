# In-game findings, 2026-09-30

Found by hot-loading this repo's stats into the running game (bg3-data-mcp `bg3_se_hot_load`) and comparing
every Apotheosis entry with what the engine actually loaded (`tests/ingame_check.py --only-layer apotheosis`):
652 entries, 10,298 fields, 52 mismatches. The engine **silently drops invalid values**, so these load as
something other than what the files say. None of the static audits can see this.

Setup: dnd55e 4.12.13.19 deployed, Script Extender v32.

## Bugs (fix next)
| Entry | Problem | Effect in-game |
| --- | --- | --- |
| `Shout_DivineForeknowledge`, `Shout_Apotheosis_TelekineticThrust`, `Target_Apotheosis_ChemicalMastery` | `Cooldown "OncePerLongRest"` isn't a valid BG3 cooldown | **No cooldown at all** |
| `Shout_Wish_GreaterDivineIntervention` | same invalid cooldown | Falls back to the inherited `OncePerCombat` |
| `Target_Apo_Befuddlement`, `Target_Apo_TrueResurrection` | Nearly every field is empty in-game | **Both spells load as empty shells**; investigate the entry definitions |
| `WildMagic_SurgeOfUndeath_Passive` | `StatsFunctorContext "OnDeath"` is invalid | **Never triggers** |
| `BRUTAL_STRIKE_STAGGERED` | `RemoveEvents "OnSavingThrowRolled"` is invalid | Never removed by a saving throw |
| `Projectile_Apotheosis_WarpingImplosion` | `DeathType "Explosion"` is invalid | No death effect |
| `MM_HOLD`, `MM_SLOW` | `TickType "None"` is invalid | Falls back to `EndTurn` |
| Several 7th-9th level spells | `HasMaterialComponent` isn't a BG3 spell flag; `SaveDC`, `TooltipHealList` aren't fields | Dropped (harmless, but misleading) |
| `Shout_KeeperOfSouls_Heal` | `CannotTargetSelf` isn't a flag | Dropped; use `TargetConditions` `not Self()` |

## Confirmed working in-game (today's fixes)
- **Aura Expansion** (Paladin 18): applying the 3 m `AURA_OF_PROTECTION` swaps it for the 9 m
  `APOTHEOSIS_AURA_OF_PROTECTION_30` (same stack group, so no double aura). Both 30 ft statuses load with
  radius 9.
- **Persistent Rage** (Barbarian 15), stats half: the `RAGE_STOP_REMOVE` marker is applied when Rage
  starts. Found and fixed in-game: `OnCreate` doesn't fire for a passive gained mid-session (level-up), so
  the passive also listens `OnStatusApplied`. The script half (refill on Initiative) needs a restart with
  a correct pak, because SE Lua only loads for mods present at startup.
- Upcasts: `Shout_HealingWord_Mass_7`, `Shout_DestructiveWave_{Radiant,Necrotic}_7-9` and
  `Zone_Sunbeam_7` exist with the correct parent spell and slot cost.

## Packaging bug (fixed in this commit)
`Scripts/pack_deploy_test.sh` used to pack **only `Mods/<mod>` as the package root**: no `Mods/<mod>/` prefix
and no `Public/` content at all. The pak deployed on 2026-07-14 therefore never delivered stats,
progressions or SE Lua to the game (the log had no `[Apotheosis]` heartbeat). The script now stages
`Mods/` + `Public/`, verifies the pak layout before deploying, refuses to deploy while BG3 is running,
backs up the previous pak and reads the correct `Script Extender Logs` folder.
