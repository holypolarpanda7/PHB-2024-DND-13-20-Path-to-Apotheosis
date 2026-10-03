"""Upcast variants at 7th-9th level (2026-10-03). Base BG3 and dnd55e give every leveled spell `_N` upcast variants
only up to 6th level, so a 7th-9th level slot can't upcast Bless, Hex, Ice Knife, Counterspell... This generator
adds the missing `_7`.._9 variants for every spell family whose variants stop at 6 (families that already reach 9,
e.g. the hand-written ones in Spell_HighLevel.txt, are left alone).

How: each `X_n` uses `X_6` and overrides only the fields that changed between the 5th and 6th level variants, with
every changed number extended linearly (dice, target counts, radii, slot level, `_6` -> `_7` names). The 2024 upcast
rules are linear per slot level, so the 5->6 step is the per-level step. A changed name that doesn't exist at the new
level (a status ACID_ARROW_7, an interrupt, a container child, an AI helper spell) is generated the same way from its
own 5th/6th level pair. A field whose change isn't a plain number step (a different loca handle, a field only one
side sets) is inherited from the 6th level variant unchanged.

Owns Spell_Upcast79.txt, Status_Upcast79.txt, Interrupt_Upcast79.txt, Passive_Upcast79.txt (fully regenerated).
Run: python3 Scripts/gen_upcasts.py   (reads the bg3-data MCP index; refresh it first if the layers changed)
"""
import json
import os
import re
import sqlite3
from pathlib import Path

GUID = "PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
DATA = Path(__file__).resolve().parent.parent / f"Public/{GUID}/Stats/Generated/Data"
DB = os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite")
OUT = {"SpellData": "Spell_Upcast79.txt", "StatusData": "Status_Upcast79.txt", "InterruptData": "Interrupt_Upcast79.txt",
       "PassiveData": "Passive_Upcast79.txt"}
TYPE_FIELD = {"SpellData": "SpellType", "StatusData": "StatusType"}
SKIP = {"Level", "RootSpellID", "DisplayName", "Description", "ExtraDescription", "ShortDescription",
        "TooltipUpcastDescription", "TooltipUpcastDescriptionParams", "Icon"}
NUM = re.compile(r"(\d+(?:\.\d+)?)")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")


class Stats:
    """Resolved stats across every layer, ignoring this generator's own output (so reruns are stable)."""

    def __init__(self):
        self.db = sqlite3.connect(DB)
        self.own = set(OUT.values())
        self._cache = {}

    def rows(self, name):
        return [r for r in self.db.execute("SELECT rank, file, type, using_, data FROM stats WHERE name=? ORDER BY rank",
                                           (name,)) if r[1] not in self.own]

    def get(self, name, below=None):
        key = (name, below)
        if key not in self._cache:
            rows = [r for r in self.rows(name) if below is None or r[0] < below]
            if not rows:
                self._cache[key] = None
            else:
                rank, _, typ, using, data = rows[-1]
                parent = self.get(name, rank) if using == name else self.get(using) if using else None
                fields = dict(parent[1]) if parent else {}
                fields.update({k: v for k, v in json.loads(data).items() if v is not None})
                self._cache[key] = (typ or (parent or ("",))[0], fields)
        return self._cache[key]

    def families(self):
        declared = {}  # fields the entries set themselves (a spell `using` an upcast inherits its PowerLevel)
        for name, file, data in self.db.execute("SELECT name, file, data FROM stats WHERE type='SpellData' ORDER BY rank"):
            if file not in self.own:
                declared.setdefault(name, {}).update({k: v for k, v in json.loads(data).items() if v is not None})
        roots = {}
        for name, f in declared.items():
            pl, root = f.get("PowerLevel"), f.get("RootSpellID")
            if root and pl and str(pl).isdigit():
                roots.setdefault(root, {})[int(pl)] = name
        out = {}
        for root, lv in roots.items():
            r = self.get(root)
            if max(lv) == 6 and r and str(r[1].get("Level", "0")).isdigit() and int(r[1].get("Level", "0")) > 0:
                prev = lv.get(5) or (root if r[1].get("Level") == "5" else None)
                out[root] = (prev, lv[6])
        return out


def step(a, b, k):
    """Extend value b (one level above a) by k more levels; (new value, [changed identifiers]) or None."""
    a, b = a.rstrip("; "), b.rstrip("; ")
    pa, pb = NUM.split(a), NUM.split(b)
    if len(pa) != len(pb) or any(x != y for x, y in zip(pa[0::2], pb[0::2])):
        return None
    out, refs = [], []
    for i, (x, y) in enumerate(zip(pa, pb)):
        if i % 2 == 0 or x == y:
            out.append(y)
            continue
        d = float(y) - float(x)
        v = max(0.0, float(y) + d * k)
        s = f"{v:.{len(y.split('.')[1])}f}" if "." in y else str(int(round(v)))
        out.append(s)
        m = IDENT.search("".join(out[:-1]))
        if m and m.group(0).endswith("_"):  # a level inside a name: ACID_ARROW_6, Target_Bless_6_AI
            tail = re.match(r"[A-Za-z0-9_]*", "".join(pb[i + 1:])).group(0)
            refs.append((m.group(0), s, tail, d))
    return "".join(out), refs


