# show-me-your-work

**Use when:** long, autonomous, multi-phase, or unattended work a human reviews later. Keep one canonical decision log.

1. Start a TSV (local by default: `decisions.tsv` in the work dir, or `.audit/<task-slug>.tsv` when several efforts run; keep out of git) with header `ts	phase	decision	why	evidence	result`.
2. Log decision points and checkpoints, not every action: a fork chosen, a unit done with its verification result, a pivot/revert with trigger, a blocker, a gate fixed. Loops: one row per iteration. Cells single-line. `why` in plain words. `evidence` is a pointer (SHA, PR #, `file:line`, artifact path), never prose. `result` is a state (`tests green`, `reverted`, `pixel-diff 0`, `INCONCLUSIVE`, `open`). Strip tabs/newlines; prefix cells starting with `= + - @` with `'`.
3. Runs: a run is one conversation incl. later turns. When adding to a log with rows, first row is phase `start`, naming the `ts` range of rows this run didn't write and identifying this run (session/agent id). Re-entering later, read the last rows first. `start` is used for nothing else.
4. Append-only: a wrong call gets a superseding row; never edit or delete. Prefer evidence from committed scripts (encode-lessons-in-structure).
5. Before handing back, audit this run's rows against this run's transcript only (`history://`; never other projects): each row maps to a real decision/action, evidence resolves and shows the claim, unlogged forks/pivots are added. Correct with superseding rows, never edits.
6. Spawn a default `task` agent (not `reviewer`: it must read the transcript via `history://`) on a different model family than yours, when one is available (self-review is no substitute), to read trail + transcript and flag: weak/absent evidence, skipped or unproven verification, risky choices (premature, scope creep, symptom-papering), gaps a casual skim misses.
7. Commit the log only when the work needs an auditable trail.

**Output:** every reply for a run with a trail ends with **Attention**: first line `reviewed by <model>`, then flags pointing at rows/moments, or "No flags". Other techniques route trails here and don't restate the format. Log text goes through **unslop**.
