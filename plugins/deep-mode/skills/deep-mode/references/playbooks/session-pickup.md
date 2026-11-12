# Session pickup

Use when: resuming work a prior agent or session started ("pick up where X left off", "continue that session", a handed-over branch or resume note). You own the resume point: read the prior trail, don't redo it.

## Steps

1. Locate the prior trail.
   - A prior omp session: consult it with `task`, `agent: "seance"`, `sourceSession: <id/path>`. The consult is the read; don't grep its `.jsonl`.
   - An `agent://`/`history://` transcript, a resume note (`$(git rev-parse --git-common-dir)/omp-resume/<slug>.md`, plus any patch beside it), a show-me-your-work trail, or a pushed branch.
   - Stay inside the active project; never read sessions from unrelated projects.
   - Done when the trail's path or session id is recorded and it lies inside the active project.
2. Read the overview and last messages first, then scan back for decision points. Parse a long transcript in a subagent and keep only the reduced timeline in the main thread (`references/principles/guard-the-context-window.md`).
   Done when a reduced timeline lists the trail's decision points and its last action.
3. Reconstruct operational state: branch and worktree, what already landed (`git log`, `git diff <base>...HEAD`), open todos, decisions made. The prior trail is authoritative input; resist re-deriving it.
   Done when the branch, worktree, landed commits, open todos, and decisions are each written down.
4. Diff done vs pending against the plan and name the resume point. Don't re-run the prior repro or redo completed work; a "verify from scratch" pass treats an authoritative trail as untrustworthy.
   Done when every plan item is marked done or pending and the resume point is named.
5. Pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run. Done when exactly one verdict is recorded with its reason.
6. Route the remaining work to the matching playbook; pickup ends here and the routed playbook owns the rest. Done when the routed playbook is named and started.
7. Verify the inherited claims against the original goal on the real artifact (`references/principles/prove-it-works.md`). A passing prior self-report is not proof.
   Done when each inherited claim has a real-artifact check result.

## Gates

- Redoing completed work is a failure of this playbook unless step 7's check shows the inherited claim is false.
- Never cross project boundaries to find a trail.
- Pickup follows SKILL.md Autonomy like any run: commits, pushes, and PRs proceed; merges need a panel pass; hard stops need the user.

## Evidence

- Where the prior agent stopped (with the trail you read).
- What you inherited vs redid (ideally nothing redone, and why if anything was).
- The resume point, the routed playbook, and the verdict.
- The outcome, including the real-artifact check of inherited claims.
