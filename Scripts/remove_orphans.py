"""Remove orphaned progression nodes (no dnd55e base) per user decision.

Removes Progression node blocks whose Name is in ORPHAN, along with their attached
per-node comment lines, and the two now-empty PSION section dividers.
"""
import os
import re
import compat_audit as ca

ORPHAN = {"ArcanaDomain", "Psion", "PsiWarper", "Telepath", "SecretAgent",
          "Metamorph", "Deadeye", "TrickShot", "Psykinetic"}

PATH = os.path.join(ca.APO, "Progressions", "Progressions.lsx")


def main():
    with open(PATH, encoding="utf-8") as f:
        lines = f.readlines()

    delete = set()
    n = len(lines)
    i = 0
    while i < n:
        if '<node id="Progression">' in lines[i]:
            j = i
            while j < n and "</node>" not in lines[j]:
                j += 1
            block = "".join(lines[i:j + 1])
            m = re.search(r'id="Name" type="LSString" value="([^"]+)"', block)
            if m and m.group(1) in ORPHAN:
                for k in range(i, j + 1):
                    delete.add(k)
                # Walk up: remove attached per-node comments / blanks, but keep
                # section dividers (lines containing "====").
                p = i - 1
                while p >= 0:
                    s = lines[p].strip()
                    if s == "" or (s.startswith("<!--") and "====" not in s):
                        delete.add(p)
                        p -= 1
                    else:
                        break
            i = j + 1
        else:
            i += 1

    # Remove the two now-empty PSION section dividers explicitly.
    for idx, ln in enumerate(lines):
        if "PSION LEVELS 13-20" in ln or "PSION SUBCLASS OVERRIDES" in ln:
            delete.add(idx)

    kept = [ln for idx, ln in enumerate(lines) if idx not in delete]

    # Collapse 3+ consecutive blank lines to a single blank line.
    out = []
    blanks = 0
    for ln in kept:
        if ln.strip() == "":
            blanks += 1
            if blanks <= 1:
                out.append(ln)
        else:
            blanks = 0
            out.append(ln)

    with open(PATH, "w", encoding="utf-8") as f:
        f.writelines(out)

    print(f"Removed {len(delete)} lines. New file length: {len(out)} (was {n}).")


if __name__ == "__main__":
    main()
