"""Subclass features at levels 13-20 that dnd55e's subclasses never reach (Scripts/subclass_gap_audit.py lists them).

Each feature follows the source dnd55e uses for the subclass (texts: References/Subclasses/Subclasses_13_20_Sources.txt):
  UA 2025 Horror Subclasses: College of Spirits 14, Hollow Warden 15, Shadow Sorcery 14/18, Hexblade 14, Undead 14
  XGE: Storm Sorcery 14/18, Divine Soul 14/18
Lua for what stats can't do: SubclassFeatures.lua.

Owns Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_SubclassFeatures.txt, the resources/progression nodes
between SUBCLASS FEATURES 13-20 markers, and their loca.
Run: python3 Scripts/gen_subclass_features.py
"""
from gen_common import Gen, patch_progressions, SHOUT_ANIM

G = Gen("subclassfeat", "SUBCLASS FEATURES 13-20")
NODES = []  # (table, name, level, passives)
ALL_BUT_FORCE_RADIANT = ["Acid", "Bludgeoning", "Cold", "Fire", "Lightning", "Necrotic", "Piercing", "Poison", "Psychic",
                         "Slashing", "Thunder"]


def node(table, name, level, *passives):
    NODES.append((table, name, level, list(passives)))


def limited(res, title, text, replenish, mx=1):
    """A once-per-rest feature's resource and the passive boost that grants it."""
    G.resource(res, mx, replenish, title, text)
    return f"ActionResource({res},{mx},0)"


# ================================================================ Sorcerer: Storm Sorcery (XGE)
STORM = "fac6ea25-a7f8-4793-b331-d884041e5adb"
G.passive("StormSorcery_14_StormsFury", "Storm's Fury",
          "When you are hit by a melee attack, you can use your Reaction to deal Lightning damage equal to your Sorcerer level to the attacker; it makes a Strength saving throw or is pushed up to 20 feet away.",
          {"Boosts": "UnlockInterrupt(Interrupt_StormsFury)"}, icon="PassiveFeature_HeartOfTheStorm_Lightning",
          comment="The base game's Storm's Fury (dnd55e blanks it at 11; XGE has it at 14).")
G.passive("StormSorcery_18_WindSoul", "Wind Soul",
          "You have Immunity to Lightning and Thunder damage and a magical Fly Speed. As an action you can give up to 3 + your Charisma modifier creatures within 30 feet a Fly Speed for 1 hour (once per Short or Long Rest).", {
              "Boosts": "Resistance(Lightning,Immune);Resistance(Thunder,Immune);UnlockSpell(Projectile_Fly_Spell);UnlockSpell(Shout_ApoWindSoul);"
                        + limited("ApoWindSoul", "Wind Soul", "Share your flight.", "ShortRest")},
          icon="Spell_Transmutation_Fly")
G.spell("Shout_ApoWindSoul", "Wind Soul: Share Flight",
        "Up to 3 + your Charisma modifier creatures within 30 feet gain a Fly Speed for 1 hour.", {
            "SpellType": "Shout", "AreaRadius": "9", "TargetConditions": "Ally() and not Dead()",
            "SpellProperties": "ApplyStatus(FLY,100,600)", "TooltipStatusApply": "ApplyStatus(FLY,100,600)",
            "UseCosts": "ActionPoint:1;ApoWindSoul:1", "VerbalIntent": "Buff", "SpellAnimation": SHOUT_ANIM},
        icon="Spell_Transmutation_Fly")
node(STORM, "StormSorcery", 14, "StormSorcery_14_StormsFury")
node(STORM, "StormSorcery", 18, "StormSorcery_18_WindSoul")

# ================================================================ Sorcerer: Shadow Sorcery (UA 2025 Horror)
SHADOW = "02d68ea9-5b8d-4f3f-a37a-96ae78d233cd"
G.spell("Target_ApoShadowWalk", "Shadow Walk",
        "While you are in Dim Light or Darkness, teleport up to 120 feet to an unoccupied space you can see that is also in Dim Light or Darkness.",
        {"TargetRadius": "36", "RechargeValues": "", "UseCosts": "BonusActionPoint:1"}, using="Target_ShadowStep",
        icon="Action_ShadowWalk")
G.passive("ShadowMagic_14_ShadowWalk", "Shadow Walk",
          "As a Bonus Action while in Dim Light or Darkness, teleport up to 120 feet to a space in Dim Light or Darkness.",
          {"Boosts": "UnlockSpell(Target_ApoShadowWalk)"}, icon="Action_ShadowWalk")
