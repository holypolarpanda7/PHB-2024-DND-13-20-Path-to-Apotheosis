"""Generate PHB 2024 spells missing from base BG3, dnd55e and Apotheosis (issue #10) and add them to the
Paladin/Ranger/Artificer 4th/5th-level lists (auto-granted at 13/17). Texts: References/Spells/Issue10_Spells.txt
(PHB 2024; Skill Empowerment from Xanathar's), extracted 2026-10-02.

Combat spells built here: Aura of Life, Aura of Purity, Conjure Volley, Swift Quiver, Geas, Raise Dead,
Skill Empowerment; Summon Celestial (dnd55e has it) joins the Paladin 5th list. Summons (Summon Elemental/
Construct, Animate Objects, Bigby's Hand, Mordenkainen's Faithful Hound) are a later pass; exploration-only
spells are documented gaps (docs/COVERAGE.md).

Run: python3 Scripts/gen_spells_2024.py
"""
import glob
import os
import re

from gen_common import Gen, PUB

G = Gen("spells2024", "SPELLS 2024")
SLOT = lambda n: f"SpellSlotsGroup:1:1:{n}"
SPELL_FLAGS = "IsSpell;HasVerbalComponent"


# ---------------------------------------------------------------- auras (Aura of Vitality's structure)
def aura(name, title, text, icon, buff_boosts, tick=None):
    key = name.upper()
    G.spell(f"Shout_{name}", title, text, {
        "SpellType": "Shout", "Level": "4", "SpellSchool": "Abjuration", "TargetConditions": "Self()", "AreaRadius": "9",
        "UseCosts": "ActionPoint:1;" + SLOT(4), "SpellProperties": f"ApplyStatus(SELF,{key}_AURA,100,100)",
        "SpellFlags": SPELL_FLAGS + ";IsConcentration", "VerbalIntent": "Buff"}, icon=icon)
    G.status(f"{key}_AURA", title, text, {
        "AuraRadius": "9", "AuraStatuses": f"IF((Ally() or Self()) and not Tagged('INANIMATE')):ApplyStatus({key}_BUFF)",
        "StackId": f"{key}_AURA", "StatusGroups": "SG_RemoveOnRespec"}, icon=icon)
    fields = {"Boosts": buff_boosts, "StackId": f"{key}_BUFF", "StatusPropertyFlags": "DisableCombatlog"}
    if tick:
        fields.update({"TickType": "StartTurn", "TickFunctors": tick})
    G.status(f"{key}_BUFF", title, None, fields, icon=icon)


aura("AuraOfLife", "Aura of Life",
     "A 30-foot aura: you and your allies in it have Resistance to Necrotic damage, and an ally with 0 Hit Points who starts its turn in it regains 1 Hit Point.",
     "Spell_Abjuration_DeathWard", "Resistance(Necrotic,Resistant)", tick="IF(IsDowned()):RegainHitPoints(1)")
aura("AuraOfPurity", "Aura of Purity",
     "A 30-foot aura: you and your allies in it have Resistance to Poison damage and Advantage on saving throws against being Charmed, Frightened, Paralyzed or Poisoned.",
     "Spell_Abjuration_ProtectionFromPoison",
     "Resistance(Poison,Resistant);Tag(CHARMED_ADV);Tag(FRIGHTENED_ADV);Tag(PARALYZED_ADV);Tag(POISONED_ADV)")

# ---------------------------------------------------------------- Ranger
G.spell("Projectile_ConjureVolley", "Conjure Volley",
        "Spectral ammunition rains on a 40-foot radius: each enemy there makes a Dexterity saving throw, taking 8d8 Force damage on a failure or half on a success.", {
            "Level": "5", "SpellSchool": "Conjuration", "TargetRadius": "45", "AreaRadius": "12", "ExplodeRadius": "12",
            "SpellRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())", "SpellSuccess": "DealDamage(8d8,Force,Magical)",
            "SpellFail": "DealDamage((8d8)/2,Force,Magical)", "TargetConditions": "Enemy() and not Dead()", "DamageType": "Force",
            "TooltipDamageList": "DealDamage(8d8,Force)", "TooltipAttackSave": "Dexterity", "UseCosts": "ActionPoint:1;" + SLOT(5),
            "SpellFlags": SPELL_FLAGS + ";HasSomaticComponent;HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold;IsHarmful;CanAreaDamageEvade"},
        using="Projectile_Fireball", icon="Action_Multiattack_Volley")
