"""Generate single PHB 2024 class features that dnd55e and Apotheosis lacked (one issue each):
- #11 Ranger 14 Nature's Veil, Ranger 17 Precise Hunter
- #12 College of Glamour 14 Unbreakable Majesty
- #13 Battle Master 15 Relentless (the +1 Superiority Die moves to the level-15 node)

Owns Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_ClassFeatures.txt; patches Progressions (by UUID),
ActionResourceDefinitions and loca. Script Extender half: ScriptExtender/Lua/ClassFeatures.lua (Relentless).

Run: python3 Scripts/gen_class_features.py && python3 Scripts/build_all_class_expectations.py
"""
from gen_common import Gen, drop_entries, patch_progressions

G = Gen("classfeatures", "CLASS FEATURES 2024")

# ---------------------------------------------------------------- #11 Ranger
G.resource("NaturesVeil", 7, "Rest", "Nature's Veil", "Become Invisible until the end of your next turn. Uses equal to your Wisdom modifier; returns on a Long Rest.")
WIS_LADDER = ";".join(f"IF(AbilityGreaterThan('Wisdom',{n},context.Source)):ActionResource(NaturesVeil,1,0)" for n in (13, 15, 17, 19, 21, 23))
G.passive("Ranger_14_NaturesVeil", "Nature's Veil",
          "As a Bonus Action, you become Invisible until the end of your next turn. You can do this a number of times equal to your Wisdom modifier (minimum once), regaining all uses on a Long Rest.",
          {"Boosts": "UnlockSpell(Shout_Ranger_NaturesVeil);ActionResource(NaturesVeil,1,0);" + WIS_LADDER},
          icon="Spell_Illusion_GreaterInvisibility", comment="Uses = Wisdom modifier, as dnd55e's WardingFlare ladder.")
G.spell("Shout_Ranger_NaturesVeil", "Nature's Veil", "Become Invisible until the end of your next turn.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "UseCosts": "BonusActionPoint:1;NaturesVeil:1",
    "SpellProperties": "ApplyStatus(SELF,RANGER_NATURES_VEIL,100,2)", "SpellFlags": "IgnoreSilence;Invisible"}, icon="Spell_Illusion_GreaterInvisibility")
G.status("RANGER_NATURES_VEIL", "Nature's Veil", "Invisible until the end of your next turn.", {"StackId": "RANGER_NATURES_VEIL"},
         using="GREATER_INVISIBILITY", comment="The 2024 Invisible condition doesn't end when you attack, like Greater Invisibility.")
G.passive("Ranger_17_PreciseHunter", "Precise Hunter",
          "You have Advantage on attack rolls against the creature currently marked by your Hunter's Mark.",
          {"Boosts": "IF(HasStatus('HUNTERS_MARK', context.Target, context.Source)):Advantage(AttackRoll)"}, icon="Spell_Divination_HuntersMark")

# ---------------------------------------------------------------- #12 College of Glamour
G.resource("UnbreakableMajesty", 1, "ShortRest", "Unbreakable Majesty", "Assume a majestic presence. Returns on a Short or Long Rest.")
G.resource("UnbreakableMajestyHit", 1, "Turn", "Unbreakable Majesty (this turn)", "Once per turn, an attacker must save or miss.")
G.passive("Glamour_14_UnbreakableMajesty", "Unbreakable Majesty",
          "As a Bonus Action, assume a majestic presence for 1 minute or until you're Incapacitated. During it, the first time a creature hits you on a turn, it must succeed on a Charisma saving throw against your spell save DC or the attack misses. Once per Short or Long Rest, or by expending a level 5+ spell slot.",
          {"Boosts": "UnlockSpell(Shout_Glamour_UnbreakableMajesty);UnlockSpell(Shout_Glamour_UnbreakableMajesty_Slot);"
                     "UnlockInterrupt(Interrupt_Glamour_UnbreakableMajesty);ActionResource(UnbreakableMajesty,1,0);ActionResource(UnbreakableMajestyHit,1,0)"},
          icon="Spell_Enchantment_CrownOfMadness")
