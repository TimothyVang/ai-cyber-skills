# Visual Parity

Use when: migrating or reimplementing UI that must stay pixel-identical. You own pixel-exact equivalence; the baseline is the spec and you don't touch it. Equivalence is proven by image diff, not by eye.

## Steps
1. Before any migration, build a visual regression harness that screenshots the current component across its states (plus the target when matching two implementations).
2. State the anti-shortcut clauses and hold them: no harness modifications, no baseline tampering, no component restructuring to make a diff pass.
3. Migrate shared primitives first as a blocking phase.
4. Migrate one component at a time; parallelize with `task` agents, one owner per component with exclusive file ownership (`references/principles/separate-before-serializing-shared-state.md`).
5. Verify each component against its baseline by image diff on the matching surface via the repo's `verify-<app>` skill (`.omp/skills/verify-<app>/`); if none, omp `eval` `browser` or bash. Nonzero diff → investigate the pixel delta, fix, re-diff; loop per component until zero.
6. Commit per component or per safe batch, run **Opening a PR** (`references/playbooks/opening-a-pr.md`), which lands a single PR through **pr-conversation** on a panel pass; a stack lands through `references/playbooks/shipping.md`.

## Gates
- No baseline, no parity claim — a blocking prerequisite, not a follow-up.
- Baseline looks wrong → stop that comparison and report it with evidence; never edit it.
- Any nonzero diff is a fail.

## Evidence
- Components migrated with each diff result; baseline harness location; what's left.
