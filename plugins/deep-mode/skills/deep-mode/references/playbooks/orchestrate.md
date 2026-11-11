# Orchestrate

Use when: a standing project or long-running goal is handed to one coordinator chat — multi-day, many stacked PRs, dozens to hundreds of subagents, few human turns ("run this whole project", "own this migration until it lands", "be my chief of staff for X", "keep pushing this goal forward across sessions"). One task to a predicate is `references/playbooks/autonomous-run.md`; one ambitious bespoke run is the **figure-it-out** technique (`references/techniques/figure-it-out.md`); work one agent could finish inside the session's budget is not a program. You run the program, never the code: decide which agent does each piece, then check what each produces.

Work two tracks at once: the tactical one (land the next unit) and the strategic one (change the environment so the unit after it goes better).

## Steps

1. Keep program state in one tracker file a cold-start coordinator can find (`$(git rev-parse --git-common-dir)/omp-resume/<program>-notes.md`, or a repo-ignored notes file; never `local://`, which is per-session; print its absolute path): units, owners, agent ids, PRs, heads, verdicts, follow-ups. Spawn workers only with `task`. No hand-rolled polling loops. Workers talk to each other directly as coworkers (the **coworkers** technique, `references/techniques/coworkers.md`); you don't relay between them.
   Keep durable knowledge in a **wiki** beside the tracker (`.../omp-resume/<program>-wiki/`), or in the shared wiki the repo or user already keeps, following its conventions. `index.md` lists every page with a one-line summary by category; each other page covers one thing (a decision, a recurring problem, a subsystem, a user preference) and links its neighbors. Pages cite sources (issues, PRs, commits, worker reports) and never copy them.
   Write wiki history, not the present: date every claim ("2026-11-11: chose X because Y"), pin code claims to a commit (`owner/repo@sha`), and supersede an old claim with a new dated one instead of rewriting it. When you learn something durable, update every page it touches and the index. Before a decision, read the index and the pages it names.
2. Assign one owner per PR. The owner is the only writer of its branch and carries it from build to merge; only it pushes, rebases, or retargets. Closing or retargeting a base PR orphans every PR above it, so the owner does that only on your call. You never author or edit code — conflicted merges, chain rebases, and fixes go to owners. Each owner self-reviews with the **pr-review** technique (`references/techniques/pr-review.md`) in local mode before each push, triaging its findings with its other review comments and reporting the review line.
3. Isolate owners: subagents share one workspace, so give each owner its own `git worktree` and exclusive file ownership; name the paths it may and may not write. Worktrees still share one `.git`, ports and databases:
   - Create worktrees one at a time; parallel `git worktree add` from a remote-tracking ref collides on `.git/config`.
   - Push with an explicit refspec (`git push <remote> HEAD:refs/heads/<branch>`), never `-u`, which also writes `.git/config`.
   - A relative remote URL resolves against the directory the push runs in; push from the main checkout when worktrees live elsewhere.
   - Give each owner its own dev-server port and database.
