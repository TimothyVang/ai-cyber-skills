# deep-mode: project brief

Start here if you're new to this repo, human or agent. It says what the project is, how it's built, how to run and prove a change, what not to do, and where help is wanted. `/deep-mode:contribute` reads this file first.

Last refreshed: 2026-11-11 against commit `ffd987c`.

## What and why

deep-mode is an MIT plugin for coding agents. It ships two things. First, a skill set: one `/deep` command routes any task to a playbook, applies named principles and techniques, keeps writes inside the project, and proves the result on the real app. Second, PR and issue bots that run on the user's own private GitHub App and their own agent subscriptions, with no API keys and no server.

The problem it solves: agents that claim work is done without proof, and AI review that needs a paid outside service. Here every change is proven on the real artifact and lands only after a three-agent verifier panel passes.

## Who it's for

- Developers who run omp, Claude Code, Codex, Cursor or another harness that loads `SKILL.md` skills, and want their agent to work with rigor.
- Repo owners who want the bots to review, fix and merge their own PRs and build the issues they open.
- Maintainers who open a project to many contributors (`/deep-mode:project-brief`) and contributors who join one (`/deep-mode:contribute`).

The workflow that must never break: install the plugin, run `/deep <task>`, and get a proven result. The skill text is the product, so a wording change is a behavior change.

## Status

Version 0.4.0 (`plugins/deep-mode/.claude-plugin/plugin.json`). The skill set is in daily use in omp and Claude Code. The bots have taken real PRs on this repo from review to merge, for example #19.

Known gaps:

