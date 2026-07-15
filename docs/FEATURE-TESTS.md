# Functional Feature Tests — Scenario & Target Doctrine

Each test targets what its mechanic actually requires. Getting this wrong
produces false failures (e.g. Frozen Haunt can never chill a friendly —
its functor gates on `Enemy(context.Target)`).

All template and faction GUIDs were extracted from base-game data
(summon spell stats, `Shared/Factions/Factions.lsx`) — never guessed.

## Target roles

| Role | Resolution |
| --- | --- |
| self / none | host character only |
| ally | party member ≠ host; fallback: spawned wolf with **Good NPC** faction |
| enemy ×N | spawned template(s) with **Evil NPC** faction near the host |

Templates (override in `ApotheosisFeatureTests.Config.Templates`):
`wolf`, `boar`, `bear` (living beasts), `skeleton`, `zombie` (undead —
for future tests that must verify paralysis-resistance branches).

Factions: hostile = Evil NPC `64321d50-…`, friendly = Good NPC `80182081-…`,
neutral `a66b2d45-…`.

## Automated scenarios

| Passive | Scenario | Target | Why this target |
| --- | --- | --- | --- |
| `WinterWalker_15_FrozenHaunt` | host casts Ray of Frost → target gains CHILLED | 1× hostile wolf | functor condition `Enemy(context.Target)` — friendlies can never chill |
| `NobleGenies_15_ElementalRebuke` | attacker Fire Bolts host → attacker gains ELEMENTAL_REBUKE_HIT | 1× hostile wolf | real scenario is an enemy striking the sorcerer; listener itself is faction-agnostic, so passing an ally GUID tests without combat |
| `Enchanter_14_AlterMemories` | host casts Modify Memory aura with two enemies in 6m → BOTH gain MM_HOLD/MM_SLOW | 2× hostile **living** wolves | aura marks *enemies* only; MM_HOLD is paralyze-type, undead could resist and corrupt the cap=2 assertion |
| `Diviner_14_GreaterPortent` | exposed grant path → PORTENT_n status | self | Lua feature, no combat interaction |
| `Archfey_14_BewitchingMagic` | apply BEWITCHING_MAGIC → scripted boost hook sticks | self | status hook on the archfey warlock |
| `DeadThree_UnholyInfiltration` | static boosts | self | stats-engine boosts, presence is the observable |

## Manual scenarios (staged with `!apospawn`)

| Passive | Staging | Verify |
| --- | --- | --- |
| `Berserker_10_Retaliation` | `!apospawn wolf hostile`, let it melee-hit the barbarian | Retaliation reaction prompt fires (dnd55e interrupt) |
| `Celestial_14_SearingVengeance` | `!apospawn bear hostile`, let it down the warlock | scripted half-HP revive path |
| `Druid_BeastSpells` | none (self) | Wild Shape grants support spells + temp slots; revert removes them |

## Notes

- Hostile spawns will start combat — that is intentional (the scenarios are
  combat features). Run in a quiet area; spawned creatures are deleted on
  test completion (`Osi.RequestDelete`).
- In combat, forced casts may queue on turn order; status polls run with
  generous timeouts (8s direct, 15s aura ticks).
- `!apofeature <Passive> <TargetGuid>` overrides target resolution with any
  live GUID when a scenario needs a specific creature already in the scene.
