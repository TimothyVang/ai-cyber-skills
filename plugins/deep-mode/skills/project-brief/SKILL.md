---
name: project-brief
description: "Maintainer workflow that opens a repo to many contributors and their agents: writes docs/PROJECT_BRIEF.md, proposes claimable GitHub Issues, installs the overlap and roadmap scripts your agent runs, PR and issue templates, and CONTRIBUTING.md, so anyone can run /deep-mode:contribute. Re-run to refresh the brief and roadmap, post overlap comments, and release expired claims. Use for /skill:project-brief, \"publish this project for contributors\", or \"set up the task board\"."
disable-model-invocation: true
---

# Project brief

Run this once per project as the maintainer, then again whenever the project drifts. It publishes three things a contributor's agent needs before it touches code: a newcomer brief, a claimable task board, and guardrails that stop two people from building the same thing. Contributors then run `/deep-mode:contribute` (see `CONTRIBUTING.md` once installed).

Paths below are relative to this skill (`skill://project-brief/...`). In omp bash, `skill://project-brief` resolves to this skill's directory. In Claude Code, use the "Base directory for this skill" path shown when the skill loads. Claude Code tool names: `ask` → `AskUserQuestion`, `task` → `Agent`, `todo` → `TodoWrite`.

Deep-mode rules apply throughout (`skill://deep-mode`): restate first, answer observable questions by running them, prove claims with evidence, and follow its Autonomy section for shared-state actions. In the user's own repo, labels, issues, comments, and the PR need no ask: publish, then report what you did and how to undo it. Ask first, once, only when the user asked to be consulted or the repo is someone else's.

## Assets

Copy these into the target repo. Never overwrite a file that already exists; merge it instead (step 4). Nothing here installs GitHub Actions: the maintainer's agent runs the overlap and roadmap scripts (steps 6 and 8).

| Asset (relative to this skill) | Destination in the target repo |
|---|---|
| `assets/PROJECT_BRIEF.template.md` | `docs/PROJECT_BRIEF.md` (filled in, step 2) |
| `assets/pr-overlap.py` | `scripts/pr-overlap.py` |
| `assets/sync-roadmap.py` | `scripts/sync-roadmap.py` |
| `assets/PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` |
| `assets/ISSUE_TEMPLATE/task.yml` | `.github/ISSUE_TEMPLATE/task.yml` |
| `assets/CONTRIBUTING.template.md` | `CONTRIBUTING.md` (filled in, step 4) |

## Shared contract

Everything below must match what `skill://contribute`, `scripts/pr-overlap.py`, and `scripts/sync-roadmap.py` expect. Don't invent variants.

- **Labels.** `help wanted` marks a claimable task. `good first issue` marks a small one. `claimed` is optional and maintainer-set.
- **Claim comment.** A contributor's agent posts this on the issue, only after its human says yes:

  ```text
  <!-- deep-mode:claim -->
  Claimed by @<login> via /contribute
  Plan: <one line>
  Files: <comma-separated repo paths; a trailing "/" means a whole directory>
  Expires: <YYYY-MM-DD, 7 days after posting>
  ```

- **Active claim.** The newest claim comment on an open issue, with `Expires` today or later, and no newer comment from the same author containing `<!-- deep-mode:unclaim -->`. An assignee also counts as a claim on the issue (not on any files). An assignee who posted a claim comment on the issue counts only through that comment: once it expires or is released, the assignment stops counting.
- **Overlap.** Two path sets overlap when a path is equal, or one is a directory prefix (`dir/`) of the other. Paths are repo-relative with forward slashes.
- **One issue = one branch = one PR.** The PR body says `Closes #N`.

## Pass

Detect the mode first: if `docs/PROJECT_BRIEF.md` exists, this is a re-run; jump to step 8 after step 1.

1. **Restate the project.** In your own words: what the project is, who uses it, what the maintainer wants contributors to do, and what this run will publish. Get the repo identity with `gh repo view --json nameWithOwner,description,defaultBranchRef,visibility,url`. Don't wait for confirmation; the human corrects you if needed. Fuzzy goal → `skill://deep-mode/references/techniques/in-your-own-words.md`.

2. **Research, then write the brief.** Fill `docs/PROJECT_BRIEF.md` from `assets/PROJECT_BRIEF.template.md`. Sources: `README*`, `STACK.md`, `AGENTS.md`/`CLAUDE.md`, package manifests, CI files, the code tree, existing `docs/`, `gh issue list --state open --limit 200 --json number,title,labels,assignees`, and any verify skill (`.omp/skills/verify-*/SKILL.md` or `.claude/skills/verify-*/SKILL.md`). For a large repo, fan out read-only `scout` tasks, one per top-level area, each returning "directory → responsibility, entry points, how it's tested".
   - **Run & verify** must be exact commands you actually ran this session, with the result. A command you couldn't run is marked `unverified` with the reason; never copy one from the README on faith.
   - **No verify skill?** Contributors prove changes through it. Offer `/skill:create-verification-skill` once; if declined, write the manual proof steps you used.
   - **Constraints and don'ts** (sensitive data, no telemetry leaving the network, licensing, files contributors must not touch, review owners) are the maintainer's call. Fill what the repo states, then `ask` for the rest in one batched question. Don't guess policy.
   - Delete template guidance comments and any section with nothing true to say. Prose → `skill://deep-mode/references/techniques/unslop.md`.

