"""Generate the Epic Boons (PHB 2024 level-19 feats) - issue #1.

BG3 feats can't require a character level, so boons are a level-19 pick list (agreed 2026-09-30):
each PHB-class level-19 progression node gets
    SelectPassives(<EpicBoons>,1,EpicBoon);SelectPassives(<EpicBoonAbility>,1,EpicBoonAbility)
instead of the ordinary feat. The +1 ability is its own pick (Ability boosts aren't capped at 20, verified
in game). Boons that restrict the ability (Irresistible Offense: Str/Dex, Spell Recall: Int/Wis/Cha) come
as one entry per allowed ability with the +1 built in; for those the ability pick is "Included in my boon"
(EpicBoons.lua removes a doubled +1 and logs it).

Owns (rewritten every run): Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_EpicBoons.txt.
Patches idempotently (between markers / by UUID): Lists/PassiveLists.lsx, ActionResourceDefinitions,
Localization/English/PHB2024-Apotheosis.xml, Progressions.lsx (level-19 nodes).
Script Extender halves live in ScriptExtender/Lua/EpicBoons.lua.

Run: python3 Scripts/gen_epic_boons.py
"""
import glob
import os
import re
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = glob.glob(os.path.join(REPO, "Public", "*"))[0]
DATA = os.path.join(PUB, "Stats", "Generated", "Data")
LOCA = glob.glob(os.path.join(REPO, "Mods", "*", "Localization", "English", "PHB2024-Apotheosis.xml"))[0]
NS = uuid.NAMESPACE_URL


def gid(key):
    return str(uuid.uuid5(NS, "apotheosis-epicboon:" + key))


LOCA_ROWS = {}


def h(key, text):
    """Deterministic loca handle (h + 32 hex, the width this mod already uses) with its English text."""
    handle = "h" + uuid.uuid5(NS, "apotheosis-epicboon-loca:" + key).hex
    LOCA_ROWS[handle] = text
    return handle


ABILITIES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
SHORT = {"Strength": "Str", "Dexterity": "Dex", "Constitution": "Con", "Intelligence": "Int", "Wisdom": "Wis", "Charisma": "Cha"}
ENERGY = ["Acid", "Cold", "Fire", "Lightning", "Necrotic", "Poison", "Psychic", "Radiant", "Thunder"]
SKILLS = ["Acrobatics", "AnimalHandling", "Arcana", "Athletics", "Deception", "History", "Insight", "Intimidation",
          "Investigation", "Medicine", "Nature", "Perception", "Performance", "Persuasion", "Religion",
          "SleightOfHand", "Stealth", "Survival"]
SKILL_NAME = {"AnimalHandling": "Animal Handling", "SleightOfHand": "Sleight of Hand"}
NIGHT_RESIST = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison", "Slashing", "Thunder"]
DARK = "(HasObscuredState(ObscuredState.HeavilyObscured) or HasObscuredState(ObscuredState.LightlyObscured))"

RESOURCES = [  # name, max, replenish, display, description
    ("EpicBoonPeerlessAim", 1, "Turn", "Peerless Aim", "Turn a missed attack into a hit. Returns at the start of your turn."),
    ("EpicBoonFate", 1, "ShortRest", "Improve Fate", "Add or subtract 2d4 from a nearby d20 roll. Returns when you roll Initiative or finish a rest."),
    ("EpicBoonEnergyChoice", 2, "Rest", "Energy Resistance Choices", "Choose your two Boon of Energy Resistance damage types. Resets on a Long Rest."),
    ("EpicBoonRecoveryDie", 10, "Rest", "Recover Vitality Dice", "Your pool of ten d10s for Recover Vitality. Returns on a Long Rest."),
    ("EpicBoonExpertiseChoice", 1, "Never", "Boon of Skill Expertise", "Choose the skill you gain Expertise in."),
]


def entry(name, typ, fields, using=None, comment=None):
    out = ([f"// {comment}"] if comment else []) + [f'new entry "{name}"', f'type "{typ}"']
    if using:
        out.append(f'using "{using}"')
    out += [f'data "{k}" "{v}"' for k, v in fields.items() if v is not None]
    return "\n".join(out) + "\n"


P, S, SP, I = [], [], [], []  # passives, statuses, spells, interrupts
BOONS, ABILITY_PASSIVES = [], []