UMBRAL = ("For 1 minute: Resistance to all damage except Force and Radiant, and if you would drop to 0 Hit Points you make a "
          "Charisma saving throw (DC 5 + half the damage taken); on a success your Hit Points instead become three times "
          "your Sorcerer level.")
G.status("APO_UMBRAL_FORM", "Umbral Form", UMBRAL, {
    "Boosts": ";".join(f"Resistance({t},Resistant)" for t in ALL_BUT_FORCE_RADIANT) + ";DownedStatus(APO_UMBRAL_GRAVE_DOWNED,7)",
    "StackId": "APO_UMBRAL_FORM", "RemoveEvents": "OnStatusApplied",
    # not on its own 0 HP stand-in (an incapacitating DOWNED-type status): a successful save keeps the form (2026-10-03)
    "RemoveConditions": "HasAnyStatus({'SG_Incapacitated'}) and not HasStatus('APO_UMBRAL_GRAVE_DOWNED')"},
    icon="Action_UmbralCloak", comment="SubclassFeatures.lua: the Strength of the Grave save at 0 HP.")
# the Last Stand pattern (gen_epic_boons.py): a downed replacement holds you at 1 HP, then Lua rolls the save
G.status("APO_UMBRAL_GRAVE_DOWNED", "Strength of the Grave", None, {"OnApplyFunctors": "RegainHitPoints(1,Guaranteed)"},
         using="RELENTLESS_ENDURANCE_DOWNED")
G.spell("Shout_ApoUmbralForm", "Umbral Form", "Adopt a shadowy form. " + UMBRAL, {
    "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "ApplyStatus(APO_UMBRAL_FORM,100,10)",
    "TooltipStatusApply": "ApplyStatus(APO_UMBRAL_FORM,100,10)", "UseCosts": "BonusActionPoint:1;ApoUmbralForm:1",
    "VerbalIntent": "Buff"}, icon="Action_UmbralCloak")
G.spell("Shout_ApoUmbralForm_SorceryPoints", "Umbral Form (6 Sorcery Points)", "Adopt a shadowy form again by spending 6 Sorcery Points. " + UMBRAL,
        {"UseCosts": "BonusActionPoint:1;SorceryPoint:6",
         "RequirementConditions": "not HasActionResource('ApoUmbralForm',1,0,false,false,context.Source)"},
        using="Shout_ApoUmbralForm", icon="Action_UmbralCloak")
G.passive("ShadowMagic_18_UmbralForm", "Umbral Form", "As a Bonus Action, once per Long Rest (or for 6 Sorcery Points): " + UMBRAL, {
    "Boosts": "UnlockSpell(Shout_ApoUmbralForm);UnlockSpell(Shout_ApoUmbralForm_SorceryPoints);"
              + limited("ApoUmbralForm", "Umbral Form", "Adopt your shadowy form.", "Rest")},
    icon="Action_UmbralCloak")
node(SHADOW, "ShadowMagic", 14, "ShadowMagic_14_ShadowWalk")
node(SHADOW, "ShadowMagic", 18, "ShadowMagic_18_UmbralForm")

# ================================================================ Sorcerer: Divine Soul (XGE)
DIVINE = "f98f8748-4842-4441-a3c0-1c2785333e02"
G.status("APO_OTHERWORLDLY_WINGS", "Otherworldly Wings", "Spectral wings: you have a Fly Speed.", {
    "Boosts": "UnlockSpell(Projectile_Fly_Spell)", "StackId": "APO_OTHERWORLDLY_WINGS",
    "RemoveEvents": "OnStatusApplied", "RemoveConditions": "HasAnyStatus({'SG_Incapacitated'})"}, icon="Spell_Transmutation_Fly")
G.spell("Shout_ApoOtherworldlyWings", "Otherworldly Wings", "Manifest spectral wings: you have a Fly Speed until you're Incapacitated.", {
    "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "ApplyStatus(APO_OTHERWORLDLY_WINGS,100,-1)",
    "TooltipStatusApply": "ApplyStatus(APO_OTHERWORLDLY_WINGS,100,-1)", "UseCosts": "BonusActionPoint:1", "VerbalIntent": "Buff"},
    icon="Spell_Transmutation_Fly")
