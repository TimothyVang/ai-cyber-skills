# Feature

Use when: adding new behavior. You own the design, review and proof. Choose local delivery or publication before implementing, per SKILL.md. Size M uses one implementation owner unless independent slices justify delegation. Size L uses separated implementation and verification.

## Steps

For a local M feature, use this short path instead of the shipping steps below:

1. Read the affected code, callers and existing checks. Name the requested behavior and the data shape that fits the existing design.
   Done when each requirement has an observable check, and no design or trust-boundary uncertainty requires size L.
2. Implement in the starting working tree. Reuse the existing test and CLI/app paths; add regression coverage for uncertain behavior, not for wording or wiring.
   Done when the requested behavior works without unrelated features or policy changes.
3. Run the actual user path, including its relevant boundaries and failure cases. Review the diff against the request and existing conventions; fix findings a code read or run proves.
   Done when the real output proves every requirement and the checked-out tree contains the result.
4. Report the changed behavior, command and observed result. Leave the changes uncommitted for local review.
   Done when the user can inspect and run the delivered files without finding another worktree or unfinished review.

Escalate real design or safety uncertainty; do not turn hypothetical extreme inputs into unrequested limits. Remote publication follows the steps below and retains its full merge gates.

1. Run the **how** technique (`references/techniques/how.md`) over the affected subsystem, then the **prior-art** technique (`references/techniques/prior-art.md`) for what the feature needs that the repo lacks.
   Done when both techniques have reached their own `Done when`.
2. If a new or changed public interface has several viable shapes, run **architect** (`references/techniques/architect.md`). Otherwise reuse the existing design.
   Done when the selected shape and its relevant tradeoff are named.
3. Write the throughput checkpoint as four `todo` items. A dimension that does not apply keeps its item as `n/a: <reason>`; never drop it:
   - Blocking first steps: gates that run before fan-out.
   - Independent workstreams: disjoint files, services, or layers parallelize; shared writes serialize.
   - Shared mutable state: default to splitting the target (`references/principles/separate-before-serializing-shared-state.md`); serialize only for real invariants.
   - Smallest safe decomposition: if one worker is best, name why.
   - Done when all four `todo` items exist, each filled or `n/a: <reason>`.
4. Pick the data shape before any logic is written (`references/principles/model-the-domain.md`): state machine over scattered booleans, table/registry over branching, typed model over repeated shape assumptions.
   Done when the chosen data shape is named in the plan before the first code edit.
5. Delegate code-writing to a default `task` agent with a specific scope: file paths, the named data shape and its organizing structure, success criteria, exclusive file ownership.
   - Implementation admits several valid shapes (error handling, abstraction layer, test structure) → delegate via the **arena** technique (`references/techniques/arena.md`) instead.
   - Size L: delegation is mandatory, no skip-with-reason, and laziness does not override it (the gain is review separation, not lines saved). A subagent that cannot spawn owns the diff directly with the same review separation. Size M: implement directly, then the pr-review self-review supplies the separation.
   - No "standing by" reply that waits on a nested agent.
   - Comments per the **no-comments** technique (`references/techniques/no-comments.md`). Surgical edits; re-ground upstream-derived files against the source.
   - Port shared-primitive improvements to every consumer and verify each.
   - Done when every delegated scope reports done against its success criteria and every consumer of a changed shared primitive is verified.
6. Verify on the matching surface (project `verify-<app>` skill first; else omp `eval` `browser` or bash). "Inconclusive" or wrong-surface is not a pass; flag it.
   Done when captured output on that surface shows the new behavior.
7. Sequence into small, ordered, verifiable units (`references/principles/sequence-verifiable-units.md`): build, verify, then the next. Stack follow-ups.
   Done when each unit has its own passing verification before the next unit starts.
8. Design contested → run one adversarial review pass by a different model family than yours, when one is available; keep only findings a run proves. Prefer empirical and formal verification.
   Done when every finding from that pass is fixed with a proving run or dismissed with a reason, or the design was not contested.
9. For publication, run **Opening a PR** (`references/playbooks/opening-a-pr.md`), which lands through **pr-conversation** on a panel pass; a stack lands through Shipping. For local work, deliver the verified changes in the starting tree without committing to a shared branch.
   Done when the requested delivery target holds; an unmerged worktree is not a delivered local feature.

## Gates

- Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline; that owner fans out internally after the blocking phase. Parent-level fan-out only for slices producing independent artifacts (audits, cross-subsystem investigations, competing experiments).
- Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.
- Not done until verified on the matching surface; inconclusive/wrong-surface blocks completion.

## Evidence

- What you built; what you chose and why (table for design alternatives).
- The throughput checkpoint (all four items).
- Verification run path and outcome on the matching surface.
- Open decisions.
