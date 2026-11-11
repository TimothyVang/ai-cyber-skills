# panel

**Use when:** deciding whether a task is done, and before every merge. The panel is the verdict: three skeptical verifiers judge the work independently, and the task is done when at least two of them agree, each with evidence you have checked.

1. **Freeze the subject.** The task's acceptance criteria (from its issue or card), the exact head SHA, the diff, and the author's evidence. A new push after this point means a new panel.
2. **Spawn three verifiers** in one `task` batch. Use default agents, since they must run things. None of them is the author. Put each on a different model family when one is available; otherwise give each a different angle (behavior, edge cases, security and data). Each brief says:
   - Be skeptical: the work is not done until you prove it is. Don't trust the author's evidence; reproduce it.
   - At `<SHA>`, run the repo's checks, prove each acceptance criterion on the real surface (the repo's `verify-<app>` skill first), and make one serious attempt to break it (the riskiest path in the diff, bad input, an edge case).
   - Never push, edit the branch, or comment on the PR.
   - Reply with `VERDICT: DONE` or `VERDICT: NOT DONE`, then each criterion with the command or artifact that shows it, then every failure with a command that reproduces it.
3. **Check the receipts.** Open every artifact a vote cites and rerun at least one of its commands. A vote whose evidence is missing, or doesn't show what it claims, counts as NOT DONE.
4. **Count.** Two or more DONE with checked evidence → the task is done. Otherwise it is not: send every NOT DONE finding, with its reproduction, back to the owner; the fix makes a new head and a fresh panel.
5. **Keep the dissent.** A NOT DONE vote in a passing panel becomes a new task on the board (or a follow-up in the report) carrying its reproduction, so nothing it found is lost.

## Gates

- Verifiers vote independently: none sees another's verdict before giving its own.
- A panel covers one head SHA. Merge only that SHA (`gh pr merge --match-head-commit <SHA>`).
- Three failed panels on one task → stop that task: mark it blocked with the findings and move on.

## Output

`panel: <done|not done> at <short sha>, <k>/3 done` then one line per verifier: model, verdict, and the receipt you checked.
