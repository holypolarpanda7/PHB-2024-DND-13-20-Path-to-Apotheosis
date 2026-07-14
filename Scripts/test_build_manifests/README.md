# Test Build Manifests

> **Note (2026-07-14):** subclass validation is no longer wizard-only. All 16
> classes / 80 subclasses now have generated expectations
> (`python Scripts/build_all_class_expectations.py` →
> `ClassExpectations.lua`), runnable in-game via `!aposub <Name> [level]` /
> `!aposubsweep <Name>`, or end-to-end via `./Scripts/test_subclass.sh <Name>`.
> The wizard manifest flow below remains the reference for choice-pipeline
> (PartyEditor) capture.

These JSON files capture real BG3 PartyEditor level-up decisions in a stable,
diffable form.

They are meant to solve the current testing gap:

- `SetLevel` and base `PROC_LevelUp` only change level state.
- They do not drive the player choice pipeline for subclass picks, feats,
  spell selections, or prepared-spell state.
- PartyEditor LSX presets *do* contain those authored choices.

## Current workflow

Extract a manifest from a PartyEditor file:

```bash
/d/BG3Modding/Mod_Projects/.venv/Scripts/python.exe \
  Scripts/extract_partyeditor_levelups.py \
  /d/BG3Modding/Mod_Projects/BaseGame/Gustav/Mods/GustavDev/Story/PartyEditor/Level12_Gale.lsx \
  --output Scripts/test_build_manifests/gale_level12_wizard.json
```

Generate canonical wizard subclass manifests in bulk:

```bash
python Scripts/generate_wizard_subclass_manifests.py
```

If a subclass is missing from PartyEditor presets, infer it from a donor
subclass (default donor: `EvocationSchool`):

```bash
python Scripts/generate_wizard_subclass_manifests.py --infer-missing
```

This writes:

- `Scripts/test_build_manifests/wizard_subclasses/wizard_abjurationschool_canonical.json`
- `Scripts/test_build_manifests/wizard_subclasses/wizard_divinationschool_canonical.json`
- `Scripts/test_build_manifests/wizard_subclasses/wizard_evocationschool_canonical.json`
- `Scripts/test_build_manifests/wizard_subclasses/wizard_illusionschool_canonical.json`
- `Scripts/test_build_manifests/wizard_subclasses/wizard_bladesingingschool_inferred.json` (when `--infer-missing` is used)
- `Scripts/test_build_manifests/wizard_subclasses/wizard_subclass_manifest_index.json`

Generate expected wizard 13-20 grants for each subclass from Apotheosis
`Progressions.lsx`:

```bash
python Scripts/build_wizard_13_20_expectations.py
```

This writes:

- `Scripts/test_build_manifests/wizard_13_20_expectations.json`

Current bulk-scan coverage:

- Found canonical presets for: `AbjurationSchool`, `DivinationSchool`, `EvocationSchool`, `IllusionSchool`
- Inference path available for missing corpus coverage: `BladesingingSchool`
- `wizard_13_20_expectations.json` currently reports complete progression
  coverage for all five wizard subclasses (including inferred Bladesinging
  manifest source).

## Purpose

- Preserve a canonical test-build decision history.
- Make level-up choices reviewable in git.
- Provide a source artifact for future save stamping or authored test-build
  generation.

## Runtime execution policy

- Use fresh game/load for each focused validation run.
- Run one subclass command at a time.
- Enforce strict expectation checks.
- Stop on first failure (do not continue and compound issues).
- Inferred manifests are allowed, but inferred-manifest failures are treated as
  hard failures.
- Use Script Extender console output only.

## Current seed manifest

- `gale_level12_wizard.json`: Larian-authored Gale wizard build extracted from
  `Level12_Gale.lsx`.
- `wizard_subclasses/*.json`: canonical subclass manifests selected from
  PartyEditor presets and indexed in
  `wizard_subclasses/wizard_subclass_manifest_index.json`.
- Inferred manifests include an `inference` block with donor source and
  confidence metadata.

## Important limitation

This repo can now *extract* realistic level-up decisions, but it still does not
have a runtime path that applies them through the live level-up UI. The current
practical use is:

1. choose or author a canonical build source
2. extract its decision manifest
3. use that manifest as the truth source for future test-character creation
   or save stamping
4. run Script Extender smoke checks against the resulting in-game build

In practice, this means you can validate level-state outcomes in game (and see
resulting character level state reflected by the engine UI), but you are not
replaying native level-up UI decisions click-by-click.