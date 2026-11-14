# panel

**Use when:** deciding whether a task is done, and before every merge. The panel is the verdict: three skeptical verifiers judge the work independently, and the task is done when at least two of them agree, each with evidence you have checked.
Every publication uses exactly three reviewers, including size S changes. All three valid responses are required; an unavailable reviewer cannot be outvoted.
A local S fix lands on no branch, so it needs no panel (`references/playbooks/opening-a-pr.md`, Size S lane).

1. **Freeze the subject.** The task's acceptance criteria (from its issue or card), the exact head SHA, the diff, and the author's evidence. A new push after this point means a new panel.
   Done when the criteria, the head SHA, the diff, and the author's evidence are written into the verifier brief.
2. **Spawn three verifiers** in one `task` batch. Use default agents, since they must run things. None of them is the author. Put each on a different model family when one is available; otherwise give each a different angle (behavior, edge cases, security and data). Each brief says:
   - Be skeptical: the work is not done until you prove it is. Don't trust the author's evidence; reproduce it.
   - At `<SHA>`, run the repo's checks, prove each acceptance criterion on the real surface (the repo's `verify-<app>` skill first), and make one serious attempt to break it (the riskiest path in the diff, bad input, an edge case).
   - Never push, edit the branch, or comment on the PR.
   - Reply with `VERDICT: DONE` or `VERDICT: NOT DONE`, then each criterion with the command or artifact that shows it, then every failure with a command that reproduces it.

   Done when every verifier has replied with a verdict for that SHA.
3. **Check the receipts.** Open every artifact a vote cites and rerun at least one of its commands. Missing or unverifiable evidence makes that response unavailable and blocks the round; a valid adverse result is NOT DONE.
   Done when all three responses have checked receipts for the frozen subject.
4. **Count.** All three valid responses and two or more DONE with checked evidence → the panel passes. Otherwise it does not: send every finding, with its reproduction, back to the owner; a changed head needs a fresh panel.
   Done when the panel line is written, and on a fail every NOT DONE finding is with the owner.
5. **Keep the dissent.** A NOT DONE vote in a passing panel becomes a new task on the board (or a follow-up in the report) carrying its reproduction, so nothing it found is lost.
   Done when every such vote has a task or follow-up that holds its reproduction.

## Gates

- Verifiers vote independently: none sees another's verdict before giving its own.
- A panel covers one head SHA. Merge only that SHA (`gh pr merge --match-head-commit <SHA>`).
- Majority does not waive a failing deterministic check, changed acceptance contract, ownership or permission gate, or stale evidence. Retain dissent; resolve blocking review findings before merge.
- Three failed panels on one task → stop that task: mark it blocked with the findings and move on.

**Done when** the panel line names one head SHA and its count, and every DONE vote counted in it has a receipt you checked.

## Output

`panel: <done|not done> at <short sha>, <k>/3 done` then one line per verifier: model, verdict, and the receipt you checked.
