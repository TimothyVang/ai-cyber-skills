# Run a goal

Use when: one goal must be driven to a checkable end without the human. Session scale covers "loop until X", "keep going until green", "going to bed, finish it". Program scale covers "run this whole project", "own this migration until it lands", "be my chief of staff for X", "keep pushing this goal forward across sessions". You own the exit condition. Define done, then drive to it without stopping.
One ambitious run needing a bespoke workflow is the **figure-it-out** technique (`references/techniques/figure-it-out.md`). A queue of work items to turn into merged PRs is Work a queue (`references/playbooks/work-a-queue.md`).

## Pick the scale

| What the user has | Use |
|---|---|
| One task, driven to a completion predicate in this session | Session scale |
| A standing project or long-running goal (multi-day, many stacked PRs, dozens to hundreds of subagents, few human turns) | Program scale |
| Work one agent could finish inside the session's budget | Session scale. It is not a program. |
| A goal to run headless or overnight with no session open | `assets/loop/loop.py` (Session scale step 3) |
| PRs and issues handled with no session at all | The GitHub App bot |

Headless engines this playbook may use:
- `assets/loop/loop.py` runs a goal file under headless omp, Claude Code, or Codex until its check passes. Details are in the Self-authoring playbook (`references/playbooks/self-authoring.md`).
- The GitHub App bot (`references/techniques/github-app.md`) polls the user's repos and runs pr-conversation and issue-conversation with no session open.

## Session scale

One task, one session, one completion predicate.

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero). Write down the command or check that evaluates it.
   Done when the predicate and its command are written down and one run of the command shows the current state.
2. Start a decision trail per the **show-me-your-work** technique (`references/techniques/show-me-your-work.md`).
   Done when the trail file exists and its absolute path is printed.
3. Pick the wake mechanism:
   - An event to watch (CI, a merge, a ref advancing) → a background `bash` job that blocks on it (`gh pr checks <pr> --watch`, `gh run watch <id>`, `timeout: 0`); its result auto-delivers. Add a long time-based heartbeat as fallback (background `sleep` with `timeout: 0`, or `sleep 3300` with `timeout: 3600`).
   - No event → a fixed-interval heartbeat (background `bash` `sleep`) sized to when the result is worth re-checking. Set `timeout: 0` (or `sleep 3300` with `timeout: 3600`), because the default 300s deadline kills longer sleeps.
   - Unattended across sessions, from a script or CI, or in another harness → write a goal file and run `python <deepmodebot skill>/assets/loop/loop.py run <goal.md>`. It runs headless omp, Claude Code, or Codex until the check passes, and it is capped, stall-stopped, and tamper-checked.
   - Interactive in one session → the harness's native `/goal` with the predicate's command named in it. Details: `references/playbooks/self-authoring.md`.
   - Done when the wake job, `loop.py` run, or `/goal` is armed and its id or command is in the trail.
4. Each iteration: make the smallest change the evidence justifies, then evaluate the predicate.
   Done when the predicate's command has run on the changed code.
5. Advanced → keep it and commit it. Didn't help → discard it. "Might help" belt-and-suspenders gets reverted, not left to ride.
   Done when the iteration's change is either committed or reverted, and `git status --porcelain` shows nothing left from it.
6. Sequence the work into verifiable units, verifying each before the next instead of batching checks at the end (`references/principles/sequence-verifiable-units.md`).
   Done when every unit kept so far had its check pass before the next unit started.
7. Own mid-run discoveries that support the goal: broken skills, related bugs, flaky verifiers, review noise, tooling failures, orphaned follow-ups, fixable drift. Fix them yourself, out-of-band fixes kept separate from the main change (on their own branch and PR). Return to the predicate after each side fix.
   Done when each discovery has its own branch and PR, and the next iteration is back on the predicate.
8. Checkpoint every iteration in the trail: one row for what changed and whether the predicate moved.
   Done when the trail has one row per iteration run.
9. Plateau → pivot the approach and keep going; a plateau is not a stop.
   Done when the trail records the pivot and the next iteration tries a different approach.

## Program scale

You run the program, never the code. Decide which agent does each piece, then check what each produces.

Work two tracks at once: the tactical one (land the next unit) and the strategic one (change the environment so the unit after it goes better).

