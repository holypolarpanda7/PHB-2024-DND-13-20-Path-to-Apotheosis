"""Generate the Illrigger levels 13-20 (issue #7) from the MCDM Illrigger dnd55e implements
(References/Classes/Illrigger.txt). Replaces the earlier placeholders (spell slots for the whole class, Prince of
Hell, flat-bonus subclass passives).

Base class: Seals 6/7 at 13/18, Interdict Boons 3/4 at 13/18 (13th-level boons join the list), Infernal Conduit
dice 7/8/9/10 at 13/15/17/19 (dnd55e's d12 series, extended), 14 Superior Interdict, 17 Infernal Majesty,
19 ASI (dnd55e's node), 20 Master of Hell and Seal damage 4d6.
Subclasses: 15th-level features; subclass interdict boons at their source levels - dnd55e grants Hell's Assassin
(13th) at 7, Dispater's Supremacy and Blood for Blood (18th) at 7 and Incontrovertible (18th) at 11, which VISION
principle 2 moves back. Architect of Ruin spell table 13-20.

Owns: Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_Illrigger.txt; patches Progressions (by UUID and
between markers), PassiveLists, ActionResourceDefinitions, LevelMapValues, loca. Removes old placeholders from
Passive.txt. Script Extender half: ScriptExtender/Lua/Illrigger.lua.

Run: python3 Scripts/gen_illrigger.py && python3 Scripts/build_all_class_expectations.py
"""
from gen_common import Gen, drop_entries, patch_progressions

G = Gen("illrigger", "ILLRIGGER 13-20")
ILLRIGGER = "33bd368d-2ff4-4add-8692-66d87372053a"
T_ILL = "bd529197-9010-417b-90dc-e6cbf2568cce"
T_AOR, T_HELL, T_PAIN, T_SANG, T_SHADOW = ("80e66947-21f9-49d5-b295-e3c97511f1b0", "c577a73f-ffb9-4391-9165-758c6601f051",
                                           "5f7ba6ef-490a-4f0b-bcfe-50cb86f9886e", "283cff6c-8c2a-4f08-afe4-419dee51bc9b",
                                           "4e800d7d-f45c-4258-a475-85452c8c615d")
SEAL_ICON, HELL_ICON = "Illrigger_1_BalefulInterdict", "Spell_Evocation_Fireball"
QUIET_FLAGS = "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"
BURNING = "(HasStatus('BURNING_SEALS_FIRE',context.Target) or HasStatus('BURNING_SEALS_NECROTIC',context.Target))"

# ---------------------------------------------------------------- level maps (dnd55e's series, extended)
G.levelmap("Seal", "fcd31786-1b71-4255-9907-37491ba8806b", {1: "1d6", 5: "2d6", 10: "3d6", 20: "4d6"}, ILLRIGGER)
G.levelmap("InfernalConduit", "b08ec6fa-0793-4ad8-98dd-95edbf7538c7",
           {6: "3d12", 8: "4d12", 10: "5d12", 12: "6d12", 13: "7d12", 15: "8d12", 17: "9d12", 19: "10d12"}, ILLRIGGER)

# ---------------------------------------------------------------- 14 Superior Interdict
G.resource("IllriggerSuperiorInterdict", 1, "Rest", "Superior Interdict", "Regain a seal when you have none. Returns on a Long Rest.")
G.passive("Illrigger_14_SuperiorInterdict", "Superior Interdict",
          "Damage from your seals ignores Resistance. As a Bonus Action, if you have no seals left, you can regain one; once per Long Rest.",
          {"Boosts": "IF(HasStatus('BURNING_SEALS_FIRE',context.Target)):IgnoreResistance(Fire,Resistant);"
                     "IF(HasStatus('BURNING_SEALS_NECROTIC',context.Target)):IgnoreResistance(Necrotic,Resistant);"
                     "ActionResource(IllriggerSuperiorInterdict,1,0);UnlockSpell(Shout_Illrigger_RegainSeal)"}, icon=SEAL_ICON)
G.spell("Shout_Illrigger_RegainSeal", "Superior Interdict: Regain Seal", "Regain one seal. You must have no seals left.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "AIFlags": "CanNotUse",
    "UseCosts": "BonusActionPoint:1;IllriggerSuperiorInterdict:1",
    "RequirementConditions": "not HasActionResource('Seal',1,0,false,false,context.Source)",
    "SpellProperties": "RestoreResource(SELF,Seal,1,0)", "SpellFlags": "IgnoreSilence"}, icon=SEAL_ICON)

# ---------------------------------------------------------------- 17 Infernal Majesty
TERROR = {1: "Cold", 2: "Fire", 3: "Necrotic", 4: "Poison"}
G.resource("IllriggerInfernalMajesty", 1, "Rest", "Infernal Majesty", "Channel the might of Hell. Returns on a Long Rest.")
G.passive("Illrigger_17_InfernalMajesty", "Infernal Majesty",
          "As a Bonus Action, channel the might of Hell for 10 minutes: Resistance to Fire, Cold and Necrotic damage, a 60-foot flying speed, and your Terrorizing Force deals 2d8 instead of 1d8. Once per Long Rest.",
          {"Boosts": "UnlockSpell(Shout_Illrigger_InfernalMajesty);ActionResource(IllriggerInfernalMajesty,1,0)"}, icon=HELL_ICON)
G.spell("Shout_Illrigger_InfernalMajesty", "Infernal Majesty", "Channel the might of Hell for 10 minutes.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "AIFlags": "CanNotUse",
    "UseCosts": "BonusActionPoint:1;IllriggerInfernalMajesty:1", "SpellProperties": "ApplyStatus(SELF,ILLRIGGER_INFERNAL_MAJESTY,100,100)",
    "SpellFlags": "IgnoreSilence"}, icon=HELL_ICON)