def boon(name, title, text, fields, variants=None):
    """variants: abilities the boon's own +1 may go to (restricted boons get one entry per ability)."""
    base = {"DisplayName": h(name + ":n", title), "Description": h(name + ":d", text),
            "Icon": fields.pop("Icon", "PassiveFeature_Generic_Magical"), "Properties": fields.pop("Properties", "Highlighted")}
    if not variants:
        P.append(entry(name, "PassiveData", {**base, **fields}))
        BOONS.append(name)
        return
    for ab in variants:
        vn = f"{name}_{SHORT[ab]}"
        boosts = ";".join(x for x in [f"Ability({ab},1)", fields.get("Boosts")] if x)
        P.append(entry(vn, "PassiveData", {**base, **fields, "Boosts": boosts,
                                             "DisplayName": h(vn + ":n", f"{title} (+1 {ab})")}))
        BOONS.append(vn)


# ---------------------------------------------------------------- PHB 2024 boons (phase 1)
boon("EpicBoon_CombatProwess", "Boon of Combat Prowess",
     "Peerless Aim: when you miss with an attack roll, you can hit instead. Once you use this, you can't again until the start of your next turn.",
     {"Boosts": "UnlockInterrupt(Interrupt_EpicBoon_PeerlessAim);ActionResource(EpicBoonPeerlessAim,1,0)"})
I.append(entry("Interrupt_EpicBoon_PeerlessAim", "InterruptData", {
    "DisplayName": h("PeerlessAim:n", "Peerless Aim"), "Description": h("PeerlessAim:d", "Your attack misses: hit instead."),
    "Icon": "PassiveFeature_Generic_Magical", "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self",
    "Container": "YesNoDecision",
    "Conditions": "not Dead(context.Observer) and HasInterruptedAttack() and Self(context.Observer,context.Source) and not AnyEntityIsItem() and IsFlatValueInterruptInteresting(99, context.Source)",
    "Properties": "AdjustRoll(OBSERVER_OBSERVER,99)", "Cost": "EpicBoonPeerlessAim:1", "InterruptDefaultValue": "Ask;Enabled"},
    comment="Boon of Combat Prowess. A natural 1 still misses (AdjustRoll can't override it) - documented gap."))

boon("EpicBoon_DimensionalTravel", "Boon of Dimensional Travel",
     "Blink Steps: immediately after you take the Attack action or the Magic action, you can teleport up to 30 feet to an unoccupied space you can see.",
     {"Boosts": None})
S.append(entry("EPIC_BLINK_STEPS", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("BlinkStatus:n", "Blink Steps"), "Description": h("BlinkStatus:d", "You can teleport up to 30 feet (free)."),
    "Icon": "Spell_Conjuration_MistyStep", "Boosts": "UnlockSpell(Target_EpicBoon_BlinkStep)", "StackId": "EPIC_BLINK_STEPS",
    "StatusPropertyFlags": "DisableCombatlog"}, comment="Applied by EpicBoons.lua after an Attack or Magic action (a cast costing an ActionPoint)."))
SP.append(entry("Target_EpicBoon_BlinkStep", "SpellData", {
    "SpellType": "Target", "Level": "0", "DisplayName": h("BlinkSpell:n", "Blink Step"),
    "Description": h("BlinkSpell:d", "Teleport up to 30 feet to an unoccupied space you can see."), "Icon": "Spell_Conjuration_MistyStep",
    "SpellProperties": "GROUND:TeleportSource();GROUND:RemoveStatus(SELF,EPIC_BLINK_STEPS)", "TargetRadius": "9",
    "TargetConditions": "CanStand('') and not Character() and not Self()", "RequirementConditions": "HasStatus('EPIC_BLINK_STEPS')",
    "UseCosts": "", "SpellFlags": "HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold", "CastTextEvent": "Cast"},
    using="Target_MistyStep"))

boon("EpicBoon_EnergyResistance", "Boon of Energy Resistance",
     "Energy Resistances: choose two of Acid, Cold, Fire, Lightning, Necrotic, Poison, Psychic, Radiant and Thunder (the choices reset on a Long Rest). Energy Redirection: when you take damage of a chosen type, your Reaction sends 2d12 + Constitution modifier of that type at the attacker (Dexterity save, DC 8 + Constitution modifier + Proficiency Bonus).",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_EnergyResistance);ActionResource(EpicBoonEnergyChoice,2,0)",
      "StatsFunctorContext": "OnLongRest", "StatsFunctors": ";".join(f"RemoveStatus(SELF,EPIC_ENERGY_RES_{t.upper()})" for t in ENERGY)})