for name, title, cost in (("Shout_Glamour_UnbreakableMajesty", "Unbreakable Majesty", "BonusActionPoint:1;UnbreakableMajesty:1"),
                          ("Shout_Glamour_UnbreakableMajesty_Slot", "Unbreakable Majesty (spell slot)", "BonusActionPoint:1;SpellSlotsGroup:1:1:5")):
    G.spell(name, title, "Assume a majestic presence for 1 minute: the first creature to hit you each turn must save or miss.", {
        "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "UseCosts": cost,
        "RequirementConditions": "not HasStatus('GLAMOUR_UNBREAKABLE_MAJESTY')",
        "SpellProperties": "ApplyStatus(SELF,GLAMOUR_UNBREAKABLE_MAJESTY,100,10)", "SpellFlags": "IgnoreSilence"}, icon="Spell_Enchantment_CrownOfMadness")
G.status("GLAMOUR_UNBREAKABLE_MAJESTY", "Unbreakable Majesty", "The first creature to hit you each turn must succeed on a Charisma saving throw or miss.", {
    "RemoveConditions": "HasStatus('SG_Incapacitated')", "RemoveEvents": "OnStatusApplied", "StackId": "GLAMOUR_UNBREAKABLE_MAJESTY"},
    icon="Spell_Enchantment_CrownOfMadness")
G.interrupt("Interrupt_Glamour_UnbreakableMajesty", "Unbreakable Majesty", "The attacker must succeed on a Charisma saving throw or miss.", {
    "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "HasStatus('GLAMOUR_UNBREAKABLE_MAJESTY', context.Observer) and Self(context.Target,context.Observer) and HasInterruptedAttack() and Enemy(context.Source,context.Observer) and not AnyEntityIsItem() and IsFlatValueInterruptInteresting(99, context.Source)",
    "Roll": "not SavingThrow(Ability.Charisma, SourceSpellDC(10, context.Observer, Ability.Charisma), false, false, context.Source)",
    "Success": "AdjustRoll(OBSERVER_OBSERVER,-99)", "Cost": "UnbreakableMajestyHit:1", "InterruptDefaultValue": "Enabled"}, icon="Spell_Enchantment_CrownOfMadness",
    comment="Hits only: IsFlatValueInterruptInteresting(99, source) = a penalty could still turn it into a miss (as base Shield's 5). Once per round: its charge returns on your turn.")

# ---------------------------------------------------------------- #13 Battle Master
G.resource("BattleMasterRelentless", 1, "Turn", "Relentless", "Once per turn, a maneuver costs no Superiority Die.")
G.passive("BattleMaster_Relentless", "Relentless",
          "Once per turn, when you use a maneuver, you can roll a d8 and use it instead of expending a Superiority Die.",
          {"Boosts": "ActionResource(BattleMasterRelentless,1,0)"}, icon="Action_ForcedManeuver",
          comment="ClassFeatures.lua returns the first Superiority Die a maneuver spends each turn.")

# ---------------------------------------------------------------- progression
NODES = {
    "55555555-5555-5555-5555-555555555502": {"PassivesAdded": "Ranger_14_NaturesVeil"},
    "55555555-5555-5555-5555-555555555505": {"PassivesAdded": "Ranger_17_PreciseHunter", "Boosts": "ActionResource(SpellSlot,1,4);ActionResource(SpellSlot,1,5)",
                                             "Selectors": "AddSpells(6b625ece-306d-576a-9fa2-896d884e4e05)"},
    "17171717-1717-1717-1717-171717171702": {"PassivesAdded": "Glamour_14_UnbreakableMajesty"},
    "aa111111-1111-1111-1111-111111111101": {"PassivesAdded": "BattleMaster_Relentless", "Boosts": "ActionResource(SuperiorityDie,1,0)",
                                             "Selectors": "SelectPassives(e51a2ef5-3663-43f9-8e74-5e28520323f1,2,Maneuvers)"},
}

if __name__ == "__main__":
    drop_entries("Passive.txt", ["BattleMaster_Relentless"])
    G.write_stats("ClassFeatures", "gen_class_features.py", "issues #11 #12 #13")
    G.patch_files()
    patch_progressions(NODES, [], "CLASS FEATURES 2024")
    G.patch_loca()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.I)} interrupts, {len(G.loca)} strings")