class Gen:
    def __init__(self):
        self.S = Stats()
        self.made = {}      # name -> (type, using, overrides)
        self.warn = []

    def exists(self, name):
        return name in self.made or self.S.get(name) is not None

    def make(self, name, prev, cur, k):
        """Create `name` = `cur` stepped k levels past `prev` (prev -> cur is one level)."""
        if name in self.made:
            return True
        typ, a = self.S.get(prev)
        _, b = self.S.get(cur)
        self.made[name] = None  # reserve against recursion
        over = {}
        for f in sorted(set(a) | set(b)):
            if f in SKIP or f == "using" or a.get(f) == b.get(f):
                continue
            if f not in a or f not in b:
                continue  # one side only: inherit the 6th level value
            av = str(a[f])
            for nm in set(re.findall(r"([A-Za-z][A-Za-z0-9_]*?)_6(?![0-9])", str(b[f]))):  # root X -> 6th level X_6
                av = re.sub(rf"(?<![A-Za-z0-9_]){nm}(?![A-Za-z0-9_])", nm + "_5", av)
            r = step(av, str(b[f]), k)
            if r is None:
                if f not in ("DescriptionParams",):
                    self.warn.append(f"{name}: {f} doesn't step ({a[f]!r} -> {b[f]!r}); inherited")
                continue
            val, refs = r
            ok = True
            for pre, num, tail, d in refs:
                ref = pre + num + tail
                if self.exists(ref):
                    continue
                n = float(num)
                rcur, rprev = (pre + _fmt(n - d * k, num) + tail), (pre + _fmt(n - d * (k + 1), num) + tail)
                if not self.S.get(rcur):
                    ok = False  # already dangling at 6th level (HELLISH_REBUKE_6): inherit, nothing to step
                    continue
                if not self.S.get(rprev):
                    rprev = pre[:-1] + tail  # the unsuffixed root stands in for the 5th level
                if self.S.get(rprev) and self.make(ref, rprev, rcur, k):
                    continue
                self.warn.append(f"{name}: {f} needs {ref}, which can't be derived; inherited")
                ok = False
            if ok:
                over[f] = val
        self.made[name] = (typ, cur, over)
        return True


def _fmt(v, like):
    return f"{v:.{len(like.split('.')[1])}f}" if "." in like else str(int(round(v)))


def write(g):
    S = g.S
    by = {t: [] for t in OUT}
    for name, (typ, using, over) in sorted(g.made.items()):
        if typ not in OUT:
            g.warn.append(f"{name}: type {typ} has no output file; skipped")
            continue
        lines = [f'new entry "{name}"', f'type "{typ}"']
        tf = TYPE_FIELD.get(typ)
        if tf:
            lines.append(f'data "{tf}" "{S.get(using)[1][tf]}"')
        lines.append(f'using "{using}"')
        lines += [f'data "{k}" "{v}"' for k, v in over.items()]
        by[typ].append("\n".join(lines))
    for typ, entries in by.items():
        head = ("// GENERATED by Scripts/gen_upcasts.py - do not edit by hand.\n"
                "// 7th-9th level upcast variants extended from the 5th->6th level step (PHB 2024 upcasting).\n\n")
        (DATA / OUT[typ]).write_text(head + "\n\n".join(entries) + "\n", newline="\r\n")
        print(f"{OUT[typ]}: {len(entries)} entries")


if __name__ == "__main__":
    g = Gen()
    fams = g.S.families()
    for root, (prev, cur) in sorted(fams.items()):
        if not prev:
            g.warn.append(f"{root}: no 5th level variant to step from; skipped")
            continue
        if not cur.endswith("_6"):
            g.warn.append(f"{root}: 6th level variant {cur} isn't named _6; skipped")
            continue
        for n in (7, 8, 9):
            name = cur[:-1] + str(n)
            g.make(name, prev, cur, n - 6)
            over = g.made[name][2]
            over["PowerLevel"] = str(n)  # never inherit 6 (a few roots leave PowerLevel blank)
            for cf in ("UseCosts", "HitCosts"):
                cost = over.get(cf) or g.S.get(cur)[1].get(cf, "")
                fixed = re.sub(r"(SpellSlotsGroup:\d+:\d+:)\d+", rf"\g<1>{n}", cost.strip())
                if fixed != cost:  # a few base _6 variants spend the wrong slot (See Invisibility_6: level 2)
                    over[cf] = fixed
    write(g)
    print(f"{len(fams)} families extended to 9th level")
    for w in g.warn:
        print("WARN", w)
