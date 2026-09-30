# Progression findings, 2026-09-30

Found while building per-level test plans (bg3-data-mcp `bg3_lint_progressions`, `bg3_test_plan`) and
confirmed in the running game (`Ext.StaticData.GetAll("Progression")`, 2026-09-30 ~17:05 CDT).

## Impact
1. **Wizard subclass levels 13-20 never load.** 56 subclass nodes use made-up UUIDs such as
   `en131313-1313-...` (`n`, `o`, `v`, `l`, `r`, `i`, `t`, `c`... aren't hex). In game the Enchanter and
   Conjurer tables contain only their L12 and L14 nodes; L13 and L15-L20 are missing, so none of those
   features or choices reach players. Affects Conjuration, Divination, Enchantment, Evocation,
   Illusion, Necromancy, Transmutation and Bladesinging (Abjuration's UUIDs are valid).
2. **Wizard level 12 asks twice.** Apotheosis added node `66666666-...-600` (to remove Spell Mastery)
   next to dnd55e's `3cb9d873-...`; both load, each with 2 spell picks and a feat. Breaks VISION
   principle 3 (levels 1-12 must play as dnd55e). Fix: override dnd55e's node by reusing its UUID with the
   full content plus `PassivesRemoved`.
3. **Double ASI at 16 and 19** for Gunslinger, Illrigger and Monster Hunter (dnd55e already has 13-20
   nodes for these; Apotheosis adds a second node per level).
4. **61 selectors point at lists that don't exist**, including `EpicBoons` (`da3e7815-...`, every class at
   19: the Epic Boon choice is empty) and every Wizard subclass "Savant" list at 13/15/17/19.

## Lint output
```
progression lint for apotheosis: 56 invalid UUIDs, 61 dangling lists, 7 stacked-choice levels
INVALID node UUIDs (56) - the game doesn't load these nodes:
  ConjurationSchool L13: co131313-1313-1313-1313-131313131301
  ConjurationSchool L15: co151515-1515-1515-1515-151515151501
  ConjurationSchool L16: co161616-1616-1616-1616-161616161601
  ConjurationSchool L17: co171717-1717-1717-1717-171717171701
  ConjurationSchool L18: co181818-1818-1818-1818-181818181801
  ConjurationSchool L19: co191919-1919-1919-1919-191919191901
  ConjurationSchool L20: co202020-2020-2020-2020-202020202001
  DivinationSchool L13: di131313-1313-1313-1313-131313131301
  DivinationSchool L15: di151515-1515-1515-1515-151515151501
  DivinationSchool L16: di161616-1616-1616-1616-161616161601
  DivinationSchool L17: di171717-1717-1717-1717-171717171701
  DivinationSchool L18: di181818-1818-1818-1818-181818181801
  DivinationSchool L19: di191919-1919-1919-1919-191919191901
  DivinationSchool L20: di202020-2020-2020-2020-202020202001
  EnchantmentSchool L13: en131313-1313-1313-1313-131313131301
  EnchantmentSchool L15: en151515-1515-1515-1515-151515151501
  EnchantmentSchool L16: en161616-1616-1616-1616-161616161601
  EnchantmentSchool L17: en171717-1717-1717-1717-171717171701
  EnchantmentSchool L18: en181818-1818-1818-1818-181818181801
  EnchantmentSchool L19: en191919-1919-1919-1919-191919191901
  EnchantmentSchool L20: en202020-2020-2020-2020-202020202001
  EvocationSchool L13: ev131313-1313-1313-1313-131313131301
  EvocationSchool L15: ev151515-1515-1515-1515-151515151501
  EvocationSchool L16: ev161616-1616-1616-1616-161616161601
  EvocationSchool L17: ev171717-1717-1717-1717-171717171701
  EvocationSchool L18: ev181818-1818-1818-1818-181818181801
  EvocationSchool L19: ev191919-1919-1919-1919-191919191901
  EvocationSchool L20: ev202020-2020-2020-2020-202020202001
  IllusionSchool L13: il131313-1313-1313-1313-131313131301
  IllusionSchool L15: il151515-1515-1515-1515-151515151501
  IllusionSchool L16: il161616-1616-1616-1616-161616161601
  IllusionSchool L17: il171717-1717-1717-1717-171717171701
  IllusionSchool L18: il181818-1818-1818-1818-181818181801
  IllusionSchool L19: il191919-1919-1919-1919-191919191901
  IllusionSchool L20: il202020-2020-2020-2020-202020202001
  NecromancySchool L13: ne131313-1313-1313-1313-131313131301
  NecromancySchool L15: ne151515-1515-1515-1515-151515151501
  NecromancySchool L16: ne161616-1616-1616-1616-161616161601
  NecromancySchool L17: ne171717-1717-1717-1717-171717171701
  NecromancySchool L18: ne181818-1818-1818-1818-181818181801
  NecromancySchool L19: ne191919-1919-1919-1919-191919191901
  NecromancySchool L20: ne202020-2020-2020-2020-202020202001
  TransmutationSchool L13: tr131313-1313-1313-1313-131313131301
  TransmutationSchool L15: tr151515-1515-1515-1515-151515151501
  TransmutationSchool L16: tr161616-1616-1616-1616-161616161601
  TransmutationSchool L17: tr171717-1717-1717-1717-171717171701
  TransmutationSchool L18: tr181818-1818-1818-1818-181818181801
  TransmutationSchool L19: tr191919-1919-1919-1919-191919191901
  TransmutationSchool L20: tr202020-2020-2020-2020-202020202001
  BladesingingSchool L13: bl131313-1313-1313-1313-131313131301
  BladesingingSchool L15: bl151515-1515-1515-1515-151515151501
  BladesingingSchool L16: bl161616-1616-1616-1616-161616161601
  BladesingingSchool L17: bl171717-1717-1717-1717-171717171701
  BladesingingSchool L18: bl181818-1818-1818-1818-181818181801
  BladesingingSchool L19: bl191919-1919-1919-1919-191919191901
  BladesingingSchool L20: bl202020-2020-2020-2020-202020202001
DANGLING list references (61):
  AbjurationSchool L13: SelectSpells(7bd7b3ea-51da-4144-b5ba-3d85dbf79353) - list not defined in base+dnd55e+apotheosis
  AbjurationSchool L15: SelectSpells(7bd7b3ea-51da-4144-b5ba-3d85dbf79353) - list not defined in base+dnd55e+apotheosis
  AbjurationSchool L17: SelectSpells(7bd7b3ea-51da-4144-b5ba-3d85dbf79353) - list not defined in base+dnd55e+apotheosis
  AbjurationSchool L19: SelectSpells(7bd7b3ea-51da-4144-b5ba-3d85dbf79353) - list not defined in base+dnd55e+apotheosis
  Artificer L13: SelectSpells(d0e1f2a3-b4c5-6d7e-8f9a-0b1c2d3e4f5a) - list not defined in base+dnd55e+apotheosis
  Artificer L14: SelectPassives(e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b) - list not defined in base+dnd55e+apotheosis
  Artificer L17: SelectSpells(d0e1f2a3-b4c5-6d7e-8f9a-0b1c2d3e4f5a) - list not defined in base+dnd55e+apotheosis
  Artificer L18: SelectPassives(e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b) - list not defined in base+dnd55e+apotheosis
  Artificer L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Barbarian L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Bard L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  BattleMaster L18: SelectPassives(a1b2c3d4-e5f6-7890-abcd-ef1234567890) - list not defined in base+dnd55e+apotheosis
  Cleric L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  ConjurationSchool L13: SelectSpells(a29ca5bb-3d26-4447-8ff5-12e9ed51a980) - list not defined in base+dnd55e+apotheosis
  ConjurationSchool L15: SelectSpells(a29ca5bb-3d26-4447-8ff5-12e9ed51a980) - list not defined in base+dnd55e+apotheosis
  ConjurationSchool L17: SelectSpells(a29ca5bb-3d26-4447-8ff5-12e9ed51a980) - list not defined in base+dnd55e+apotheosis
  ConjurationSchool L19: SelectSpells(a29ca5bb-3d26-4447-8ff5-12e9ed51a980) - list not defined in base+dnd55e+apotheosis
  DivinationSchool L13: SelectSpells(8e445849-3d0f-4cce-8f9c-b162e3e03ba2) - list not defined in base+dnd55e+apotheosis
  DivinationSchool L15: SelectSpells(8e445849-3d0f-4cce-8f9c-b162e3e03ba2) - list not defined in base+dnd55e+apotheosis
  DivinationSchool L17: SelectSpells(8e445849-3d0f-4cce-8f9c-b162e3e03ba2) - list not defined in base+dnd55e+apotheosis
  DivinationSchool L19: SelectSpells(8e445849-3d0f-4cce-8f9c-b162e3e03ba2) - list not defined in base+dnd55e+apotheosis
  Druid L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  EnchantmentSchool L13: SelectSpells(c930bb09-0c28-4683-ac8e-49ee3262338b) - list not defined in base+dnd55e+apotheosis
  EnchantmentSchool L15: SelectSpells(c930bb09-0c28-4683-ac8e-49ee3262338b) - list not defined in base+dnd55e+apotheosis
  EnchantmentSchool L17: SelectSpells(c930bb09-0c28-4683-ac8e-49ee3262338b) - list not defined in base+dnd55e+apotheosis
  EnchantmentSchool L19: SelectSpells(c930bb09-0c28-4683-ac8e-49ee3262338b) - list not defined in base+dnd55e+apotheosis
  EvocationSchool L13: SelectSpells(0260a3ae-9ff6-4e24-a081-506f6db2ebf3) - list not defined in base+dnd55e+apotheosis
  EvocationSchool L15: SelectSpells(0260a3ae-9ff6-4e24-a081-506f6db2ebf3) - list not defined in base+dnd55e+apotheosis
  EvocationSchool L17: SelectSpells(0260a3ae-9ff6-4e24-a081-506f6db2ebf3) - list not defined in base+dnd55e+apotheosis
  EvocationSchool L19: SelectSpells(0260a3ae-9ff6-4e24-a081-506f6db2ebf3) - list not defined in base+dnd55e+apotheosis
  Fighter L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  GlamourCollege L14: AddSpells(8ad26d20-d989-4195-9af0-818a86dfed07) - list not defined in base+dnd55e+apotheosis
  Gunslinger L13: SelectPassives(f2a3b4c5-d6e7-8f9a-0b1c-2d3e4f5a6b7c) - list not defined in base+dnd55e+apotheosis
  Gunslinger L17: SelectPassives(f2a3b4c5-d6e7-8f9a-0b1c-2d3e4f5a6b7c) - list not defined in base+dnd55e+apotheosis
  Gunslinger L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Illrigger L13: SelectSpells(a3b4c5d6-e7f8-9a0b-1c2d-3e4f5a6b7c8d) - list not defined in base+dnd55e+apotheosis
  Illrigger L17: SelectSpells(a3b4c5d6-e7f8-9a0b-1c2d-3e4f5a6b7c8d) - list not defined in base+dnd55e+apotheosis
  Illrigger L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  IllusionSchool L13: SelectSpells(b4308398-d948-4ef1-a0d5-9da1da860917) - list not defined in base+dnd55e+apotheosis
  IllusionSchool L15: SelectSpells(b4308398-d948-4ef1-a0d5-9da1da860917) - list not defined in base+dnd55e+apotheosis
  IllusionSchool L17: SelectSpells(b4308398-d948-4ef1-a0d5-9da1da860917) - list not defined in base+dnd55e+apotheosis
  IllusionSchool L19: SelectSpells(b4308398-d948-4ef1-a0d5-9da1da860917) - list not defined in base+dnd55e+apotheosis
  Monk L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  MonsterHunter L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  NecromancySchool L13: SelectSpells(7cb1296f-113c-4fc6-a1c8-e18288aa6360) - list not defined in base+dnd55e+apotheosis
  NecromancySchool L15: SelectSpells(7cb1296f-113c-4fc6-a1c8-e18288aa6360) - list not defined in base+dnd55e+apotheosis
  NecromancySchool L17: SelectSpells(7cb1296f-113c-4fc6-a1c8-e18288aa6360) - list not defined in base+dnd55e+apotheosis
  NecromancySchool L19: SelectSpells(7cb1296f-113c-4fc6-a1c8-e18288aa6360) - list not defined in base+dnd55e+apotheosis
  Paladin L13: SelectSpells(4a614e36-b7af-4e84-9d44-7c6ab4ad884f) - list not defined in base+dnd55e+apotheosis
  Paladin L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Ranger L13: SelectSpells(8a34b59f-b7ac-4283-a4cb-2c5e4e1f2e91) - list not defined in base+dnd55e+apotheosis
  Ranger L14: SelectPassives(eb28ac6c-0a84-4d94-bce6-a2c2caa9ae56) - list not defined in base+dnd55e+apotheosis
  Ranger L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Rogue L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Sorcerer L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  TransmutationSchool L13: SelectSpells(538dd943-cd46-4140-a75e-d51b747c1367) - list not defined in base+dnd55e+apotheosis
  TransmutationSchool L15: SelectSpells(538dd943-cd46-4140-a75e-d51b747c1367) - list not defined in base+dnd55e+apotheosis
  TransmutationSchool L17: SelectSpells(538dd943-cd46-4140-a75e-d51b747c1367) - list not defined in base+dnd55e+apotheosis
  TransmutationSchool L19: SelectSpells(538dd943-cd46-4140-a75e-d51b747c1367) - list not defined in base+dnd55e+apotheosis
  Warlock L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
  Wizard L19: SelectPassives(da3e7815-685b-469c-9bba-0f5a7cc93fd1) - list not defined in base+dnd55e+apotheosis
STACKED choices (7): several nodes for one table+level each grant choices/feats - all load, so they're offered twice:
  Gunslinger L16: dnd55e b43cff97-4be7-482d-8a16-fb29f5b98766 [AllowImprovement]; apotheosis dddddddd-dddd-dddd-dddd-ddddddddd904 [AllowImprovement]
  Gunslinger L19: dnd55e 465b1578-a2dd-476a-b4ac-d3955332b5f3 [AllowImprovement]; apotheosis dddddddd-dddd-dddd-dddd-ddddddddd907 [AllowImprovement] [Selectors]
  Illrigger L16: dnd55e eaf61ae1-48a3-4f69-b4b6-a8918fceff76 [AllowImprovement]; apotheosis eeeeeeee-eeee-eeee-eeee-eeeeeeeee904 [AllowImprovement]
  Illrigger L19: dnd55e 4a4409e5-37a1-44a0-aad7-4d13c1fc3283 [AllowImprovement]; apotheosis eeeeeeee-eeee-eeee-eeee-eeeeeeeee907 [AllowImprovement] [Selectors]
  MonsterHunter L16: dnd55e 5d7b26ac-ffe1-4283-8c54-d255be7a7ec5 [AllowImprovement]; apotheosis f1000000-0000-0000-0000-000000000904 [AllowImprovement]
  MonsterHunter L19: dnd55e 3cfad678-8735-43ae-be06-16f070317a42 [AllowImprovement]; apotheosis f1000000-0000-0000-0000-000000000907 [AllowImprovement] [Selectors]
  Wizard L12: dnd55e 3cb9d873-5f41-4c3c-88f1-b7574c1bf661 [AllowImprovement] [Selectors]; apotheosis 66666666-6666-6666-6666-666666666600 [AllowImprovement] [Selectors]
```

## Next
Fix per VISION.md (principles 2-3: features at their 2024 level, 1-12 unchanged), re-run
`bg3_lint_progressions("apotheosis")` until clean, then continue the Wizard test runs (tests/bg3/wizard.toml).
