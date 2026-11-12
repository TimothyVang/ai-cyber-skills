# Shipping

Use when: a PR or stack is ready to land: the user asks to merge, land, or ship, or an autonomous playbook (Work a queue, Run a goal) reaches merge-ready. Starts where `references/playbooks/babysit.md` ends.
You own what lands: verify each PR independently, land only the verified run from the root, then keep your hands off the stack.

## Steps

1. Name the scope (which PRs). Use `gh`; never require Graphite. Done when the PR numbers are listed bottom to top.
2. Verify each PR with the **panel** technique (`references/techniques/panel.md`) at its head: three skeptical verifiers that did not write the code run the change the way a user would (the repo's `verify-<app>` skill first, else `eval` `browser` or bash), parent against head.
   The PR is `PASS` when at least two agree with evidence you checked; post the panel line on the PR (`gh pr comment <pr> --body-file <file>`).
   Green CI and an approving bot review are not verdicts: neither runs the change as a user would. An author's self-check doesn't count.
   - Review: run the **pr-review** technique (`references/techniques/pr-review.md`) in PR mode on the exact head being landed.
     The verdict counts only once that round is on that head (never triage a stale SHA) with no P0/P1 open and every P2 fixed or dismissed with a recorded reason.
     It is evidence beside the verdict, not a substitute: a clean review waives no live proof.
   - Done when every PR in scope has a posted panel line and a pr-review line, each naming its current head SHA.
3. Find the run: walk up from the lowest unmerged PR and stop at the first without a panel pass at its current head. The PRs below it are the run; the top one is the ceiling.
   - A verified PR above an unverified one waits.
   - One whose branch neither holds nor needs the unverified code may move onto trunk and land alone, after a fresh verdict, since its old one ran with that code beneath it.
   - Done when the run's PRs and its ceiling are named.
4. A panel covers one head. After any new head (a fix, or step 8's restack), run a fresh panel there; `git patch-id` decides only which earlier evidence its verifiers may reuse:
   - Same patch → the old lanes' results go to the new panel as receipts.
   - Differs only in tests, docs, or lint config → a lane's result stands if what it ran builds the same at both SHAs apart from noise (a difference that also appears between two builds of the verdict SHA, or an embedded commit SHA). Report each kind of noise with its files. The change itself still gets fresh checks and a review.
   - A lane with no build output (e.g. a dev server) can't show this → rerun it. Re-verify anything else that drifted.
   - Review isn't carried by patch-id: any head change after the verdict, including step 8's restack, needs a pr-review re-review on the new head (technique step 6) before the PR counts as review-clean.
   - Done when every new head has a panel verdict and a review round at that SHA.
5. Land bottom-up, one PR at a time. First `gh pr merge <child> --disable-auto` on every PR stacked above it that has auto-merge armed (`gh pr view <child> --json autoMergeRequest`), so none can land on its old head when its base moves.
   Then `gh pr merge <pr> --match-head-commit <panel SHA>` with the repo's merge method (`--squash`, `--merge`, or `--rebase`) on the run's lowest unmerged PR. A PR whose base is still its parent's branch merges into that branch, not trunk.
   After each landing on trunk, run the checks there; red → open a revert PR at once.
   Done when the merge command returned and the trunk checks are green, or a revert PR is open.
6. Read each PR back: `gh pr view <pr> --json state,mergedAt,baseRefName`. A merge command can report success when a merge queue only queued it, and requested auto-merge is not a merge. Landed = `MERGED` with trunk as base.
7. Arm auto-merge only pinned to the panel's head: `gh pr merge <pr> --auto --match-head-commit <panel SHA>`. GitHub's docs don't promise that check holds until the merge lands, so treat the pin as a guard, not proof.
   A push after arming → `gh pr merge <pr> --disable-auto`, then a fresh panel (step 4) before arming again. Done when `gh pr view <pr> --json autoMergeRequest` shows auto-merge armed at the panel SHA.
8. After each landing, move the next PR (its auto-merge already off, step 5): `gh pr edit <pr> --base <trunk>`, move its patch onto the merge result, `git push --force-with-lease`.
   Run a fresh panel at the new head (step 4); merge, or re-arm per step 7, once checks pass and that panel passes. Done when the next PR's base is trunk and its new head has a panel pass.
9. Leave the stack alone while it lands. Step 8 is the only branch/base change. Watch with `gh pr checks <pr> --watch` (background `bash`, `timeout: 0`) and re-read `gh pr view` each time it returns, until the ceiling reads merged.
   A base that moves to trunk when its parent merges is expected, not damage. A stalled merge: find out why before changing anything. Done when the ceiling PR reads `MERGED`.
10. Stop at the ceiling. Extending the run takes new verdicts, a new pass from step 2.

## Gates

- No panel pass at the current head → that PR and everything above it waits.
- The latest pr-review round isn't on the head being landed, or a P0/P1 is open, or any P2 stands neither fixed nor dismissed with a reason → that PR waits.
- Never give an approval. Never bypass a branch protection the forge enforces, except a required review on the user's own PR under the **pr-conversation** technique's Authorization (`references/techniques/pr-conversation.md`).
- Ceiling reached → stop.

## Evidence

- The verified run and its ceiling.
- Each PR's verdict, who produced it, and the SHA/patch-id it covers (plus any noise reported under step 4).
- Each PR's review line per the pr-review technique's Output (`review: <ready|changes needed|needs discussion> at <short sha>, ...`), at the head that landed.
- What landed and how you confirmed it (`gh pr view` state, `mergedAt`, base).
- What the next gap needs (missing verdict, failing check, drift).
