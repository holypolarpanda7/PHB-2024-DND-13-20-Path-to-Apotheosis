# Level 7–9 Spell Testing Script

A read-and-execute runbook for verifying all 40 new 7th–9th level spells
(`Spell_Epic79.txt`). Work top to bottom. Each spell is force-cast by the
Script Extender and its real effect is checked (a status landing, HP
dropping, or a lethal kill), so most of the work is automated — you build
one character per caster class, level it, and run a handful of console
commands.

Two kinds of coverage:

1. **Functional** (automated) — `!apospells <Subclass>` force-casts each
   assigned spell and logs `SpellTest <name>: PASS|FAILED`. Force-cast
   ignores class/slot ownership, so you do **not** need the exact subclass
   for this part — any character of the right *tier* can run any command.
2. **Learnability** (manual spot-check) — while leveling the matching
   subclass, confirm the listed spells actually appear in the prepare/known
   spell UI. This is the only check that proves the `SpellLists.lsx` wiring,
   which automation can't easily reach.

---

## 0. One-time setup

1. **Deploy the current build** (from WSL, uses Git Bash for `/c/` paths):
   ```
   "/mnt/c/Program Files/Git/bin/bash.exe" -lc "cd /d/BG3Modding/Mod_Projects/PHB-2024-DND-13-20-Path-to-Apotheosis && ./Scripts/pack_deploy_test.sh"
   ```
   This packs the mod, deploys the `.pak` to the BG3 `Mods\` folder, and
   ensures the Apotheosis UUID is enabled in `modsettings.lsx`.

2. **Launch BG3 from Steam** (not Vortex — Steam avoids the console
   input lockups). A separate Script Extender console window opens with the
   game.

3. **Enter the server REPL**: click the console window, type `server`, press
   Enter. Console commands below are typed there. (Commands are prefixed
   `!` — the SE console recognizes them without the `server` context too,
   but the REPL is where you'll read output.)

4. **Sanity check**: type `!apospelllist` and press Enter. You should see all
   40 spell tests grouped by subclass. If the command is unknown, the mod
   isn't loaded — re-check step 1 and that the profile has it enabled.

**Where results go:** the live console prints every `SpellTest …: PASS/FAILED`
line as it runs. Persistent copies are in
`C:\Users\holyp\AppData\Local\Larian Studios\Baldur's Gate 3\Extender Logs\`
(newest timestamped file). Grep it for `[Apotheosis]` to isolate our output.

**Leveling a test character quickly:** these spells unlock with the 7th/8th/9th
spell slots at class levels **13 / 15 / 17**. Use an existing high-level
save per class, or in the console pulse XP:
```
Osi.AddExperience(GetHostCharacter(), 100000)
```
then take the level-up in the normal UI (this is also where you do the
learnability spot-check). Reach at least the **max level** listed for each
class below.

---

## 1. How to run each class session

For each class: build/load a character of that class, reach the target
level, then run the commands. A `!apospells <Subclass>` run ends with a
summary line:

```
SubclassSpells <Subclass>: ALL CHECKS PASSED      <- good
SubclassSpells <Subclass>: FAILED                 <- at least one spell failed; scroll up for the SpellTest FAILED line
```

Individual spells log `SpellTest <name>: PASS` or `SpellTest <name>: FAILED <reason>`.

> **Save-based spells can flake.** Enemy-debuff spells (Plane Shift, Antipathy,
> Maze, Imprisonment, etc.) roll a saving throw against the spawned wolf. A
> wolf usually fails, but if you see a lone FAILED with "a save may have
> succeeded", just re-run that one with `!apospell <SpellStatId>`.

> **Spent your slot?** Force-cast should bypass slot cost. If a same-tier
> spell silently no-ops (no PASS, no FAILED), Long Rest to refresh and
> re-run the single spell.

---

## 2. WIZARD — reach level 17

Wizard is a prepared caster: every wizard spell on the list is castable once
learned, so functional coverage is easy. Build **any** wizard, reach L17,
and run all nine commands. If you specifically rolled a given school, do its
learnability check too.

Run:
```
!apospells EvocationSchool
!apospells NecromancySchool
!apospells ConjurationSchool
!apospells AbjurationSchool
!apospells EnchantmentSchool
!apospells DivinationSchool
!apospells IllusionSchool
!apospells TransmutationSchool
!apospells BladesingingSchool
```

