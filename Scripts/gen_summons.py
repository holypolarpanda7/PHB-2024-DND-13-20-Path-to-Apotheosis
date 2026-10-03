"""PHB 2024 summon spells for issue #10, as new creatures (dnd55e-style): each creature form is its own root template
(RootTemplates/Apotheosis_Summons.lsf) with its own Character stats, and the spell level is applied on summoning as a
per-level status (the dnd55e Spiritual Weapon pattern): your Proficiency Bonus, your spell attack modifier and save
DC, and the stat block's "+ spell level" rows (AC, HP, damage, Multiattack).

Pass 1: Summon Elemental (Air/Earth/Fire/Water) and Summon Construct (Clay/Metal/Stone).

AC: the engine adds the Dexterity modifier to the `Armor` stat, so Armor = stat-block AC - Dex modifier.

Attacks: the Slam is the creature's unarmed attack, so the engine's Extra Attack gives the Multiattack. The creature
attacks with an ability whose modifier is +0 (Wisdom), so with your PB and spellcasting modifier added the attack
bonus equals your spell attack modifier.

Models: every creature's look comes from MODELS below (a base-game template for now). Swap a parent to give a form a
new model or effects - nothing else references it.

Spell lists: dnd55e's class lists are overridden by UUID with their current contents plus these spells (re-run after
syncing dnd55e), and the Apotheosis-owned lists (WizardUpToL7-9, Apotheosis Ranger SLevel 4) get them too.

Owns Stats/Generated/Data/{Character,Status,Spell,Passive,Interrupt}_Summons.txt and RootTemplates/Apotheosis_Summons.lsf.
Run: python3 Scripts/gen_summons.py
"""
import glob
import os
import re

from gen_common import Gen, PUB, DND, TARGET_ANIM

G = Gen("summons", "SUMMONS 10")
SLOT = lambda n: f"SpellSlotsGroup:1:1:{n}"
RES_TYPES = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison", "Psychic",
             "Radiant", "Slashing", "Thunder"]
PB = "ProficiencyBonusOverride(Owner.LevelMapValue(StandardProficiencyBonusScale))"
CASTER = f"{PB};RollBonus(Attack,Owner.SpellCastingAbilityModifier);SpellSaveDC(Owner.SpellCastingAbilityModifier)"
EXTRA_ATTACK = {1: "", 2: "ExtraAttack", 3: "ExtraAttack_2", 4: "ExtraAttack_3"}

# Placeholder models: base-game templates the new creatures inherit their look, sounds and effects from.
MODELS = {
    "ElementalAir": "284b9c7f-1e04-48b7-af41-9029d1fa753c",    # Elemental_Air_ConjureElemental
    "ElementalEarth": "2ad47124-e41a-460e-b97a-f8e9efd32ed8",  # Elemental_Earth_ConjureElemental
    "ElementalFire": "88a6c664-877c-4d6e-81ad-dd377df2634e",   # Elemental_Fire_ConjureElemental
    "ElementalWater": "f21e144a-3237-4faa-a99c-a15e1937bc2c",  # Elemental_Water_ConjureElemental
    "ConstructClay": "6597824a-fc73-474a-b594-b3bbd8591016",   # Construct_FleshGolem
    "ConstructMetal": "f1662ccf-44cb-4e27-8810-ca2d3eea2adf",  # dnd55e AnimatedArmor_SteelDefender
    "ConstructStone": "b5bd29ba-8105-4123-920f-a2c64a4e1dfc",  # Myrmidon_Earth_ConjureElemental
}


def resistances(res=(), immune=()):
    return {f"{t}Resistance": "Immune" if t in immune else "Resistant" if t in res else "" for t in RES_TYPES}


