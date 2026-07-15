"""13-20 completeness audit for Path to Apotheosis.

Reports, per class (base, ProgressionType=0) and per subclass (ProgressionType=1):
  - which levels 13-20 have progression nodes
  - spell-slot / class-feature boosts present
  - referenced passives and whether each is REAL (has mechanical Boosts/functors)
    or STUB (only DisplayName/Description/Icon -> placeholder).
"""
import os
import re
from collections import defaultdict
import compat_audit as ca

PROG = os.path.join(ca.APO, "Progressions", "Progressions.lsx")
PASSIVE = os.path.join(ca.APO, "Stats", "Generated", "Data", "Passive.txt")

# Passives referenced by progressions may be implemented upstream; without
# these sources dnd55e/base-game passives are misreported as STUB.
UPSTREAM_PASSIVES = [
    # load order matters: base game first so dnd55e self-`using` overrides
    # (e.g. ControlledChaos) inherit the vanilla functional definition
    os.path.join(ca.WS, "BaseGame", "Shared", "Public", "Shared",
                 "Stats", "Generated", "Data", "Passive.txt"),
    os.path.join(ca.WS, "BaseGame", "Shared", "Public", "SharedDev",
                 "Stats", "Generated", "Data", "Passive.txt"),
    os.path.join(ca.DND, "Stats", "Generated", "Data", "Passive.txt"),
]

FUNCTIONAL_KEYS = ("Boosts", "StatsFunctorContext", "StatsFunctors", "ToggleOnFunctors",
                   "ToggleOffFunctors", "BoostContext", "BoostConditions")


def parse_passives():
    """Return name -> dict of data keys; classify real/stub."""
    text = ca.read(PASSIVE)
    entries = {}
    cur = None
    using = {}
    for line in text.splitlines():
        m = re.match(r'\s*new entry "([^"]+)"', line)
        if m:
            cur = m.group(1)
            entries[cur] = set()
            continue
        if cur:
            mu = re.match(r'\s*using "([^"]+)"', line)
            if mu:
                using[cur] = mu.group(1)
                continue
            md = re.match(r'\s*data "([^"]+)"', line)
            if md:
                entries[cur].add(md.group(1))

    def is_real(name, seen=None):
        seen = seen or set()
        if name in seen:
            return False
        seen.add(name)
        keys = entries.get(name, set())
        if any(k in keys for k in FUNCTIONAL_KEYS):
            return True
        if name in using:
            # inherits from a base passive; treat external (base-game/dnd) as real
            base = using[name]
            if base in entries:
                return is_real(base, seen)
            return True  # using an external passive => assume functional
        return False

    return {n: is_real(n) for n in entries}, entries


def parse_upstream_passives():
    """name -> True if an upstream (dnd55e/base-game) definition has functional keys."""
    real = {}
    for path in UPSTREAM_PASSIVES:
        if not os.path.exists(path):
            print(f"WARNING: upstream passive source missing: {path}")
            continue
        text = ca.read(path)
        cur = None
        for line in text.splitlines():
            m = re.match(r'\s*new entry "([^"]+)"', line)
            if m:
                cur = m.group(1)
                real.setdefault(cur, False)
                continue
            if cur:
                md = re.match(r'\s*data "([^"]+)"', line)
                if md and md.group(1) in FUNCTIONAL_KEYS:
                    real[cur] = True
                mu = re.match(r'\s*using "([^"]+)"', line)
                if mu and mu.group(1) != cur and real.get(mu.group(1)):
                    real[cur] = True
                # self-`using` inherits the earlier source's definition,
                # which real[cur] already reflects - nothing to do
        # entries seen in an earlier source keep their True flags
    return real


def parse_progressions():
    text = ca.read(PROG)
    nodes = []
    for m in re.finditer(r'<node id="Progression">(.*?)</node>', text, re.S):
        body = m.group(1)

        def a(n):
            mm = re.search(r'id="%s"[^>]*value="([^"]*)"' % n, body)
            return mm.group(1) if mm else None
        nodes.append({"Name": a("Name"), "Level": a("Level"), "Type": a("ProgressionType"),
                      "Passives": a("PassivesAdded"), "Boosts": a("Boosts"),
                      "Selectors": a("Selectors"), "AllowImprovement": a("AllowImprovement")})
    return nodes


def main():
    passive_real, _ = parse_passives()
    nodes = parse_progressions()

    base = defaultdict(dict)   # class -> level -> node
    sub = defaultdict(list)    # subclass -> nodes
    for n in nodes:
        if not n["Name"]:
            continue
        if n["Type"] == "0":
            base[n["Name"]][n["Level"]] = n
        else:
            sub[n["Name"]].append(n)

    upstream_real = parse_upstream_passives()

    def passive_status(plist):
        if not plist:
            return []
        out = []
        for p in plist.split(";"):
            p = p.strip()
            if not p:
                continue
            if passive_real.get(p, False):
                out.append((p, "REAL"))
            elif p not in passive_real and upstream_real.get(p, False):
                out.append((p, "REAL-UPSTREAM"))
            elif p not in passive_real and p in upstream_real:
                out.append((p, "STUB-UPSTREAM"))
            elif p not in passive_real:
                out.append((p, "UNDEFINED"))
            else:
                out.append((p, "STUB"))
        return out

    print("########## BASE CLASSES (levels 13-20) ##########")
    for cls in sorted(base):
        levels = base[cls]
        present = sorted((l for l in levels if l and l.isdigit() and 13 <= int(l) <= 20), key=int)
        missing = [str(l) for l in range(13, 21) if str(l) not in levels]
        stubs = []
        reals = []
        for l in present:
            for p, st in passive_status(levels[l]["Passives"]):
                (reals if st.startswith("REAL") else stubs).append(f"L{l}:{p}")
        print(f"\n{cls}: levels {present}" + (f"  MISSING {missing}" if missing else "  [complete 13-20]"))
        if reals:
            print(f"   REAL passives: {reals}")
        if stubs:
            print(f"   STUB passives: {stubs}")

    print("\n\n########## SUBCLASSES (feature nodes) ##########")
    for sc in sorted(sub):
        nodes_sc = sub[sc]
        bits = []
        for n in nodes_sc:
            for p, st in passive_status(n["Passives"]):
                bits.append(f"L{n['Level']}:{p}[{st}]")
        levels = sorted({n["Level"] for n in nodes_sc if n["Level"]}, key=lambda x: int(x))
        print(f"{sc}: levels {levels}  {bits}")

    # Summary
    all_stub = sum(1 for n, r in passive_real.items() if not r)
    all_real = sum(1 for n, r in passive_real.items() if r)
    print(f"\n\n########## PASSIVE SUMMARY ##########")
    print(f"Total passives defined: {len(passive_real)}  REAL: {all_real}  STUB: {all_stub}")


if __name__ == "__main__":
    main()
