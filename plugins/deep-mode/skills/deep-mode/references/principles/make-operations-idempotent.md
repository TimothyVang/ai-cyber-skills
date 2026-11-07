# make-operations-idempotent

Group: architecture. When: designing commands, lifecycle steps, or loops that run amid crashes, restarts, retries.
- **Rule.** Converge to the correct state regardless of run count or where the previous run stopped. Derive each step from existing state: read current, compare to goal, apply only the difference.
- Leftovers (locks, temp files, half-written records, claimed jobs) must be recognizable as stale by the next run, judged by evidence that holds wherever the previous run stopped. E.g. write to a temp path and rename into place; compare artifacts by content, not creation order.
- **Test.** (1) Runs twice in a row? (2) Previous run crashed at every possible point? (3) Re-execution converges to the same end state? Any "depends on what was left behind" → add a reconciliation step.
- **Anti-patterns.** Markers the next run can't judge, turning every crash into manual cleanup.
