# Opening a PR

Use when: ending any playbook that lands code. Opening the PR is part of the work, not a step to ask about (SKILL.md Autonomy).

## Size S lane

A size S change takes a shorter lane to merge. The diff decides the size, not the author's opinion.

Rules:

- A change is size S when it has at most 30 changed lines (added plus deleted) in at most 2 files.
- Measure it with `git diff --numstat <base>...<head>`. Sum both number columns over every row. Count the rows for files.
- It must touch nothing about auth, permissions, secrets or credentials, input parsing at a trust boundary, database migrations, CI workflows, or agent config.
- Anything else is M or L and takes the Steps below in full.
- The deep-mode bot (`references/techniques/github-app.md`) applies the light panel by itself when a PR's diff fits S.

Steps:

1. Restate the change in one line. Done when the one-line restate is your first message on the task.
2. Make the change in a worktree off main and commit it (Steps 2 and 3 below). Done when `git diff --numstat origin/<default>...HEAD` shows at most 30 changed lines in at most 2 files and no path in the areas the rules exclude. If it shows more, leave this lane and run the Steps below.
3. Prove it once on the real artifact. Done when you have one real run's command and output that shows the change working.
4. Review your own diff yourself against the **pr-review** checklist (`references/techniques/pr-review.md`), which is its four lenses and its smell baseline. Spawn no subagents and do not run PR-Agent. Done when every finding is fixed or dismissed with a reason and you have the pr-review line for the committed head.
5. Open the PR as in Steps 6 to 11 below. Done when `gh pr view <n> --json isDraft,url` shows `false` and the URL.
6. Land it through the **pr-conversation** technique (`references/techniques/pr-conversation.md`) with a **light panel** (`references/techniques/panel.md`, Light panel).
   One verifier, from a different model family when one is available, must PASS with evidence at the exact head.
   Done when that vote is PASS at the head SHA, the required checks are green, and the repo check (a base-branch `.deep-mode.json` `"check"`) exits 0 at that head.
7. Merge with `gh pr merge <n> --match-head-commit <sha>`. Done when `gh pr view <n> --json state` prints `MERGED`.
8. Run the trunk check on the merge commit (pr-conversation step 8). Done when the repo check passes there, or a verifier passes it when no check is set, or a revert PR is open.

## Steps

The S lane above skips step 5's subagents and step 12 (PR-Agent). Its panel is the light panel.

1. Check the change is ready: verified on the real surface, no hard stop (SKILL.md Autonomy) involved. Done when you have the real run's command and output and no hard stop applies.
2. Work from a git worktree off main. Parallel `task` agents on one branch: give each exclusive files, or a separate worktree. Dirty branch with unrelated work → save it as a patch, fresh worktree, apply. Snarled worktree → reset from main, redo minimally.
   Done when `git status` in the worktree shows only this work.
3. Commit liberally, then rebase into small, ordered commits. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs to the just-made commit; new commit when separable. Bodies don't restate the subject.
   Done when `git log --oneline origin/<default>..HEAD` lists small commits in story order and no fixup commit is left.
4. Before commit, review the diff for slop; before review, apply the **no-comments** technique (`references/techniques/no-comments.md`). Done when the diff has no comment outside the no-comments keep-list.
5. Before pushing, run the **pr-review** technique (`references/techniques/pr-review.md`) in local mode on the committed branch and fix, dismiss with a reason, or escalate per its step 5.
   The S lane reviews its diff itself, with no subagents.
   Done when every finding is fixed, dismissed with a reason, or escalated, and you have the pr-review line for the committed head.
6. Write titles, descriptions, and commit bodies with the **technical-writing** technique (`references/techniques/technical-writing.md`; every layer except Diátaxis; STE vocabulary: one word per action, keep articles, plain verb over `-ing`), then the **unslop** technique (`references/techniques/unslop.md`).
   Done when the unslop pass flags nothing left in the title, body, or commit bodies.
7. Title: Conventional Commits `type(scope): subject`, no trailing period. Type `feat|fix|docs|refactor|test|chore|perf`; scope is the area; subject short, imperative, names the real symbol carrying the change.
   Done when the title matches `type(scope): subject` with an allowed type and no trailing period.
