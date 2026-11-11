# Bug Fix

Use when: something is broken and needs a fix. You own the task: plan, review, verify; delegate investigation and the fix to `task` subagents (pick reasoning level per job) and stay in the lead.

Be scientific: every shipped line traces to runtime evidence. A "might help" belt-and-suspenders change is a hypothesis, not a fix — it does not ship. When evidence refutes a hypothesis, revert what it motivated. Ship the smallest change the evidence justifies.

## Steps
1. Reproduce it yourself on the matching surface via the repo's `verify-<app>` skill (`.omp/skills/verify-<app>/`); if none, omp `eval` `browser` or bash — even if a debug protocol says to ask the user. If it won't reproduce directly: synthesize the trigger, tighten conditions, or instrument until it fires.
2. Binary-search the cause:
   - Seed candidate hypotheses with the **how** technique (`references/techniques/how.md`) over the subsystem and the **why** technique (`references/techniques/why.md`) for regression history.
   - Each pass, take the split that cuts the most remaining space, get runtime evidence, eliminate.
   - State unclear → add instrumentation/logging and read it as the code runs; don't guess.
   - Long or stubborn hunt → keep looping (see `references/playbooks/autonomous-run.md` for the wake mechanism) until one hypothesis survives.
   - Confirm the surviving *mechanism* with runtime evidence before planning the fix.
3. Plan the fix. Crosses a function boundary → the **architect** technique (`references/techniques/architect.md`) first. Size L or a fix that splits cleanly → delegate implementation to a default `task` agent with a specific scope and exclusive file ownership. Size M → make the fix yourself; review separation comes from the **pr-review** self-review (`references/techniques/pr-review.md`, local mode) before reporting.
4. Verify on the same surface: the original repro now passes.
5. Order the evidence so the failing repro is shown before the fix (`references/principles/sequence-verifiable-units.md`); when committing, that is also the commit order. Use the **tdd** technique (`references/techniques/tdd.md`) for failing-test-first when a cheap local test path exists; skip it when the test would be expensive, integration-heavy, or unclear.
6. Commit, run **Opening a PR** (`references/playbooks/opening-a-pr.md`), and land it through `references/playbooks/shipping.md` on a panel pass.

## Gates
- Ask the user to reproduce only with a stated, specific reason the control surface can't reach the target, and only after driving it as far as it goes.
- No fix planned before the mechanism is confirmed by runtime evidence.
- "Inconclusive" or wrong-surface verification is not a pass — flag it. Unit tests show branch behavior, not bug absence.
- Refuted hypothesis → revert its changes. Speculative hardening never ships.
- Contested fix design only: an adversarial cross-model review (a different model family than yours, when available) may be run; keep only findings a run proves.

## Evidence
- What was broken, root cause, the fix, how you verified.
- Failing-then-passing repro output, pasted verbatim.