G.status("ILLRIGGER_INFERNAL_MAJESTY", "Infernal Majesty",
         "Resistance to Fire, Cold and Necrotic damage, a flying speed, and Terrorizing Force deals 2d8.", {
             "Boosts": "Resistance(Fire,Resistant);Resistance(Cold,Resistant);Resistance(Necrotic,Resistant);UnlockSpell(Projectile_Fly_Spell);"
                       + ";".join(f"IF(HasPassive('Illrigger_11_TerrorizingForce_{i}',context.Source)):CharacterWeaponDamage(1d8,{t})" for i, t in TERROR.items()),
             "StackId": "ILLRIGGER_INFERNAL_MAJESTY", "StatusGroups": "SG_RemoveOnRespec"}, icon=HELL_ICON,
         comment="Terrorizing Force's 1d8 + this 1d8 = 2d8. The Blood Price rider and reforming in Hell aren't implemented (docs/COVERAGE.md).")

# ---------------------------------------------------------------- 20 Master of Hell
G.resource("IllriggerMasterOfHell", 1, "Rest", "Master of Hell", "Summon a hellstorm. Returns on a Long Rest.")
G.passive("Illrigger_20_MasterOfHell", "Master of Hell",
          "As an action, summon a hellstorm in a 50-foot-radius sphere within 150 feet: Inferno, Pestilence or Darkness, affecting only enemies. Once per Long Rest.",
          {"Boosts": "UnlockSpell(Shout_Illrigger_MasterOfHell);ActionResource(IllriggerMasterOfHell,1,0)"}, icon=HELL_ICON)
STORMS = {
    "Inferno": ("Dexterity", "Hellfire rains down: 5d10 Fire and 5d10 Necrotic damage, and creatures that fail burn (1d10 Fire and 1d10 Necrotic at the end of each turn until they succeed on the save).",
                "DealDamage(5d10,Fire,Magical);DealDamage(5d10,Necrotic,Magical);ApplyStatus(ILLRIGGER_HELLFIRE,100,10)",
                "DealDamage((5d10)/2,Fire,Magical);DealDamage((5d10)/2,Necrotic,Magical)", None, "Fire"),
    "Pestilence": ("Constitution", "A foul miasma: 5d10 Poison and 5d10 Necrotic damage, and creatures that fail are Poisoned for 1 minute.",
                   "DealDamage(5d10,Poison,Magical);DealDamage(5d10,Necrotic,Magical);ApplyStatus(POISONED,100,10)",
                   "DealDamage((5d10)/2,Poison,Magical);DealDamage((5d10)/2,Necrotic,Magical)", None, "Poison"),
    "Darkness": ("Constitution", "A bitter storm: 10d10 Cold damage (half on a success), and enemies in the area are Blinded for 1 minute.",
                 "DealDamage(10d10,Cold,Magical)", "DealDamage((10d10)/2,Cold,Magical)", "ApplyStatus(ILLRIGGER_HELLSTORM_GLOOM,100,10)", "Cold"),
}
G.spell("Shout_Illrigger_MasterOfHell", "Master of Hell", "Summon a hellstorm in a 50-foot-radius sphere.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "AIFlags": "CanNotUse",
    "ContainerSpells": ";".join(f"Projectile_Illrigger_MasterOfHell_{k}" for k in STORMS), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "ActionPoint:1;IllriggerMasterOfHell:1"}, icon=HELL_ICON)
for k, (ab, text, ok, half, always, dtype) in STORMS.items():
    G.spell(f"Projectile_Illrigger_MasterOfHell_{k}", f"Master of Hell: {k}", text, {
        "SpellContainerID": "Shout_Illrigger_MasterOfHell", "Level": "0", "SpellSchool": "",
        "TargetRadius": "45", "AreaRadius": "15", "ExplodeRadius": "15",
        "SpellRoll": f"not SavingThrow(Ability.{ab}, SourceSpellDC())", "SpellSuccess": ok, "SpellFail": half, "SpellProperties": always,
        "TargetConditions": "Enemy() and not Dead()", "TooltipAttackSave": ab, "DamageType": dtype,
        "UseCosts": "ActionPoint:1;IllriggerMasterOfHell:1", "AIFlags": "CanNotUse",
        "SpellFlags": "HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold;IsHarmful;CanAreaDamageEvade"},
        using="Projectile_Fireball", icon=HELL_ICON)
G.status("ILLRIGGER_HELLFIRE", "Hellfire", "Burning with hellfire: at the end of each turn, a Dexterity saving throw or 1d10 Fire and 1d10 Necrotic damage; a success ends it.", {
    "TickType": "EndTurn", "OnTickRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())",
    "OnTickSuccess": "DealDamage(1d10,Fire,Magical);DealDamage(1d10,Necrotic,Magical)", "OnTickFail": "RemoveStatus(SELF,ILLRIGGER_HELLFIRE)",
    "StackId": "ILLRIGGER_HELLFIRE"}, icon="Status_Burning")
G.status("ILLRIGGER_HELLSTORM_GLOOM", "Hellstorm Gloom", "Blinded by the hellstorm's gloom.", {"StackId": "ILLRIGGER_HELLSTORM_GLOOM"},
         using="BLINDED", comment="The source ends it when the creature leaves the area; here it lasts the minute (docs/COVERAGE.md).")

# ---------------------------------------------------------------- 13th-level interdict boons
FREE_ATTACK = "UnlockSpellVariant(ExtraAttackCheck(),ModifyUseCosts(Replace,ActionPoint,0,0,ActionPoint),ModifyIconGlow(),ModifyTooltipDescription())"
FREE_ATTACK_END = {"RemoveConditions": "ExtraAttackSpellCheck() and HasUseCosts('ActionPoint',false,context.Target) and not IsOffHandAttack()",
                   "RemoveEvents": "OnSpellCast"}


def boon13(name, title, text, fields=None, icon=SEAL_ICON, comment=None):
    G.passive(name, title, text, fields, icon=icon, comment=comment)
    BOONS_13.append(name)


BOONS_13 = []
boon13("InterdictBoons_13_DissOnslaught", "Dis's Onslaught (Passive)",
       "When you use a Bonus Action to place a seal, you can make one weapon attack as part of the same Bonus Action.",
       comment="Illrigger.lua applies ILLRIGGER_DISS_ONSLAUGHT on a Bonus Action seal (OnCastResolved didn't fire for it).")
