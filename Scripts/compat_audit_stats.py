"""Stat-level compatibility audit: Apotheosis vs current dnd55e (+ vanilla).

Reports:
  1. Apotheosis `using` parents that resolve nowhere
  2. Referenced spells / statuses / passives that resolve nowhere
  3. dnd55e entries Apotheosis overrides (same name) and whether dnd55e changed them since BASELINE
  4. Spells implemented by BOTH mods (same display name or same core id)

Env: DND55E_ROOT (git checkout of current dnd55e, default ../dnd55e = the upstream reference clone; git pull it first),
     BASELINE (dnd55e date Apotheosis was last synced against, default 2026-07-15).
"""
import glob, os, re, subprocess, sys
from collections import defaultdict

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APO_MOD = "PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
DND_MOD = "DnD2024_897914ef-5c96-053c-44af-0be823f895fe"
APO = os.path.join(WS, "PHB-2024-DND-13-20-Path-to-Apotheosis")
DNDR = os.environ.get("DND55E_ROOT", os.path.join(WS, "dnd55e"))
BASELINE = os.environ.get("BASELINE", "2026-07-15")
VAN = "/mnt/d/SteamLibrary/steamapps/common/Baldurs Gate 3/Data/Editor/Mods"
SPELL_PREFIX = r"(?:Target|Projectile|Shout|Zone|Rush|Throw|Teleportation|Wall|ProjectileStrike)"

def parse_txt(text):
    out = {}
    for block in re.split(r'\n(?=new entry ")', "\n" + text):
        m = re.match(r'\s*new entry "([^"]+)"', block)
        if not m:
            continue
        e = {"type": None, "using": None, "data": {}}
        for line in block.splitlines()[1:]:
            if line.startswith('type '):
                e["type"] = line.split('"')[1]
            elif line.startswith('using '):
                e["using"] = line.split('"')[1]
            else:
                d = re.match(r'data "([^"]+)" "(.*)"$', line)
                if d:
                    e["data"][d.group(1)] = d.group(2)
        out[m.group(1)] = e
    return out

def load_dir(d):
    ents = {}
    for f in sorted(glob.glob(os.path.join(d, "*.txt"))):
        for k, v in parse_txt(open(f, encoding="utf-8", errors="replace").read()).items():
            v["file"] = os.path.basename(f)
            ents[k] = v
    return ents

apo = load_dir(os.path.join(APO, "Public", APO_MOD, "Stats", "Generated", "Data"))
dnd = load_dir(os.path.join(DNDR, "Public", DND_MOD, "Stats", "Generated", "Data"))

# vanilla names from the game's editor .stats (spell names there lack the type prefix)
van = set()
for f in glob.glob(VAN + "/*/Stats/**/*.stats", recursive=True):
    kind = os.path.basename(f)[:-6]
    pre = kind + "_" if "SpellData" in f else ""
    for n in re.findall(r'<field name="Name" [^>]*value="([^"]*)"', open(f, encoding="utf-8-sig", errors="replace").read()):
        van.add(pre + n)

known = set(apo) | set(dnd) | van

