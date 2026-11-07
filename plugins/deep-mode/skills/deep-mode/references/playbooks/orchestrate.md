# Orchestrate

Use when: a standing project is handed to one coordinator chat — multi-day, many stacked PRs, dozens to hundreds of subagents, few human turns ("run this whole project", "own this migration until it lands"). One task to a predicate is `references/playbooks/autonomous-run.md`; one ambitious bespoke run is the **figure-it-out** technique (`references/techniques/figure-it-out.md`); work one agent could finish inside the session's budget is not a program. You run the program, never the code: decide which agent does each piece, then check what each produces.

## Steps

1. Keep program state in one tracker file a cold-start coordinator can find (`$(git rev-parse --git-common-dir)/omp-resume/<program>-notes.md`, or a repo-ignored notes file; never `local://`, which is per-session; print its absolute path): units, owners, agent ids, PRs, heads, verdicts, follow-ups. Spawn workers only with `task`. No hand-rolled polling loops; never relay messages or status between agents.
2. Assign one owner per PR. The owner is the only writer of its branch and carries it from build to merge; only it pushes, rebases, or retargets. Closing or retargeting a base PR orphans every PR above it, so the owner does that only on your call. You never author or edit code — conflicted merges, chain rebases, and fixes go to owners. Each owner runs the **greptile** technique (`references/techniques/greptile.md`) loop, steps 1-7, on its PR after every push, within the user's grant, triaging Greptile findings with its other review comments and reporting the greptile line.
3. Isolate owners: subagents share one workspace, so give each owner its own `git worktree` and exclusive file ownership; name the paths it may and may not write.
4. Give each independent task a fresh worker whose kickoff carries everything it needs, including each upstream report it depends on, pasted in full. Workers can't see siblings.
5. Write every kickoff with: goal, the evidence that proves done (a command and its expected output, a `verify-<app>` check, or an artifact), allowed and forbidden paths, forbidden actions (push/merge only if the user granted them). Can't name the evidence → the unit isn't scoped yet.
6. Start with one unit: take it through kickoff, owner, verifier, and landing before fanning out, so a kickoff flaw costs one agent, not fifty. On near-identical cheap units, the first unit is that test.
7. Fan out: about ten workers in flight per coordinator; start the next as each finishes instead of waiting on a batch. Add a sub-coordinator only when one area has many parallel workers; it owns that area's kickoffs and sends you one rollup, never raw reports. Max three levels: you, sub-coordinators, workers.
8. When new work needs a worker's checkout, uncommitted changes, or running process, message that worker (`write agent://<id>`, which also revives it) or spawn a fresh worker pointed at its worktree/branch. There is no fork. Never message a worker just to check on it.
9. Give each PR a verifier that isn't its author: a default `task` agent (it must run the app and prove behavior; `reviewer` is read-only and only reviews a diff), on a different model family than the author's when one is available. The owner merges only on that verifier's pass at the current head. When Greptile is installed (technique step 1), that pass requires a Greptile round on the current head (step 3) with every finding fixed or dismissed with a reason; the round is evidence, never a substitute for the verifier's live proof. Not installed → record it; never a blocker.
10. Supervise by artifacts: read the diff or artifact, not only the summary. Green CI is an input, not a verdict; behavioral work needs more than a type check. A new push needs a new verdict and a new Greptile round. Sample each sub-coordinator's kickoffs while its workers run and fix its instructions when one fails. The same Greptile finding class on two or more PRs → hand it to a worker running the **correct** technique (`references/techniques/correct.md`) for a lint rule, type, or test (greptile step 5).
11. Send back work that drifts from scope or grows past the ask; keep only fixes that block the program, park the rest as follow-ups.
12. Check live PR state before reporting it: `gh pr view <pr>` and `gh pr checks <pr>`, not a worker's last report. Account for every spawned worker as done, replaced, or absorbed.
13. Stop or replace a worker that stalls or loops, judged by pushes and PR activity, not status text. Retry by cause: smaller scope after a context limit, same kickoff after a dropped connection, a different model after a tool error. After two retries, drop the unit and replan around it. A stopped worker that returns late: check its result against the PR's current state and hand unique findings to a fresh worker.

## Gates

- Merging requires the user's explicit grant for the program (or per PR) plus a non-author verifier's pass at the current head (including a Greptile round on that head when installed); without the grant, owners stop at merge-ready and landing goes through `references/playbooks/shipping.md`. A clean Greptile score never waives live proof, and a non-clean round doesn't block once every remaining finding has a recorded dismissal.
- Ask the user (`ask`) only for a real decision or blocker: an irreversible action, a product/preference call no experiment settles, or a dead end that survived a replan. Rebase mechanics, retries, CI flakes, review triage, and "should I keep going" never reach the user.
- Two failed retries on a unit → drop and replan, don't retry a third time.

## Evidence

- What landed against the goal.
- Each PR's live state and verdict, with its link and the technique's greptile line.
- Repeated Greptile finding classes routed to **correct**, and the guardrail each produced.
- What was dropped and why; parked follow-ups.
- Every worker accounted for.
- Decisions waiting on the user.