G.status("ILLRIGGER_DISS_ONSLAUGHT", "Dis's Onslaught", "Your next weapon attack this turn costs no action.",
         {"Boosts": FREE_ATTACK, **FREE_ATTACK_END, "StackId": "ILLRIGGER_DISS_ONSLAUGHT", "StatusPropertyFlags": "DisableCombatlog"}, icon=SEAL_ICON)

boon13("InterdictBoons_13_FlashOfBrimstone", "Flash of Brimstone",
       "When you place a seal, you can teleport to an unoccupied space within 5 feet of the target (no action).",
       comment="Illrigger.lua applies ILLRIGGER_FLASH_READY whenever you place a seal.")
G.status("ILLRIGGER_FLASH_READY", "Flash of Brimstone", "You can teleport next to the creature you just sealed.",
         {"Boosts": "UnlockSpell(Target_Illrigger_FlashOfBrimstone)", "StackId": "ILLRIGGER_FLASH_READY", "StatusPropertyFlags": "DisableCombatlog"}, icon=SEAL_ICON)
G.spell("Target_Illrigger_FlashOfBrimstone", "Flash of Brimstone", "Teleport to a space within 5 feet of an interdicted creature.", {
    "SpellType": "Target", "Level": "0", "TargetRadius": "18", "TargetConditions": "HasStatus('INTERDICTED') and not Self()",
    "UseCosts": "", "SpellProperties": "TeleportSource();RemoveStatus(SELF,ILLRIGGER_FLASH_READY)", "AIFlags": "CanNotUse",
    "SpellFlags": "IgnoreSilence;HasHighGroundRangeExtension"}, icon=SEAL_ICON)

boon13("InterdictBoons_13_HellishFrenzy", "Hellish Frenzy",
       "At the start of your turn, you can expend a seal to become frenzied until the start of your next turn: your speed doubles, you gain +2 AC, and you can make one extra weapon attack.",
       {"Boosts": "UnlockSpell(Shout_Illrigger_HellishFrenzy)"})
G.spell("Shout_Illrigger_HellishFrenzy", "Hellish Frenzy", "Expend a seal: doubled speed, +2 AC and an extra weapon attack until your next turn.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "UseCosts": "Seal:1", "AIFlags": "CanNotUse",
    "RequirementConditions": "not HasStatus('ILLRIGGER_HELLISH_FRENZY')",
    "SpellProperties": "ApplyStatus(SELF,ILLRIGGER_HELLISH_FRENZY,100,1);ApplyStatus(SELF,ILLRIGGER_HELLISH_FRENZY_ATTACK,100,1)",
    "SpellFlags": "IgnoreSilence"}, icon=SEAL_ICON)
G.status("ILLRIGGER_HELLISH_FRENZY", "Hellish Frenzy", "Speed doubled and +2 AC.",
         {"Boosts": "ActionResourceMultiplier(Movement,200,0);AC(2)", "StackId": "ILLRIGGER_HELLISH_FRENZY"}, icon=SEAL_ICON)
G.status("ILLRIGGER_HELLISH_FRENZY_ATTACK", "Hellish Frenzy: Extra Attack", "One weapon attack costs no action.",
         {"Boosts": FREE_ATTACK, **FREE_ATTACK_END, "StackId": "ILLRIGGER_HELLISH_FRENZY_ATTACK", "StatusPropertyFlags": "DisableCombatlog"}, icon=SEAL_ICON)

boon13("InterdictBoons_13_Hellsight", "Hellsight", "As an action, expend a seal to gain Truesight out to 60 feet for 1 hour.",
       {"Boosts": "UnlockSpell(Shout_Illrigger_Hellsight)"})
G.spell("Shout_Illrigger_Hellsight", "Hellsight", "Expend a seal: Truesight for 1 hour.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "UseCosts": "ActionPoint:1;Seal:1", "AIFlags": "CanNotUse",
    "SpellProperties": "ApplyStatus(SELF,ILLRIGGER_HELLSIGHT,100,600)", "SpellFlags": "IgnoreSilence"}, icon=SEAL_ICON)
G.status("ILLRIGGER_HELLSIGHT", "Hellsight", "Truesight.", {"StackId": "ILLRIGGER_HELLSIGHT"}, using="TRUESIGHT")

boon13("InterdictBoons_13_ImpalingShot", "Impaling Shot",
       "When you hit an interdicted creature with a ranged weapon attack, you can expend a seal as a Bonus Action: until the end of your next turn its AC drops by your Proficiency Bonus.",
       {"Boosts": "UnlockInterrupt(Interrupt_Illrigger_ImpalingShot)"})
G.interrupt("Interrupt_Illrigger_ImpalingShot", "Impaling Shot", "Expend a seal: the target's AC drops by your Proficiency Bonus until the end of your next turn.", {
    "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "Self(context.Source,context.Observer) and not Self() and IsRangedWeaponAttack() and not IsMiss() and HasStatus('INTERDICTED',context.Target) and not AnyEntityIsItem()",
    "Properties": "ApplyStatus(ILLRIGGER_IMPALED,100,2)", "Cost": "BonusActionPoint:1;Seal:1", "InterruptDefaultValue": "Ask;Enabled"}, icon=SEAL_ICON)
G.status("ILLRIGGER_IMPALED", "Impaled", "AC lowered by the Illrigger's Proficiency Bonus.",
         {"Boosts": "AC(0-Cause.ProficiencyBonus)", "StackId": "ILLRIGGER_IMPALED"}, icon=SEAL_ICON)

boon13("InterdictBoons_13_IronGaol", "Iron Gaol",
       "As an action, touch a creature and expend four seals: it must succeed on a Charisma saving throw or be pulled into Hell's prisons for 1 minute (repeating the save at the end of each of its turns). A creature of level 4 or lower stays there.",
       {"Boosts": "UnlockSpell(Target_Illrigger_IronGaol)"})
