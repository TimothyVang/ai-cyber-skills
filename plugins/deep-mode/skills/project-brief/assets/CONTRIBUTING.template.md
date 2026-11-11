<!-- Template from the deep-mode project-brief skill. Replace every {{...}} and delete this comment. -->

# Contributing to {{PROJECT_NAME}}

Thanks for helping. Many people and their agents work on this repo at once, so the rules below exist to keep two people from building the same thing and to make every PR easy to trust.

Read [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) first: what the project is, how to run it, and what not to do.

## 1. Install deep-mode

deep-mode is an agent plugin that restates the goal, plans, proves changes on the real app, and reports with evidence.

**omp**

```bash
omp plugin marketplace add TimothyVang/deep-mode
omp plugin install deep-mode@deep-mode
```

**Claude Code**

```text
/plugin marketplace add TimothyVang/deep-mode
/plugin install deep-mode@deep-mode
```

You also need the GitHub CLI, signed in (`gh auth status`), and Python 3.10+.

## 2. Run `/deep-mode:contribute`

In your clone of `{{OWNER/REPO}}`:

```text
/deep-mode:contribute
/deep-mode:contribute #42
/deep-mode:contribute something small in the docs
```

Your agent reads the brief, lists open `help wanted` issues that nobody has claimed and that don't overlap open PRs or other claims, and recommends one. Nothing public happens without your yes: the agent asks before it claims, comments, commits, pushes, or opens a PR.

## 3. Claim before you start

One issue = one branch = one PR. Claim the issue before writing code by posting this comment on it (your agent drafts it for you):

```text
<!-- deep-mode:claim -->
Claimed by @<your-login> via /contribute
Plan: <one line>
Files: <comma-separated repo paths; a trailing "/" means a whole directory>
Expires: <YYYY-MM-DD, 7 days after posting>
```

- **Files** lists every path you expect to change. Use `dir/` for a whole directory. Be specific: other contributors' agents avoid these paths.
- A claim is active until its `Expires` date. Still working? Post a fresh claim comment with a new date.
- An issue with an assignee counts as claimed too.
- Giving up? Comment on the issue with `<!-- deep-mode:unclaim -->` on its own line plus a short note, so someone else can pick it up.
- Expired claims are released: the maintainer comments that the issue is open again.
- Don't claim more than you can finish in a week. Split big tasks first.

## 4. Check for overlap, twice

Two path sets overlap when a path is equal or one is a directory (`dir/`) containing the other. Check before you start and again before you open the PR:

```bash
python scripts/pr-overlap.py check --repo {{OWNER/REPO}} --files src/a.py,docs/ --exclude-issue N
```

After claiming, pass `--exclude-issue <your issue>` so your own claim isn't reported. Exit code `0` means no overlap. `3` means an open PR or an active claim touches the same paths; the output lists them. Coordinate on that issue or PR, or pick another task. `2` means a usage or `gh` error. To list active claims: `python scripts/pr-overlap.py claims --repo {{OWNER/REPO}}`.

## 5. Build and prove it

Follow [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for setup, conventions, and constraints. Before calling a change done, run it on the real app and capture what you saw:

```bash
{{TEST_COMMANDS}}
```

{{VERIFY_PATH}}

Passing tests alone are not proof. Show the behavior.

## 6. Open the PR

Use the PR template. Every PR must have:

- `Closes #N` for the issue you claimed (one issue per PR).
- **Evidence:** the exact commands you ran and their output, or screenshots, showing the change works on the real app.
- **Overlap check:** the result of `scripts/pr-overlap.py check` against your changed files.
- **deep-mode report:** if an agent did the work, paste its final report (goal restated, what changed, how it was proven).
- Only the files your claim named. Touching more? Update your claim first and re-run the overlap check.

## 7. Review

- **Checks** must pass, run locally before you open the PR and again after each fix: {{CI_CHECKS}}. Paste the output in the PR. There is no CI.
- **Overlap check:** your agent runs `python scripts/pr-overlap.py comment --repo {{OWNER/REPO}} --pr <N>` after opening the PR, and the maintainer's agent re-runs it on open PRs. It posts one comment when your PR touches the same files as another open PR or an active claim. Resolve the overlap with the other author before merge.
- **Review:** before opening a PR, your agent self-reviews its branch with deep-mode's pr-review technique (local mode) and fixes or dismisses each finding. Maintainers review PRs with `/deep-mode:review-pr`; address or reply to each finding.
- A maintainer reviews and merges. Push follow-up commits to the same branch; don't open a second PR for the same issue.

## Without an agent

Everything above works by hand: post the claim comment, run the overlap check, fill in the PR template with your evidence.

## Roadmap

[ROADMAP.md](ROADMAP.md) is generated from GitHub Issues by `scripts/sync-roadmap.py`. Edit issues, not that file.