| Subclass | Spell(s) | Unlocks at | Effect verified |
| --- | --- | --- | --- |
| EvocationSchool | Delayed Blast Fireball | L13 | wolf takes fire damage / dies |
| NecromancySchool | Finger of Death, Clone | L13 / L15 | APO_FINGER_OF_DEATH on wolf; APO_CLONE on self |
| ConjurationSchool | Simulacrum, Maze | L13 / L15 | APO_SIMULACRUM on self; BANISHED on wolf |
| AbjurationSchool | Antimagic Field, Mind Blank | L15 | APO_ANTIMAGIC_AURA / APO_MIND_BLANK on self |
| EnchantmentSchool | Befuddlement | L15 | FEEBLEMIND on wolf |
| DivinationSchool | Telepathy | L15 | APO_TELEPATHIC_BOND on ally |
| IllusionSchool | Weird | L17 | FRIGHTENED on wolf (+ psychic dmg) |
| TransmutationSchool | Sequester | L13 | RESILIENT_SPHERE on ally |
| BladesingingSchool | Etherealness | L13 | APO_ETHEREAL on self |

**Learnability spot-check:** at a level-up on a wizard, open Prepare Spells
and confirm the spell(s) for your school appear in the 7th/8th/9th tier.

---

## 3. CLERIC — reach level 17

Prepared caster. Build any cleric, reach L17, run:
```
!apospells LightDomain
!apospells LifeDomain
!apospells KnowledgeDomain
!apospells WarDomain
!apospells GraveDomain
```

| Subclass | Spell | Unlocks at | Effect verified |
| --- | --- | --- | --- |
| LightDomain | Divine Word | L13 | wolf STUNNED/BLINDED or killed |
| LifeDomain | Conjure Celestial | L13 | APO_CELESTIAL_AURA on self |
| KnowledgeDomain | Symbol | L13 | STUNNED on wolf (+ psychic dmg) |
| WarDomain | Holy Aura | L15 | APO_HOLY_AURA on self |
| GraveDomain | True Resurrection | L17 | **MANUAL** — see §7 |

---

## 4. DRUID — reach level 17

Prepared caster. Build any druid, reach L17, run:
```
!apospells CircleOfTheMoon
!apospells CircleOfTheLand
!apospells CircleOfTheSea
!apospells CircleOfStars
```

| Subclass | Spell(s) | Unlocks at | Effect verified |
| --- | --- | --- | --- |
| CircleOfTheMoon | Animal Shapes, Shapechange | L15 / L17 | APO_BESTIAL / APO_COLOSSUS on self |
| CircleOfTheLand | Antipathy, Earthquake | L15 | FRIGHTENED / PRONE on wolf |
| CircleOfTheSea | Control Weather, Tsunami, Storm of Vengeance | L15 / L15 / L17 | APO_STORM_AURA on self; Tsunami dmg; APO_VENGEANCE_AURA on self |
| CircleOfStars | Sunburst | L15 | BLINDED on wolf (+ radiant dmg) |

---

## 5. SORCERER — reach level 15

**Known caster** — the learnability check matters most here, because you must
actively *select* these spells at level-up. Build any sorcerer, reach L15,
run:
```
!apospells DraconicBloodline
!apospells WildMagicPath
!apospells AberrantSorcery
!apospells ClockworkSorcery
!apospells SpellfireSorcery
```

| Subclass | Spell | Unlocks at | Effect verified |
| --- | --- | --- | --- |
| DraconicBloodline | Fire Storm | L13 | wolf takes fire damage / dies |
| WildMagicPath | Prismatic Spray | L13 | wolf takes multi-type damage / dies |
| AberrantSorcery | Reverse Gravity | L13 | PRONE on wolf (+ bludgeoning) |
| ClockworkSorcery | Teleport | L13 | **MANUAL** — see §7 |
| SpellfireSorcery | Incendiary Cloud | L15 | wolf takes fire damage / dies |

**Learnability spot-check:** at the L13 / L15 sorcerer spell-selection step,
confirm each 7th/8th spell above is offered in the known-spell list.

---

## 6. WARLOCK — reach level 17

Build any warlock, reach L17, run:
```
!apospells Fiend
!apospells GreatOldOne
!apospells Archfey
!apospells Celestial
```