3. **Propose the task board.** Draft issues shaped like `assets/ISSUE_TEMPLATE/task.yml`: Goal, Why, Area / files, Done when, Skills needed, Size. Sources: open issues without a task shape, TODO/FIXME clusters, README roadmap items, gaps you found writing the brief, failing or missing tests.
   - Make **Area / files** concrete repo paths; overlap checks depend on them. Split tasks so open tasks touch disjoint paths where you can. Size L means split it first.
   - Label every task `help wanted`; add `good first issue` to S tasks that need no deep context.
   - Prefer adding a task shape to an existing issue over a duplicate; list those as "edit #N" rather than "new".
   - Draft the full list (title, size, labels, area/files, new vs. edit) and the issue bodies; step 7 publishes them together with the files. Write each body to a `mktemp -p .scratch` file (the repo's git-excluded scratch folder; never system temp) using `### <field label>` headings in form order (the shape GitHub renders for form issues).

4. **Install the assets** per the table above, into the working tree only.
   - Missing file → copy it. Existing identical file → leave it. Existing different file → show the diff and merge by hand: keep the maintainer's content, add only missing sections. Never overwrite.
   - `CONTRIBUTING.md`: fill `{{...}}` placeholders from the brief (repo, run and verify commands, constraints). If one exists, merge the deep-mode sections (install, claim rules, overlap check, PR requirements, review flow) into it.
   - A repo that already carries the old `.github/workflows/pr-overlap.yml` or `roadmap.yml` from an earlier run: delete them in the step 7 PR and say so. Deep-mode replaces GitHub Actions; the agent runs both scripts instead.
   - Optional: add `.github/CODEOWNERS` lines from the brief's architecture map when the repo has more than one maintainer. It goes in the step 7 PR and under "Decisions I made".

5. **Ensure labels.** As part of step 7, create or update the labels before creating issues. `--force` updates an existing label instead of failing:

   ```bash
   gh label create "help wanted" --repo OWNER/REPO --color 008672 --description "Claimable task: run /deep-mode:contribute" --force
   gh label create "good first issue" --repo OWNER/REPO --color 7057ff --description "Small, well-scoped task for newcomers" --force
   gh label create "claimed" --repo OWNER/REPO --color fbca04 --description "Someone is working on this" --force
   ```

   Labels are shared state: name each one you created or changed in the report.

6. **Write the roadmap** after the issues exist (step 7). `python scripts/sync-roadmap.py --repo OWNER/REPO --out ROADMAP.md` (on Windows, `py -3` if `python` isn't Python 3). Read the result back and check every created issue appears under `## Open to claim`. Then run `python scripts/pr-overlap.py claims --repo OWNER/REPO` to prove the overlap script works against this repo; paste its output in your report.

7. **Publish, then report.** In the user's own repo this needs no ask (deep-mode Autonomy). Ensure the labels (step 5), create or edit the issues with `gh issue create --repo OWNER/REPO --title ... --body-file "$f" --label "help wanted"`, write the roadmap (step 6), and ship the files through `skill://deep-mode/references/playbooks/opening-a-pr.md`: a branch and a PR, never a push to the default branch.
   In the report, list the task list, the labels, and every file you wrote or merged with a one-line reason, under "Decisions I made", each with how to undo it (close the issue, delete the label, revert the PR). When the user asked to be consulted, or the repo isn't theirs, show the same list in one question first and publish only what they approve.

8. **Re-run mode.** When the brief already exists:
   - **Refresh the brief.** `git log --since=<brief's last commit date> --stat` plus a re-read of changed areas. Update only sections that drifted; re-run the Run & verify commands and update their recorded results.
   - **Release expired claims.** Fetch comments: `gh issue list --repo OWNER/REPO --state open --label "help wanted" --limit 200 --json number,title,assignees,labels,comments`. Find issues whose newest claim comment has an `Expires` date before today and no later unclaim. Comment on each: `Claim by @<login> expired on <date>. This issue is open to claim again; comment here if you're still on it.` Remove the `claimed` label if set (`gh issue edit N --remove-label claimed`), and list the released claims in the report.
     Never unassign anyone without the user's yes. The issue is open again either way: both scripts skip an assignee whose own claim comment lapsed.
   - **Assets.** Diff each installed asset against this skill's copy; propose updates as in step 4.
   - **New tasks.** Repeat step 3 for gaps since the last run.
   - **Overlap comments.** For each open PR: `python scripts/pr-overlap.py comment --repo OWNER/REPO --pr N`. It posts or updates one comment per PR (marker `<!-- deep-mode:overlap -->`).
   - **Roadmap.** Re-run step 6 and include a changed `ROADMAP.md` in what step 7 ships.
   - Then step 7, which publishes and runs steps 5 and 6.

## Report

Restate the goal, then: brief sections written (and which are `unverified`), issues created or edited (numbers and links), assets installed or merged, labels ensured, `ROADMAP.md` result, `pr-overlap.py claims` output, and what you shipped or left uncommitted. Name anything blocked and why.
