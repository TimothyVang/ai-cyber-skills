# Autonomous run

Use when: one task must be driven to a checkable end state without the human ("loop until X", "keep going until green", "going to bed, finish it"). A multi-day program with many PRs and workers is `references/playbooks/orchestrate.md`; one ambitious run needing a bespoke workflow is the **figure-it-out** technique (`references/techniques/figure-it-out.md`). You own the exit condition: define done, then drive to it without stopping.

## Steps

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero). Write down the command or check that evaluates it.
2. Start a decision trail per the **show-me-your-work** technique (`references/techniques/show-me-your-work.md`).
3. Pick the wake mechanism:
   - An event to watch (CI, a merge, a ref advancing) → a background `bash` job that blocks on it (`gh pr checks <pr> --watch`, `gh run watch <id>`, `timeout: 0`); its result auto-delivers. Add a long time-based heartbeat as fallback (background `sleep` with `timeout: 0`, or `sleep 3300` with `timeout: 3600`).
   - No event → a fixed-interval heartbeat (background `bash` `sleep`) sized to when the result is worth re-checking; set `timeout: 0` (or `sleep 3300` with `timeout: 3600`) — the default 300s deadline kills longer sleeps.
   - Unattended across sessions, from a script or CI, or in another harness → write a goal file and run `python <deep-mode skill>/assets/loop/loop.py run <goal.md>` (headless omp, Claude Code, or Codex until the check passes; capped, stall-stopped, tamper-checked). Interactive in one session → the harness's native `/goal` with the predicate's command named in it. Details: `references/playbooks/self-authoring.md`.
4. Each iteration: make the smallest change the evidence justifies, then evaluate the predicate.
5. Advanced → keep it and commit it. Didn't help → discard it. "Might help" belt-and-suspenders gets reverted, not left to ride.
6. Sequence the work into verifiable units, verifying each before the next instead of batching checks at the end (`references/principles/sequence-verifiable-units.md`).
7. Own mid-run discoveries that support the goal: broken skills, related bugs, flaky verifiers, review noise, tooling failures, orphaned follow-ups, fixable drift. Fix them yourself, out-of-band fixes kept separate from the main change (on their own branch and PR). Return to the predicate after each side fix.
8. Checkpoint every iteration in the trail: one row for what changed and whether the predicate moved.
9. Plateau → pivot the approach and keep going; a plateau is not a stop.

## Gates

- Stop only when the predicate is met, or on a genuine dead end (surface it rather than spin).
- Never relax the predicate to declare victory.
- Don't park reversible work for the human or use `ask`. Decide product and design calls yourself and log them (SKILL.md Autonomy). Surface only irreversible actions outside the grant, what only the user can supply, or a real dead end.
- Push and open PRs as the work needs; merges need a panel pass and go through `references/playbooks/shipping.md`.

## Evidence

- The exit condition and the check that evaluates it.
- Iterations run (trail link), what landed, what was discarded and why.
- Side fixes made and where they live.
- Final predicate state, shown by running the check.