G.passive("DivineSoul_14_OtherworldlyWings", "Otherworldly Wings", "As a Bonus Action, manifest spectral wings and gain a Fly Speed.",
          {"Boosts": "UnlockSpell(Shout_ApoOtherworldlyWings)"}, icon="Spell_Transmutation_Fly")
G.spell("Shout_ApoUnearthlyRecovery", "Unearthly Recovery",
        "While you have fewer than half your Hit Points, regain Hit Points equal to half your Hit Point maximum.", {
            "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "RegainHitPoints(MaxHP/2)",
            "TooltipDamageList": "RegainHitPoints(MaxHP/2)",
            "RequirementConditions": "HasHPPercentageWithoutTemporaryHPLessThan(50, context.Source)",
            "UseCosts": "BonusActionPoint:1;ApoUnearthlyRecovery:1", "VerbalIntent": "Healing"}, icon="Spell_Evocation_CureWounds")
G.passive("DivineSoul_18_UnearthlyRecovery", "Unearthly Recovery",
          "Once per Long Rest, as a Bonus Action while below half your Hit Points, regain half your Hit Point maximum.", {
              "Boosts": "UnlockSpell(Shout_ApoUnearthlyRecovery);"
                        + limited("ApoUnearthlyRecovery", "Unearthly Recovery", "Recover from grievous injuries.", "Rest")},
          icon="Spell_Evocation_CureWounds")
node(DIVINE, "DivineSoul", 14, "DivineSoul_14_OtherworldlyWings")
node(DIVINE, "DivineSoul", 18, "DivineSoul_18_UnearthlyRecovery")