def slam(name, title, dice, dtype, icon, text, base_level):
    """The Slam: `dice` + the spell's level, one variant per level (`name`_N) that the creature's level status
    unlocks. Not a DamageBonus boost (it would add to everything the creature deals, e.g. Heated Body's retaliation)
    and not a condition on the caster's level status (a summon's attack runs with you, the summoner, as its source:
    found 2026-10-02)."""
    for lvl in range(base_level, 10):
        G.spell(f"{name}_{lvl}", title, text, {
            "SpellType": "Target", "SpellRoll": "Attack(AttackType.MeleeUnarmedAttack)",
            "SpellSuccess": f"DealDamage({dice}+{lvl},{dtype},Magical)", "TooltipDamageList": f"DealDamage({dice}+{lvl},{dtype})",
            "TooltipAttackSave": "MeleeUnarmedAttack", "DamageType": dtype, "VerbalIntent": "Damage"},
            using="Target_UnarmedAttack", icon=icon)


def level_status(kind, form, lvl):
    return f"APO_{kind.upper()}SPIRIT_{form.upper()}_{lvl}"


def spirit(kind, form, title, char, skills, base_level, ac_step, hp_step, slam_name, statuses_extra=""):
    """One summonable form: Character stats, root template and the per-level statuses (levels base..9)."""
    stats = f"Apo_{kind}Spirit_{form}"
    G.character(stats, char, using="_Base")
    tpl = G.template(f"{kind}{form}", stats, MODELS[f"{kind}{form}"], stats, title, skills=skills, level=9,
                     spellset="CommonSummonActions")
    levels = {}
    for lvl in range(base_level, 10):
        st = level_status(kind, form, lvl)
        up = lvl - base_level
        extra = EXTRA_ATTACK[lvl // 2]
        G.status(st, f"Level {lvl} {title}", f"Summoned with a level {lvl} spell slot: uses your Proficiency Bonus, spell attack modifier and spell save DC.", {
            "Boosts": f"{CASTER};AC({up});IncreaseMaxHP({hp_step * up});UnlockSpell({slam_name}_{lvl})" + statuses_extra.format(lvl=lvl),
            "Passives": extra or None, "StackId": f"APO_{kind.upper()}SPIRIT_LEVEL",
            "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead"}, icon="Spell_Conjuration_ConjureElemental")
        levels[lvl] = st
    return tpl, levels


def summon_spell(root, title, text, school, base_level, forms, icon, radius="18", fields=None):
    """Linked container `root` with one child per form; each child has upcast variants base+1..9 (dnd55e/base
    Spiritual Weapon layout: Child_N with RootSpellID=Child, SpellContainerID=root, PowerLevel=N)."""
    children = [f"{root}_{f}" for f, *_ in forms]
    common = {"SpellType": "Target", "Level": str(base_level), "SpellSchool": school, "TargetRadius": radius,
              "UseCosts": "ActionPoint:1;" + SLOT(base_level), "VerbalIntent": "Summon",
              "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;CannotTargetItems;CannotTargetCharacter;IsConcentration",
              "SpellAnimation": "6f42f5f3-7a5a-4441-a02e-71b0450ac4b7,,;,,;c0513845-6e0e-42e8-9a8c-baa5e2b6ead6,,;fbf20742-9dbf-475b-9ff5-42e4b08064ad,,;42aaefdc-cf9b-4249-b159-285041851f69,,;,,;20e11c98-fff9-4417-88de-5bcc2368a1bd,,;,,;,,",
              "PrepareEffect": "7e42016a-29f9-4922-908b-dbf010dff168", "CastEffect": "ebd046f7-066f-4acf-b671-dd451201c58b",
              "PositionEffect": "37218caf-c844-479e-830e-d4c3fc2b9591", "PrepareSound": "Spell_Prepare_ClericSummon_Gen",
              "PrepareLoopSound": "Spell_Loop_ClericSummon_Gen", "CastSound": "Spell_Cast_Summon_PlanarAlly_L6to8",
              "MemoryCost": "1", **(fields or {})}
    G.spell(root, title, text, {**common, "ContainerSpells": ";".join(children),
                                "SpellFlags": common["SpellFlags"] + ";IsLinkedSpellContainer"}, icon=icon)
    for (form, ftitle, tpl, levels, extra_status), child in zip(forms, children):
        props = lambda lvl: (f"GROUND:Summon({tpl},-1,Projectile_AiHelper_Summon_Strong,,'{root}Stack',{levels[lvl]},"
                             f"UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK{',' + extra_status if extra_status else ''})")
        G.spell(child, f"{title}: {ftitle}", text, {
            **common, "SpellContainerID": root, "SpellProperties": props(base_level),
            "TargetConditions": f"CanStand('{tpl}') and not Character() and not Self()"}, icon=icon)
        for lvl in range(base_level + 1, 10):
            G.spell(f"{child}_{lvl}", f"{title}: {ftitle}", text, {
                "SpellProperties": props(lvl), "UseCosts": "ActionPoint:1;" + SLOT(lvl), "RootSpellID": child,
                "PowerLevel": str(lvl)}, using=child, icon=icon)
    return root


# ================================================================ Summon Elemental (level 4)
ELEMENTS = [  # form, damage type, resistances, immunities, extra skills
    ("Air", "Lightning", ("Lightning", "Thunder"), ("Poison",), ["Projectile_Fly"]),
    ("Earth", "Bludgeoning", ("Piercing", "Slashing"), ("Poison",), []),
    ("Fire", "Fire", (), ("Fire", "Poison"), []),
    ("Water", "Cold", ("Acid",), ("Poison",), []),
]
ELEMENTAL_TEXT = ("You call forth an Elemental spirit of the chosen element (Concentration, up to 1 hour). It uses your Proficiency "
                  "Bonus, spell attack modifier and spell save DC; AC 11 + the spell's level, 50 HP + 10 for each level above 4, "
                  "and a number of Slam attacks equal to half the spell's level (1d10 + 4 + the spell's level).")
el_forms = []
for el, dtype, res, imm, skills in ELEMENTS:
    sl = f"Target_ApoElementalSpirit_Slam_{el}"
    slam(sl, "Slam", "1d10+4", dtype, f"Action_Monster_Elemental{el}_MultiAttack" if el != "Earth" else "Action_Monster_ElementalEarth_MultiAttack",
         f"Melee attack with your spell attack modifier: 1d10 + 4 + the spell's level {dtype} damage.", 4)
    char = {"Level": "9", "Strength": "18", "Dexterity": "15", "Constitution": "17", "Intelligence": "4", "Wisdom": "10",
            "Charisma": "16", "Armor": "13", "ArmorType": "None", "Vitality": "50",
            "ActionResources": "ActionPoint:1;BonusActionPoint:1;Movement:12;ReactionActionPoint:1",
            "UnarmedAttackAbility": "Wisdom", "UnarmedRangedAttackAbility": "Wisdom", "SpellCastingAbility": "Wisdom",
            "DarkvisionRange": "18", "Passives": "AttackOfOpportunity;Darkvision;DarknessRules;ShortResting",
            "PersonalStatusImmunities": "SG_Paralyzed;SG_Petrified;PETRIFIED;SG_Poisoned",
            "DifficultyStatuses": "STATUS_EASY:PLAYER_BONUSES_EASYMODE", **resistances(res, imm)}
    tpl, levels = spirit("Elemental", el, f"{el} Elemental Spirit", char, ["Shout_Dodge"] + skills, 4, 1, 10, sl)
    el_forms.append((el, el, tpl, levels, None))
summon_spell("Target_ApoSummonElemental", "Summon Elemental", ELEMENTAL_TEXT, "Conjuration", 4, el_forms,
             "Spell_Conjuration_ConjureElemental")

# ================================================================ Summon Construct (level 4)
CONSTRUCT_TEXT = ("You call forth the spirit of a Construct made of Clay, Metal or Stone (Concentration, up to 1 hour). It uses your "
                  "Proficiency Bonus, spell attack modifier and spell save DC; AC 13 + the spell's level, 40 HP + 15 for each level "
                  "above 4, and a number of Slam attacks equal to half the spell's level (1d8 + 4 + the spell's level). Clay: Berserk "
                  "Lashing. Metal: Heated Body. Stone: Stony Lethargy.")
SLAM_C = "Target_ApoConstructSpirit_Slam"
slam(SLAM_C, "Slam", "1d8+4", "Bludgeoning", "Action_Slam",
     "Melee attack with your spell attack modifier: 1d8 + 4 + the spell's level Bludgeoning damage.", 4)

# Clay: Berserk Lashing (reaction: Slam a creature that damaged it, if it can reach)
for lvl in range(4, 10):  # one per level: it makes that level's Slam (the clay level status unlocks it)
    # the reaction's Slam costs the reaction, not an action: Extra Attack keys on an action cost and would
    # otherwise queue a free Slam after every Berserk Lashing (seen 2026-10-03)
    G.spell(f"{SLAM_C}_{lvl}_Reaction", "Berserk Lashing", "The spirit Slams the creature that damaged it.",
            {"UseCosts": "ReactionActionPoint:1"}, using=f"{SLAM_C}_{lvl}")
    G.interrupt(f"Interrupt_ApoBerserkLashing_{lvl}", "Berserk Lashing",
                "When a creature damages the spirit, it makes a Slam attack against that creature as a reaction.", {
                    "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                    "Conditions": "IsAbleToReact(context.Observer) and Enemy(context.Source,context.Observer) and HasFunctor(StatsFunctorType.DealDamage) and IsHit() and not AnyEntityIsItem() and not DistanceToEntityGreaterThan(2, context.ObserverPosition, context.Source) and HasLastAttackTriggered()",
                    "Properties": f"UseSpell(SWAP,{SLAM_C}_{lvl}_Reaction,true,true,true)", "Cost": "ReactionActionPoint:1",
                    "Stack": "ApoBerserkLashing", "InterruptDefaultValue": "Enabled"}, icon="Action_Slam")
G.passive("Apo_ConstructSpirit_BerserkLashing", "Berserk Lashing",
          "Reaction: when a creature damages the spirit, the spirit makes a Slam attack against it.", icon="Action_Slam")
# Metal: Heated Body (a creature that hits it with a melee attack takes 1d10 Fire)
G.passive("Apo_ConstructSpirit_HeatedBody", "Heated Body",
          "A creature that hits the spirit with a melee attack takes 1d10 Fire damage.", {
              "StatsFunctorContext": "OnAttacked",
              "Conditions": "IsMeleeAttack() and HasDamageEffectFlag(DamageFlags.Hit) and not SpellTypeIs(SpellType.Throw)",
              "StatsFunctors": "DealDamage(SWAP,1d10,Fire,Magical)"}, icon="Spell_Evocation_FireShield_Warm")
# Stone: Stony Lethargy (a creature starting its turn within 10 ft: Wisdom save or no Opportunity Attacks, half Speed)
G.status("APO_STONY_LETHARGY", "Stony Lethargy",
         "Speed halved and can't make Opportunity Attacks (reactions) until the start of its next turn.", {
             "Boosts": "ActionResourceMultiplier(Movement,50,0);ActionResourceBlock(ReactionActionPoint)",
             "StackId": "APO_STONY_LETHARGY", "TickType": "StartTurn"}, icon="Spell_Transmutation_Slow")
G.status("APO_STONY_LETHARGY_NEAR", "Within reach of Stony Lethargy", None, {
    "StackId": "APO_STONY_LETHARGY_NEAR", "TickType": "StartTurn",
    "TickFunctors": "IF(not SavingThrow(Ability.Wisdom, SourceSpellDC())):ApplyStatus(APO_STONY_LETHARGY,100,1)",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.status("APO_STONY_LETHARGY_AURA", "Stony Lethargy",
         "A creature that starts its turn within 10 feet of the spirit makes a Wisdom saving throw against your spell save DC; on a failure its Speed is halved and it can't make Opportunity Attacks until the start of its next turn.", {
             "AuraRadius": "3", "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_STONY_LETHARGY_NEAR)",
             "StackId": "APO_STONY_LETHARGY_AURA", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead"},
         icon="Spell_Transmutation_Slow")

con_forms = []
for mat, passive, extra_status in (("Clay", "Apo_ConstructSpirit_BerserkLashing", None),
                                   ("Metal", "Apo_ConstructSpirit_HeatedBody", None),
                                   ("Stone", None, "APO_STONY_LETHARGY_AURA")):
    char = {"Level": "9", "Strength": "18", "Dexterity": "10", "Constitution": "18", "Intelligence": "14", "Wisdom": "11",
            "Charisma": "5", "Armor": "17", "ArmorType": "None", "Vitality": "40",
            "ActionResources": "ActionPoint:1;BonusActionPoint:1;Movement:9;ReactionActionPoint:1",
            "UnarmedAttackAbility": "Wisdom", "UnarmedRangedAttackAbility": "Wisdom", "SpellCastingAbility": "Wisdom",
            "DarkvisionRange": "18",
            "Passives": "AttackOfOpportunity;Darkvision;DarknessRules;ShortResting" + (f";{passive}" if passive else ""),
            "PersonalStatusImmunities": "SG_Charmed;SG_Frightened;FEARED;SG_Paralyzed;SG_Poisoned",
            "DifficultyStatuses": "STATUS_EASY:PLAYER_BONUSES_EASYMODE", **resistances(("Poison",))}
    tpl, levels = spirit("Construct", mat, f"{mat} Construct Spirit", char, ["Shout_Dodge"], 4, 1, 15, SLAM_C,
                         ";UnlockInterrupt(Interrupt_ApoBerserkLashing_{lvl})" if mat == "Clay" else "")
    con_forms.append((mat, mat, tpl, levels, extra_status))
summon_spell("Target_ApoSummonConstruct", "Summon Construct", CONSTRUCT_TEXT, "Conjuration", 4, con_forms,
             "Spell_Conjuration_FindFamiliar")

# ================================================================ spell lists
# (class, spell level) -> spells. dnd55e lists named "5.5 <Class> SLevel <N>..." (incl. "to N"/"to Bard" copies).
CLASS_ADDS = {
    ("Druid", 4): ["Target_ApoSummonElemental"],
    ("Wizard", 4): ["Target_ApoSummonElemental", "Target_ApoSummonConstruct"],
}
APO_ADDS = {  # Apotheosis-owned lists, by name
    "Apotheosis Ranger SLevel 4 List": ["Target_ApoSummonElemental"],
    "WizardUpToL7": ["Target_ApoSummonElemental", "Target_ApoSummonConstruct"],
    "WizardUpToL8": ["Target_ApoSummonElemental", "Target_ApoSummonConstruct"],
    "WizardUpToL9": ["Target_ApoSummonElemental", "Target_ApoSummonConstruct"],
}
NODE = re.compile(r'[ \t]*<node id="SpellList">\s*(?:(?!</node>).)*?</node>\n', re.S)


def patch_lists():
    path = os.path.join(PUB, "Lists", "SpellLists.lsx")
    s = open(path, encoding="utf-8").read()
    for name, add in APO_ADDS.items():
        m = re.search(rf'(<attribute id="Name" type="FixedString" value="{re.escape(name)}"/>\s*<attribute id="Spells" type="LSString" value=")([^"]*)', s)
        assert m, name
        have = [x for x in m.group(2).split(";") if x]
        s = s[:m.start(2)] + ";".join(have + [a for a in add if a not in have]) + s[m.end(2):]
    open(path, "w", encoding="utf-8", newline="").write(s)
    dnd = open(os.path.join(DND, "Lists", "SpellLists.lsx"), encoding="utf-8").read()
    rows = []
    for node in NODE.findall(dnd):
        name = re.search(r'id="Name" type="FixedString" value="([^"]*)"', node)
        if not name:
            continue
        add = [sp for (cls, lvl), sps in CLASS_ADDS.items() for sp in sps
               if re.match(rf"5\.5 {cls} SLevel {lvl}( |$)", name.group(1))]
        if add:
            def extend(m):
                have = [x for x in m.group(2).split(";") if x]
                return m.group(1) + ";".join(have + [a for a in dict.fromkeys(add) if a not in have])
            rows.append("                " + re.sub(r'(id="Spells" type="LSString" value=")([^"]*)', extend, node.strip()) + "\n")
    G._between(path, rows)
    return len(rows)


if __name__ == "__main__":
    G.write_stats("Summons", "gen_summons.py", "issue #10")
    G.write_templates("Apotheosis_Summons")
    n = patch_lists()
    G.patch_loca()
    print(f"{len(G.C)} creatures, {len(G.T)} templates, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.P)} passives, "
          f"{len(G.I)} interrupts; {n} dnd55e lists overridden")
