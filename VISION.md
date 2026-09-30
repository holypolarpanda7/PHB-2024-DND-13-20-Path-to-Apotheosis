# Path to Apotheosis: Vision

## Goal

Baldur's Gate 3, even with dnd55e, is designed for levels 1–12. **Path to Apotheosis raises that to the
full level 1–20 D&D experience.** It adds every class and subclass feature for levels 13–20, 7th- to
9th-level spells and slots, and the content needed to support play at those levels.

## Principles

1. **PHB 2024 is the source of truth.** Class and subclass features, spell text and level placement
   follow the 2024 rules. For subclasses outside the PHB, follow the source dnd55e uses for them.
2. **Every feature at its 2024 level.** dnd55e compresses features above level 12 into lower levels to
   fit its cap (for example, Psychic Veil at Soulknife 9 when the rules say 13). Apotheosis moves them
   back: a `PassivesRemoved` node at dnd55e's level and a `PassivesAdded` node at the 2024 level.
3. **Build on dnd55e; don't replace it.** dnd55e is a dependency. Where dnd55e already has a feature,
   use its implementation unless ours is more accurate. Don't override dnd55e entries just to change
   them. The level 1–12 game must play the same as dnd55e alone, apart from moving compressed features
   back to their 2024 levels (principle 2).
4. **Accuracy over homebrew.** Implement the feature as written. If BG3 can't do something (for
   example, moving through creatures), use the closest faithful approximation and document the gap.
   Never replace a rule with a different mechanic because it's easier.
5. **Complete the curve.** Fill gaps at levels 13–20 for every class and subclass dnd55e ships:
   features, 7th- to 9th-level spells, upcasts of existing spells to 9th level, spell slots, XP and the
   level cap.
6. **Stay in sync with dnd55e.** dnd55e changes often. Re-audit against the current upstream
   reference clone (`../dnd55e`): `Scripts/compat_audit*.py`, `Scripts/build_all_class_expectations.py`.
   When dnd55e adds something we also built, compare the two (principles 1–4) and keep the better
   one.

## Check before acting

Before any change, confirm:

- [ ] Does it move the game toward complete 1–20 play (the goal)?
- [ ] Does it match the 2024 rules text and level (principles 1 and 2)?
- [ ] Does dnd55e already have it? If so, whose version is more accurate, and at what level (principle 3)?
- [ ] Does it leave dnd55e's levels 1–12 unchanged, apart from moving compressed features back
      (principle 3)?
- [ ] If it can't be faithful, is the approximation the closest possible, and is the gap documented
      (principle 4)?