# ================================================================ Warlock: Hexblade (UA 2025 Horror)
HEXBLADE = "2b9b50de-48e2-4b1c-b40d-6050aa85009a"
G.status("APO_INFECTIOUS_HEX", "Infectious Hex", None, {
    "StackId": "APO_INFECTIOUS_HEX", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Marker on the hexed target: SubclassFeatures.lua deals 1d6 Necrotic to another creature within 30 feet of it.")
G.status("APO_INFECTIOUS_HEX_DAMAGE", "Infectious Hex", None, {
    "OnApplyFunctors": "DealDamage(1d6,Necrotic,Magical)", "StackId": "APO_INFECTIOUS_HEX_DAMAGE",
    "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.status("APO_RESILIENT_HEX", "Resilient Hex", "Taking damage can't break your Concentration on Hex.", {
    "Boosts": "ConcentrationIgnoreDamage(Enchantment)", "StackId": "APO_RESILIENT_HEX",
    "StatusPropertyFlags": "DisableCombatlog"}, icon="Spell_Enchantment_Hex",
    comment="SubclassFeatures.lua keeps it on only while you concentrate on Hex.")
G.passive("Hexblade_14_MasterfulHex", "Masterful Hex",
          "Your attacks against the target of your Hex score a Critical Hit on a 19 or 20. When you use a Hexblade's Maneuver, one other creature within 30 feet of the cursed target takes 1d6 Necrotic damage. Taking damage can't break your Concentration on Hex.", {
              "Boosts": "IF(HasHexStatus()):ReduceCriticalAttackThreshold(1)",
              "StatsFunctorContext": "OnDamage", "Conditions": "HasHexStatus() and IsAttack()",
              "StatsFunctors": "ApplyStatus(APO_INFECTIOUS_HEX,100,0)"}, icon="Spell_Enchantment_Hex")
node(HEXBLADE, "Hexblade", 14, "Hexblade_14_MasterfulHex")

# ================================================================ Warlock: Undead Patron (UA 2025 Horror)
UNDEAD = "35c30532-8f59-4980-b21b-4f729d2cd786"
G.status("APO_VITALITY_SIPHON", "Vitality Siphon", None, {
    "OnApplyFunctors": "RegainHitPoints(max(1,CharismaModifier))", "StackId": "APO_VITALITY_SIPHON",
    "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.passive("UndeadPatron_14_SuperiorDread", "Superior Dread",
          "While in your Form of Dread you have a Fly Speed, and once per turn when you deal Necrotic damage you regain Hit Points equal to your Charisma modifier (minimum 1).", {
              "BoostContext": "OnStatusApplied;OnStatusRemoved",
              "Boosts": "IF(HasStatus('FORM_OF_DREAD',context.Source)):UnlockSpell(Projectile_Fly_Spell)",
              "StatsFunctorContext": "OnDamage",
              "Conditions": "HasStatus('FORM_OF_DREAD',context.Source) and HasDamageDoneForType(DamageType.Necrotic)",
              "StatsFunctors": "ApplyStatus(SELF,APO_VITALITY_SIPHON,100,0)", "Properties": "Highlighted;OncePerTurn"},
          icon="Spell_Necromancy_VampiricTouch")
node(UNDEAD, "UndeadPatron", 14, "UndeadPatron_14_SuperiorDread")

# ================================================================ Bard: College of Spirits (UA 2025 Horror)
SPIRITS = "3669d6ce-d951-4491-8c23-fe2fa922357c"
SPIRIT_NAMES = ["Beloved", "Sharpshooter", "Avenger", "Renegade", "Fortune Teller", "Wayfarer", "Trickster", "Shade",
                "Arsonist", "Coward"]
G.passive("Spirits_14_MysticalConnection", "Mystical Connection",
          "Whenever you roll on the Spirits from Beyond table, you roll twice and choose: the second spirit is offered as a free switch.",
          {}, icon="Spirits_3_SpiritsFromBeyond", comment="SubclassFeatures.lua rolls the second spirit (the die dnd55e uses).")
for i, nm in enumerate(SPIRIT_NAMES):
    clear = ";".join(f"RemoveStatus(SELF,SPIRITS_FROM_BEYOND_{k})" for k in range(10))
    G.status(f"APO_MYSTICAL_CONNECTION_{i}", f"Mystical Connection: {nm}",
             f"Your second roll on the Spirits from Beyond table: {nm}. You can switch to it (no action).", {
                 "Boosts": f"UnlockSpell(Shout_ApoMysticalConnection_{i})", "StackId": "APO_MYSTICAL_CONNECTION"},
             icon="Spirits_3_SpiritsFromBeyond")
    G.spell(f"Shout_ApoMysticalConnection_{i}", f"Mystical Connection: take the {nm}",
            f"Take the {nm} instead of the spirit you rolled first.", {
                "SpellType": "Shout", "TargetConditions": "Self()",
                "SpellProperties": f"{clear};RemoveStatus(SELF,APO_MYSTICAL_CONNECTION_{i});ApplyStatus(SELF,SPIRITS_FROM_BEYOND_{i},100,-1)",
                "UseCosts": "", "VerbalIntent": "Buff"},
            icon="Spirits_3_SpiritsFromBeyond")
node(SPIRITS, "SpiritsCollege", 14, "Spirits_14_MysticalConnection")

# ================================================================ Ranger: Hollow Warden (UA 2025 Horror)
HOLLOW = "e5e8acd6-4fd3-4295-8e78-3a77b8c30f2d"
G.passive("HollowWarden_15_AncientEndurance", "Ancient Endurance",
          "Timeless: you have Immunity to Exhaustion. Persistent Hunt: if you drop to 0 Hit Points while transformed by Wrath of the Wild and don't die outright, you can expend a level 4+ spell slot; your Hit Points instead become five times the slot's level.",
          {"Boosts": "StatusImmunity(EXHAUSTED);IF(HasStatus('WRATH_OF_THE_WILD',context.Source) and not HasStatus('APO_PERSISTENT_HUNT_SPENT',context.Source)):DownedStatus(APO_PERSISTENT_HUNT_DOWNED,7)",
           "BoostContext": "OnStatusApplied;OnStatusRemoved"}, icon="PassiveFeature_Generic_Magical",
          comment="SubclassFeatures.lua: Persistent Hunt (spends the lowest level 4+ slot you have).")
G.status("APO_PERSISTENT_HUNT_DOWNED", "Persistent Hunt", None, {"OnApplyFunctors": "RegainHitPoints(1,Guaranteed)"},
         using="RELENTLESS_ENDURANCE_DOWNED")
G.status("APO_PERSISTENT_HUNT_SPENT", "Persistent Hunt", None, {
    "StackId": "APO_PERSISTENT_HUNT_SPENT", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Set when no level 4+ slot was left, so the next drop goes down normally instead of looping.")
node(HOLLOW, "HollowWarden", 15, "HollowWarden_15_AncientEndurance")


def write():
    new_nodes = []
    for table, name, level, passives in NODES:
        new_nodes.append((G.gid(f"node:{table}:{level}"), name, level, 1, table, {"PassivesAdded": ";".join(passives)}))
    G.write_stats("SubclassFeatures", "gen_subclass_features.py", "13-20 subclass features")
    G.patch_files()
    patch_progressions({}, new_nodes, G.marker)
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.resources)} resources, {len(NODES)} nodes")