- Bot autostart is proven on Windows only. The launchd (macOS) and systemd or cron (Linux) paths in `bot.py` have not run on a real machine (#38, #39).
- The wizard template has not run under macOS's default bash 3.2 (#40).
- The git-guardrails hooks have unit-style checks (`git-guard.sh --check`) but no recorded live run inside omp or Claude Code (#41, #42).
- The tracker technique documents GitHub and local trackers in full; GitLab falls under "other" with no exact commands (#43).
- `check_skill.py` reports five false positives (#44), and the overlap script's path and claim-parsing functions have no tests (#45).

The bots are building some fixes themselves right now (open issues #21, #27, #29, #30, #37). Those are not open to claim.

Open work lives in GitHub Issues labeled `help wanted`; [ROADMAP.md](../ROADMAP.md) is generated from them.

## Architecture map

| Path | Responsibility | Entry point |
|---|---|---|
| `plugins/deep-mode/skills/deep-mode/` | The main skill: routing, rules, autonomy, and the reply format | `SKILL.md` |
| `plugins/deep-mode/skills/deep-mode/references/playbooks/` | One file per task type (bug fix, feature, spec, tickets, board, land a PR and more) | the playbook named in the Playbooks section of `SKILL.md` |
| `plugins/deep-mode/skills/deep-mode/references/techniques/` | Reusable techniques (tdd, panel, pr-review, tracker, wizard, git-guardrails, github-app and more) | the technique file a playbook names |
| `plugins/deep-mode/skills/deep-mode/references/principles/` | Named principles the playbooks cite | the principle file a playbook names |
| `plugins/deep-mode/skills/deep-mode/references/` other folders | Cited reference guides: `harnesses/`, `architecture/`, `credentials/`, `cloud-devsecops/`, `domain-rules/`, `frontend/`, `trending/` | each folder's `README.md` |
| `plugins/deep-mode/skills/deep-mode/assets/github-app/` | The PR and issue bots: poller, GitHub App auth, installer, autostart | `bot.py`, `install.py`, `test_bot.py` |
| `plugins/deep-mode/skills/deep-mode/assets/` other folders | Scripts the skill copies or runs: containment guards (`contain/`), git guard hooks (`git-guardrails/`), goal loop (`loop/`), wizard template (`wizard/`), security audit, scrape, PR-Agent | the script in each folder |
| `plugins/deep-mode/skills/deep-mode/scripts/` | `check_skill.py` (validates a skill folder) and `trending.py` (trending-repo catalog) | each script's docstring |
| `plugins/deep-mode/skills/project-brief/`, `contribute/` | Maintainer and contributor flows for open collaboration, with the overlap and roadmap scripts | `SKILL.md`, `assets/` |
| `plugins/deep-mode/skills/deep-stack/`, `create-verification-skill/`, `maintain-verification-skill/` | Stack picks and ship loop; per-repo `verify-<app>` skills | `SKILL.md` |
| `plugins/deep-mode/commands/` | Slash commands: `/deep`, `review-pr`, `land-pr`, `contribute`, `project-brief` | `deep.md` |
| `plugins/deep-mode/hooks/hooks.json` | Claude Code hook that arms the containment guard | `hooks.json` |
| `.omp-plugin/`, `.claude-plugin/` | Marketplace manifests for omp and Claude Code | `marketplace.json` |
| `scripts/` | Repo gate (`check.py`), overlap check, roadmap generator | `check.py` |
| `docs/` | The GitHub Pages site, `llms.txt`, images | `index.html` |

A harness loads `SKILL.md`, which routes a task to one playbook. The playbook cites techniques and principles by path (`references/...md`), and `check.py` fails on any link that doesn't resolve. The bots are separate Python: `bot.py` polls the repos where the user's app is installed, runs ACP agents through acpx for each role, posts their turns as the app, and uses the user's own `gh` and git credentials for pushes and merges.

## Stack

- Skill text: Markdown, read by the agent harness. No build step.
- Scripts: Python 3 standard library only (`bot.py`, `install.py`, `check.py`, `loop.py`, the overlap and roadmap scripts). Bash for the wizard and the Claude Code git guard. TypeScript for the omp hooks (`omp-contain.ts`, `git-guard.ts`).
- External tools the scripts call: `git`, `gh`, `acpx` (bots), `openssl` (app auth), `jq` (optional, git guard).
- No package manifest, no lockfile, no CI. The checks run locally.

## Run and verify

Every command below ran on Windows 11 with Python 3.13 and Git Bash at commit `ffd987c`, with the result shown. The test and check block ran again, top to bottom from the repo root, at `7285779`.

Setup:

```bash
gh repo clone TimothyVang/deep-mode && cd deep-mode
```

Run the skill from your checkout (unverified in this pass: each run spends agent subscription usage):

```bash
claude -p "/deep-mode:deep <task>" --plugin-dir plugins/deep-mode
omp -p "/deep <task>"   # after installing the plugin from this checkout
```

Test and check (run these before every PR; there is no CI):

```bash
py -3 scripts/check.py                     # prints OK
py -3 plugins/deep-mode/skills/deep-mode/assets/github-app/test_bot.py   # Ran 63 tests ... OK
py -3 plugins/deep-mode/skills/deep-mode/scripts/check_skill.py plugins/deep-mode/skills/*
#   prints 5 problems, exit 1: each path exists in another skill or at the repo root (#44)
bash plugins/deep-mode/skills/deep-mode/assets/git-guardrails/git-guard.sh --check 'git reset --hard'
#   prints the block reason, exit 2
py -3 plugins/deep-mode/skills/deep-mode/assets/github-app/bot.py --help   # lists once, watch, status, install-autostart, uninstall-autostart
```

Use `python3` instead of `py -3` on macOS and Linux.

Prove a change on the real app:

There is no `verify-<app>` skill in this repo. The app is the agent's behavior, so prove a skill change by running it:

1. Make a throwaway repo with a small planted bug or task that exercises your change.
2. Run the agent on it before and after your change (`omp -p "/deep <task>"`, `claude -p "/deep-mode:deep <task>" --plugin-dir plugins/deep-mode`, or Codex as in `CONTRIBUTING.md`).
3. Put what the agent did before and after in the PR. For bigger changes, follow the Eval playbook (`plugins/deep-mode/skills/deep-mode/references/playbooks/eval.md`).

For bot changes, add or update a test in `test_bot.py`, then preview a real cycle with `bot.py once --repo <owner/repo> --dry-run`, which posts nothing.

## Conventions

- Skill text uses short declarative sentences, one rule per line, and plain words. No long dashes. See the style section in [CONTRIBUTING.md](../CONTRIBUTING.md).
- Markdown lines stay under 760 bytes (omp's `read` cuts long lines). `check.py` enforces it.
- Link other skill files as `references/<folder>/<file>.md`, never with a `#anchor`. `check.py` fails on broken or anchored links.
- Every `SKILL.md` has `name` and `description` frontmatter, and `name` matches its folder.
- Prefer a lint, test or script over more prose.
- Branch names: `<issue number>-<slug>` for claimed tasks. Commit subjects follow `type(scope): summary`, for example `fix(github-app): ...`.
- Git and forge actions follow the Autonomy section of `plugins/deep-mode/skills/deep-mode/SKILL.md`.

## Constraints and don'ts

- Write only deep-mode's own names. `check.py` fails on the names of other products and people (the white-label check); `LICENSE` and `NOTICE.md` files are the only place upstream credits live.
- Don't edit `references/frontend/` or `references/cloud-devsecops/` by hand. They are distilled from other repos (each folder's `README.md` names its source). Open an issue instead.
- Don't hand-edit `references/trending/`. `plugins/deep-mode/skills/deep-mode/scripts/trending.py` writes it.
- Keep every `LICENSE` file and the `NOTICE.md` table intact when moving or copying a component.
- No secrets, tokens, or real user data in skill text, tests, or fixtures. `brand.local.json` stays git-ignored.
- On this repo the bots implement every issue the owner opens unless it is labeled `discussion-only`. Contributor tasks carry that label so the bots leave them to you. The bots only comment on PRs from other people; they never merge them.
- Don't edit files that an open PR or an active claim holds. Run the overlap check first.

## Where help is wanted

- **Cross-platform proof.** Run the bot autostart, the wizard template, and the git guard hooks on machines and harnesses the maintainer can't easily reach (macOS, Linux, omp, Claude Code), and fix what breaks: #38, #39, #40, #41, #42. Skills: Python or bash, plus access to that OS or harness.
- **Trackers.** Exact GitLab commands for the tracker technique: #43. Skills: GitLab and `glab`.
- **Tooling and tests.** Make the skill checker clean on every skill (#44), and add tests for the overlap script (#45). Skills: Python.

- All claimable tasks: issues labeled [`help wanted`](https://github.com/TimothyVang/deep-mode/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
- Small starter tasks: [`good first issue`](https://github.com/TimothyVang/deep-mode/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

## How to contribute

Install the deep-mode plugin and run `/deep-mode:contribute` in a clone of this repo. Your agent reads this brief, picks an unclaimed task that doesn't overlap open PRs or other claims, claims it after you say yes, and builds and proves it before opening a PR. Full rules, including how to do it without an agent: [CONTRIBUTING.md](../CONTRIBUTING.md).
