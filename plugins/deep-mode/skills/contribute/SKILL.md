---
name: contribute
description: "Join someone else's project as a contributor: learn it from the maintainer's brief, pick an unclaimed `help wanted` issue that doesn't overlap open PRs or claims, claim it, build and prove it the deep-mode way, and open a PR. Use for /deep-mode:contribute, \"help out on this repo\", or \"find me something to work on\"."
---

# Contribute

You are a guest in someone else's project. The maintainer set it up with `skill://project-brief` (a newcomer brief, a claimable task board, guardrails). Your job: learn the project, find work nobody else holds, say out loud that you hold it, and ship one small, proven PR.

All deep-mode rules apply (`skill://deep-mode`). Three matter most here:

- **Nothing public without the human's explicit yes.** Claim comments, issue or PR comments, self-assigning, forks, commits, pushes, and PRs each need a yes for that action. Draft first, show it, wait.
- **Restate the goal first** with the **in-your-own-words** technique (`skill://deep-mode/references/techniques/in-your-own-words.md`).
- **Prove it on the real app** and put the evidence in the PR.

Shell notes: use `mktemp` for scratch files, never `/tmp`. Use `python` (or `python3` where `python` is missing). Below, `R` is `owner/name` and `N` is the issue number.

## Overlap tool

Use the repo's copy when it exists, else the plugin's copy (omp: `skill://project-brief/assets/pr-overlap.py`; Claude Code: `<this skill's base directory>/../project-brief/assets/pr-overlap.py`):

```bash
OVERLAP=scripts/pr-overlap.py; [ -f "$OVERLAP" ] || OVERLAP="skill://project-brief/assets/pr-overlap.py"
python "$OVERLAP" claims --repo R --json
python "$OVERLAP" check --repo R --files a,b,dir/ --exclude-issue N
```

`check` exit codes: `0` no overlap, `3` overlap (read the table), `2` usage or `gh` error (fix it; an error is not a pass). Paths are repo-relative with forward slashes; a trailing `/` means a whole directory. Say which copy you used. Every `check` you run after claiming must pass `--exclude-issue N` (and `--exclude-pr <your PR>` once your PR exists), otherwise your own claim is reported as overlap.

## Claim format

The claim is one issue comment in exactly this shape (the marker line first, nothing else in the comment):

```
<!-- deep-mode:claim -->
Claimed by @<login> via /contribute
Plan: <one line>
Files: <comma-separated repo paths; a trailing "/" means a whole directory>
Expires: <YYYY-MM-DD, 7 days after posting>
```

- `<login>`: `gh api user -q .login`.
- `Expires`: `python -c "import datetime as d;print(d.datetime.now(d.timezone.utc).date()+d.timedelta(days=7))"` (UTC).
- The newest claim comment on an issue wins. To renew or change `Files`, post a new claim comment; don't edit the old one.
- To release, post a comment from the same account that contains `<!-- deep-mode:unclaim -->`:

```
<!-- deep-mode:unclaim -->
Released by @<login>: <one-line reason>
```

## Steps

1. **Find the repo.**
   - In a git clone → `gh repo view --json nameWithOwner,defaultBranchRef,viewerPermission`.
   - Given a URL or `owner/name` → `gh repo clone R` into a directory the human picks (default: the current directory), then the same `gh repo view`.
   - `viewerPermission` is not `WRITE`, `MAINTAIN`, or `ADMIN` → you can't push branches here. Tell the human you need a fork, and on their yes run `gh repo fork R --remote` (the fork becomes `origin`, the project becomes `upstream`). From then on "main" means `upstream`'s default branch.
   - Below, "main" means the default branch from `defaultBranchRef`, whatever its name.

2. **Read the project.** From the repo root, read whichever exist: `docs/PROJECT_BRIEF.md`, `STACK.md`, `CONTRIBUTING.md`, `AGENTS.md` (or `CLAUDE.md`), `ROADMAP.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and the verify skill (`.omp/skills/verify-*/SKILL.md`, or the path the brief names).
   - No `docs/PROJECT_BRIEF.md` → tell the human the maintainer hasn't run `project-brief`, so there is no curated brief or claim board yet. Learn the project with the **how** technique (`skill://deep-mode/references/techniques/how.md`) instead, and still use the overlap tool's plugin copy for PRs and claims.
   - No verify skill → note it; you'll prove changes by hand in step 7 (deep-mode's **Prove it on the real artifact** rule covers the options).