G.spell("Target_Illrigger_IronGaol", "Iron Gaol", "Expend four seals: a Charisma saving throw or the target is imprisoned in Hell.", {
    "SpellType": "Target", "Level": "0", "TargetRadius": "1.5", "TargetConditions": "Character() and not Self()",
    "UseCosts": "ActionPoint:1;Seal:4", "SpellRoll": "not SavingThrow(Ability.Charisma, SourceSpellDC())",
    "SpellSuccess": "IF(CharacterLevelGreaterThan(4)):ApplyStatus(ILLRIGGER_IRON_GAOL,100,10);IF(not CharacterLevelGreaterThan(4)):ApplyStatus(ILLRIGGER_IRON_GAOL_FOREVER,100,-1)",
    "TooltipAttackSave": "Charisma", "SpellFlags": "IsHarmful;IsMelee", "AIFlags": "CanNotUse"}, icon=SEAL_ICON)
G.status("ILLRIGGER_IRON_GAOL", "Iron Gaol", "Imprisoned in Hell. Repeats the Charisma saving throw at the end of each turn.", {
    "TickType": "EndTurn", "OnTickRoll": "SavingThrow(Ability.Charisma, SourceSpellDC())",
    "OnTickSuccess": "RemoveStatus(SELF,ILLRIGGER_IRON_GAOL)", "StackId": "ILLRIGGER_IRON_GAOL"}, using="BANISHED")
G.status("ILLRIGGER_IRON_GAOL_FOREVER", "Iron Gaol", "Imprisoned in Hell, left to find their own way out.",
         {"StackId": "ILLRIGGER_IRON_GAOL"}, using="BANISHED")

boon13("InterdictBoons_13_LastWord", "Last Word",
       "When you drop to 0 Hit Points with seals remaining, you expend up to three and explode: 3d6 Fire damage per seal to each enemy within 30 feet (Dexterity saving throw for half), and you regain that many Hit Points.",
       comment="Illrigger.lua triggers it on DOWNED.")
for n in (1, 2, 3):
    G.spell(f"Projectile_Illrigger_LastWord_{n}", f"Last Word ({n} seal{'s' if n > 1 else ''})", f"{3 * n}d6 Fire damage to enemies within 30 feet.", {
        "Level": "0", "SpellSchool": "", "AreaRadius": "9", "ExplodeRadius": "9", "TargetRadius": "1",
        "SpellRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())", "SpellSuccess": f"DealDamage({3 * n}d6,Fire,Magical)",
        "SpellFail": f"DealDamage(({3 * n}d6)/2,Fire,Magical)", "TargetConditions": "Enemy() and not Dead()", "UseCosts": "",
        "AIFlags": "CanNotUse", "SpellFlags": "IsHarmful;CanAreaDamageEvade"}, using="Projectile_Fireball", icon=HELL_ICON)
    G.status(f"ILLRIGGER_LAST_WORD_{n}", "Last Word", None, {
        "OnApplyFunctors": f"CreateExplosion(Projectile_Illrigger_LastWord_{n});RegainHitPoints({3 * n}d6,Guaranteed)",
        "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator;ApplyToDead"}, icon=HELL_ICON)

boon13("InterdictBoons_13_SoulsDoom", "Soul's Doom",
       "When you use a Bonus Action to place a seal, you scorch it into the target's soul: for 1 minute, whenever it takes damage, it takes extra damage equal to your Proficiency Bonus.",
       comment="Illrigger.lua dooms the target of a Bonus Action seal.")
G.status("ILLRIGGER_SOULS_DOOM", "Soul's Doom", "Takes extra damage equal to the Illrigger's Proficiency Bonus whenever it takes damage.",
         {"StackId": "ILLRIGGER_SOULS_DOOM"}, icon=SEAL_ICON, comment="Illrigger.lua deals the extra damage.")

# ---------------------------------------------------------------- interdict boon list
DND_BOONS = ["InterdictBoons_2_AbatingSeal", "InterdictBoons_2_Bedevil", "InterdictBoons_2_SoulEater", "InterdictBoons_2_StyxsApathy",
             "InterdictBoons_2_SwiftRetribution", "InterdictBoons_7_AcheronsChain", "InterdictBoons_7_ConflagrantChannel",
             "InterdictBoons_7_ShadowShroud", "InterdictBoons_7_UnleashHell", "InterdictBoons_7_VengefulShot"]
BOON_LIST = G.passive_list("IllriggerInterdiction13", DND_BOONS + BOONS_13)
BOON_PICK = f"SelectPassives({BOON_LIST},1,IllriggerInterdiction)"

# ---------------------------------------------------------------- subclasses
DARK = "(HasObscuredState(ObscuredState.HeavilyObscured) or HasObscuredState(ObscuredState.LightlyObscured))"
BURN_NECROTIC = "ApplyStatus({who},BURNING_SEALS_NECROTIC,100,0)"  # burning a seal the dnd55e way (INTERDICTED's removal deals it)

# Architect of Ruin 13: Spellbreaker - a Counterspell without a slot against an interdicted caster
G.passive("ArchitectOfRuin_13_Spellbreaker", "Spellbreaker",
          "When an interdicted creature you can see within 60 feet casts a spell, you can use your Reaction to burn its seals (no damage) and Counterspell it without a spell slot.",
          {"Boosts": "UnlockInterrupt(Interrupt_Illrigger_Spellbreaker)"}, icon="PassiveFeature_Counterspell")
G.interrupt("Interrupt_Illrigger_Spellbreaker", "Spellbreaker", "Burn the caster's seals to Counterspell it without a spell slot.", {
    "Conditions": "CanSee(context.Observer, context.Source) and not DistanceToEntityGreaterThan(18, context.ObserverPosition, context.Source) and IsAbleToReact(context.Observer) and not Self(context.Source, context.Observer) and Enemy(context.Source, context.Observer) and IsSpell() and not Uninterruptible() and not HasStringInSpellRoll('WeaponAttack') and not AnyEntityIsItem() and HasStatus('INTERDICTED',context.Source)",
    "Cost": "ReactionActionPoint:1", "Properties": "RemoveStatus(OBSERVER_SOURCE,INTERDICTED)"}, icon="PassiveFeature_Counterspell")
