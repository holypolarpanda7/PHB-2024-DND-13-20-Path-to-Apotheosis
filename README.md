# PHB 2024 — Path to Apotheosis (Levels 13–20)

Extends the [DnD 5.5e (PHB 2024) mod](https://github.com/Yoonmoonsik/dnd55e) past
Baldur's Gate 3's level-12 cap: full class progressions, subclass features, spell
slots (7th–9th level), and epic boons for levels 13–20.

**Requires:** the DnD 2024 (dnd55e) mod and
[Script Extender](https://github.com/Norbyte/bg3se) (for a handful of scripted
features and the test tooling).

## Coverage

- **16 base classes** complete for levels 13–20 (including dnd55e's Artificer,
  Gunslinger, Illrigger, Monster Hunter, Spellslinger).
- **80 subclasses** with 13–20 feature nodes.
- 9th-level spell slots work natively (base `SpellSlot` resource has `MaxLevel=9`).
- Known gaps and stub features are tracked in
  [docs/COVERAGE.md](docs/COVERAGE.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `Public/<guid>/Progressions/Progressions.lsx` | All 13–20 class/subclass progression rows |
| `Public/<guid>/Stats/Generated/Data/` | Passives, spells, statuses, interrupts |
| `Mods/<guid>/Localization/English/` | Loca XML (never leave XML comments in these — Toolkit crash) |
| `Mods/<guid>/ScriptExtender/Lua/BootstrapServer.lua` | Scripted features + smoke-test framework |
| `Mods/<guid>/ScriptExtender/Lua/ClassExpectations.lua` | AUTO-GENERATED per-level grant expectations (all classes) |
| `Mods/<guid>/ScriptExtender/Lua/WizardManifestExpectations.lua` | AUTO-GENERATED wizard manifest expectations |
| `Scripts/` | Build, audit, and test automation |

## Testing workflow

Day-to-day testing uses a normal (Steam) game launch with the deployed `.pak`;
the Larian Toolkit is only for packaging/release checks.

```bash
# 1. pack + deploy + enable in modsettings (run while BG3 is closed)
./Scripts/pack_deploy_test.sh

# 2. launch BG3 from Steam, load a save whose host is the class under test

# 3. validate a subclass end-to-end (sweeps host 13->20, checks each level)
./Scripts/test_subclass.sh EvocationSchool

# or a single level:
./Scripts/test_subclass.sh ZealotPath --check 14
```

`test_subclass.sh` sends the console command to the live SE console window,
watches the Script Extender log for the PASS/FAIL outcome, prints the per-level
detail, and (by default) kills BG3 on failure so the patch loop can continue.

### SE console commands (server context)

| Command | What it does |
| --- | --- |
| `!apolist` | List every known class/subclass name |
| `!aposub <Name> [level]` | Check expected grants at one level (any class/subclass) |
| `!aposubsweep <Name> [start] [end]` | Level 13→20 sweep with per-level checks |
| `!aposmokehelp` | Full command help |
| `!apowizmanifest <School>` | Wizard manifest-driven strict validation |
| `!apowizsweep [start] [end]` | Wizard level sweep |

Expectations are generated from `Progressions.lsx` — regenerate after any
progression change:

```bash
python Scripts/build_all_class_expectations.py     # all classes -> ClassExpectations.lua
python Scripts/build_wizard_13_20_expectations.py  # wizard JSON matrix
python Scripts/generate_wizard_expectations_lua.py # wizard JSON -> Lua
```

## Audit scripts

```bash
python Scripts/completeness_audit.py  # per-class/subclass 13-20 node + passive coverage
python Scripts/compat_audit.py        # TableUUID cross-check against dnd55e
```

More detail on the manifest system and runtime policy:
[Scripts/test_build_manifests/README.md](Scripts/test_build_manifests/README.md)
and the
[agent runbook](Scripts/test_build_manifests/AGENT_LEVELUP_TESTING_RUNBOOK.md).
