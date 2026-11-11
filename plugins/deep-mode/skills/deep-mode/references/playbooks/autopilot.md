# Autopilot

Use when: a queue of PRs is to be built and verified with full autonomy, one owner per PR. Mode `merge` (the default: "autopilot this queue", "full autopilot"): owners carry each PR to merged. Mode `stack-only` ("autopilot, don't merge", "stack them, don't ship", "build the stack, I'll land it"): built and verified, then handed to the operator to land. You own the verdicts, never the PRs: nothing merges until a panel of verifiers who never wrote the code has passed the code that lands.

## Steps

1. Declare the mode: `merge` unless the user said not to merge. Record the mode in the trail and in every heartbeat-tick prompt.
2. Apply the operator's gates first: the grant covers only the queue's items. Items the operator names as theirs and PRs outside the queue stop at merge-ready. A request to state the plan is not a go.
3. Spawn one owner per PR with `task`, each in its own `git worktree` with exclusive file ownership (shared-`.git` rules: `references/playbooks/orchestrate.md` step 3). The autopilot request authorizes owners to push their own branches and open PRs; merging only in `merge` mode. Each owner builds, opens its PR early (per `references/playbooks/opening-a-pr.md`) so CI and bots run alongside, proves the change on the real artifact, and babysits to green per `references/playbooks/babysit.md`.
   Before an owner starts, a different agent writes hidden acceptance tests from the PR's spec. They are stored in the root's store, outside every owner's worktree, and are black-box tests of the spec's public behavior. Run them on trunk: they must fail there, or they test nothing; rewrite once, then record the PR as lacking hidden tests. Owners see only failure output, with every line of test source blanked: test runners echo the failing assertion in their tracebacks.
4. Topology:
   - `merge`: owners run in parallel off trunk, never stacked, so each PR lands on its own.
   - `stack-only`: stack a PR only when it builds on another PR; base it on that PR's branch. Each PR rebases onto its parent's branch; the stack root rebases onto trunk. A new head on a lower PR restacks those above; a PR whose `git patch-id` is unchanged by the restack keeps its verdict.
5. Owners make the code ready: apply the **unslop** (`references/techniques/unslop.md`) and **no-comments** (`references/techniques/no-comments.md`) techniques, run the repo's checks for the touched paths on the committed head, rebase onto the base it lands on (step 4), then self-review that head with the **pr-review** technique (`references/techniques/pr-review.md`) in local mode, fixing, dismissing with a reason, or asking per its step 5. Report the code-ready head, with its review line, once that review stops (technique step 7) and before self-proof and the swarm.
6. Owners report every later head, and report merge-ready once self-proof, CI, and babysit are done. Fix rounds stay on that base unless trunk conflicts, breaks CI, or lands a known concurrent change to the same files (each rebase restarts CI). Rerun touched-path checks and a pr-review re-review (technique step 6) after every fix round, before any push that needs a verifier is handed over; each head report carries the review line for that exact head. Three fix rounds without passing → the owner holds and reports to the root, which decides or asks the operator.
7. Assume any agent can die:
   - Owners push soon after starting, start a decision trail per the **show-me-your-work** technique (`references/techniques/show-me-your-work.md`) in the root's store (a shared file the root names under the git common dir, e.g. `$(git rev-parse --git-common-dir)/omp-resume/autopilot-<queue>.tsv` — never `local://`, which a cold-start or replacement session can't see; print its absolute path), and push each finished unit before starting the next.
   - Whoever spawns a subagent records its id, state, and a stuck-after runtime from past runs of its kind in that store, so the root can probe it if the parent dies.
   - Force-push only your own branch, `--force-with-lease` pinned to the SHA you last pushed or took over. Any push you didn't make → stop and report to the root.
8. Swarm-verify once at the code-ready SHA per the **swarm** technique (`references/techniques/swarm.md`): independent verifiers re-run the gates, run the PR's hidden acceptance tests at that head, prove the load-bearing behavior live on the real surface (the repo's `verify-<app>` skill or a named driver), and audit the diff. Not clean without the live lane, nor before you audit the merge-ready report's receipts. Before merge-ready, the root runs the pr-review technique in PR mode on the head being verified: no P0/P1 open, every P2 fixed or dismissed with a reason; a review line for an older SHA needs a fresh round.
   The verdict itself is a **panel** (`references/techniques/panel.md`) at that head, its three verifiers given the swarm's receipts and the review line: 2 of 3 agreeing with evidence is a pass.