I_FIX = G.I[-1].replace('type "InterruptData"\n', 'type "InterruptData"\nusing "Interrupt_Counterspell"\n')
G.I[-1] = I_FIX

# Architect of Ruin 15: Vile Transmogrification
G.resource("IllriggerVileSeals", 1, "Rest", "Vile Transmogrification: Seals", "Turn a spell slot into seals. Returns on a Long Rest.")
G.resource("IllriggerVileSlots", 1, "Rest", "Vile Transmogrification: Slots", "Turn seals into a spell slot. Returns on a Long Rest.")
G.passive("ArchitectsOfRuin_15_VileTransmogrification", "Vile Transmogrification",
          "As a Bonus Action, expend a spell slot to regain seals equal to its level, or expend three seals per level to regain a spell slot. Each option once per Long Rest.",
          {"Boosts": "UnlockSpell(Shout_Illrigger_VileTransmogrification);ActionResource(IllriggerVileSeals,1,0);ActionResource(IllriggerVileSlots,1,0)"}, icon=SEAL_ICON)
VILE = [f"Shout_Illrigger_Vile_Seals_{n}" for n in (1, 2, 3, 4)] + [f"Shout_Illrigger_Vile_Slot_{n}" for n in (1, 2)]
G.spell("Shout_Illrigger_VileTransmogrification", "Vile Transmogrification", "Trade spell slots and seals.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "AIFlags": "CanNotUse", "ContainerSpells": ";".join(VILE),
    "SpellFlags": "IsLinkedSpellContainer", "UseCosts": "BonusActionPoint:1"}, icon=SEAL_ICON)
for n in (1, 2, 3, 4):
    G.spell(f"Shout_Illrigger_Vile_Seals_{n}", f"Spell Slot to Seals (level {n})", f"Expend a level {n} spell slot to regain {n} seal{'s' if n > 1 else ''}.", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_Illrigger_VileTransmogrification", "TargetConditions": "Self()",
        "AIFlags": "CanNotUse", "UseCosts": f"BonusActionPoint:1;SpellSlot:1:{n};IllriggerVileSeals:1",
        "SpellProperties": f"RestoreResource(SELF,Seal,{n},0)", "SpellFlags": "IgnoreSilence"}, icon=SEAL_ICON)
for n in (1, 2):
    G.spell(f"Shout_Illrigger_Vile_Slot_{n}", f"Seals to Spell Slot (level {n})", f"Expend {3 * n} seals to regain a level {n} spell slot.", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_Illrigger_VileTransmogrification", "TargetConditions": "Self()",
        "AIFlags": "CanNotUse", "UseCosts": f"BonusActionPoint:1;Seal:{3 * n};IllriggerVileSlots:1",
        "SpellProperties": f"RestoreResource(SELF,SpellSlot,1,{n})", "SpellFlags": "IgnoreSilence"}, icon=SEAL_ICON)

# Architect of Ruin 18: Hell Mage (Illrigger.lua places the seal)
G.passive("ArchitectOfRuin_18_HellMage", "Hell Mage (Passive)",
          "When you or an ally within 30 feet succeeds on a saving throw against an enemy's spell or magical effect, you place a seal on that enemy.", icon=SEAL_ICON)

# Hellspeaker 13: Slippery Ploy - a Charisma save or the attack/spell aimed at you is lost
G.passive("Hellspeaker_13_SlipperyPloy", "Slippery Ploy",
          "When a creature targets you with an attack or spell, you can use your Reaction to place a seal on it: it must succeed on a Charisma saving throw or lose the attack or spell.",
          {"Boosts": "UnlockInterrupt(Interrupt_Illrigger_SlipperyPloy)"}, icon=SEAL_ICON)
G.interrupt("Interrupt_Illrigger_SlipperyPloy", "Slippery Ploy", "Place a seal on the attacker: a Charisma saving throw or its attack or spell is lost.", {
    "InterruptContext": "OnSpellCast", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
    "Conditions": "IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and not Self(context.Source,context.Observer) and Enemy(context.Source,context.Observer) and not Uninterruptible() and not AnyEntityIsItem() and not DistanceToEntityGreaterThan(18, context.ObserverPosition, context.Source)",
    "Properties": "ApplyStatus(OBSERVER_SOURCE,INTERDICTED,100,-1)",
    "Roll": "not SavingThrow(Ability.Charisma, SourceSpellDC(10, context.Observer, Ability.Charisma), false, false, context.Source)",
    "Success": "Counterspell()", "Cost": "ReactionActionPoint:1;Seal:1", "InterruptDefaultValue": "Ask;Enabled"}, icon=SEAL_ICON)

# Hellspeaker 15: Quid Pro Quo (Illrigger.lua swaps in the devil)
G.resource("IllriggerQuidProQuo", 1, "Rest", "Quid Pro Quo", "Banish a creature to Hell. Returns on a Long Rest once you succeed.")
G.passive("Hellspeaker_15_QuidProQuo", "Quid Pro Quo",
          "As an action, a creature within 30 feet makes a Charisma saving throw or is banished to Hell for 1 minute (repeating the save each turn), and a devil appears in its place as your ally. Once you succeed, you can't again until a Long Rest; a creature that saves is immune for 24 hours.",
          {"Boosts": "UnlockSpell(Target_Illrigger_QuidProQuo);ActionResource(IllriggerQuidProQuo,1,0)"}, icon=SEAL_ICON)
