"""Apply the 36 safe progression TableUUID remaps to Apotheosis Progressions.lsx.

Reuses compat_audit.main() to compute the old->new map, then rewrites the file.
Leaves orphaned content (Psion/Arcana/stale gunslinger) untouched for a separate decision.
"""
import os
import compat_audit as ca


def main():
    remap, _ = ca.main()
    path = os.path.join(ca.APO, "Progressions", "Progressions.lsx")
    text = ca.read(path)
    total = 0
    print("\n=== APPLYING REMAP ===")
    for old, new in remap.items():
        token_old = f'value="{old}"'
        token_new = f'value="{new}"'
        # Only replace within TableUUID context to avoid touching node UUIDs.
        pattern = f'id="TableUUID" type="guid" {token_old}'
        replacement = f'id="TableUUID" type="guid" {token_new}'
        n = text.count(pattern)
        if n:
            text = text.replace(pattern, replacement)
            total += n
            print(f"  {old} -> {new}  ({n})")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nTotal TableUUID references rewritten: {total}")


if __name__ == "__main__":
    main()
