"""True Polymorph follow-ups (issue #23) on top of the #20 build (Spell_HighLevel.txt / Status_BOOST.txt /
TruePolymorph.lua):
- Creature into creature, CR 7 forms (target level 7+): the four elemental Myrmidons and the Mind Flayer, from the
  base game's player shapeshift templates, on the Apotheosis_TruePolymorph rule (you keep your own HP) with
  temporary HP equal to the form's Vitality, as the #20 forms.
- Object into creature (CR 9 or lower, friendly to you): the target object turns into a Minotaur, Dire Wolf,
  Phase Spider or Shadow Mastiff that follows you; TruePolymorph.lua swaps the object for the creature, and back
  if Concentration ends before the hour is up.

Owns Stats/Generated/Data/{Status,Spell}_TruePolymorph.txt; patches Target_TruePolymorph's ContainerSpells.
Run: python3 Scripts/gen_true_polymorph.py
"""
import glob
import os
import re

from gen_common import Gen, DATA

G = Gen("truepolymorph", "TRUE POLYMORPH 23")
RULE = "95fbb220-88d3-417a-a6cb-782153f5584f"  # Apotheosis_TruePolymorph (Shapeshift/Rulebook.lsx)
ICON = "Spell_Transmutation_Polymorph"

# key, name, template, Vitality (temporary HP), minimum target level (= CR)
CREATURE_FORMS = [
    ("EARTHMYRMIDON", "Earth Myrmidon", "86b5ed60-c0a8-41d0-88a5-ed77985820eb", 103, 7),
    ("FIREMYRMIDON", "Fire Myrmidon", "9c5e77bc-0e65-4c11-865a-46d892cc06fe", 90, 7),
    ("AIRMYRMIDON", "Air Myrmidon", "3feb7490-c75e-446a-b8af-d459a164a0a6", 90, 7),
    ("WATERMYRMIDON", "Water Myrmidon", "6c9ea298-14dd-4485-ac3c-fdf818f6b110", 90, 7),
    ("MINDFLAYER", "Mind Flayer", "ba20ee39-92ed-4aad-830d-4871103f48c2", 150, 7),
]
OBJECT_FORMS = [  # creature templates that act on their own (the Devilish Ox forms)
    ("MINOTAUR", "Minotaur", "867c3061-624e-4b02-babb-a23e743fb5d3"),
    ("DIREWOLF", "Dire Wolf", "67f39af3-b9ea-4e95-8237-7aa4f6bd7cef"),
    ("PHASESPIDER", "Phase Spider", "5acff443-0e4f-4d26-ae1c-deb640d2f729"),
    ("SHADOWMASTIFF", "Shadow Mastiff", "94696b69-bd4b-4ddb-885a-51790025f758"),
]
CHILD = lambda key: f"Target_TruePolymorph_{key.title().replace('myrmidon', 'Myrmidon').replace('flayer', 'Flayer')}"

children = []
for key, name, template, hp, lvl in CREATURE_FORMS:
    st = f"TRUE_POLYMORPH_{key}"
    G.status(st, f"True Polymorph: {name}", f"Transformed into a {name}. You keep your Hit Points and have temporary Hit Points equal to the form's; the transformation ends when they run out.", {
        "StatusType": "POLYMORPHED", "TemplateID": template, "Rules": RULE, "StackId": "POLYMORPH"},
        using="HAV_DevilishOX_POLYMORPH_MINOTAUR", icon=ICON)
    G.status(st + "_PERMANENT", f"True Polymorph: {name}", f"Permanently transformed into a {name} (the caster held Concentration for the full hour).",
             {"StatusType": "POLYMORPHED"}, using=st, icon=ICON)
    G.status(f"TRUE_POLYMORPH_TEMPHP_{key}", f"{name} form", f"{hp} temporary Hit Points from the {name} form.", {
        "Boosts": f"TemporaryHP({hp})", "StackId": "TRUE_POLYMORPH_TEMPHP", "StackType": "Overwrite",
        "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"}, icon="statIcons_MAG_TemporaryHP")
    child = CHILD(key)
    children.append(child)
    G.spell(child, f"True Polymorph: {name}", f"A creature of level {lvl} or higher becomes a {name} (Wisdom save if unwilling).", {
        "SpellType": "Target", "SpellContainerID": "Target_TruePolymorph", "ContainerSpells": "",
        "TargetConditions": f"Character() and not Dead() and not IsImmuneToStatus('SG_Polymorph') and context.Target.Level >= {lvl}",
        "SpellRoll": "not SavingThrow(Ability.Wisdom, SourceSpellDC()) or Ally() or Self()",
        "SpellSuccess": f"ApplyStatus({st},100,600)", "TooltipStatusApply": f"ApplyStatus({st},100,600)",
        "SpellFail": "ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL_POLYMORPHED, 100, 0)", "ConcentrationSpellID": "Target_TruePolymorph"},
        using="Target_TruePolymorph", icon=ICON)

for key, name, template in OBJECT_FORMS:
    st = f"TRUE_POLYMORPH_OBJECT_{key}"
    G.status(st, f"True Polymorph: becoming a {name}", f"This object is a {name} that follows the caster.", {
        "StackId": "TRUE_POLYMORPH_OBJECT", "StatusPropertyFlags": "DisableOverhead;ApplyToDead"}, icon=ICON,
        comment=f"TruePolymorph.lua swaps the object for a {name} ({template}) while this lasts.")
    child = f"Target_TruePolymorph_Object{name.replace(' ', '')}"
    children.append(child)
    G.spell(child, f"True Polymorph: Object into {name}", f"A nonmagical object you can see (not worn or carried) becomes a {name} that is friendly to you.", {
        "SpellType": "Target", "SpellContainerID": "Target_TruePolymorph", "ContainerSpells": "",
        "TargetConditions": "Item() and not Dead()", "SpellRoll": "", "SpellSuccess": "", "SpellFail": "",
        "SpellProperties": f"ApplyStatus({st},100,600)", "TooltipStatusApply": f"ApplyStatus({st},100,600)",
        "ConcentrationSpellID": "Target_TruePolymorph", "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent;IsConcentration"},
        using="Target_TruePolymorph", icon=ICON)


def patch_container():
    path = os.path.join(DATA, "Spell_HighLevel.txt")
    s = open(path, encoding="utf-8").read()
    m = re.search(r'(new entry "Target_TruePolymorph"\r?\n(?:(?!new entry ).)*?data "ContainerSpells" ")([^"]*)(")', s, re.S)
    assert m, "Target_TruePolymorph ContainerSpells not found"
    have = [x for x in m.group(2).split(";") if x]
    s = s[:m.start(2)] + ";".join(have + [c for c in children if c not in have]) + s[m.end(2):]
    open(path, "w", encoding="utf-8", newline="").write(s)


if __name__ == "__main__":
    G.write_stats("TruePolymorph", "gen_true_polymorph.py", "issue #23")
    patch_container()
    G.patch_loca()
    print(f"{len(G.S)} statuses, {len(G.SP)} spells; container +{len(children)}")