G.spell("Target_Illrigger_QuidProQuo", "Quid Pro Quo", "A Charisma saving throw or the target is banished to Hell for 1 minute and a devil takes its place.", {
    "SpellType": "Target", "Level": "0", "TargetRadius": "9", "TargetConditions": "Character() and not Self() and not HasStatus('ILLRIGGER_QUID_PRO_QUO_IMMUNE')",
    "UseCosts": "ActionPoint:1", "RequirementConditions": "HasActionResource('IllriggerQuidProQuo',1,0,false,false,context.Source)",
    "SpellRoll": "not SavingThrow(Ability.Charisma, SourceSpellDC())",
    "SpellSuccess": "ApplyStatus(ILLRIGGER_QUID_PRO_QUO,100,10);UseActionResource(SELF,IllriggerQuidProQuo,1,0)",
    "SpellFail": "ApplyStatus(ILLRIGGER_QUID_PRO_QUO_IMMUNE,100,-1)", "TooltipAttackSave": "Charisma",
    "SpellFlags": "IsHarmful", "AIFlags": "CanNotUse"}, icon=SEAL_ICON)
G.status("ILLRIGGER_QUID_PRO_QUO", "Quid Pro Quo", "Banished to Hell. Repeats the Charisma saving throw at the end of each turn.", {
    "TickType": "EndTurn", "OnTickRoll": "SavingThrow(Ability.Charisma, SourceSpellDC())",
    "OnTickSuccess": "RemoveStatus(SELF,ILLRIGGER_QUID_PRO_QUO)", "StackId": "ILLRIGGER_QUID_PRO_QUO"}, using="BANISHED")
