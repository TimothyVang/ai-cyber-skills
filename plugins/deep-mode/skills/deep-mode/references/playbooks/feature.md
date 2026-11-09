# Feature

Use when: adding new behavior. You own the design: plan, review, verify. Size L: delegate implementation and stay in the lead. Size M: implement yourself and get review separation from the **pr-review** self-review (`references/techniques/pr-review.md`, local mode).

## Steps

1. Run the **how** technique (`references/techniques/how.md`) over the affected subsystem.
2. Run the **architect** technique (`references/techniques/architect.md`) for parallel design exploration.
3. Write the throughput checkpoint as four `todo` items. A dimension that does not apply keeps its item as `n/a: <reason>`; never drop it:
   - Blocking first steps: gates that run before fan-out.
   - Independent workstreams: disjoint files, services, or layers parallelize; shared writes serialize.
   - Shared mutable state: default to splitting the target (`references/principles/separate-before-serializing-shared-state.md`); serialize only for real invariants.
   - Smallest safe decomposition: if one worker is best, name why.
4. Pick the data shape before any logic is written (`references/principles/model-the-domain.md`): state machine over scattered booleans, table/registry over branching, typed model over repeated shape assumptions.
5. Delegate code-writing to a default `task` agent with a specific scope: file paths, the named data shape and its organizing structure, success criteria, exclusive file ownership.
   - Implementation admits several valid shapes (error handling, abstraction layer, test structure) → delegate via the **arena** technique (`references/techniques/arena.md`) instead.
   - Size L: delegation is mandatory, no skip-with-reason, and laziness does not override it (the gain is review separation, not lines saved). A subagent that cannot spawn owns the diff directly with the same review separation. Size M: implement directly, then the pr-review self-review supplies the separation.
   - No "standing by" reply that waits on a nested agent.
   - Comments per the **no-comments** technique (`references/techniques/no-comments.md`). Surgical edits; re-ground upstream-derived files against the source.
   - Port shared-primitive improvements to every consumer and verify each.
6. Verify on the matching surface (project `verify-<app>` skill first; else omp `eval` `browser` or bash). "Inconclusive" or wrong-surface is not a pass; flag it.
7. Sequence into small, ordered, verifiable units (`references/principles/sequence-verifiable-units.md`): build, verify, then the next. Stack follow-ups.
8. Design contested → run one adversarial review pass by a different model family than yours, when one is available; keep only findings a run proves. Prefer empirical and formal verification.
9. Run **Opening a PR** (`references/playbooks/opening-a-pr.md`) only if the user asked to commit or open a PR.

## Gates

- Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline; that owner fans out internally after the blocking phase. Parent-level fan-out only for slices producing independent artifacts (audits, cross-subsystem investigations, competing experiments).
- Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.
- Not done until verified on the matching surface; inconclusive/wrong-surface blocks completion.
- No git writes (commit, push, PR) unless the user asked.

## Evidence

- What you built; what you chose and why (table for design alternatives).
- The throughput checkpoint (all four items).
- Verification run path and outcome on the matching surface.
- Open decisions.