def loca(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    return {h: re.sub(r"<[^>]+>", "", x.replace("&lt;", "<").replace("&gt;", ">")).strip()
            for h, x in re.findall(r'contentuid="([^"]+)"[^>]*>(.*?)</content>', t, re.S)}
apo_loca = {}
for f in glob.glob(os.path.join(APO, "Mods", APO_MOD, "Localization", "English", "*.xml")):
    apo_loca.update(loca(f))
dnd_loca = loca(os.path.join(DNDR, "Mods", DND_MOD, "Localization", "English", "english.xml"))
def name_of(e, table):
    h = e["data"].get("DisplayName", "").split(";")[0]
    return table.get(h) or apo_loca.get(h) or dnd_loca.get(h) or ""

problems = 0
print(f"Apotheosis entries: {len(apo)}   dnd55e entries: {len(dnd)}   vanilla names: {len(van)}")

# 1. using
print("\n=== 1. UNRESOLVED `using` PARENTS ===")
for n, e in sorted(apo.items()):
    if e["using"] and e["using"] not in known:
        print(f"  {e['file']}: {n} using {e['using']}"); problems += 1

# 2. references
print("\n=== 2. UNRESOLVED REFERENCES (spells / statuses / passives) ===")
ref_pats = {
    "spell": re.compile(r"\b(" + SPELL_PREFIX + r"_[A-Za-z0-9_]+)"),
    "status": re.compile(r"(?:ApplyStatus\((?:SELF,|TARGET,|SOURCE,)?|HasStatus\(')([A-Z][A-Z0-9_]+)"),
    "passive": re.compile(r"HasPassive\('([A-Za-z0-9_]+)'"),
}
unres = defaultdict(set)
for n, e in apo.items():
    for k, v in e["data"].items():
        for kind, pat in ref_pats.items():
            for r in pat.findall(v):
                if r not in known and not r.startswith("SG_"):
                    unres[(kind, r)].add(n)
        if k in ("Passives", "PassivesOnEquip") :
            for p in filter(None, v.split(";")):
                if p not in known:
                    unres[("passive", p)].add(n)
for (kind, r), users in sorted(unres.items()):
    print(f"  {kind:7s} {r:45s} used by {', '.join(sorted(users))[:120]}"); problems += 1
# spell ids used by Apotheosis spell lists / progressions
for f in glob.glob(os.path.join(APO, "Public", APO_MOD, "**", "*.lsx"), recursive=True):
    t = open(f, encoding="utf-8", errors="replace").read()
    for sp in set(re.findall(r'id="(?:Spells|SpellsPrepared)"[^>]*value="([^"]*)"', t)):
        for s in filter(None, sp.split(";")):
            if s not in known:
                print(f"  listref {s:45s} in {os.path.relpath(f, APO)}"); problems += 1
    for sp in set(re.findall(r'(?:AddSpells|UnlockSpell)\(([A-Za-z0-9_]+)', t)):
        pass

# 3. overrides
print(f"\n=== 3. dnd55e ENTRIES APOTHEOSIS OVERRIDES (changed in dnd55e since {BASELINE}?) ===")
base = subprocess.run(["git", "-C", DNDR, "rev-list", "-1", f"--before={BASELINE}", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
old_cache = {}
def old_entry(e_file, name):
    rel = f"Public/{DND_MOD}/Stats/Generated/Data/{e_file}"
    if rel not in old_cache:
        r = subprocess.run(["git", "-C", DNDR, "show", f"{base}:{rel}"], capture_output=True, text=True)
        old_cache[rel] = parse_txt(r.stdout) if r.returncode == 0 else {}
    return old_cache[rel].get(name)
ovr = sorted(n for n in apo if n in dnd)
changed = []
for n in ovr:
    old = old_entry(dnd[n]["file"], n)
    cur = dnd[n]
    if old is None:
        state = "NEW in dnd55e since baseline"
    elif (old["using"], old["data"]) != (cur["using"], cur["data"]):
        diff = sorted(k for k in set(old["data"]) | set(cur["data"]) if old["data"].get(k) != cur["data"].get(k))
        clobbered = [k for k in diff if k in apo[n]["data"]]
        state = f"CHANGED fields {diff}" + (f"  <-- Apotheosis ALSO sets {clobbered}" if clobbered else "")
    else:
        continue
    changed.append(n)
    print(f"  {n:45s} [{apo[n]['file']}] {state}")
print(f"  ({len(ovr)} overrides total, {len(changed)} changed upstream since {BASELINE}, baseline commit {base[:9]})")

# 4. duplicates
print("\n=== 4. SPELLS IMPLEMENTED BY BOTH MODS ===")
def core(n):
    n = re.sub("^" + SPELL_PREFIX + "_", "", n)
    n = re.sub(r"^(Apo|Epic|HL|Apotheosis)_", "", n)
    return re.sub(r"_(\d|spellscroll|Container)$", "", n).lower()
dnd_spells = {n: e for n, e in dnd.items() if e["type"] == "SpellData" and n not in van}
dnd_by_name, dnd_by_core = defaultdict(list), defaultdict(list)
for n, e in dnd_spells.items():
    dn = name_of(e, dnd_loca).lower()
    if dn:
        dnd_by_name[dn].append(n)
    dnd_by_core[core(n)].append(n)
seen = set()
for n, e in sorted(apo.items()):
    if e["type"] != "SpellData" or n in dnd or n in van:
        continue
    if re.search(r"_[789]$", n):  # our 7th-9th level upcast tiers of existing spells, not duplicates
        continue
    dn = name_of(e, apo_loca).lower()
    hits = set(dnd_by_name.get(dn, [])) | set(dnd_by_core.get(core(n), []))
    if hits:
        key = (dn, core(n))
        print(f"  APO {n:45s} '{name_of(e, apo_loca)}' [{e['file']}]  ~ dnd55e {sorted(hits)[:4]}")
        problems += 1
print(f"\nproblems (sections 1, 2, 4): {problems}")
