"""Subclass spells at levels 13 and 17 for the half-casters (Paladin oaths, Ranger subclasses, Artificer subclasses).

dnd55e stops at level 12, so the last two rows of every Oath / Ranger / Artificer subclass spell table were never
granted. Sources (the edition dnd55e follows for each subclass, matched by its level 3-9 rows):
  PHB 2024: Devotion, Glory, Ancients, Vengeance, Fey Wanderer, Gloom Stalker
  XGE: Conquest   SCAG: Crown   TCoE: Watchers, Swarmkeeper   DMG 2014: Oathbreaker (dnd55e's level 9 matches it)
  UA 2025 Forgotten Realms: Noble Genies, Winter Walker   UA 2025 Horror: Hollow Warden
  TCoE / Eberron: Forge of the Artificer (same 13/17 rows): Alchemist, Armorer, Artillerist, Battle Smith
Spells BG3 doesn't have (no base, dnd55e or Apotheosis version) are listed in MISSING and skipped.
Texts: References/Subclasses/Subclasses_13_20_Sources.txt and the PHB 2024 in The Oracle.

Owns: SpellLists.lsx (between SUBCLASS SPELLS markers) and Progressions.lsx nodes (same markers).
Run: python3 Scripts/gen_subclass_spells.py
"""
import os

from gen_common import Gen, PUB, patch_progressions

G = Gen("subclassspells", "SUBCLASS SPELLS 13-17")

# subclass progression Name, TableUUID, class, {level: [spell ids]}
SUBCLASSES = [
    ("Devotion", "941ca27d-02f7-4f59-bd33-63fa3366134d", "Paladin", {13: ["Target_FreedomOfMovement", "Target_GuardianOfFaith"], 17: ["Target_FlameStrike"]}),
    ("Glory", "0b77ab31-6a51-4531-b924-95193d4b51c7", "Paladin", {13: ["Target_FreedomOfMovement"], 17: []}),
    ("Ancients", "b82864a7-b093-4553-a802-e176831029c1", "Paladin", {13: ["Target_IceStorm", "Target_Stoneskin"], 17: []}),
    ("Vengeance", "f769aa02-1f74-4fb6-b94c-8850143daa20", "Paladin", {13: ["Target_Banishment", "Teleportation_DimensionDoor"], 17: ["Target_HoldMonster", "Target_Scrying"]}),
    ("Conquest", "06cd782b-69b2-4200-93ea-77a611f87363", "Paladin", {13: ["Target_DominateBeast", "Target_Stoneskin"], 17: ["Target_Cloudkill", "Target_DominatePerson"]}),
    ("Crown", "e3a25a7a-e793-4b99-9d4a-0fbc17fcc1ff", "Paladin", {13: ["Target_Banishment", "Target_GuardianOfFaith"], 17: ["Shout_CircleOfPower", "Target_Geas"]}),
    ("Watchers", "403102da-744a-4f16-b392-c1da7e9bbf2c", "Paladin", {13: ["Shout_AuraOfPurity", "Target_Banishment"], 17: ["Target_HoldMonster", "Target_Scrying"]}),
    ("Oathbreaker", "f0d6f933-4532-463f-b378-a1e8b0164325", "Paladin", {13: ["Target_Blight", "Target_Confusion"], 17: ["Target_Contagion", "Target_DominatePerson"]}),
    ("NobleGenie", "86ae831e-aa1b-4f18-b3d2-6c60fc32ff3c", "Paladin", {13: ["Target_ConjureElementals_Minor_Container", "Target_ApoSummonElemental"], 17: ["Target_Smite_Banishing"]}),
    ("FeyWanderer", "4c844e73-f3c4-4490-9c65-d6d9f8007e8d", "Ranger", {13: ["Teleportation_DimensionDoor"], 17: []}),
    ("GloomStalker", "caa60bb8-8ca3-4871-b034-e10a6bc8ca29", "Ranger", {13: ["Target_Invisibility_Greater"], 17: ["Target_Seeming"]}),
    ("HollowWarden", "e5e8acd6-4fd3-4295-8e78-3a77b8c30f2d", "Ranger", {13: [], 17: ["Target_Awaken"]}),
    ("Swarmkeeper", "54ad9a98-9656-4aa5-858e-b302f83c4577", "Ranger", {13: ["Target_ArcaneEye"], 17: ["Target_InsectPlague"]}),
    ("WinterWalker", "d16b57a3-866e-42eb-9553-dc27f7bf8625", "Ranger", {13: ["Target_IceStorm"], 17: ["Zone_ConeOfCold"]}),
    ("Alchemist", "c36e28a1-2fd5-475b-9689-09b83c9fd63d", "Artificer", {13: ["Target_DeathWard", "Projectile_VitriolicSphere"], 17: ["Target_Cloudkill", "Teleportation_RaiseDead"]}),
    ("Armorer", "45578db1-e4a0-4f9e-8aff-2916385d3b05", "Artificer", {13: ["Shout_FireShield", "Target_Invisibility_Greater"], 17: []}),
    ("Artillerist", "56a06eeb-4bc2-4910-88a9-cd4b25480a3c", "Artificer", {13: ["Target_IceStorm", "Wall_WallOfFire"], 17: ["Zone_ConeOfCold"]}),
    ("BattleSmith", "88bb5c8e-b795-486a-82f0-b2531f396604", "Artificer", {13: ["Shout_AuraOfPurity", "Shout_FireShield"], 17: ["Target_Smite_Banishing", "Target_CureWounds_Mass"]}),
]
MISSING = {  # in the source table but not in BG3 (base, dnd55e or Apotheosis) - documented gaps
    "Devotion": ["Commune (17)"], "Glory": ["Compulsion (13)", "Legend Lore (17)", "Yolande's Regal Presence (17)"],
    "Ancients": ["Commune with Nature (17)", "Tree Stride (17)"], "NobleGenie": ["Contact Other Plane (17)"],
    "FeyWanderer": ["Mislead (17)"], "HollowWarden": ["Hallucinatory Terrain (13)"],
    "Armorer": ["Passwall (17)", "Wall of Force (17)"], "Artillerist": ["Wall of Force (17)"],
}
SELECTOR = {"Paladin": "AddSpells({},OathSpells,,,AlwaysPrepared)", "Ranger": "AddSpells({},,,,AlwaysPrepared)",
            "Artificer": "AddSpells({},,,,AlwaysPrepared)"}


def build():
    lists, nodes = [], []
    for name, table, cls, by_level in SUBCLASSES:
        for lvl, spells in sorted(by_level.items()):
            if not spells:
                continue
            lu = G.gid(f"list:{name}:{lvl}")
            lists.append(f'''                <node id="SpellList">
                    <attribute id="Comment" type="LSString" value="Apotheosis {name} spells level {lvl}"/>
                    <attribute id="Name" type="FixedString" value="Apotheosis {name} Spells Level {lvl}"/>
                    <attribute id="Spells" type="LSString" value="{';'.join(spells)}"/>
                    <attribute id="UUID" type="guid" value="{lu}"/>
                </node>
''')
            nodes.append((G.gid(f"node:{name}:{lvl}"), name, lvl, 1, table, {"Selectors": SELECTOR[cls].format(lu)}))
    G._between(os.path.join(PUB, "Lists", "SpellLists.lsx"), lists)
    patch_progressions({}, nodes, G.marker)
    return len(lists), len(nodes)


if __name__ == "__main__":
    n_lists, n_nodes = build()
    print(f"{n_lists} spell lists, {n_nodes} progression nodes; missing in BG3: "
          + "; ".join(f"{k}: {', '.join(v)}" for k, v in MISSING.items()))
