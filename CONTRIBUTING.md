# Contributing

Anyone can improve these skills, starting with the Ai Cyber community. Changes land through pull requests.

Many people and their agents work on this repo at once. The rules below keep two people from building the same thing and make every PR easy to trust. Read [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) first: what the project is, how to run it, and what not to do.

## Flow

1. Branch from `main`.
2. Edit. Each plugin lives in `plugins/<name>/`; skills in `plugins/<name>/skills/<skill>/SKILL.md`.
3. Run `python scripts/check.py`. It must print `OK`. There is no CI; this local run is the gate.
4. Open a PR. Say what agent behavior you saw, what you changed, and how you tested it, including the check output.
5. A maintainer reviews and merges.

To pick up a task from the board, claim it first (sections 2 to 4 below).

## 1. Install deep-mode

deep-mode is an agent plugin that restates the goal, plans, proves changes on the real app, and reports with evidence.

Install the plugin in omp, Claude Code, or Codex with the commands in the Install section of [README.md](README.md). Each is two commands: add the `TimothyVang/deep-mode` marketplace, then install the `deep-mode` plugin from it.

You also need the GitHub CLI, signed in (`gh auth status`), and Python 3.10+.

## 2. Run `/deep-mode:contribute`

In your clone of `TimothyVang/deep-mode`:

```text
/deep-mode:contribute
/deep-mode:contribute #42
/deep-mode:contribute something small in the docs
```

Your agent reads the brief, lists open `help wanted` issues that nobody has claimed and that don't overlap open PRs or other claims, and recommends one. Nothing public happens without your yes: the agent asks before it claims, comments, commits, pushes, or opens a PR.

Task issues carry the `discussion-only` label too. It tells this repo's bots not to build them, so they stay open for you.

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
- An issue with an assignee counts as claimed too, unless that assignee posted a claim comment on it: then only the comment counts.
- Giving up? Comment on the issue with `<!-- deep-mode:unclaim -->` on its own line plus a short note, so someone else can pick it up.
- Expired claims are released. The scripts stop counting a claim the day after `Expires`, even when the claimant is still assigned, and the maintainer comments that the issue is open again.
- Don't claim more than you can finish in a week. Split big tasks first.

## 4. Check for overlap, twice

Two path sets overlap when a path is equal or one is a directory (`dir/`) containing the other. Check before you start and again before you open the PR:

```bash
python scripts/pr-overlap.py check --repo TimothyVang/deep-mode --files scripts/check.py,docs/ --exclude-issue N
```

After claiming, pass `--exclude-issue <your issue>` so your own claim isn't reported. Exit code `0` means no overlap. `3` means an open PR or an active claim touches the same paths; the output lists them. Coordinate on that issue or PR, or pick another task. `2` means a usage or `gh` error. To list active claims: `python scripts/pr-overlap.py claims --repo TimothyVang/deep-mode`.

## 5. Build and prove it