1. Keep program state in one tracker file a cold-start coordinator can find: units, owners, agent ids, PRs, heads, verdicts, follow-ups.
   - The file is `$(git rev-parse --git-common-dir)/omp-resume/<program>-notes.md`, or a repo-ignored notes file. Never `local://`, which is per-session. Print its absolute path.
   - Spawn workers only with `task`. No hand-rolled polling loops. Workers talk to each other directly as coworkers (the **coworkers** technique, `references/techniques/coworkers.md`); you don't relay between them.
   - Keep durable knowledge in a **wiki** beside the tracker (`.../omp-resume/<program>-wiki/`), or in the shared wiki the repo or user already keeps, following its conventions. `index.md` lists every page with a one-line summary by category.
   - Each other page covers one thing (a decision, a recurring problem, a subsystem, a user preference) and links its neighbors. Pages cite sources (issues, PRs, commits, worker reports) and never copy them.
   - Write wiki history, not the present. Date every claim ("2026-11-11: chose X because Y"), pin code claims to a commit (`owner/repo@sha`), and supersede an old claim with a new dated one instead of rewriting it.
   - When you learn something durable, update every page it touches and the index. Before a decision, read the index and the pages it names.
   - Done when the tracker file and the wiki's `index.md` exist and both absolute paths are printed.
2. Assign one owner per PR. The owner is the only writer of its branch and carries it from build to merge; only it pushes, rebases, or retargets. Closing or retargeting a base PR orphans every PR above it, so the owner does that only on your call.
   You never author or edit code. Conflicted merges, chain rebases, and fixes go to owners. Each owner self-reviews with the **pr-review** technique (`references/techniques/pr-review.md`) in local mode before each push, triaging its findings with its other review comments and reporting the review line.
   Done when every open PR has exactly one owner in the tracker.
3. Isolate owners. Subagents share one workspace, so give each owner its own `git worktree` at `<root>/.worktrees/<branch>` (inside the repo, git-excluded; never a sibling or temp folder, per SKILL.md "Contain the work") and exclusive file ownership. Name the paths it may and may not write. Worktrees still share one `.git`, ports and databases:
   - Create worktrees one at a time; parallel `git worktree add` from a remote-tracking ref collides on `.git/config`.
   - Push with an explicit refspec (`git push <remote> HEAD:refs/heads/<branch>`), never `-u`, which also writes `.git/config`.
   - A relative remote URL resolves against the directory the push runs in; push from the main checkout.
   - Give each owner its own dev-server port and database.
   - Done when the tracker lists each owner's worktree path, port, and database, and no two owners share one.
4. Give each independent task a fresh worker whose kickoff carries everything it needs, including each upstream report it depends on, pasted in full, and the team roster: every coworker's agent id, role, and files owned.
   Done when every kickoff holds its upstream reports and the roster.
5. Write every kickoff with: goal, the evidence that proves done (a command and its expected output, a `verify-<app>` check, or an artifact), allowed and forbidden paths, and the hard stops (SKILL.md Autonomy). Can't name the evidence → the unit isn't scoped yet.
   Done when every kickoff names its proof, its allowed and forbidden paths, and the hard stops.
6. Start with one unit. Take it through kickoff, owner, verifier, and landing before fanning out, so a kickoff flaw costs one agent, not fifty. On near-identical cheap units, the first unit is that test.
   Done when the first unit has landed or been dropped with a reason, and each kickoff flaw it exposed is fixed in the kickoff you reuse.
7. Fan out: about ten workers in flight per coordinator; start the next as each finishes instead of waiting on a batch. Add a sub-coordinator only when one area has many parallel workers; it owns that area's kickoffs and sends you one rollup, never raw reports. Max three levels: you, sub-coordinators, workers.
   Done when about ten workers are in flight, or every remaining unit is running or done.
8. When new work needs a worker's checkout, uncommitted changes, or running process, message that worker (`write agent://<id>`, which also revives it) or spawn a fresh worker pointed at its worktree/branch. There is no fork. Never message a worker just to check on it.
   Done when the tracker shows the new work under the worker holding that state, or under a fresh worker on its worktree.
9. Give each PR a **panel** (`references/techniques/panel.md`): three verifiers that didn't author it (one, the light panel, for a size S PR), default `task` agents (they must run the app and prove behavior; `reviewer` is read-only and only reviews a diff), on different model families when available.
   The owner merges only on a panel pass at the current head. That pass includes a pr-review round in PR mode on the current head with no P0/P1 open and every P2 fixed or dismissed with a reason; the review is evidence, never a substitute for the panel's live proof.
   Done when every merged PR has a panel pass and a pr-review line at its merge head in the tracker.
10. Supervise by artifacts. Read the diff or artifact, not only the summary. Green CI is an input, not a verdict; behavioral work needs more than a type check. A new push needs a new verdict and a new pr-review round.
    Sample each sub-coordinator's kickoffs while its workers run and fix its instructions when one fails. The same pr-review finding class on two or more PRs → hand it to a worker running the **correct** technique (`references/techniques/correct.md`) for a lint rule, type, or test.
    Done when every verdict in the tracker names the diff or artifact you read at that head.
