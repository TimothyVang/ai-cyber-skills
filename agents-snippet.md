## Rigor

For large or risky work (multi-file features, migrations, perf work, multi-PR work, autonomous or overnight runs), or when I say "deep mode" or "poteto mode", read `skill://deep-mode` and follow it. `/poteto <task>` does the same. Skip it for ordinary small tasks.

## Verification

A behavior change is done only when it has been proven on the running app. Passing tests are not proof.

- If the repo has `.omp/skills/verify-*/`, use that skill. Read its `SKILL.md` and the matching `features/` file before launching, driving, or debugging the app. Run its `doctor` first.
- If the repo has none and the task changes user-visible behavior, say so once and offer `/skill:create-verification-skill`. Until one exists, prove the change by running the real app or CLI path yourself.
- Report evidence: commands run, screenshots or snapshots, observed end state. "Fixed" without artifacts is not done.
- When you change a user-facing feature, update its feature-map file in the same change.
- When an agent repeats the same mistake, prefer a lint rule, type, or test over another line in this file.