G.spell("Shout_SwiftQuiver", "Swift Quiver",
        "Concentration, 1 minute: when you cast it and as a Bonus Action until it ends, make two attacks with a bow or crossbow.", {
            "SpellType": "Shout", "Level": "5", "SpellSchool": "Transmutation", "TargetConditions": "Self()",
            "UseCosts": "BonusActionPoint:1;" + SLOT(5),
            "SpellProperties": "ApplyStatus(SELF,SWIFT_QUIVER,100,10);ApplyStatus(SELF,SWIFT_QUIVER_FIRST,100,1)",
            "SpellFlags": SPELL_FLAGS + ";HasSomaticComponent;IsConcentration"}, icon="Action_Multiattack_Volley")
G.status("SWIFT_QUIVER", "Swift Quiver", "As a Bonus Action, make two attacks with a bow or crossbow.",
         {"Boosts": "UnlockSpell(Projectile_SwiftQuiver_Volley)", "StackId": "SWIFT_QUIVER"}, icon="Action_Multiattack_Volley")
G.status("SWIFT_QUIVER_FIRST", "Swift Quiver", "The volley that comes with the casting.",
         {"Boosts": "UnlockSpell(Projectile_SwiftQuiver_Volley_Free)", "StackId": "SWIFT_QUIVER_FIRST",
          "StatusPropertyFlags": "DisableCombatlog;DisablePortraitIndicator"}, icon="Action_Multiattack_Volley")
for suffix, cost, extra in (("", "BonusActionPoint:1", ""), ("_Free", "", ";RemoveStatus(SELF,SWIFT_QUIVER_FIRST)")):
    G.spell(f"Projectile_SwiftQuiver_Volley{suffix}", "Swift Quiver: Volley", "Make two attacks with a bow or crossbow.", {
        "AmountOfTargets": "2", "UseCosts": cost, "SpellProperties": extra.lstrip(";") or None,
        "WeaponTypes": "Ammunition"}, using="Projectile_MainHandAttack", icon="Action_Multiattack_Volley")

# ---------------------------------------------------------------- Paladin 5th
G.spell("Target_Geas", "Geas",
        "A creature within 60 feet must succeed on a Wisdom saving throw or be Charmed by you for 30 days. Casting takes 1 minute (not in combat).", {
            "SpellType": "Target", "Level": "5", "SpellSchool": "Enchantment", "TargetRadius": "18",
            "TargetConditions": "Character() and not Self() and not Dead()", "RequirementConditions": "not Combat(context.Source)",
            "SpellRoll": "not SavingThrow(Ability.Wisdom, SourceSpellDC())", "SpellSuccess": "ApplyStatus(GEAS,100,-1)",
            "TooltipAttackSave": "Wisdom", "UseCosts": "ActionPoint:1;" + SLOT(5), "SpellFlags": SPELL_FLAGS + ";IsHarmful"},
        icon="Spell_Enchantment_DominatePerson")
G.status("GEAS", "Geas", "Charmed by the caster's command for 30 days.", {"StackId": "GEAS"}, using="CHARMED",
         comment="The 5d10 Psychic for acting against the command isn't implemented (docs/COVERAGE.md).")
G.spell("Teleportation_RaiseDead", "Raise Dead",
        "Revive a creature that died no more than 10 days ago with 1 Hit Point; poisons end. It takes a -4 penalty to D20 Tests, reduced by 1 each Long Rest. Casting takes 1 hour (not in combat).", {
            "Level": "5", "UseCosts": "ActionPoint:1;" + SLOT(5), "RequirementConditions": "not Combat(context.Source)",
            "OriginTargetConditions": "not Tagged('BLOCK_RESURRECTION') and not Self() and not Item() and Dead() and Tagged('PLAYABLE') and not Tagged('UNDEAD')",
            "OriginSpellProperties": "RegainHitPoints(1);Resurrect(100,1);RemoveStatus(POISONED);ApplyStatus(RAISE_DEAD_ORDEAL_4,100,-1);ApplyStatus(RESURRECTING,100,1)"},
        using="Teleportation_Revivify", icon="Spell_Necromancy_Revivify")
