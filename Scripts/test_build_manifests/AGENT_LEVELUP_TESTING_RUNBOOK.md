# Agent Runbook: Realistic Wizard Level-Up Testing

> **Note (2026-07-14):** for any non-wizard class/subclass, use the generic
> path instead: regenerate `ClassExpectations.lua` with
> `python Scripts/build_all_class_expectations.py`, then run
> `./Scripts/test_subclass.sh <Name>` (wraps `!aposubsweep <Name>` + log watch
> + kill-on-fail). This runbook remains the wizard manifest/choice-pipeline
> reference.

Use this runbook when an agent needs to refresh canonical wizard manifests and
run level 13-20 Apotheosis validation against realistic level-up choices.

## Goal

Produce reproducible, reviewable test inputs from PartyEditor and then run
smoke checks against those inputs.

## Runtime policy (locked)

- Test session starts from a fresh game/load.
- Developer chooses one wizard subclass command at a time.
- Validation mode is strict.
- Failure behavior is stop-on-first-failure.
- Inferred manifests are allowed, but manifest-related failures are hard
  failures and stop immediately.
- Output channel is Script Extender console logs only.

## Step 1: Refresh subclass manifests

From repo root:

```bash
python Scripts/generate_wizard_subclass_manifests.py
```

If coverage gaps remain (for example Bladesinging), run inference mode:

```bash
python Scripts/generate_wizard_subclass_manifests.py --infer-missing
```

Inference mode synthesizes missing subclass manifests by substituting subclass
GUID selections from a donor canonical manifest (default donor:
`EvocationSchool`).

Expected outputs:

- `Scripts/test_build_manifests/wizard_subclasses/wizard_*_canonical.json`
- `Scripts/test_build_manifests/wizard_subclasses/wizard_subclass_manifest_index.json`

If `missing_subclasses` is non-empty in the index, the agent must report that
coverage gap explicitly.

If `inferred_manifests` is non-empty, the agent must mark those builds as
"inferred" (not canonical) in test reporting.

## Step 2: Validate extracted artifacts

Sanity checks:

```bash
python -m json.tool Scripts/test_build_manifests/wizard_subclasses/wizard_subclass_manifest_index.json > /dev/null
python -m json.tool Scripts/test_build_manifests/wizard_subclasses/wizard_evocationschool_canonical.json > /dev/null
```

Then verify index summary:

- `generated_manifests` count
- `missing_subclasses`
- source files and preset indices used for canonical picks

## Step 3: Build 13-20 expectation matrix

Generate expected grants from Apotheosis progression data:

```bash
python Scripts/build_wizard_13_20_expectations.py
```

Output:

- `Scripts/test_build_manifests/wizard_13_20_expectations.json`

Agent must verify each subclass has `has_subclass_entries: true`.

## Step 4: Prepare build for runtime smoke tests

From repo root:

```bash
./Scripts/pack_deploy_test.sh
```

This packs/deploys and ensures modsettings contains the Apotheosis UUID.

## Step 5: Runtime smoke execution

In Script Extender console (`server` context), run:

```lua
-- planned interface (to be implemented):
Apotheosis.Smoke.Wizard.RunManifest("EvocationSchool")
```

Expected operator flow:

1. Load fresh game.
2. Run one subclass command.
3. Review strict PASS/FAIL console output.
4. Fix first failure before running the next subclass.

Notes on in-game visuals:

- The engine can reflect level state changes on the character UI, but this path
  does not drive the native level-up choice UI pipeline automatically.
- Validation remains manifest-vs-runtime-state, not UI-click replay.

## Step 6: Report format the agent should return

The agent response must include:

1. Which canonical manifests were generated (file names)
2. Which wizard subclasses are still missing from PartyEditor corpus
3. Which manifests are inferred and which donor subclass/source they used
4. Whether pack/deploy readiness checks passed
5. Smoke test outcome summary, including failing checks by name
6. Expectation matrix summary (wizard base entries + subclass entry counts)
7. First-failure stop point (subclass, level, check name)

## Notes

- GUID-to-name resolution is built into extraction flows. Keep GUID fields and
  resolved name fields together in manifests.
- The extraction path captures authored choices; it does not automate UI
  level-up actions.
- If Bladesinging remains missing, use a manually authored test character path
  and record that manifest source separately.
