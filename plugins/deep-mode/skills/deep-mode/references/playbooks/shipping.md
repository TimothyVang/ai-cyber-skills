# Shipping

Use when: the user explicitly asks to merge, land, ship, or "merge when ready" a PR or stack. Starts where `references/playbooks/babysit.md` ends. You own what lands: verify each PR independently, land only the verified run from the root, then keep your hands off the stack.

## Steps

1. Confirm the explicit request to land and its scope (which PRs). That request is the only merge permission; without it, stop at merge-ready. Use `gh`; never require Graphite.
2. Verify each PR independently: one verifier per PR, a `task` subagent that did not write the code, runs the change the way a user would — the repo's `verify-<app>` skill first, else `eval` `browser` or bash — parent against head, and posts `PASS`, `PASS+NOTES`, or `FAIL` on the PR (`gh pr comment <pr> --body-file <file>`). Green CI and an approving bot review are not verdicts: neither runs the change as a user would. An author's self-check doesn't count.
   - Review: run the **pr-review** technique (`references/techniques/pr-review.md`) in PR mode on the exact head being landed. The verdict counts only once that round is on that head (never triage a stale SHA) with no P0/P1 open and every P2 fixed or dismissed with a recorded reason. It is evidence beside the verdict, not a substitute: a clean review waives no live proof.
3. Find the run: walk up from the lowest unmerged PR and stop at the first without `PASS`/`PASS+NOTES`. The PRs below it are the run; the top one is the ceiling.
   - A verified PR above an unverified one waits.
   - One whose branch neither holds nor needs the unverified code may move onto trunk and land alone — after a fresh verdict, since its old one ran with that code beneath it.
4. Re-check that each verdict still describes the code: compare `git patch-id` at the verdict SHA with the current head.
   - Same patch → verdict stands.
   - Differs only in tests, docs, or lint config → a lane's result stands if what it ran builds the same at both SHAs apart from noise (a difference that also appears between two builds of the verdict SHA, or an embedded commit SHA). Report each kind of noise with its files. The change itself still gets fresh checks and a review.
   - A lane with no build output (e.g. a dev server) can't show this → rerun it. Re-verify anything else that drifted.
   - Review isn't carried by patch-id: any head change after the verdict, including step 8's restack, needs a pr-review re-review on the new head (technique step 6) before the PR counts as review-clean.
5. Land bottom-up, one PR at a time: `gh pr merge <pr> --squash` on the run's lowest unmerged PR. A PR whose base is still its parent's branch merges into that branch, not trunk.
6. Read each PR back: `gh pr view <pr> --json state,mergedAt,baseRefName`. A merge command can report success when a merge queue only queued it, and requested auto-merge is not a merge. Landed = `MERGED` with trunk as base.
7. Arm `gh pr merge --auto` only on a PR whose verdict and pr-review round cover its current head — auto-merge lands whatever head is ready.
8. After each landing, move the next PR: `gh pr edit <pr> --base <trunk>`, move its patch onto the merge result, `git push --force-with-lease`. Step 4's patch-id rule decides whether its verdict survives; merge once checks pass and the verdict survives.
9. Leave the stack alone while it lands. Step 8 is the only branch/base change. Watch with `gh pr checks <pr> --watch` (background `bash`, `timeout: 0`) and re-read `gh pr view` each time it returns, until the ceiling reads merged. A base that moves to trunk when its parent merges is expected, not damage. A stalled merge: find out why before changing anything.
10. Stop at the ceiling. Extending the run takes new verdicts — a new pass from step 2.

## Gates

- No explicit land request → no merge; hand back at merge-ready.
- No `PASS`/`PASS+NOTES` from a non-author verifier at the current patch → that PR and everything above it waits.
- The latest pr-review round isn't on the head being landed, or a P0/P1 is open, or any P2 stands neither fixed nor dismissed with a reason → that PR waits.
- Never give or bypass an approval or branch protection the forge enforces.
- Ceiling reached → stop.

## Evidence

- The verified run and its ceiling.
- Each PR's verdict, who produced it, and the SHA/patch-id it covers (plus any noise reported under step 4).
- Each PR's review line per the pr-review technique's Output (`review: <ready|changes needed|needs discussion> at <short sha>, ...`), at the head that landed.
- What landed and how you confirmed it (`gh pr view` state, `mergedAt`, base).
- What the next gap needs (missing verdict, failing check, drift).
