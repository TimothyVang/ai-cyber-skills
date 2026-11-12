# sequence-verifiable-units

Group: verification. When: multi-step work (sweeps, migrations, runs of similar edits) and stacking commits/PRs.
- **Rule.** Small units, each ending in a checkable state; don't advance until the current one is green.
- **Execution.** Each unit is a bracket: known-good state, one change, run the check, proceed. Rebase onto clean trunk first so checks measure the real baseline. When a lever does the edits the per-unit check is nearly free — run it anyway.
- **Delivery.** Stack commits/PRs in the order that proves the work: failing test first, then the fix; subtraction before reshape; baseline before treatment; scaffold before feature. Each commit lands on its own; the sequence reads as an argument.
- **Anti-patterns.** Batching checks at the end, building further on a broken base.
