# Perf Issue

Use when: something is slow or heavy and needs a one-off fix tied to a measurement. For sustained improvement against a metric use `references/playbooks/hillclimb.md`. You own the measurement story: plan, review, verify the numbers. Measure; don't read source instead of measuring.

## Steps
1. Capture a baseline trace on the matching surface via the repo's `verify-<app>` skill (`.omp/skills/verify-<app>/`); if none, omp `eval` `browser` or bash. Vet it, and every later number, with the **benchmark-checklist** technique (`references/techniques/benchmark-checklist.md`).
2. Ground hypotheses with the **how** technique (`references/techniques/how.md`). Try the performance mantras in order, cheapest first; stop at the first that meets the target:
   1. Don't do it (stop work whose result nothing uses).
   2. Do it, but don't do it again.
   3. Do it less.
   4. Do it later.
   5. Do it when they're not looking.
   6. Do it concurrently.
   7. Do it cheaper.
3. Plan the fix from the trace. Crosses a function boundary → the **architect** technique (`references/techniques/architect.md`) first. Size L → delegate implementation to a default `task` agent (exclusive file ownership, reasoning level per job) and review the diff. Size M → make the change yourself, then run the **pr-review** self-review (`references/techniques/pr-review.md`, local mode).
4. Verify each attempt before trying the next (`references/principles/sequence-verifiable-units.md`). Capture a post-fix trace.
5. Parse and compare artifacts (JSON → sqlite, diff).
6. Cite the measurement in the hand-off (and the commit and PR description).
7. Commit, run **Opening a PR** (`references/playbooks/opening-a-pr.md`), and land it through `references/playbooks/shipping.md` on a panel pass.

## Gates
- Every fix tied to a measurement; no perf ceiling claimed without running it.
- Stop at the earliest mantra that meets the target.
- "Inconclusive" or wrong-surface is not a pass — flag it.

## Evidence
- Baseline number, post-fix number, delta, artifact path(s).