SP.append(entry("Shout_EpicBoon_EnergyResistance", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("EnergyChoose:n", "Energy Resistance"),
    "Description": h("EnergyChoose:d", "Choose a damage type to resist (two per Long Rest)."), "Icon": "Spell_Abjuration_ProtectionFromEnergy",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_EnergyResistance_{t}" for t in ENERGY), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "EpicBoonEnergyChoice:1", "TargetConditions": "Self()"}))
for t in ENERGY:
    SP.append(entry(f"Shout_EpicBoon_EnergyResistance_{t}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_EnergyResistance",
        "DisplayName": h(f"EnergyChoose{t}:n", f"Energy Resistance: {t}"), "Description": h(f"EnergyChoose{t}:d", f"You resist {t} damage until your next Long Rest."),
        "Icon": "Spell_Abjuration_ProtectionFromEnergy", "UseCosts": "EpicBoonEnergyChoice:1", "TargetConditions": "Self()",
        "RequirementConditions": f"not HasStatus('EPIC_ENERGY_RES_{t.upper()}')",
        "SpellProperties": f"ApplyStatus(SELF,EPIC_ENERGY_RES_{t.upper()},100,-1)"}))
    S.append(entry(f"EPIC_ENERGY_RES_{t.upper()}", "StatusData", {
        "StatusType": "BOOST", "DisplayName": h(f"EnergyRes{t}:n", f"Energy Resistance: {t}"),
        "Description": h(f"EnergyRes{t}:d", f"Resistant to {t} damage; your Reaction can redirect it (Boon of Energy Resistance)."),
        "Icon": "Spell_Abjuration_ProtectionFromEnergy", "Boosts": f"Resistance({t},Resistant)", "StackId": f"EPIC_ENERGY_RES_{t.upper()}",
        "StatusPropertyFlags": "IgnoreResting"}))
    SP.append(entry(f"Target_EpicBoon_EnergyRedirection_{t}", "SpellData", {
        "SpellType": "Target", "Level": "0", "DisplayName": h(f"Redirect{t}:n", f"Energy Redirection ({t})"),
        "Description": h(f"Redirect{t}:d", f"Redirect {t} damage: 2d12 + Constitution modifier, Dexterity save."),
        "Icon": "Spell_Abjuration_ProtectionFromEnergy", "TargetRadius": "18", "TargetConditions": "Character() and not Dead() and not Self()",
        "SpellRoll": "not SavingThrow(Ability.Dexterity, 8+ConstitutionModifier+ProficiencyBonus)",
        "SpellSuccess": f"DealDamage(2d12+ConstitutionModifier,{t},Magical)", "TooltipDamageList": f"DealDamage(2d12+ConstitutionModifier,{t})",
        "TooltipAttackSave": "Dexterity", "UseCosts": "", "SpellFlags": "IsHarmful", "CastTextEvent": "Cast"},
        comment="Cast by EpicBoons.lua (spends your Reaction) at whoever dealt the damage." if t == ENERGY[0] else None))

boon("EpicBoon_Fate", "Boon of Fate",
     "Improve Fate: when you or a creature within 60 feet succeeds on or fails a d20 roll, you can roll 2d4 and add it to or subtract it from the roll. Usable again when you roll Initiative or finish a Short or Long Rest.",
     {"Boosts": "UnlockInterrupt(Interrupt_EpicBoon_Fate_AllyAttack);UnlockInterrupt(Interrupt_EpicBoon_Fate_AllySave);"
                "UnlockInterrupt(Interrupt_EpicBoon_Fate_EnemyAttack);UnlockInterrupt(Interrupt_EpicBoon_Fate_EnemySave);ActionResource(EpicBoonFate,1,0)"})
for key, cond, sign, label in [
        ("AllyAttack", "HasInterruptedAttack() and (Self(context.Observer,context.Source) or Ally(context.Source,context.Observer))", "", "Improve Fate: bless an attack"),
        ("AllySave", "HasInterruptedSavingThrow() and (Self(context.Observer,context.Target) or Ally(context.Target,context.Observer))", "", "Improve Fate: bless a save"),
        ("EnemyAttack", "HasInterruptedAttack() and Enemy(context.Source,context.Observer)", "0-", "Improve Fate: curse an attack"),
        ("EnemySave", "HasInterruptedSavingThrow() and Enemy(context.Target,context.Observer)", "0-", "Improve Fate: curse a save")]:
    I.append(entry(f"Interrupt_EpicBoon_Fate_{key}", "InterruptData", {
        "DisplayName": h(f"Fate{key}:n", label), "Description": h(f"Fate{key}:d", ("Add" if not sign else "Subtract") + " 2d4 to the roll."),
        "Icon": "PassiveFeature_Generic_Magical", "InterruptContext": "OnPostRoll", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
        "Conditions": f"not Dead(context.Observer) and {cond} and not AnyEntityIsItem() and IsFlatValueInterruptInteresting(8)",
        "Properties": f"AdjustRoll(OBSERVER_OBSERVER,{sign}2d4)", "Cost": "EpicBoonFate:1", "InterruptDefaultValue": "Ask;Enabled"}))

boon("EpicBoon_Fortitude", "Boon of Fortitude",
     "Fortified Health: your Hit Point maximum increases by 40. Whenever you regain Hit Points, you regain extra Hit Points equal to your Constitution modifier (once per turn).",
     {"Boosts": "IncreaseMaxHP(40)", "StatsFunctorContext": "OnHealed",
      "StatsFunctors": "IF(not HasStatus('EPIC_FORTITUDE_USED')):ApplyStatus(SELF,EPIC_FORTITUDE_HEAL,100,0)"})
S.append(entry("EPIC_FORTITUDE_HEAL", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("FortHeal:n", "Fortified Health"), "Icon": "PassiveFeature_Generic_Magical",
    "OnApplyFunctors": "ApplyStatus(EPIC_FORTITUDE_USED,100,1);RegainHitPoints(max(1,ConstitutionModifier))",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"}))
S.append(entry("EPIC_FORTITUDE_USED", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("FortUsed:n", "Fortified Health used"), "Icon": "PassiveFeature_Generic_Magical",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"}))

boon("EpicBoon_IrresistibleOffense", "Boon of Irresistible Offense",
     "Overcome Defenses: your Bludgeoning, Piercing and Slashing damage ignores Resistance. Overwhelming Strike: when you roll a 20 on an attack roll, deal extra damage equal to the ability score this boon increased.",
     {"Boosts": "IgnoreResistance(Bludgeoning,Resistant);IgnoreResistance(Piercing,Resistant);IgnoreResistance(Slashing,Resistant)",
      "StatsFunctorContext": "OnAttack", "StatsFunctors": "IF(IsCritical()):ApplyStatus(EPIC_OVERWHELMING_MARK,100,0)"},
     variants=["Strength", "Dexterity"])
S.append(entry("EPIC_OVERWHELMING_MARK", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("Overwhelm:n", "Overwhelming Strike"), "Icon": "PassiveFeature_Generic_Magical",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Marks a critical hit's target; EpicBoons.lua deals the extra damage (= the boosted ability score)."))

boon("EpicBoon_Recovery", "Boon of Recovery",
     "Last Stand: when you would drop to 0 Hit Points, you drop to 1 instead and regain half your Hit Point maximum (once per Long Rest). Recover Vitality: a pool of ten d10s; as a Bonus Action, spend dice and regain that many Hit Points.",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_RecoverVitality);ActionResource(EpicBoonRecoveryDie,10,0)",
      "StatsFunctorContext": "OnCreate;OnLongRest", "StatsFunctors": "ApplyStatus(SELF,EPIC_LAST_STAND,100,-1)",
      "Properties": "Highlighted;OncePerLongRest"})
S.append(entry("EPIC_LAST_STAND", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("LastStand:n", "Last Stand"), "Description": h("LastStand:d", "The next time you would drop to 0 Hit Points, you drop to 1 and regain half your Hit Point maximum."),
    "Icon": "PassiveFeature_RelentlessEndurance", "Boosts": "DownedStatus(EPIC_LAST_STAND_DOWNED,6)", "StackId": "EPIC_LAST_STAND",
    "StatusGroups": "SG_RemoveOnRespec", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead;IgnoreResting"},
    comment="Boon of Recovery, cloned from Relentless Endurance (priority 6 beats it). EpicBoons.lua heals to 1 + half max HP."))
S.append(entry("EPIC_LAST_STAND_DOWNED", "StatusData", {
    "OnApplyFunctors": "RemoveStatus(EPIC_LAST_STAND);RegainHitPoints(1,Guaranteed)"}, using="RELENTLESS_ENDURANCE_DOWNED"))
SP.append(entry("Shout_EpicBoon_RecoverVitality", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Vitality:n", "Recover Vitality"),
    "Description": h("Vitality:d", "Spend d10s from your Recover Vitality pool to regain Hit Points."), "Icon": "Action_SecondWind",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_RecoverVitality_{n}" for n in (1, 2, 3, 5, 10)), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "BonusActionPoint:1;EpicBoonRecoveryDie:1", "TargetConditions": "Self()"}))
for n in (1, 2, 3, 5, 10):
    SP.append(entry(f"Shout_EpicBoon_RecoverVitality_{n}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_RecoverVitality",
        "DisplayName": h(f"Vitality{n}:n", f"Recover Vitality ({n}d10)"), "Description": h(f"Vitality{n}:d", f"Spend {n} dice: regain {n}d10 Hit Points."),
        "Icon": "Action_SecondWind", "UseCosts": f"BonusActionPoint:1;EpicBoonRecoveryDie:{n}", "TargetConditions": "Self()",
        "SpellProperties": f"RegainHitPoints({n}d10)", "TooltipDamageList": f"RegainHitPoints({n}d10)"}))

boon("EpicBoon_Skill", "Boon of Skill",
     "All-Around Adept: you gain proficiency in all skills. Expertise: choose one skill in which you lack Expertise and gain Expertise in it.",
     {"Boosts": ";".join(f"ProficiencyBonus(Skill,{s})" for s in SKILLS) + ";UnlockSpell(Shout_EpicBoon_Expertise);ActionResource(EpicBoonExpertiseChoice,1,0)"})
SP.append(entry("Shout_EpicBoon_Expertise", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Expertise:n", "Boon of Skill: Expertise"),
    "Description": h("Expertise:d", "Choose one skill to gain Expertise in (once)."), "Icon": "PassiveFeature_Generic_Magical",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_Expertise_{s}" for s in SKILLS), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "EpicBoonExpertiseChoice:1", "TargetConditions": "Self()"}))
for s_ in SKILLS:
    nm = SKILL_NAME.get(s_, s_)
    SP.append(entry(f"Shout_EpicBoon_Expertise_{s_}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_Expertise",
        "DisplayName": h(f"Expertise{s_}:n", f"Expertise: {nm}"), "Description": h(f"Expertise{s_}:d", f"Gain Expertise in {nm}."),
        "Icon": "PassiveFeature_Generic_Magical", "UseCosts": "EpicBoonExpertiseChoice:1", "TargetConditions": "Self()",
        "SpellProperties": f"ApplyStatus(SELF,EPIC_EXPERTISE_{s_.upper()},100,-1)"}))
    S.append(entry(f"EPIC_EXPERTISE_{s_.upper()}", "StatusData", {
        "StatusType": "BOOST", "DisplayName": h(f"ExpertiseSt{s_}:n", f"Expertise: {nm}"), "Icon": "PassiveFeature_Generic_Magical",
        "Boosts": f"ExpertiseBonus({s_})", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;IgnoreResting"}))

boon("EpicBoon_Speed", "Boon of Speed",
     "Escape Artist: as a Bonus Action, you can take the Disengage action, which also ends the Grappled condition on you. Quickness: your Speed increases by 30 feet.",
     {"Boosts": "ActionResource(Movement,9,0);UnlockSpell(Shout_EpicBoon_EscapeArtist)"})
SP.append(entry("Shout_EpicBoon_EscapeArtist", "SpellData", {
    "DisplayName": h("Escape:n", "Escape Artist"), "Description": h("Escape:d", "Disengage as a Bonus Action and end the Grappled condition on yourself."),
    "SpellProperties": "ApplyStatus(DISENGAGE,100,1);RemoveStatus(SELF,GRAPPLED)"}, using="Shout_Disengage_BonusAction"))

boon("EpicBoon_SpellRecall", "Boon of Spell Recall",
     "Free Casting: whenever you cast a spell with a level 1-4 spell slot, roll 1d4. If the number matches the slot's level, the slot isn't expended. (Requires the Spellcasting feature.)",
     {"Boosts": None}, variants=["Intelligence", "Wisdom", "Charisma"])

boon("EpicBoon_NightSpirit", "Boon of the Night Spirit",
     "Merge with Shadows: while in Dim Light or Darkness, you can become Invisible as a Bonus Action until you take an action, Bonus Action or Reaction. Shadowy Form: while in Dim Light or Darkness, you resist all damage except Psychic and Radiant.",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_MergeWithShadows);" + ";".join(f"IF({DARK}):Resistance({t},Resistant)" for t in NIGHT_RESIST)})
SP.append(entry("Shout_EpicBoon_MergeWithShadows", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Merge:n", "Merge with Shadows"),
    "Description": h("Merge:d", "In Dim Light or Darkness: become Invisible until you act."), "Icon": "Action_Monk_CloakOfShadows",
    "UseCosts": "BonusActionPoint:1", "TargetConditions": "Self()", "RequirementConditions": DARK,
    "SpellProperties": "ApplyStatus(SELF,EPIC_MERGE_WITH_SHADOWS,100,-1)", "SpellFlags": "Invisible", "CastTextEvent": "Cast"}))
S.append(entry("EPIC_MERGE_WITH_SHADOWS", "StatusData", {
    "DisplayName": h("MergeSt:n", "Merged with Shadows"), "Description": h("MergeSt:d", "Invisible until you take an action, Bonus Action or Reaction.")},
    using="CLOAK_OF_SHADOWS_MONK"))

boon("EpicBoon_Truesight", "Boon of Truesight", "Truesight: you have Truesight with a range of 60 feet.",
     {"StatsFunctorContext": "OnCreate;OnLongRest;OnShortRest", "StatsFunctors": "ApplyStatus(SELF,TRUESIGHT,100,-1)"})

# ---------------------------------------------------------------- ability pick
for ab in ABILITIES:
    n = f"EpicBoonAbility_{SHORT[ab]}"
    P.append(entry(n, "PassiveData", {"DisplayName": h(n + ":n", f"Epic Boon: +1 {ab}"),
                                      "Description": h(n + ":d", f"Increase your {ab} score by 1 (to a maximum of 30)."),
                                      "Icon": "PassiveFeature_Generic_Magical", "Properties": "Highlighted", "Boosts": f"Ability({ab},1)"}))
    ABILITY_PASSIVES.append(n)
P.append(entry("EpicBoonAbility_InBoon", "PassiveData", {
    "DisplayName": h("InBoon:n", "Epic Boon: increase included in my boon"),
    "Description": h("InBoon:d", "Pick this if your boon already names its ability, e.g. Boon of Irresistible Offense (+1 Strength)."),
    "Icon": "PassiveFeature_Generic_Magical", "Properties": None}))
ABILITY_PASSIVES.append("EpicBoonAbility_InBoon")

BOON_LIST, ABILITY_LIST = gid("list:boons"), gid("list:ability")


# ---------------------------------------------------------------- write / patch
def write_stats():
    head = ("// GENERATED by Scripts/gen_epic_boons.py (Epic Boons, issue #1) - edit the generator, not this file.\n"
            "// Script Extender half: ScriptExtender/Lua/EpicBoons.lua\n\n")
    for fname, rows in (("Passive_EpicBoons.txt", P), ("Status_EpicBoons.txt", S), ("Spell_EpicBoons.txt", SP), ("Interrupt_EpicBoons.txt", I)):
        with open(os.path.join(DATA, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(head + "\n".join(rows))


def patch_between(path, start, end, block, anchor):
    s = open(path, encoding="utf-8").read()
    if start in s:
        s = s[:s.index(start)] + block + s[s.index(end) + len(end):]
    else:
        i = s.rindex(anchor)
        s = s[:i] + block + s[i:]
    open(path, "w", encoding="utf-8", newline="").write(s)


def patch_lists():
    path = os.path.join(PUB, "Lists", "PassiveLists.lsx")
    block = ("                <!-- EPIC BOONS BEGIN (Scripts/gen_epic_boons.py) -->\n"
             f"""                <node id="PassiveList">
                    <attribute id="Name" type="FixedString" value="EpicBoons"/>
                    <attribute id="Passives" type="LSString" value="{','.join(BOONS)}"/>
                    <attribute id="UUID" type="guid" value="{BOON_LIST}"/>
                </node>
                <node id="PassiveList">
                    <attribute id="Name" type="FixedString" value="EpicBoonAbility"/>
                    <attribute id="Passives" type="LSString" value="{','.join(ABILITY_PASSIVES)}"/>
                    <attribute id="UUID" type="guid" value="{ABILITY_LIST}"/>
                </node>
                <!-- EPIC BOONS END -->
""")
    patch_between(path, "                <!-- EPIC BOONS BEGIN", "<!-- EPIC BOONS END -->\n", block, "            </children>")


def patch_resources():
    path = glob.glob(os.path.join(PUB, "ActionResourceDefinitions", "*.lsx"))[0]
    rows = []
    for name, mx, rep, disp, desc in RESOURCES:
        rows.append(f"""                <node id="ActionResourceDefinition">
                    <attribute id="DisplayName" type="TranslatedString" handle="{h('res:' + name + ':n', disp)}" version="1"/>
                    <attribute id="Description" type="TranslatedString" handle="{h('res:' + name + ':d', desc)}" version="1"/>
                    <attribute id="IsHidden" type="bool" value="false"/>
                    <attribute id="MaxLevel" type="uint32" value="0"/>
                    <attribute id="MaxValue" type="uint32" value="{mx}"/>
                    <attribute id="Name" type="FixedString" value="{name}"/>
                    <attribute id="ReplenishType" type="FixedString" value="{rep}"/>
                    <attribute id="ShowOnActionResourcePanel" type="bool" value="true"/>
                    <attribute id="UUID" type="guid" value="{gid('res:' + name)}"/>
                </node>
""")
    block = "                <!-- EPIC BOONS BEGIN (Scripts/gen_epic_boons.py) -->\n" + "".join(rows) + "                <!-- EPIC BOONS END -->\n"
    patch_between(path, "                <!-- EPIC BOONS BEGIN", "<!-- EPIC BOONS END -->\n", block, "            </children>")


def patch_loca():
    s = open(LOCA, encoding="utf-8").read()
    s = re.sub(r'  <content contentuid="(h[0-9a-f]{32})" version="\d+">[^<]*</content>\n',
               lambda m: "" if m.group(1) in LOCA_ROWS else m.group(0), s)
    def esc(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rows = "".join(f'  <content contentuid="{k}" version="1">{esc(v)}</content>\n' for k, v in LOCA_ROWS.items())
    i = s.rindex("</contentList>")
    s = s[:i] + rows + s[i:]
    assert "<!--" not in s, "loca must not contain XML comments (Toolkit crash)"
    open(LOCA, "w", encoding="utf-8", newline="").write(s)


PHB_CLASSES = {"Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"}


def patch_progressions():
    path = os.path.join(PUB, "Progressions", "Progressions.lsx")
    s = open(path, encoding="utf-8").read()
    sel = f"SelectPassives({BOON_LIST},1,EpicBoon);SelectPassives({ABILITY_LIST},1,EpicBoonAbility)"
    done = []

    def fix(m):
        b = m.group(0)
        name = re.search(r'id="Name" type="LSString" value="([^"]*)"', b)
        lvl = re.search(r'id="Level" type="uint8" value="(\d+)"', b)
        if not (name and lvl and name.group(1) in PHB_CLASSES and lvl.group(1) == "19") or "IsMulticlass" in b:
            return b
        b = re.sub(r'\s*<attribute id="AllowImprovement" type="bool" value="true"/>', "", b)
        if 'id="Selectors"' in b:
            def merged(mm):
                keep = [x for x in mm.group(2).split(";") if x and "EpicBoon" not in x]
                return mm.group(1) + ";".join(keep + [sel]) + mm.group(3)
            b = re.sub(r'(id="Selectors" type="LSString" value=")([^"]*)(")', merged, b)
        else:
            b = re.sub(r'(\s*)(<attribute id="TableUUID")', lambda mm: f'{mm.group(1)}<attribute id="Selectors" type="LSString" value="{sel}"/>{mm.group(1)}{mm.group(2)}', b, count=1)
        done.append(name.group(1))
        return b

    s = re.sub(r'<node id="Progression">(?:(?!</node>).)*?</node>', fix, s, flags=re.S)
    open(path, "w", encoding="utf-8", newline="").write(s)
    return done


if __name__ == "__main__":
    write_stats()
    patch_lists()
    patch_resources()
    patch_loca()
    classes = patch_progressions()
    print(f"{len(BOONS)} boon entries, {len(ABILITY_PASSIVES)} ability options, {len(P)} passives, {len(S)} statuses, "
          f"{len(SP)} spells, {len(I)} interrupts, {len(LOCA_ROWS)} strings; level 19 set for {sorted(classes)}")