8. Body: a one-minute briefing for a reviewer who has the diff; short sentences, few identifiers; under ~40 lines (it becomes the squash body). `##` headings in this order, dropping empty ones:
   - `## Why`: problem and approach, 1 to 3 sentences. No SHAs, rebase genealogy, "based on main".
   - `## What changed`: 1 to 3 bullets; name both sides of a rename or retarget.
   - `## Scope`: always; 1 to 3 items on what it covers and deliberately leaves out.
   - `## Tradeoffs`: only rejected alternatives a reviewer would ask about.
   - `## Blast Radius`: 1 to 2 sentences on who/what it touches and why safe or risky; if main is red, the cost of leaving it red.
   - `## Verification`: 1 to 3 bullets, each a real run path and outcome. Perf: one primary number with unit, `before → after`, link to the arena/swarm directory.
   - Then videos/screenshots that prove a claim. SHAs, lane recitals, file-by-file checklists, "CLEAN" verdicts go in a linked artifact.

   Done when the body has `## Scope` and `## Verification`, its headings follow this order, and it is under 40 lines.
9. Use `gh` for every PR operation (create, edit, view, watch, merge). Do not require Graphite. Done when every PR operation you ran was a `gh` command.
10. Prefer five narrow PRs to one large one. Stack = base-branch chain: root targets trunk; each child rebases onto its parent's exact tip and targets the parent (`gh pr create --base <parent-branch>`, retarget with `gh pr edit <pr> --base <parent-branch>`). When a parent merges, rebase its child onto trunk and retarget. Branch from trunk only for independent work; rebase on trunk before substantial stack work.
    Done when `gh pr view <n> --json baseRefName` shows trunk for the root and the parent's branch for each child.
11. Open every PR ready, never draft (omit `--draft`; if it opens as draft, `gh pr ready <n>`). Run `gh pr view <n>` before referring to PR status. Done when `gh pr view <n> --json isDraft` prints `false` for every PR.
12. Run the **pr-agent** technique (`references/techniques/pr-agent.md`) on the PR: describe, review, improve, with each finding triaged. Repeat it after each later push. It needs `omp`; on a machine without it, skip this step, say so in the report, and let pr-conversation's review in step 13 carry it.
    The S lane skips this step.
    Done when describe, review, and improve ran on the current head and every finding has a triage outcome, or the report says why it was skipped.
13. Hand the PR to the **pr-conversation** technique (`references/techniques/pr-conversation.md`), which reviews, fixes, verifies, and lands it with no ask. When the deep-mode bot (`references/techniques/github-app.md`) watches the repo, it picks the PR up on its next poll; don't run a second conversation in the session.
    A stack is the exception: finish it, then land it through `references/playbooks/shipping.md`. The bot merges only into the default branch or a protected branch, so a stack's children wait on their own until they target the trunk.
    To keep it from merging the stack's root, or any PR, before you are ready, add the `hold` label (`gh label create hold --force`, then `gh pr edit <n> --add-label hold`) and remove it when the PR may land.
    Done when the PR has a pr-conversation line, or the bot's kickoff comment is on it, or it carries `hold` while its stack waits for Shipping.
14. Post the URL and keep building; report the pr-review line from step 5 for the pushed head. Done when the report holds every PR URL and its pr-review line for the pushed head.

## Gates

- Commits, pushes, and PRs need no ask. Merges need a panel pass (`references/techniques/panel.md`): your own single PR lands through pr-conversation, and a stack through `references/playbooks/shipping.md`.
- A size S PR (Size S lane) needs only the light panel. Every other PR needs the three-verifier panel.
- Do not babysit (watch checks, answer review) each PR of a stack. Finish the phase or stack first; then run a babysit pass (`gh pr checks --watch`, `gh pr view --json reviews,comments`, and the **pr-review** technique steps 5-7 in PR mode on the current head) once the whole stack exists. Push back when feedback drifts from intent.
- A subagent that opens a PR posts the URL and its review line and returns without babysitting or landing, unless its brief assigns that loop.
- pr-review is evidence, not a gate: a clean review never waives the Verification section's real runs. Never report a review for a stale head SHA; a new push needs a new round.

## Evidence

- PR URL(s), title(s), base branch per PR, and stack order.
- Ready (not draft) status confirmed via `gh pr view`.
- Verification section contents.
- Per PR, the pr-review technique's review line (`review: <ready|changes needed|needs discussion> at <short sha>, ...`) and the local-mode findings with their triage.
- Per S lane PR, the `git diff --numstat` totals (lines and files) that put it in S.
- Per PR handed on, the pr-conversation line (`conversation: <merged|blocked> at <short sha>, ...`), or that the deep-mode bot took it.
