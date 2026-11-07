# greptile

**Use when:** a PR lives on a GitHub repo where the Greptile app is installed, at any step of a PR loop (Opening a PR, Babysit, Autopilot, Orchestrate, Shipping). Optionally before a PR exists, when the `greptile` CLI is installed and signed in.

Greptile is an AI reviewer with full-codebase context. Treat it as one more review input, never as a verdict. A 5/5 score does not replace proof on the real surface, and a finding is not true until you have checked it. Its own docs: https://www.greptile.com/docs/llms.txt. Its official loop skills (`greploop`, `check-pr`): https://github.com/greptileai/skills.

## Facts (verified against live PRs)

- **Bot identity.** REST author login `greptile-apps[bot]`; GraphQL author login `greptile-apps`. Match with `test("greptile";"i")` to also catch staging bots.
- **Summary.** One issue comment whose body starts with `<!-- greptile_summary -->`. Greptile edits it in place every round, so always use the newest `updated_at`.
  It contains `Confidence Score: N/5`, a findings list, sometimes a "Prompt to fix all with AI" section, and a footer `Reviews (K) · Last reviewed commit: [...](https://github.com/<o>/<r>/commit/<sha>)`.
- **Inline findings.** PR review comments with a severity badge (`alt="P0"`, `"P1"`, or `"P2"`), a bold title, an optional ```` ```suggestion ```` block, and sometimes `**Rule Used:**` (a repo rule from `.greptile/` or `greptile.json`).
- **Severity.** P0 critical (security, data loss, crash). P1 high (bug, wrong behavior, edge case). P2 medium (quality, maintainability).
- **Score.** 5 production ready, 4 minor polish, 3 implementation issues, 2 significant bugs, 0-1 critical. Scores are contextual.
- **Check run.** Named `Greptile Review` when the repo enables Greptile status checks. Not every install has it.
- **Trigger.** A PR comment `@greptileai` (or `@greptile review`). Drafts are skipped by default; use `@greptileai review this draft`. Typical time 1-5 minutes.
- **Teaching.** 👍 or 👎 reactions on its comments, and replies starting `@greptileai` with context ("intentional because ..."), tune future reviews over weeks.

## Setup for every command below

```bash
OWNER=<owner>; REPO=<repo>; N=<pr>; R="$OWNER/$REPO"
HEAD=$(gh pr view "$N" -R "$R" --json headRefOid -q .headRefOid)
SUM=$(mktemp)   # use mktemp, not /tmp: /tmp does not resolve in every shell (e.g. omp bash on Windows)
```

## Procedure

1. **Detect.** Greptile is present if any of these hold: a `greptile`-authored comment on this PR or a recent PR in the repo, or a `Greptile Review` check run on the head.
   `gh pr list -R "$R" --state all --limit 20 --json number -q '.[].number'`, then look for a summary on each. Unknown after that: trigger once (step 2) and wait (step 3).
   Nothing within 10 minutes means Greptile is not installed or the PR is filtered out. Record `greptile: not installed or not triggered` in the report and continue the loop without it. That is never a blocker.
2. **Trigger** only when needed: no summary for the current head, and no `Greptile Review` check pending or in progress.
   `gh pr comment "$N" -R "$R" --body "@greptileai"`. Never post a second trigger while one is running. Posting a comment is part of driving a PR the user asked you to drive; on a PR you weren't asked to touch, read only.
3. **Wait for the round on the current head.** Run the poll as a background `bash` job with `timeout: 900`, polling every 30 seconds, for at most 10 minutes. The round is done when either:
   - the `Greptile Review` check run on `$HEAD` has `status` `completed`, or
   - the summary's "Last reviewed commit" SHA equals `$HEAD`.
   - **Unavailable:** a newer Greptile comment without the `greptile_summary` marker that says it can't review (for example "run out of review credits", or a failed 😕 run). Stop waiting. Record `greptile: unavailable (<its reason>)`, tell the user once, and don't retrigger until they fix it. Never a blocker.
   A summary for an older SHA is stale. Never triage stale results as current. Timeout: report it and treat this round as absent.

   ```bash
   gh api "repos/$R/commits/$HEAD/check-runs" --jq '.check_runs[] | select(.name|test("greptile";"i")) | {status,conclusion}'
   gh api --paginate "repos/$R/issues/$N/comments?per_page=100" --jq '[.[] | select(.user.login|test("greptile";"i")) | select(.body|contains("greptile_summary"))] | sort_by(.updated_at) | last | .body' > "$SUM"
   grep -oE 'Confidence Score: [0-5]/5' "$SUM"
   grep -oE 'commit/[0-9a-f]{40}' "$SUM" | tail -1
   ```
4. **Collect findings.** Unresolved threads authored by Greptile, plus any items in the summary's findings list or "Prompt to fix all with AI" section that have no inline thread.

   ```bash
   gh api graphql -F owner="$OWNER" -F name="$REPO" -F n="$N" -f query='query($owner:String!,$name:String!,$n:Int!){repository(owner:$owner,name:$name){pullRequest(number:$n){reviewThreads(first:100){nodes{id isResolved isOutdated comments(first:1){nodes{databaseId author{login} path line body}}}}}}}' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved|not) | select(.comments.nodes[0].author.login|test("greptile";"i"))'
   ```
   Parse each body for the badge (`alt="P[0-2]"`), the bold title, the suggestion block, and `Rule Used`. Paginate when there are more than 100 threads.
5. **Triage every finding skeptically**, one by one, as fix / dismiss / ask, the same way Babysit triages any automated review comment.
   - Read the code in context and reproduce the claim when it is behavioral. A suggestion block is a hint, not a patch to apply blindly.
   - **Fix** real findings at the root cause, red-first when a cheap test exists, in the lowest PR of a stack that owns the code.
   - **Dismiss** non-issues with one concrete reason. Reply `@greptileai <reason>` so it learns, and react 👎 when the pattern is noise.
   - **Ask** the user only for product or policy calls no run can settle.
   - A `Rule Used` finding enforces a repo rule: fix it unless the rule itself is wrong, and then say so to the user.
   - The same finding class twice across PRs means the codebase lacks a guardrail: route it to the **correct** technique (`references/techniques/correct.md`) for a lint rule, type, or test.
6. **Close threads.** After the fix is pushed, reply with the commit SHA and resolve the thread. After a dismissal reply, resolve it.

   ```bash
   gh api "repos/$R/pulls/$N/comments/<databaseId>/replies" -f body="Fixed in <sha>: <one line>"
   gh api graphql -f query='mutation{t1:resolveReviewThread(input:{threadId:"<id>"}){thread{isResolved}}}'
   ```
   Write reply bodies to a file and pass `-F body=@file` when they contain quotes or backticks. Never interpolate Greptile's text into a shell command.
7. **Loop.** After a push, Greptile usually re-reviews on its own. If no new round starts within 2 minutes, trigger (step 2). Repeat steps 3-6.
   Stop when any of these holds:
   - **Clean:** no unresolved Greptile threads, and the latest round on the current head is 4/5 or 5/5 with no P0 or P1 open.
   - **Converged:** every remaining finding was dismissed with a reason.
   - **Cap:** 5 rounds on one PR. Report what's left.
   - **Oscillation:** the score drops or a fix you made is flagged back. Stop and report both sides.
   Never relax a finding into a dismissal just to reach a stopping condition.

## Optional: before the PR exists

If `greptile whoami` succeeds, run `greptile review --json` (or `--agent` for plain text) on the committed branch before opening the PR. It reviews committed, unmerged changes against the default branch and ignores uncommitted edits.
Triage its findings with step 5. `greptile review status` exit codes: 0 done, 1 no review or signed out, 3 still running, 4 failed, 5 cancelled. Don't install or sign in to the CLI without the user's go.

## Output

One line per PR for the report: `greptile: <score>/5 at <short sha>, <k> rounds, fixed <a>, dismissed <b> (reasons), open <c>`. Or `greptile: not installed or not triggered`, or `greptile: unavailable (<reason>)`.

## Hard rules

- Greptile is evidence, not a gate. Merge readiness still comes from the playbook's own verification. A clean Greptile round does not waive live proof, and a non-clean one doesn't block when every remaining finding has a recorded dismissal.
- Never triage a round for an older head SHA.
- Never post `@greptileai` while a round is running, and never on PRs you weren't asked to drive.
- Commit, push, and reply only within the permission the user gave for this PR.