G.status("ILLRIGGER_QUID_PRO_QUO_IMMUNE", "Quid Pro Quo Immunity", "Immune to Quid Pro Quo until a Long Rest.", {
    "StackId": "ILLRIGGER_QUID_PRO_QUO_IMMUNE", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"}, icon=SEAL_ICON)

# Painkiller 13: By the Throat
G.passive("Painkiller_13_ByTheThroat", "By the Throat",
          "When you use a Bonus Action to place a seal, the target must succeed on a Wisdom saving throw or be Restrained until the end of its next turn.",
          icon=SEAL_ICON, comment="Illrigger.lua casts Target_Illrigger_ByTheThroat (a real save) on a Bonus Action seal.")
G.spell("Target_Illrigger_ByTheThroat", "By the Throat", "A Wisdom saving throw or Restrained until the end of its next turn.", {
    "SpellType": "Target", "Level": "0", "TargetRadius": "30", "TargetConditions": "Character() and not Self()", "UseCosts": "",
    "SpellRoll": "not SavingThrow(Ability.Wisdom, SourceSpellDC())", "SpellSuccess": "ApplyStatus(ILLRIGGER_BY_THE_THROAT,100,1)",
    "TooltipAttackSave": "Wisdom", "SpellFlags": "IsHarmful;IgnoreSilence", "AIFlags": "CanNotUse"}, icon=SEAL_ICON)
G.status("ILLRIGGER_BY_THE_THROAT", "By the Throat", "Restrained by infernal chains.", {"StackId": "ILLRIGGER_BY_THE_THROAT"}, using="RESTRAINED")

# Painkiller 15: Deathstrike - a hit on an interdicted creature becomes a crit and burns a seal with doubled dice
G.resource("IllriggerDeathstrike", 6, "Rest", "Deathstrike", "Turn a hit into a critical hit. Uses equal to your Proficiency Bonus; returns on a Long Rest.")
G.passive("Painkiller_15_Deathstrike", "Deathstrike",
          "When you hit an interdicted creature with a melee weapon attack, you can use your Reaction to burn a seal on it: the hit becomes a critical hit and the seal's damage dice are doubled. Uses equal to your Proficiency Bonus per Long Rest.",
          {"Boosts": "UnlockInterrupt(Interrupt_Illrigger_Deathstrike)"}, icon=SEAL_ICON)
G.interrupt("Interrupt_Illrigger_Deathstrike", "Deathstrike", "Burn a seal: this hit becomes a critical hit, and the seal's damage dice are doubled.", {
    "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "IsAbleToReact(context.Observer) and Self(context.Source,context.Observer) and HasInterruptedAttack() and IsMeleeWeaponAttack() and not AnyEntityIsItem() and HasStatus('INTERDICTED',context.Target) and not IsFlatValueInterruptInteresting(30, context.Source)",
    "Properties": "SetRoll(20);" + BURN_NECROTIC.format(who="OBSERVER_TARGET") + ";ApplyStatus(OBSERVER_TARGET,ILLRIGGER_DEATHSTRIKE_SEAL,100,0)",
    "Cost": "ReactionActionPoint:1;IllriggerDeathstrike:1", "InterruptDefaultValue": "Ask;Enabled"}, icon=SEAL_ICON)

G.status("ILLRIGGER_DEATHSTRIKE_SEAL", "Deathstrike", None, {
    "OnApplyFunctors": "DealDamage(Cause.LevelMapValue(Seal),Necrotic,Magical)", "StatusPropertyFlags": QUIET_FLAGS}, icon=SEAL_ICON,
    comment="The burned seal's second set of dice (dnd55e's INTERDICTED deals the first).")

# Sanguine Knight 13: Sanguine Gift (Illrigger.lua; toggle so it doesn't spend seals unasked)
G.passive("SanguineKnight_13_SanguineGift", "Sanguine Gift",
          "While this is on, when a creature you can see within 30 feet regains Hit Points, you expend a seal and it regains extra Hit Points equal to your Illrigger level.",
          {"Properties": "Highlighted;IsToggled;ToggledDefaultAddToHotbar", "ToggleGroup": "IllriggerSanguineGift",
           "ToggleOnFunctors": "ApplyStatus(SELF,ILLRIGGER_SANGUINE_GIFT,100,-1)", "ToggleOffFunctors": "RemoveStatus(SELF,ILLRIGGER_SANGUINE_GIFT)"}, icon=SEAL_ICON)
G.status("ILLRIGGER_SANGUINE_GIFT", "Sanguine Gift", "Healing near you is strengthened by your seals.", {
    "StackId": "ILLRIGGER_SANGUINE_GIFT", "StatusPropertyFlags": "IgnoreResting;DisableOverhead;DisableCombatlog"}, icon=SEAL_ICON)

# Sanguine Knight 15: Haemal Exchange (Illrigger.lua passes the d8 to the nearest ally)
G.passive("SanguineKnight_15_HaemalExchange", "Haemal Exchange",
          "When an interdicted creature within 60 feet makes an attack roll or saving throw, you can use your Reaction to burn a seal on it: it subtracts 1d8 from the roll, and the nearest ally within 30 feet adds 1d8 to its next attack roll or saving throw.",
          {"Boosts": "UnlockInterrupt(Interrupt_Illrigger_HaemalExchange_Attack);UnlockInterrupt(Interrupt_Illrigger_HaemalExchange_Save)"}, icon=SEAL_ICON)
for kind, who, cond in (("Attack", "context.Source", "HasInterruptedAttack() and IsFlatValueInterruptInteresting(8, context.Source)"),
                        ("Save", "context.Target", "HasInterruptedSavingThrow() and IsFlatValueInterruptInteresting(8)")):
    obs = "OBSERVER_SOURCE" if kind == "Attack" else "OBSERVER_TARGET"
    G.interrupt(f"Interrupt_Illrigger_HaemalExchange_{kind}", "Haemal Exchange", "Burn a seal: the creature subtracts 1d8 and an ally gains 1d8.", {
        "InterruptContext": "OnPostRoll", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
        "Conditions": f"IsAbleToReact(context.Observer) and {cond} and HasStatus('INTERDICTED',{who}) and Enemy({who},context.Observer) and not DistanceToEntityGreaterThan(18, context.ObserverPosition, {who}) and not AnyEntityIsItem()",
        "Properties": "AdjustRoll(OBSERVER_OBSERVER,0-1d8);" + BURN_NECROTIC.format(who=obs) + ";ApplyStatus(OBSERVER_OBSERVER,ILLRIGGER_HAEMAL_PENDING,100,1)",
        "Cost": "ReactionActionPoint:1", "InterruptDefaultValue": "Ask;Enabled"}, icon=SEAL_ICON)
G.status("ILLRIGGER_HAEMAL_PENDING", "Haemal Exchange", None, {"StatusPropertyFlags": QUIET_FLAGS}, icon=SEAL_ICON)
G.status("ILLRIGGER_HAEMAL_EMPOWER", "Haemal Exchange", "Adds 1d8 to the next attack roll or saving throw.", {
    "Boosts": "RollBonus(Attack,1d8);RollBonus(SavingThrow,1d8)", "RemoveEvents": "OnAttack", "RemoveConditions": "IsAttack()",
    "StackId": "ILLRIGGER_HAEMAL_EMPOWER"}, icon=SEAL_ICON, comment="Removed after the next attack; Illrigger.lua removes it after the next saving throw.")

# Shadowmaster 15: Doomed to the Shadows - Strike from the Dark with d8s, +2d8 in dim light or darkness
G.levelmap("ApoProficiencyBonusD8", G.gid("lm:pbd8"), {1: "2d8", 5: "3d8", 9: "4d8", 13: "5d8", 17: "6d8"})
SFTD = "DealDamage(LevelMapValue(ApoProficiencyBonusD8), MainMeleeWeaponDamageType,Magical);IF(" + DARK + "):DealDamage(2d8, MainMeleeWeaponDamageType,Magical)"
G.passive("Shadowmaster_Illrigger_15_DoomedToTheShadows", "Doomed to the Shadows",
          "Strike from the Dark deals a number of d8s equal to your Proficiency Bonus instead of d4s, and an extra 2d8 if the target is in dim light or darkness.",
          {"Boosts": "ActionResource(StrikeFromTheDark,1,0);UnlockSpell(Target_Illrigger_StrikeFromTheDark);UnlockInterrupt(Interrupt_Illrigger_StrikeFromTheDark)"},
          icon=SEAL_ICON, comment="Replaces dnd55e's Shadowmaster_3_StrikeFromTheDark (removed at 15) with upgraded copies.")
G.interrupt("Interrupt_Illrigger_StrikeFromTheDark", "Strike from the Dark", "Deal extra damage to an interdicted creature.", {
    "Conditions": "Self(context.Source,context.Observer) and not Self() and HasDamageEffectFlag(DamageFlags.Hit) and (IsMainHandWeaponAttack() or IsOffHandAttack()) and IsMeleeWeaponAttack() and not IsKillingBlow() and HasDamageEffectFlag(DamageFlags.AttackAdvantage) and not HasDamageEffectFlag(DamageFlags.AttackDisadvantage) and not SpellId('Target_StrikeFromTheDark') and not SpellId('Target_Illrigger_StrikeFromTheDark') and not AnyEntityIsItem() and HasStatus('INTERDICTED',context.Target)",
    "Properties": SFTD})
G.I[-1] = G.I[-1].replace('type "InterruptData"\n', 'type "InterruptData"\nusing "Interrupt_StrikeFromTheDark"\n')
G.spell("Target_Illrigger_StrikeFromTheDark", "Strike from the Dark", "A melee attack that deals extra damage to an interdicted creature.", {
    "SpellSuccess": "DealDamage(MainMeleeWeapon+LevelMapValue(ApoProficiencyBonusD8), MainMeleeWeaponDamageType);IF(" + DARK + "):DealDamage(2d8, MainMeleeWeaponDamageType);ExecuteWeaponFunctors(MainHand);"},
    using="Target_StrikeFromTheDark")

# Shadowmaster 18: Dark Malediction (Illrigger.lua keeps it on interdicted creatures)
G.passive("Shadowmaster_18_DarkMalediction", "Dark Malediction (Passive)",
          "Creatures you interdict radiate darkness in a 10-foot radius.", icon=SEAL_ICON)
G.status("ILLRIGGER_DARK_MALEDICTION", "Dark Malediction", "Radiates darkness in a 10-foot radius.", {
    "OnApplyFunctors": "CreateSurface(3,1,DarknessCloud,true)", "TickType": "StartTurn", "TickFunctors": "CreateSurface(3,1,DarknessCloud,true)",
    "StackId": "ILLRIGGER_DARK_MALEDICTION"}, icon=SEAL_ICON)

# ---------------------------------------------------------------- progression
WIZ3, WIZ4 = "22755771-ca11-49f4-b772-13d8b8fecd93", "820b1220-0385-426d-ae15-458dc8a6f5c0"  # dnd55e "5.5 Wizard SLevel 3/4"
SEL = lambda lst: f"SelectSpells({lst},1,1,EldritchKnightAbjEvo)"
E = "eeeeeeee-eeee-eeee-eeee-eeeeeeeee9"
NODES = {
    E + "01": {"Boosts": "ActionResource(Seal,1,0)", "Selectors": BOON_PICK},
    E + "02": {"PassivesAdded": "Illrigger_14_SuperiorInterdict"},
    E + "03": {}, E + "04": {},
    E + "05": {"PassivesAdded": "Illrigger_17_InfernalMajesty"},
    E + "06": {"Boosts": "ActionResource(Seal,1,0)", "Selectors": BOON_PICK},
    E + "07": {},
    E + "08": {"PassivesAdded": "Illrigger_20_MasterOfHell"},
    # Architect of Ruin: spells known 9/10/10/11/11/11/12/13 at 13-20; 3rd-level slots 2 at 13, 3 at 16; one 4th at 19
    "32323232-3232-3232-3232-323232323213": {"Boosts": "ActionResource(SpellSlot,2,3)", "Selectors": SEL(WIZ3), "PassivesAdded": "ArchitectOfRuin_13_Spellbreaker"},
    "32323232-3232-3232-3232-323232323201": {"PassivesAdded": "ArchitectsOfRuin_15_VileTransmogrification"},
    "32323232-3232-3232-3232-323232323217": None,
    "32323232-3232-3232-3232-323232323202": {"PassivesAdded": "ArchitectOfRuin_18_HellMage"},
    "32323232-3232-3232-3232-323232323219": {"Boosts": "ActionResource(SpellSlot,1,4)", "Selectors": SEL(WIZ4)},
    "32323232-3232-3232-3232-323232323220": {"Selectors": SEL(WIZ4)},
    # subclass boons back at their source levels (principle 2)
    "aa333333-3333-3333-3333-333333333302": {"PassivesAdded": "HellSpeaker_11_Incontrovertible"},
    "34343434-3434-3434-3434-343434343402": {"PassivesAdded": "PainKiller_7_DispatersSupremacy"},
    "35353535-3535-3535-3535-353535353502": {"PassivesAdded": "SanguineKnight_7_BloodForBlood"},
    "36363636-3636-3636-3636-363636363602": {"PassivesAdded": "Shadowmaster_18_DarkMalediction"},
    "aa333333-3333-3333-3333-333333333301": {"PassivesAdded": "Hellspeaker_15_QuidProQuo"},
    "34343434-3434-3434-3434-343434343401": {"PassivesAdded": "Painkiller_15_Deathstrike", "Boosts": "ActionResource(IllriggerDeathstrike,5,0)"},
    "35353535-3535-3535-3535-353535353501": {"PassivesAdded": "SanguineKnight_15_HaemalExchange"},
    "36363636-3636-3636-3636-363636363601": {"PassivesAdded": "Shadowmaster_Illrigger_15_DoomedToTheShadows", "PassivesRemoved": "Shadowmaster_3_StrikeFromTheDark"},
}
NEW_NODES = [
    (G.gid("aor14"), "ArchitectOfRuin", 14, 1, T_AOR, {"Selectors": SEL(WIZ3)}),
    (G.gid("aor16"), "ArchitectOfRuin", 16, 1, T_AOR, {"Boosts": "ActionResource(SpellSlot,1,3)", "Selectors": SEL(WIZ3)}),
    (G.gid("hell11"), "Hellspeaker", 11, 1, T_HELL, {"PassivesRemoved": "HellSpeaker_11_Incontrovertible"}),
    (G.gid("pain7"), "Painkiller", 7, 1, T_PAIN, {"PassivesRemoved": "PainKiller_7_DispatersSupremacy"}),
    (G.gid("sang7"), "SanguineKnight", 7, 1, T_SANG, {"PassivesRemoved": "SanguineKnight_7_BloodForBlood"}),
    (G.gid("shadow7"), "Shadowmaster", 7, 1, T_SHADOW, {"PassivesRemoved": "Shadowmaster_7_HellsAssassin"}),
    (G.gid("shadow13"), "Shadowmaster", 13, 1, T_SHADOW, {"PassivesAdded": "Shadowmaster_7_HellsAssassin"}),
    (G.gid("hell13"), "Hellspeaker", 13, 1, T_HELL, {"PassivesAdded": "Hellspeaker_13_SlipperyPloy"}),
    (G.gid("pain13"), "Painkiller", 13, 1, T_PAIN, {"PassivesAdded": "Painkiller_13_ByTheThroat"}),
    (G.gid("pain17"), "Painkiller", 17, 1, T_PAIN, {"Boosts": "ActionResource(IllriggerDeathstrike,1,0)"}),
    (G.gid("sang13"), "SanguineKnight", 13, 1, T_SANG, {"PassivesAdded": "SanguineKnight_13_SanguineGift"}),
]
OLD = ["ArchitectsOfRuin_15_VileTransmogrification", "Hellspeaker_15_QuidProQuo", "Painkiller_15_Deathstrike", "SanguineKnight_15_HaemalExchange",
       "Shadowmaster_Illrigger_15_DoomedToTheShadows", "Illrigger_InfernalConduit", "Illrigger_PrinceOfHell", "ArchitectsOfRuin_18_HellMage", "Hellspeaker_18_Incontrovertible",
       "Painkiller_18_DispatersSupremacy", "SanguineKnight_18_BloodForBlood", "Shadowmaster_Illrigger_18_DarkMalediction"]

if __name__ == "__main__":
    drop_entries("Passive.txt", OLD)
    G.write_stats("Illrigger", "gen_illrigger.py", "Illrigger 13-20, issue #7")
    G.patch_files()
    patch_progressions(NODES, NEW_NODES, "ILLRIGGER 13-20")
    G.patch_loca()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.I)} interrupts, {len(G.loca)} strings")