3. **Brief the human in plain words.** Five to ten sentences, no jargon dump:
   - What the project is and who uses it.
   - How it runs locally (the exact commands from the brief or CONTRIBUTING; say if you haven't run them yet).
   - Where help is wanted (themes from `ROADMAP.md` or the `help wanted` label).
   - The house rules that will affect them (tests, style, review, sign-off).
   - The human didn't say what they want to work on → ask: interest area, skills, and time budget. This is a preference call, so asking is right.

4. **List candidate issues.**
   ```bash
   gh issue list --repo R --state open --label "help wanted" --limit 200 --json number,title,labels,assignees,url,body
   python "$OVERLAP" claims --repo R --json
   ```
   - Drop issues with an active claim or an assignee.
   - Task issues from the maintainer's template use body headings `### Goal`, `### Why`, `### Area / files`, `### Done when`, `### Skills needed`, and `### Size` (`S`, `M`, or `L`). Read them when present; free-form issues get your own estimate.
   - Keep the ones that match the human's interest and the issue's `### Skills needed`.
   - Order smallest-first: `good first issue` first, then `### Size` `S` → `M` → `L`, then by how few files and how little design the issue implies.
   - Show three to five candidates: number, title, one-line why it fits, and size (`### Size` or your guess, labeled as a guess). The human picks; recommend one.

5. **Plan and check for overlap.** For the chosen issue:
   - Read the issue and its comments in full: `gh issue view N --repo R --comments`.
   - Restate the goal (in-your-own-words), then draft a short plan that names every file or directory you expect to touch. Seed the list from the issue's `### Area / files` when present, then correct it from the code; `### Done when` is your acceptance check.
   - Run the overlap check with those paths: `python "$OVERLAP" check --repo R --files <paths>`. Don't pass `--exclude-issue N` here: you haven't claimed yet, so any claim on N is someone else's and must show up.
   - Check work the tool can't see: `git fetch --all --prune`, then `git branch -r --list "*N*"` and branches named after the same area, and `git log origin/main --since=30.days --oneline -- <paths>` (use `upstream/main` on a fork) for recent changes to the same area.
   - Overlap found (exit `3`, a matching branch, or a fresh commit that already does part of it) → never silently duplicate. Show the human what overlaps and offer three paths:
     - **Pick another issue** (back to step 4).
     - **Coordinate**: draft a short comment on the other issue or PR asking whether they're still on it or would split the work. Post only on a yes, then wait for their answer before building.
     - **Build on top (stack)**: branch from their PR branch and target it as the base, per the stacking rule in the Opening a PR playbook. Say so in your claim's `Plan`.
   - No overlap (exit `0`) → say so, with the command you ran.

6. **Claim it.** Show the human the exact claim comment (format above, with the real login, plan, files, and date). On their yes:
   - Right before posting, run `python "$OVERLAP" claims --repo R --json`. Issue N already has an active claim or an assignee from another login → stop, tell the human, and go back to step 4 or coordinate as in step 5.
   - Write the body to a `mktemp` file and post it: `gh issue comment N --repo R --body-file "$f"`.
   - Self-assign if the repo permits: `gh issue edit N --repo R --add-assignee @me`. A permission error is fine; the claim comment is the record.
   - Right after posting, run `gh issue view N --repo R --comments` and confirm no other author posted a claim comment after your step-4 read. One did → post the unclaim comment (format above) for yourself, tell the human, and pick other work (step 4) or coordinate with them (step 5).

7. **Build it the deep-mode way.**
   - Branch `<issue#>-<slug>` from the latest main: `git fetch origin && git switch -c N-<slug> origin/main` (from `upstream/main` on a fork; from the parent PR branch when stacking).
   - Route to the matching deep-mode playbook and follow it step by step: new behavior → `skill://deep-mode/references/playbooks/feature.md`; broken behavior → `skill://deep-mode/references/playbooks/bug-fix.md`; same behavior, better structure → `skill://deep-mode/references/playbooks/refactoring.md`. Say which one and why.
   - Follow the repo's own rules from step 2 over generic habits (formatter, test command, commit style).
   - Prove it on the real app with the verify skill or by hand, and keep the evidence (commands and output, screenshots, video).
   - Need a file outside the plan → stop, tell the human, and post an updated claim comment with the new `Files` (on their yes) before you touch it.

8. **Before the PR.**
   - Rebase on the latest main: `git fetch origin && git rebase origin/main` (`upstream/main` on a fork). Re-run the tests and the real-app proof if the rebase pulled in changes near your files.
   - List the real changed files: `git diff --name-only origin/main...HEAD | paste -sd, -`.
   - Re-run the check with those files: `python "$OVERLAP" check --repo R --files <changed files> --exclude-issue N`.
   - New overlap since step 5 → report it to the human with the table and coordinate as in step 5 before opening anything.
   - Changed files grew past the claim → post an updated claim (on a yes) so others see the real footprint.
   - Self-review: run deep-mode's pr-review technique in local mode (`skill://deep-mode/references/techniques/pr-review.md`) on your branch diff; fix or dismiss (with a reason) each finding, ask the human on judgment calls, and keep its `review:` result line.

9. **Open the PR** with deep-mode's Opening a PR playbook (`skill://deep-mode/references/playbooks/opening-a-pr.md`), only after the human says yes to commit, push, and open.
   - Push the branch (to your fork when you forked; `gh pr create` then targets the project).
   - The body fills the repo's `.github/PULL_REQUEST_TEMPLATE.md` when one exists; otherwise use the playbook's headings.
   - The body must include `Closes #N`, the verification evidence from step 7, the overlap result from step 8 (the command and "no overlap", or what overlaps and how you coordinated), and a note that a self-review ran with its `review:` result line.
   - The repo's `pr-overlap.yml` workflow, if installed, will comment on the PR with its own overlap check; read that comment and act on it.
   - Post the PR URL to the human.

10. **Close the loop.**
    - Merged → `Closes #N` closes the issue; nothing else to post.
    - Abandoned, rejected, or you stop for any reason → on the human's yes, post the unclaim comment (format above) with a one-line reason, and unassign yourself: `gh issue edit N --repo R --remove-assignee @me`. Close your PR if one is open, saying why.
    - Still working when `Expires` approaches → post a fresh claim comment with a new date (on a yes) and a one-line status.

## Rules of the road

- One issue, one branch, one PR. Found a second problem? Tell the human and suggest a new issue; don't fold it in.
- Keep claims fresh: renew before `Expires`, release the moment you stop. A stale claim blocks other people.
- Never touch files outside the plan without first posting an updated claim.
- Never push to someone else's branch. To build on their work, stack a branch on top of theirs or ask them.
- Never claim, comment, assign, fork, commit, push, or open a PR without the human's explicit yes for that action.
- The maintainer's brief, CONTRIBUTING, and AGENTS rules beat this skill's defaults wherever they disagree; say when they do.