| Subclass | Spell(s) | Unlocks at | Effect verified |
| --- | --- | --- | --- |
| Fiend | Forcecage, Imprisonment | L13 / L17 | RESILIENT_SPHERE / PETRIFIED on wolf |
| GreatOldOne | Plane Shift, Dominate Monster | L13 / L15 | BANISHED / DOMINATE_PERSON on wolf |
| Archfey | Demiplane | L15 | RESILIENT_SPHERE on self |
| Celestial | Astral Projection | L17 | APO_ASTRAL_FORM on self |

> **Warlock caveat:** these spells carry a normal `SpellSlotsGroup:…:7/8/9`
> cost, but warlocks use Pact Magic / Mystic Arcanum, not full 7–9 slots. The
> automated force-cast still validates the spell mechanics. Separately verify
> in normal play whether a warlock can actually pay for / cast them through
> the Arcanum UI — if not, that's a spell-layer follow-up, not a test failure.

---

## 7. BARD — reach level 13

**Known caster.** Build any bard, reach L13, run:
```
!apospells SwordsCollege
!apospells GlamourCollege
!apospells LoreCollege
!apospells ValorCollege
```

| Subclass | Spell | Unlocks at | Effect verified |
| --- | --- | --- | --- |
| SwordsCollege | Mordenkainen's Sword | L13 | **MANUAL** — see §7 |
| GlamourCollege | Mirage Arcane | L13 | SLOW/BLINDED on wolf |
| LoreCollege | Magnificent Mansion | L13 | SANCTUARY on self |
| ValorCollege | Power Word Fortify | L13 | APO_FORTIFIED on self |

**Learnability spot-check:** at bard spell-selection / Magical Secrets,
confirm each spell above appears.

---

## 8. Manual spells (visual confirmation)

Five spells can't be auto-verified by a status poll. Stage each and watch:

| Spell | Class/Subclass | Steps | Look for |
| --- | --- | --- | --- |
| **Mordenkainen's Sword** | Bard / SwordsCollege | `!apospawn wolf hostile`, then cast Mordenkainen's Sword at it | a spiritual greatsword summon appears on the turn order and attacks |
| **Teleport** | Sorcerer / ClockworkSorcery | cast Teleport at a distant patch of ground (up to 30m) | the caster blinks to the target point |
| **Finger of Death (zombie rider)** | Wizard / NecromancySchool | `!apospawn` a **humanoid** hostile, cast Finger of Death to kill it | the corpse rises as a zombie fighting on your side |
| **Clone (revive rider)** | Wizard / NecromancySchool | cast Clone on self (APO_CLONE applies), then let an enemy down you | you are revived once at full HP (`APO_CLONE` consumed) |
| **True Resurrection** | Cleric / GraveDomain | `!apospawn wolf friendly`, kill it, then cast True Resurrection on the corpse | the ally returns to life at full HP with a short Bless |

`!apospawn <template> [faction]` templates: `wolf, boar, bear, skeleton, zombie`;
factions: `hostile, friendly, neutral`. Spawns are auto-deleted when an
automated test finishes; delete manual ones with
`Osi.RequestDelete("<guid>")` (the spawn command prints the guid).

---

## 9. Quick reference — every command

```
!apospelllist                     -- list all 40 spell tests by subclass
!apospells <Subclass>             -- run all spell tests for one subclass
!apospell  <Target_Apo_...>       -- re-run a single spell by its stat id
!apospawn  <template> [faction]   -- stage a manual-test target
```

Class → commands, in the order to run them:

- **Wizard (L17):** EvocationSchool, NecromancySchool, ConjurationSchool, AbjurationSchool, EnchantmentSchool, DivinationSchool, IllusionSchool, TransmutationSchool, BladesingingSchool
- **Cleric (L17):** LightDomain, LifeDomain, KnowledgeDomain, WarDomain, GraveDomain
- **Druid (L17):** CircleOfTheMoon, CircleOfTheLand, CircleOfTheSea, CircleOfStars
- **Sorcerer (L15):** DraconicBloodline, WildMagicPath, AberrantSorcery, ClockworkSorcery, SpellfireSorcery
- **Warlock (L17):** Fiend, GreatOldOne, Archfey, Celestial
- **Bard (L13):** SwordsCollege, GlamourCollege, LoreCollege, ValorCollege

**Done when:** every `!apospells` run prints `ALL CHECKS PASSED`, and the five
manual spells in §8 are visually confirmed.
