# Babysit

Use when: the user asks to babysit, get green, make merge-ready, address review comments, or check on PRs, normally once a phase or whole stack is built, not when a PR opens. Landing ("merge", "ship", "land") is `references/playbooks/shipping.md` for a stack and the **pr-conversation** technique (`references/techniques/pr-conversation.md`) for one PR of the user's own; both start where this ends. You own the merge frontier: declare a mode, clear one PR at a time, stop at the human's line.

## Steps

1. Declare the mode before any poll:
   - `drive` (default; "babysit this", "get it green", "merge-ready"): loop to merge-ready.
   - `background`: triage without blocking, for a plan still executing.
   - `threads-only` ("address the review comments"): answer threads, touch nothing else.
   - `check` ("check on X", "is it green"): one status pass, then report. Small or docs-only PRs get `check`, not `drive`.
   - Done when the mode is stated in the run's first message, before any `gh` call.
2. Confirm nothing else is already babysitting this stack. One babysitter per stack. Done when no other live agent or job claims this stack.
3. Find the frontier: the lowest unmerged PR. It is the only PR that matters until it merges. Read upstack threads and batch them; never fix upstack at the cost of restarting the frontier's checks. Caught upstack while the frontier is red → go back down.
   Done when the frontier PR number is named and the frozen bottom-to-top PR list is recorded.
4. Read the forge state (GitHub CLI; never require Graphite):
   - `gh pr view <pr> --json state,isDraft,mergeable,mergeStateStatus,reviewDecision,baseRefName,headRefOid,statusCheckRollup`
   - `gh pr checks <pr> --required`; in `drive`, `gh pr checks <pr> --watch` as a background `bash` job (`timeout: 0`); re-read the PR and threads every time it returns.
   - Threads: `gh api graphql` over `pullRequest.reviewThreads` (`id isResolved isOutdated comments{databaseId author body path line}`).
   - Review (not `check`): alongside the CI watch, run the **pr-review** technique (`references/techniques/pr-review.md`) in PR mode for the current `headRefOid` as a background subagent: steps 1-4 on the first head, then step 6 (Re-review) on each new head.
   - A review for an older SHA is stale: never triage it; after any push, the new head needs its own round before the PR counts as review-clean. `check` mode only reads the latest `<!-- deep-mode:review -->` review; it never runs one.
   - Done when the forge state above is read for the current `headRefOid` and, outside `check`, a review round for that SHA is running or posted.
5. Work blockers in order (conflicts, then review threads, then CI) and batch every known fix into one push wave. Push fixes to the PR's own branch; landing starts where this playbook ends (see Use when).
   Done when each known blocker is in the current push wave or reported upward.
6. Conflict (`mergeStateStatus: DIRTY`) or stale base (`BEHIND`):
   - The user's own PR (pr-conversation's own-PR test) in `drive`: resolve it. Merge the base into the head branch (`git merge origin/<base>`), resolve the conflicts, run the repo's checks, and push. Never rebase or force-push. Run the drift sweep in the same wave: trunk may have grown callers of code the PR deletes or moves.
   - Anyone else's PR, or `check` mode: report, don't resolve. Name the branch that needs the base merged and the drift sweep it needs, and stop; don't fall through to CI to look busy.
   - Done when `mergeStateStatus` is neither `DIRTY` nor `BEHIND`, or the conflict is reported upward with branch and drift sweep.