4. Give each independent task a fresh worker whose kickoff carries everything it needs, including each upstream report it depends on, pasted in full, and the team roster: every coworker's agent id, role, and files owned.
5. Write every kickoff with: goal, the evidence that proves done (a command and its expected output, a `verify-<app>` check, or an artifact), allowed and forbidden paths, and the hard stops (SKILL.md Autonomy). Can't name the evidence → the unit isn't scoped yet.
6. Start with one unit: take it through kickoff, owner, verifier, and landing before fanning out, so a kickoff flaw costs one agent, not fifty. On near-identical cheap units, the first unit is that test.
7. Fan out: about ten workers in flight per coordinator; start the next as each finishes instead of waiting on a batch. Add a sub-coordinator only when one area has many parallel workers; it owns that area's kickoffs and sends you one rollup, never raw reports. Max three levels: you, sub-coordinators, workers.
8. When new work needs a worker's checkout, uncommitted changes, or running process, message that worker (`write agent://<id>`, which also revives it) or spawn a fresh worker pointed at its worktree/branch. There is no fork. Never message a worker just to check on it.
9. Give each PR a **panel** (`references/techniques/panel.md`): three verifiers that didn't author it, default `task` agents (they must run the app and prove behavior; `reviewer` is read-only and only reviews a diff), on different model families when available. The owner merges only on a panel pass at the current head. That pass includes a pr-review round in PR mode on the current head with no P0/P1 open and every P2 fixed or dismissed with a reason; the review is evidence, never a substitute for the panel's live proof.
10. Supervise by artifacts: read the diff or artifact, not only the summary. Green CI is an input, not a verdict; behavioral work needs more than a type check. A new push needs a new verdict and a new pr-review round. Sample each sub-coordinator's kickoffs while its workers run and fix its instructions when one fails. The same pr-review finding class on two or more PRs → hand it to a worker running the **correct** technique (`references/techniques/correct.md`) for a lint rule, type, or test.
11. Send back work that drifts from scope or grows past the ask; keep only fixes that block the program, park the rest as follow-ups.
12. Check live PR state before reporting it: `gh pr view <pr>` and `gh pr checks <pr>`, not a worker's last report. Account for every spawned worker as done, replaced, or absorbed.
13. Stop or replace a worker that stalls or loops, judged by pushes and PR activity, not status text. Retry by cause: smaller scope after a context limit, same kickoff after a dropped connection, a different model after a tool error. After two retries, drop the unit and replan around it. A stopped worker that returns late: check its result against the PR's current state and hand unique findings to a fresh worker.
14. Strategic track. Before each new unit, ask what change to the environment would make it and later units go right by default, and hand that to a worker as its own unit: narrower interfaces, a lint rule, type, or test (**correct**), a pre-commit hook (`references/techniques/pre-commit.md`), a git guard (`references/techniques/git-guardrails.md`), a `CODING_STANDARDS.md` rule the reviewer enforces, or data the agents lack (dev-server logs teed to a file, a test database, browser access). No workarounds: a deviation from the repo's conventions gets fixed before more feature work lands on top of it.
15. Run the **retro** technique (`references/techniques/retro.md`) on about one in five finished workers, the ones that failed, stalled, or needed a retry first, reading the worker's `history://<id>` transcript. Decide which candidates to pursue yourself and dispatch them as units; file the rest.
16. A chunk too big for one PR goes through the Spec playbook (`references/playbooks/spec.md`), then Tickets (`references/playbooks/tickets.md`), then Implement spec (`references/playbooks/implement-spec.md`), with this playbook still owning the workers.
17. Schedule the recurring work: a wiki lint (contradictions, orphan pages, missing links, claims newer sources overtook), a sweep of open PRs and issues, and checks on anything the goal depends on. Use the harness's scheduler if it has one; otherwise a background heartbeat job as in Autonomous run step 3. Recurring work that should outlive this session goes in the final report as a proposed schedule (cron or Task Scheduler running `omp -p @<prompt file>`, or the harness's equivalent) for the user to enable.

## Gates

- Merging needs a **panel** pass (`references/techniques/panel.md`) at the current head plus a pr-review round on that head; landing goes through `references/playbooks/shipping.md`. A clean review never waives live proof, and a P2 doesn't block once it has a recorded dismissal.
- Make decisions yourself per SKILL.md Autonomy and log them. Ask the user (`ask`) only for a hard stop or a dead end that survived a replan. Rebase mechanics, retries, CI flakes, review triage, product calls, merges, and "should I keep going" never reach the user.
- Two failed retries on a unit → drop and replan, don't retry a third time.

## Evidence

- What landed against the goal.
- Each PR's live state and verdict, with its link and the pr-review technique's review line.
- Repeated pr-review finding classes routed to **correct**, and the guardrail each produced.
- Environment changes made on the strategic track, and the retros sampled with what each produced.
- The wiki's path and the pages added or superseded.
- What was dropped and why; parked follow-ups.
- Every worker accounted for.
- Decisions made on the user's behalf, each with how to reverse it; anything still waiting on the user.