9. Re-verify by size of change: new behavior, a redesign, or a large new diff → another full swarm; a rebase, conflict resolution, or minor fix → one verifier at the new head; wording-only → none. `references/playbooks/shipping.md`'s patch-id rule can carry a lane's result; every new head needs its own green CI and its own pr-review round.
10. Block a PR only for a problem you can show: a failing run at the head or a doc line the PR made wrong. A problem the base (trunk or the PR below) already has doesn't block unless the PR copies or newly reaches it. Only a user-facing bug, a failed gate, or a wrong shipped doc blocks; everything else is a follow-up.
11. Finish by mode:
    - `stack-only`: stop when each PR is verified and green at its current head; hand the PRs to the operator. After handoff nobody pushes without the operator's go.
    - `merge`: the owner merges only what you verified, tested on the trunk it lands on, and always with `gh pr merge <pr> --match-head-commit <verified SHA>` so no other head can land. Once the swarm's lanes start, merge prep rebases onto current trunk, reports the new head, waits for green CI. Right before merging, fetch trunk and ask whether its changes can affect the patch:
      - Untested code would land (conflict, file both sides changed, change to which checks run) → rebase and wait for CI.
      - Lockfile both sides changed → no rebase if a frozen install passes on the merge result and the PR's changed packages resolve as on the head; a failing install means rebase and repair.
      - Trunk changed a caller of the patch or something it depends on → run the patch's checks on the merge result; merge on a pass.
      - Otherwise merge. A third rebase past merge prep → hold and report to the root, which sequences the colliding work.
      - After each merge, run the repo's checks on the new trunk. Red → open a revert PR and report it to the root. Build the revert with `git revert` or `git restore --source=<pre-merge SHA> --staged --worktree -- .`; a diff piped to `git apply` fails under `core.autocrlf`. Trunk itself is never pushed.
12. Run the root layer:
    - Anything that loosens a gate (raised budget, allowlist entry) needs a verifier's proof, then your fresh countersign — the owner is the one who wants green. Under a grant covering approvals, the countersign is the approval; the owner's record points at it.
    - A disabled or soft-failed check always comes out.
    - Never give or bypass an approval the forge enforces.
13. Once owners are running, run an hourly heartbeat (background `bash` `sleep 3300` with `timeout: 3600`, or any longer sleep with `timeout: 0`) until no delegated work is left. Each tick:
    - Re-read this playbook and the mode; fix drift (unreported head, unrecorded agent) by having its owner record it.
    - Probe every agent down to the leaf lanes (`read proc://`, `agent://<id>`) and judge by side effects (pushes, trail rows), not status text.
    - Stuck = errors, can't start turns, nothing new past its stuck-after runtime, or an owner with no push and no trail row by the first tick. Waiting on you or the operator is not stuck — answer it. Replace a stuck agent at once, without waiting for its stop to land.
    - Changed something for the operator → catch them up (see Evidence); changed nothing → stay quiet.
14. On the operator's stop, stand down at once: send every owner a zero-writes order (`write agent://<id>`); each reports where it stands and keeps its brief until released.

## Gates

- Merge only in `merge` mode, only queue items, only on a panel pass at the head and trunk it lands on. Green CI alone never authorizes a merge.
- `stack-only`: never merge; after handoff, no pushes without the operator's go.
- Never bypass forge-enforced approvals; loosened gates need proof + countersign.
- Operator stop → zero writes immediately.
- No verdict from an agent that wrote the code; verifiers use a different model family than the author when one is available.
- pr-review is evidence, not a substitute for the swarm: a PR isn't merge-ready (or handed off) until the root's review line is on its current head with no P0/P1 open and every P2 fixed or dismissed with a reason. A clean review never waives the swarm.

## Evidence

Catch the operator up in plain words, opening with what waits on them (or that nothing does):
- Each PR: link, state, verdict, the head it covers, and its review line (per `references/techniques/pr-review.md` Output).
- `merge`: what merged and how confirmed (`gh pr view <pr> --json state,mergedAt,baseRefName`). `stack-only`: each PR with its verdict, in place of what merged.
- Countersigns and why; open operator gates; parked follow-ups.
- Links to the trails.
