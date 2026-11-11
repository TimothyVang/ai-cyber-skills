# Hillclimb

Use when: sustained, iterative improvement of one measurable thing against a target (a one-off fix is `references/playbooks/bug-fix.md` or `references/playbooks/perf-issue.md`). You own the metric and the experiment's integrity: supervise and review, delegate the attempts.

Core discipline: one change, one measurement, keep or revert. Never stack untested changes; never claim a win from code inspection (`references/principles/prove-it-works.md`).

## Steps
1. Ground workload and architecture with the **how** technique (`references/techniques/how.md`): name the workload dimensions that move the result (data size, history, state, concurrency) and pick a case that reproduces the user's complaint.
2. Fix one metric, the better direction, and a checkable stop predicate pairing a target with a minimum attempt count (e.g. "≥50% better than baseline and ≥10 iterations"). Use the user's numbers, else agree them.
3. Build the harness (`references/principles/build-the-lever.md`): run contrasting realistic workloads; confirm the target case shows the symptom and easier cases separate. Can't distinguish → revise workload or metric.
4. Vet the harness with the **benchmark-checklist** technique (`references/techniques/benchmark-checklist.md`); make it print its error count and a work-done count. Freeze it: one repeatable command, median of N samples to clear noise.
5. Record the baseline metric and a green run of the regression gate before any change.
6. Keep the decision log per the **show-me-your-work** technique (`references/techniques/show-me-your-work.md`): its gitignored `decisions.tsv` with header `ts\tphase\tdecision\twhy\tevidence\tresult`, plus metric columns after `result` (`before\tafter\tdelta\ttests`). One row per attempt: `decision` = hypothesis and change, `result` = kept/reverted. Read it before each attempt.
7. Ground each hypothesis in a specific mechanism from step 1 ("defer X off boot path because it blocks first paint"), not "try memoizing something". Perf metric → order by the mantras in `references/playbooks/perf-issue.md` step 2 (order only, not its stop rule).
8. Loop, one hypothesis per iteration:
   - Delegate the change to a default `task` agent with tight scope; review the diff rather than typing it (`references/principles/guard-the-context-window.md`). Independent live hypotheses may fan out in parallel, each with exclusive file ownership (`references/principles/separate-before-serializing-shared-state.md`).
   - Measure before/after with the frozen harness; run the regression gate.
   - Keep only if the metric moves past noise and the gate stays green; else revert fully.
   - Kept → keep a patch per kept change (diff ready); commit each kept change, only changed files (`git add <files>`, never `-A`). Log the row either way.
   - Unattended run → borrow only the wake mechanism from `references/playbooks/autonomous-run.md`, not its stop rule.
9. On a plateau (several rejects in a row): pivot category, combine near-misses, re-read the source, or try something more radical.
10. Stack the kept commits in landing order, run **Opening a PR** (`references/playbooks/opening-a-pr.md`), and land them through `references/playbooks/shipping.md` on a panel pass.

## Gates
- No reproducing case → fix the repro, don't hillclimb.
- Harness frozen after vetting: no edits mid-run.
- Every iteration ends in a check before the next begins (`references/principles/sequence-verifiable-units.md`).
- A "might help" tweak is never kept. Correctness and simplicity outrank the number: revert a win that breaks behavior; keep a simplification that holds the number (`references/principles/laziness-protocol.md`).
- Stop only when the predicate is met, or remaining ideas are marginal and not worth their cost. Never relax the predicate; never quit while cheap untried hypotheses remain. Stuck → surface it, don't spin.

## Evidence
- Metric and target; baseline → final with % delta.
- Iterations run (kept vs reverted); each accepted fix on one line.
- `decisions.tsv` path; the best next idea if pushed further.