11. Send back work that drifts from scope or grows past the ask; keep only fixes that block the program, park the rest as follow-ups.
    Done when every out-of-scope change is out of its PR or parked as a follow-up in the tracker.
12. Check live PR state before reporting it: `gh pr view <pr>` and `gh pr checks <pr>`, not a worker's last report. Account for every spawned worker as done, replaced, or absorbed.
    Done when every PR you report matches a `gh pr view` and `gh pr checks` run just before the report, and every spawned worker is marked done, replaced, or absorbed.
13. Stop or replace a worker that stalls or loops, judged by pushes and PR activity, not status text. Retry by cause: smaller scope after a context limit, same kickoff after a dropped connection, a different model after a tool error. After two retries, drop the unit and replan around it.
    A stopped worker that returns late: check its result against the PR's current state and hand unique findings to a fresh worker.
    Done when no running worker has gone an hour, or the interval you set for it, without a push or PR activity, and no unit has had a third retry.
14. Strategic track. Before each new unit, ask what change to the environment would make it and later units go right by default, and hand that to a worker as its own unit.
    Candidates: narrower interfaces, a lint rule, type, or test (**correct**), a pre-commit hook (`references/techniques/pre-commit.md`), a git guard (`references/techniques/git-guardrails.md`), a `CODING_STANDARDS.md` rule the reviewer enforces, or data the agents lack (dev-server logs teed to a file, a test database, browser access).
    No workarounds. A deviation from the repo's conventions gets fixed before more feature work lands on top of it.
    Done when each new unit has an environment change dispatched as its own unit, or a tracker note that none applies.
15. Run the **retro** technique (`references/techniques/retro.md`) on about one in five finished workers, the ones that failed, stalled, or needed a retry first, reading the worker's `history://<id>` transcript. Decide which candidates to pursue yourself and dispatch them as units; file the rest.
    Done when the tracker lists each sampled retro and marks each candidate it produced dispatched or filed.
16. A chunk too big for one PR goes through the Spec playbook (`references/playbooks/spec.md`), then Tickets (`references/playbooks/tickets.md`), then Phased build in build mode (`references/playbooks/phased-build.md`), with this playbook still owning the workers.
    Done when the chunk has a spec, tickets, and an integration branch with an owner in the tracker.
17. Schedule the recurring work: a wiki lint (contradictions, orphan pages, missing links, claims newer sources overtook), a sweep of open PRs and issues, and checks on anything the goal depends on.
    Use the harness's scheduler if it has one; otherwise a background heartbeat job as in Session scale step 3. Recurring work that should outlive this session goes in the final report as a proposed schedule (cron or Task Scheduler running `omp -p @<prompt file>`, or the harness's equivalent) for the user to enable.
    Done when each recurring job is scheduled with its id in the tracker, or listed in the final report as a proposed schedule.

## Gates

Both scales:
- Stop only when the completion predicate is met (session scale step 1; at program scale, the goal's acceptance criteria), or on a genuine dead end (surface it rather than spin).
- Never relax the predicate to declare victory.
- Don't park reversible work for the human or use `ask`. Decide product and design calls yourself and log them (SKILL.md Autonomy). Surface only irreversible actions outside the grant, what only the user can supply, or a real dead end.
- Push and open PRs as the work needs. Merges need a panel pass and go through `references/playbooks/shipping.md`.

Program scale also:
- Merging needs a **panel** pass (`references/techniques/panel.md`) at the current head plus a pr-review round on that head; landing goes through `references/playbooks/shipping.md`. A clean review never waives live proof, and a P2 doesn't block once it has a recorded dismissal.
- Ask the user (`ask`) only for a hard stop or a dead end that survived a replan. Rebase mechanics, retries, CI flakes, review triage, product calls, merges, and "should I keep going" never reach the user.
- Two failed retries on a unit → drop and replan, don't retry a third time.

## Evidence

Session scale:
- The exit condition and the check that evaluates it.
- Iterations run (trail link), what landed, what was discarded and why.
- Side fixes made and where they live.
- Final predicate state, shown by running the check.

Program scale:
- What landed against the goal.
- Each PR's live state and verdict, with its link and the pr-review technique's review line.
- Repeated pr-review finding classes routed to **correct**, and the guardrail each produced.
- Environment changes made on the strategic track, and the retros sampled with what each produced.
- The wiki's path and the pages added or superseded.
- What was dropped and why; parked follow-ups.
- Every worker accounted for.
- Decisions made on the user's behalf, each with how to reverse it; anything still waiting on the user.