Follow [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for setup, conventions, and constraints. Before calling a change done, run the checks and prove the change on the real thing:

```bash
python scripts/check.py                    # must print OK
python plugins/deep-mode/skills/deep-mode/assets/github-app/test_bot.py   # for bot changes
```

A skill or playbook change is proven by running an agent with it (see "Testing a behavior change" below). A bot change is proven by a test in `test_bot.py` plus a `bot.py once --repo <owner/repo> --dry-run` preview. A platform task (macOS, Linux, a harness) is proven by the commands and output from that platform.

Passing tests alone are not proof. Show the behavior.

## 6. Open the PR

Use the PR template. Every PR must have:

- `Closes #N` for the issue you claimed (one issue per PR).
- **Evidence:** the exact commands you ran and their output, or screenshots, showing the change works on the real app.
- **Overlap check:** the result of `scripts/pr-overlap.py check` against your changed files.
- **deep-mode report:** if an agent did the work, paste its final report (goal restated, what changed, how it was proven).
- Only the files your claim named. Touching more? Update your claim first and re-run the overlap check.

## 7. Review

- **Checks** must pass, run locally before you open the PR and again after each fix: `python scripts/check.py` prints `OK`, and `test_bot.py` passes when you touched the bots. Paste the output in the PR. There is no CI.
- **Overlap check:** your agent runs `python scripts/pr-overlap.py comment --repo TimothyVang/deep-mode --pr <N>` after opening the PR, and the maintainer's agent re-runs it on open PRs. It posts one comment when your PR touches the same files as another open PR or an active claim. Resolve the overlap with the other author before merge.
- **Review:** before opening a PR, your agent self-reviews its branch with deep-mode's pr-review technique (local mode) and fixes or dismisses each finding. This repo's bots post review comments on your PR; maintainers also review with `/deep-mode:review-pr`. Address or reply to each finding.
- A maintainer merges. The bots never merge a contributor's PR. Push follow-up commits to the same branch; don't open a second PR for the same issue.

## Without an agent

Everything above works by hand: post the claim comment, run the overlap check, fill in the PR template with your evidence.

## Roadmap

[ROADMAP.md](ROADMAP.md) is a snapshot of the task board, generated from GitHub Issues by `scripts/sync-roadmap.py`. Edit issues, not that file.

- It goes stale between syncs. The live board is the open `help wanted` issues plus `python scripts/pr-overlap.py claims --repo TimothyVang/deep-mode`. `/deep-mode:contribute` reads those, not the file.
- The maintainer's agent refreshes it on every `/deep-mode:project-brief` re-run with `python scripts/sync-roadmap.py --repo TimothyVang/deep-mode` and ships the changed file in that run's PR.
- To see whether it is current: `python scripts/sync-roadmap.py --repo TimothyVang/deep-mode --check`. Exit `1` means out of date.
- Leave it out of task PRs. A regenerated roadmap in every PR would overlap all the others.

## What the check enforces

- Every `SKILL.md` has `name` and `description` frontmatter, and `name` matches its folder.
- Every `references/...md` link resolves to a real file. No `#anchor` links (omp can't read them).
- No line longer than 760 bytes (omp's `read` cuts long lines).
- Marketplace and plugin manifests, and `plugins/*/hooks/hooks.json`, are valid JSON and point at real folders.
- No upstream project or author names outside `LICENSE*` and `NOTICE*` files. The list is `BANNED` in `scripts/check.py`; attribution lives in `NOTICE.md`.
- The README's playbook, principle, and technique counts match the folders, and `docs/llms-full.txt` matches the files it embeds (`python scripts/check.py --fix` rewrites it).
- In deep-mode's `SKILL.md`, the rules above `## Routes` fit in 20,000 bytes (about 5,000 tokens), which is what Claude Code keeps of a skill after it compacts a long session. Put lookup tables below that heading and long detail in `references/`.
- Every Python file parses, and every `test_*.py` folder passes (`assets/contain`, `assets/loop`, `assets/github-app`, `assets/git-guardrails`, `assets/pr-conversation`). The tests need `git` and `bash`; the omp hook cases also need `bun` and are skipped without it. The check takes about two minutes.

## Keep it rebrandable

Resellers ship this repo under their own brand with `scripts/whitelabel.py` (see `docs/rebrand.md`). When you add a name, a page section, an image or a manifest field, run `python scripts/test_whitelabel.py` and build the example brand into a folder outside the repo: `python scripts/whitelabel.py --brand brand/examples/acme.json --out ../acme-review`. It must print `OK` with 0 leftovers.

A line that names the product grows when a reseller's names are longer. `test_whitelabel.py` builds this repo with the longest names a brand file may carry (`MAX_BYTES` in `scripts/media/brandlib.py`) and fails on any Markdown line that would pass 760 bytes. Split a line it reports.

## Testing a behavior change

A wording change can change what agents do. Before a PR that changes a playbook or technique, run the change on a throwaway repo with a small planted bug:

```bash
omp -p --plugin-dir plugins/deep-mode "/deep-mode:deep <task that exercises your change>"
claude -p "/deep-mode:deep <task>" --plugin-dir plugins/deep-mode
codex exec "\$deep-mode:deep-mode <task>"   # after `codex plugin marketplace add <this checkout>` and `codex plugin add deep-mode@deep-mode`
```

Report what the agent did before and after in the PR. For bigger changes, follow the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`).

## Style for skill text

- Short declarative sentences. One rule per line.
- Prefer a lint, test, or script over more prose (see the `encode-lessons-in-structure` principle).
- Git and forge actions follow the Autonomy section of `plugins/deep-mode/skills/deep-mode/SKILL.md`: agents commit, push, open PRs, and merge on a panel pass, and stop only at its hard stops. A skill that needs a new hard stop adds it there, not in its own text.