7. Triage each review thread (human or bot) and each pr-review finding skeptically. See Review-comment triage below; pr-review findings go through the same fix / dismiss / escalate (technique step 5).
   Fix real findings red-first in the lowest PR that owns the code, never at the tip unless the owning PR merged (then step 9's follow-up PR). Upstack fixes wait for the next frontier push wave. Push the wave before replying so the reply cites the commit.
   Done when every thread and finding is classified fix, dismiss, or escalate, and every fix is pushed.
8. Reply via a JSON file, never interpolating comment text into a shell command: `gh api --method POST repos/<owner>/<repo>/pulls/<pr>/comments/<comment-id>/replies --input <payload.json>`; resolve with the `resolveReviewThread` GraphQL mutation.
   Post pr-review results per technique step 5, then re-review per steps 6-7 on each new head until it stops (no P0/P1 open and every P2 fixed or dismissed, 3-round cap, or oscillation; report the last two upward). Never relax a finding into a dismissal to stop.
   Done when every fixed or dismissed thread has a reply and is resolved, and the re-review loop has hit one of its stop conditions.
9. Never mutate stack topology: no base retarget, rebase, stack-wide submit, or force-push from inside a babysit. Fix on the owning branch; report anything rebase-shaped upward.
   A **Work a queue** (`references/playbooks/work-a-queue.md`) PR owner babysitting its own PR is that owner: it rebases its own branch and pushes with `git push --force-with-lease` pinned to its last-pushed SHA.
   Sole sanctioned creation: a fix whose owning PR already merged becomes a new PR on top of the remaining stack (never a rewrite of merged history); append it to the frozen stack list, drop the merged owner.
   Done when every PR's base is unchanged from the frozen list, apart from sanctioned follow-up PRs appended to it.
10. Classify CI before any retrigger:
    - Flake/infra → one fresh full run (`gh run rerun <run-id>`, not `--failed`/`--job`). One retry only; an identical second failure was never flake. Reclassify and read the child logs.
    - Failure in code the diff never touches → suspect a stale base; check `git merge-base --is-ancestor <trunk-sha> <head>` and handle it as step 6 instead of burning retries.
    - Only a failure in the diff's own code gets a commit.
    - Done when every failing required check is classified flake, stale base, or diff-caused, with its action taken.
11. Trust the forge's merge verdict, not a green check list. For a stack, capture the PR list bottom-to-top once and reuse that frozen list on every re-arm. If another actor merges the frontier, continue with the new frontier.
    Done when the frontier's `mergeStateStatus` read live is `CLEAN` or every stack PR is merged; in `check` mode, when that status is reported.
12. Answer user questions mid-loop and continue; only an explicit stop ends `drive` early.
13. At the stop, sweep the run's triage decisions once. Offer any team-useful dismissal pattern as a candidate entry for the repo's shared review-triage doc (its own PR); never keep it only in private memory.
    Done when the report lists each candidate pattern, or says there were none.

## Review-comment triage

Verify every claim against the code before acting. Not every comment is a required change; not every comment is noise.
- `fix`: plausible correctness, security, privacy, data-loss, auth, billing, migration, idempotency, race, or shipped-behavior issue → fix in the lowest owning PR, reply with the commit SHA, resolve.
- `dismiss`: matches a known low-risk pattern AND current code/context proves no change is needed → short reason, resolve. Typical: intentional visual change the PR states; "unused" symbol a verified upstack PR uses (not public API); deliberate temporary duplication beside a path being deleted (not security/billing/data/API); an enforced (not assumed) framework/type invariant covers it; owner-declared follow-up the PR doesn't worsen; bot self-withdrew and you verified the rule locally.
- `escalate`: novel, high-severity, ambiguous, or security/privacy/auth/billing/data-retention/permission, migration/schema/idempotency/concurrency/cross-system, even if a past PR dismissed something similar. Decide it yourself: when a fix reduces risk without changing the PR's intent, make it; when it would change the intent, make that product call, act on it, and log it (SKILL.md Autonomy). When in doubt, fix.
- Cheap checks first: if a claim is runnable (e.g. "test no longer matches the doc"), run it on the tip; red confirms, green is the dismissal proof. Earlier fixed passes don't make the next finding noise.
- A finding already fixed at the tip is stale only if the guard runs before the side effect and covers the principal in question.
- Don't widen a deliberately narrow error condition (e.g. fallback gated on `ENOENT`) into a catch-all that masks the real error, unless it misses a same-category case.
- Findings against manual reimplementations of native platform behavior (scroll, sticky, hit-testing, event forwarding) have been consistently real: default to fix.

## Gates

- Stop `drive` at merge-ready: PR open, not draft, `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, required checks green, no unresolved threads without a pushed fix or a recorded dismissal, and a completed pr-review round on the current head SHA with no P0/P1 open. With a merge queue, a blocker-free frontier is merge-ready: report and stop watching; don't wait for merges.
- pr-review is evidence, not a waiver: a clean review never waives the checks above, and a P2 doesn't block once it has a recorded dismissal.
- All stack PRs merged by others → done.
- Owner approval (`reviewDecision: REVIEW_REQUIRED`) is a wait, not a blocker to fix. On the user's own PR, the **pr-conversation** technique's Authorization decides whether its panel replaces that review.
- Merge-ready is not merged. The user's own PR in `drive` goes straight on to the **pr-conversation** technique's panel and merge, with no ask. A stack lands through `references/playbooks/shipping.md`, each PR on a panel pass. Anyone else's PR stops at merge-ready. Surface escalations and keep working the rest.
- `check` mode: one pass, no edits.

## Evidence

- Mode, frontier PR, and its final forge state (`mergeStateStatus`, checks, `reviewDecision`) read live at the end.
- Each push wave: commit SHAs and which blockers each cleared.
- Each thread: fix / dismiss / escalate, with the commit or the proof behind the dismissal.
- Per PR, the pr-review technique's one-line report: `review: <ready|changes needed|needs discussion> at <short sha>, <k> rounds, open P0/P1/P2 <a>/<b>/<c>, fixed <d>, dismissed <e>`.
- CI classifications and any rerun; each base merge pushed on the user's own PR, and any conflict reported upward on others' (branch + drift sweep).
- What waits on the human (hard stops, escalated threads).
