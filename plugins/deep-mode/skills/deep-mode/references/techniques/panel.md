# panel

**Use when:** deciding whether a task is done, and before every merge. The panel is the verdict: three skeptical verifiers judge the work independently, and the task is done when at least two of them agree, each with evidence you have checked.
A size S change gets the light panel instead (Light panel, below). Every other change keeps the three-verifier panel.
A local S fix that nobody pushes or merges needs no panel (`references/playbooks/opening-a-pr.md`, Size S lane).

1. **Freeze the subject.** The task's acceptance criteria (from its issue or card), the exact head SHA, the diff, and the author's evidence. A new push after this point means a new panel.
   Done when the criteria, the head SHA, the diff, and the author's evidence are written into the verifier brief.
2. **Spawn three verifiers** in one `task` batch. Use default agents, since they must run things. None of them is the author. Put each on a different model family when one is available; otherwise give each a different angle (behavior, edge cases, security and data). Each brief says:
   - Be skeptical: the work is not done until you prove it is. Don't trust the author's evidence; reproduce it.
   - At `<SHA>`, run the repo's checks, prove each acceptance criterion on the real surface (the repo's `verify-<app>` skill first), and make one serious attempt to break it (the riskiest path in the diff, bad input, an edge case).
   - Never push, edit the branch, or comment on the PR.
   - Reply with `VERDICT: DONE` or `VERDICT: NOT DONE`, then each criterion with the command or artifact that shows it, then every failure with a command that reproduces it.

   Done when every verifier has replied with a verdict for that SHA.
3. **Check the receipts.** Open every artifact a vote cites and rerun at least one of its commands. A vote whose evidence is missing, or doesn't show what it claims, counts as NOT DONE.
   Done when every vote is marked checked or counted as NOT DONE, and you have one rerun command and its output per vote.
4. **Count.** Two or more DONE with checked evidence → the task is done. Otherwise it is not: send every NOT DONE finding, with its reproduction, back to the owner; the fix makes a new head and a fresh panel.
   Done when the panel line is written, and on a fail every NOT DONE finding is with the owner.
5. **Keep the dissent.** A NOT DONE vote in a passing panel becomes a new task on the board (or a follow-up in the report) carrying its reproduction, so nothing it found is lost.
   Done when every such vote has a task or follow-up that holds its reproduction.

## Light panel

The light panel is one verifier instead of three. It is used only for a size S change, as the Size S lane in `references/playbooks/opening-a-pr.md` defines it.

- The diff's measured size and paths decide S, not the author's opinion.
- Measure it with `git diff --numstat <base>...<head>`. Sum the added and deleted columns over every row. Count the rows for files.
- S means at most 30 changed lines in at most 2 files.
- S also means no path touches auth, permissions, secrets or credentials, input parsing at a trust boundary, database migrations, CI workflows, or agent config.
- Anything else is M or L and gets the three-verifier panel.

Run the steps above with these changes:

- Step 2 spawns one verifier, from a different model family than the author when one is available. Its brief is the same, except its break attempt stays within inputs the code plausibly sees. A failure only past that (a bill in the trillions) is a follow-up in the report, not NOT DONE.
- Step 4 passes only when that one verifier votes DONE (PASS in pr-conversation) with evidence you checked at the exact head.
- Step 5 does not apply, since a pass has no dissent.

The deep-mode bot (`references/techniques/github-app.md`) applies the light panel by itself when a PR's diff fits S. It judges from size and paths only; a `full-panel` label on the PR gets the three-verifier panel for what paths can't show, such as input parsing at a trust boundary.

## Gates

- Verifiers vote independently: none sees another's verdict before giving its own.
- A panel covers one head SHA. Merge only that SHA (`gh pr merge --match-head-commit <SHA>`).
- Three failed panels on one task → stop that task: mark it blocked with the findings and move on.

**Done when** the panel line names one head SHA and its count, and every DONE vote counted in it has a receipt you checked.

## Output

`panel: <done|not done> at <short sha>, <k>/3 done` then one line per verifier: model, verdict, and the receipt you checked. A light panel reports `<k>/1 done (light, S: <lines> lines, <files> files)`.
