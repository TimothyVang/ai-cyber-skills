# Opening a PR

Use when: ending any playbook that lands code, and only when the user asked to commit, push, or open a PR. Without that ask, stop at a clean working tree diff and report.

## Steps

1. Confirm the user asked for git writes. No ask → stop here; report the diff instead.
2. Work from a git worktree off main. Parallel `task` agents on one branch: give each exclusive files, or a separate worktree. Dirty branch with unrelated work → save it as a patch, fresh worktree, apply. Snarled worktree → reset from main, redo minimally.
3. Commit liberally, then rebase into small, ordered commits. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs to the just-made commit; new commit when separable. Bodies don't restate the subject.
4. Before commit, review the diff for slop; before review, apply the **no-comments** technique (`references/techniques/no-comments.md`).
5. Optional pre-PR review: when `greptile whoami` succeeds, run the **greptile** technique (`references/techniques/greptile.md`) section "before the PR exists" on the committed branch and triage its findings with technique step 5. CLI absent or signed out → skip it; never install or sign in without the user's go.
6. Write titles, descriptions, and commit bodies with the **technical-writing** technique (`references/techniques/technical-writing.md`; every layer except Diátaxis; STE vocabulary: one word per action, keep articles, plain verb over `-ing`), then the **unslop** technique (`references/techniques/unslop.md`).
7. Title: Conventional Commits `type(scope): subject`, no trailing period. Type `feat|fix|docs|refactor|test|chore|perf`; scope is the area; subject short, imperative, names the real symbol carrying the change.
8. Body: a one-minute briefing for a reviewer who has the diff; short sentences, few identifiers; under ~40 lines (it becomes the squash body). `##` headings in this order, dropping empty ones:
   - `## Why`: problem and approach, 1–3 sentences. No SHAs, rebase genealogy, "based on main".
   - `## What changed`: 1–3 bullets; name both sides of a rename or retarget.
   - `## Scope`: always; 1–3 items on what it covers and deliberately leaves out.
   - `## Tradeoffs`: only rejected alternatives a reviewer would ask about.
   - `## Blast Radius`: 1–2 sentences on who/what it touches and why safe or risky; if main is red, the cost of leaving it red.
   - `## Verification`: 1–3 bullets, each a real run path and outcome. Perf: one primary number with unit, `before → after`, link to the arena/swarm directory.
   - Then videos/screenshots that prove a claim. SHAs, lane recitals, file-by-file checklists, "CLEAN" verdicts go in a linked artifact.
9. Use `gh` for every PR operation (create, edit, view, watch, merge). Do not require Graphite.
10. Prefer five narrow PRs to one large one. Stack = base-branch chain: root targets trunk; each child rebases onto its parent's exact tip and targets the parent (`gh pr create --base <parent-branch>`, retarget with `gh pr edit <pr> --base <parent-branch>`). When a parent merges, rebase its child onto trunk and retarget. Branch from trunk only for independent work; rebase on trunk before substantial stack work.
11. Open every PR ready, never draft (omit `--draft`; if it opens as draft, `gh pr ready <n>`); Greptile skips drafts by default. Run `gh pr view <n>` before referring to PR status.
12. After opening, run the **greptile** technique steps 1 Detect, 2 Trigger, and 3 Wait (background job) to get the first round on the current head. Not installed → record that and continue; never a blocker.
13. Post the URL and keep building; add the technique's greptile line when the round lands.

## Gates

- No commit, push, PR, or merge without the user's ask.
- Do not babysit (watch checks, answer review) per PR. Finish the phase or stack first; run a babysit pass (`gh pr checks --watch`, `gh pr view --json reviews,comments`, and the **greptile** technique steps 4-7 on the current head) only when the user asks, after the whole stack exists. Push back when feedback drifts from intent.
- A subagent that opens a PR posts the URL and its greptile line and returns without babysitting, unless its brief assigns the babysit loop.
- Greptile is evidence, not a gate: a clean score never waives the Verification section's real runs, and Greptile not installed never blocks opening. Never report a round for a stale head SHA; a new push needs a new round.

## Evidence

- PR URL(s), title(s), base branch per PR, and stack order.
- Ready (not draft) status confirmed via `gh pr view`.
- Verification section contents.
- Per PR, the technique's greptile line (`greptile: <score>/5 at <short sha>, ...` or `greptile: not installed or not triggered`), plus pre-PR `greptile review` findings and their triage when it ran.