for n in (4, 3, 2, 1):
    G.status(f"RAISE_DEAD_ORDEAL_{n}", "Back from the Dead", f"-{n} to D20 Tests. The penalty drops by 1 after each Long Rest.", {
        "Boosts": f"RollBonus(Attack,-{n});RollBonus(SavingThrow,-{n});RollBonus(SkillCheck,-{n});RollBonus(RawAbility,-{n})",
        "OnRemoveFunctors": f"ApplyStatus(RAISE_DEAD_ORDEAL_{n - 1},100,-1)" if n > 1 else None, "StackId": "RAISE_DEAD_ORDEAL"},
        icon="Spell_Necromancy_Revivify", comment="Removed by a Long Rest (no IgnoreResting); the next step replaces it.")

# ---------------------------------------------------------------- Artificer 5th
SKILLS = ["Acrobatics", "AnimalHandling", "Arcana", "Athletics", "Deception", "History", "Insight", "Intimidation", "Investigation",
          "Medicine", "Nature", "Perception", "Performance", "Persuasion", "Religion", "SleightOfHand", "Stealth", "Survival"]
NICE = {"AnimalHandling": "Animal Handling", "SleightOfHand": "Sleight of Hand"}
G.spell("Target_SkillEmpowerment", "Skill Empowerment",
        "Touch a willing creature: for up to 1 hour (Concentration) it has Expertise in one skill of your choice.", {
            "SpellType": "Target", "Level": "5", "SpellSchool": "Transmutation", "TargetRadius": "1.5", "TargetConditions": "Character() and (Ally() or Self())",
            "ContainerSpells": ";".join(f"Target_SkillEmpowerment_{s}" for s in SKILLS), "SpellFlags": "IsLinkedSpellContainer",
            "UseCosts": "ActionPoint:1;" + SLOT(5)}, icon="Spell_Transmutation_EnhanceAbility")
for s in SKILLS:
    G.spell(f"Target_SkillEmpowerment_{s}", f"Skill Empowerment: {NICE.get(s, s)}", f"Expertise in {NICE.get(s, s)} for up to 1 hour.", {
        "SpellType": "Target", "Level": "5", "SpellSchool": "Transmutation", "SpellContainerID": "Target_SkillEmpowerment",
        "TargetRadius": "1.5", "TargetConditions": "Character() and (Ally() or Self())", "UseCosts": "ActionPoint:1;" + SLOT(5),
        "SpellProperties": f"ApplyStatus(SKILL_EMPOWERMENT_{s.upper()},100,600)", "SpellFlags": SPELL_FLAGS + ";HasSomaticComponent;IsConcentration"},
        icon="Spell_Transmutation_EnhanceAbility")
    G.status(f"SKILL_EMPOWERMENT_{s.upper()}", f"Skill Empowerment: {NICE.get(s, s)}", f"Expertise in {NICE.get(s, s)}.",
             {"Boosts": f"ExpertiseBonus({s})", "StackId": "SKILL_EMPOWERMENT"}, icon="Spell_Transmutation_EnhanceAbility")

# ---------------------------------------------------------------- lists (the Apotheosis lists auto-granted at 13/17)
LISTS = {
    "b88aff43-b75a-5947-b283-3c6ca5bf2591": ["Shout_AuraOfLife", "Shout_AuraOfPurity"],                        # Paladin 4th
    "bce36493-022a-5a20-8b8d-fd97f89be9a7": ["Target_Geas", "Teleportation_RaiseDead", "Target_SummonCelestial"],  # Paladin 5th
    "6b625ece-306d-576a-9fa2-896d884e4e05": ["Projectile_ConjureVolley", "Shout_SwiftQuiver"],                  # Ranger 5th
    "dfb36751-25c2-59d2-a021-69cdac534724": ["Target_SkillEmpowerment"],                                        # Artificer 5th
}


def patch_lists():
    path = os.path.join(PUB, "Lists", "SpellLists.lsx")
    s = open(path, encoding="utf-8").read()
    for uuid_, add in LISTS.items():
        m = re.search(rf'(<attribute id="Spells" type="LSString" value=")([^"]*)("/>\s*<attribute id="UUID" type="guid" value="{uuid_}")', s)
        assert m, uuid_
        have = [x for x in m.group(2).split(";") if x]
        s = s[:m.start(2)] + ";".join(have + [a for a in add if a not in have]) + s[m.end(2):]
    open(path, "w", encoding="utf-8", newline="").write(s)


if __name__ == "__main__":
    G.write_stats("Spells2024", "gen_spells_2024.py", "issue #10")
    patch_lists()
    G.patch_loca()
    print(f"{len(G.S)} statuses, {len(G.SP)} spells, {len(G.loca)} strings")
