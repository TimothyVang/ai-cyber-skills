# deep-mode

**deep-mode** brings rigorous engineering habits to [omp](https://github.com/can1357/oh-my-pi) and Claude Code agents. It ships the `/poteto` command, verification skills, its own PR review loop, and `rasmic-stack`. It replaces GitHub Actions, Greptile, and CodeRabbit: checks, reviews, security audits, overlap comments, and roadmap syncs are run by your own agent on your own subscription. Built for the Ai Cyber community; anyone can use and improve it.

deep-mode is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT). Her idea is "if you want to go fast, go deep first": agents prove their work instead of claiming it.

## What you get

| Piece | What it does |
|---|---|
| `/poteto <anything>` | The one command. It reads your request and the repo, routes it (fix, feature, review a PR, drive a kanban board, chart a big effort, grill a plan, contribute to a project, set up a project for helpers, start a new app and pick its stack), sizes it (fast path for small jobs, full playbook for big ones), proves the result on the real app, lands it on a 3-agent panel pass, and reports what it decided. |
| `deep-mode` skill | 26 playbooks (bug fix, feature, board, wayfinder, factory, perf, refactor, prototype, babysit, shipping, autopilot, and more), 24 principles, and 28 techniques, including the verdict panel, grill, coworkers, prior-art search (GitHub, package registries, docs) before building, a security audit of each PR run by your agent, and PR-Agent run locally on the subscription your omp is logged into (Claude or Codex). |
| `create-verification-skill` | Builds a per-repo `verify-<app>` skill: a control CLI plus a feature map, so agents can drive your app and capture proof. |
| `maintain-verification-skill` | Keeps that verify skill accurate as the app changes. |
| `rasmic-stack` skill | Ras Mic's stack picks and the philosophy behind them: 57 cited decision rules from 166 of his videos. For web and SaaS apps it uses his exact picks. For any other app (CLI, desktop, mobile, AI agent, data/ML, security tooling) it applies his rules, labels those picks **inferred**, prototypes the risky ones, and writes a cited `STACK.md`. It also carries his UI design workflow and rstack software factory. |
| PR review | `/deep-mode:review-pr <PR number>` reviews a PR with your own agent and parallel reviewer subagents, keeps only findings a code read or run proves, posts one comment-only GitHub review (on your own repo without asking), and re-reviews new commits until clean. Agents also self-review before opening a PR. No outside review service; code stays where the agent runs. |
| Land a PR | `/deep-mode:land-pr <PR number>` finishes and merges your own PR with no human: reviewer bots post findings in the PR thread, the author bot answers each with a fix or a reason, three verifier bots vote on the final head, and on a pass it merges. Where the branch requires an approving review, it admin-merges only on your request or when the base branch's `.deep-mode.json` sets `"autonomousMerge": true`, and never over a failing check. Every bot runs on your own subscription in omp; no API keys. |
| `project-brief` (maintainer) | Publishes a project for contributors: a newcomer brief (`docs/PROJECT_BRIEF.md`), small claimable tasks as GitHub Issues, a generated `ROADMAP.md`, PR and issue templates, `CONTRIBUTING.md`, and two scripts the agent runs (no GitHub Actions): one comments when PRs touch the same files, one regenerates the roadmap. |
| `contribute` (contributor) | `/deep-mode:contribute <what you'd like to work on>` briefs a newcomer's agent on the project, finds an unclaimed task that doesn't overlap open PRs or other claims, claims it, builds and proves it through deep-mode, and opens a PR that closes the issue. |
| Trending catalog | `scripts/trending.py` collects new and trending repos (GitHub Trending, GitHub search for new fast risers and agent topics like skills and MCP, and githubawesome.com), enriches them with stars, license, and language, and writes a categorized digest to `references/trending/`. Before building anything, deep-mode searches it, refreshing it first when it is over a day old, so newer projects can beat the idea it already knows. |

The agent works on its own: it makes product and design calls, commits, pushes, opens PRs, keeps a kanban board, and merges. A task is done, and a PR merges, only when a panel of three skeptical verifier agents runs it and at least two agree, with evidence the agent has checked. Parallel agents talk to each other directly, like coworkers. It still asks you before deploys, deleting things it didn't create, rewriting shared history, messaging people outside the repo, spending money, or using secrets only you have.

## Install

### omp

```bash
omp plugin marketplace add TimothyVang/deep-mode
omp plugin install deep-mode@deep-mode
```

Then, in any repo:

```text
/deep-mode:poteto <your task>
```

Plugin commands are prefixed with the plugin name. For a bare `/poteto`, copy `plugins/deep-mode/commands/poteto.md` to `~/.omp/agent/commands/`.

Optional: append `agents-snippet.md` to `~/.omp/agent/AGENTS.md`. It routes large or risky work to deep-mode and sets the verification rule for every session.

### Claude Code

```text
/plugin marketplace add TimothyVang/deep-mode
/plugin install deep-mode@deep-mode
```

The skills name omp tools (`task`, `todo`, `ask`). Claude Code's equivalents are `Agent`, `TodoWrite`, and `AskUserQuestion`.

### Manual

Copy every folder in `plugins/deep-mode/skills/` to `~/.omp/agent/skills/` (or `~/.claude/skills/`), and the files in `plugins/deep-mode/commands/` to your commands folder.

## Use it

```text
/poteto the coupon total is wrong. fix it
/poteto add CSV export to the reports page
/poteto review PR 42
/poteto what can I work on in this project?
/poteto set this project up so other people can contribute
/poteto start a new app: a CLI that converts Sigma rules for our SIEM
/poteto check on PR 42, and ship it when it's green
```

- You never pick a skill or playbook. `/poteto` routes, sizes, and runs it.
- Small jobs take the fast path. Big ones get the full playbook, subagents, and a decision log.
- It decides and acts without asking: commits, pushes, PRs, board cards, and merges after a panel pass. It asks once at the end only for hard stops (deploys, deletions, shared-history rewrites, outside messages, money, secrets), and lists every decision it made so you can reverse any.
- On a new repo, medium and large jobs first build a `verify-<app>` skill so the agent can prove changes. Later runs reuse it.
- The direct commands still work: `/deep-mode:review-pr`, `/deep-mode:land-pr`, `/deep-mode:contribute`, `/deep-mode:project-brief`.

## Collaborate on a project

Maintainer, once per project (and again when it changes):

```text
/deep-mode:project-brief
```

Contributor, after installing the plugin:

```text
/deep-mode:contribute I know Python and want to help with detections
```

- **Claims:** a contributor's agent posts a claim comment on the issue (who, plan, files, expiry in 7 days). Other agents read claims and skip claimed work.
- **Overlap check:** before starting and before opening a PR, the agent compares its files with every open PR and active claim. On overlap it picks other work, coordinates on the issue, or builds on top. After opening the PR it runs `scripts/pr-overlap.py comment` so the PR carries an overlap comment; the maintainer's agent re-runs it on open PRs.
- **Limits:** claims are a convention, not a lock. The overlap check catches shared files, not logic conflicts in different files; local checks, review, and the panel catch those.
- **Review:** the maintainer reviews each PR with `/deep-mode:review-pr <PR number>`; contributors' agents self-review before opening one.

## Trending catalog

`plugins/deep-mode/skills/deep-mode/scripts/trending.py` keeps `references/trending/` current with no scheduler: `find <terms>` runs `update` first when the catalog is over a day old (about a minute; uses `GITHUB_TOKEN`, `GH_TOKEN`, or `gh auth token`), and `find --no-refresh` skips that. `catalog.json` keeps every repo seen in the last 120 days with first-seen date and star growth; `README.md` is the digest agents read. Commit a refreshed catalog when you want the repo copy current for other installs. To add a source, write a `source_*` function in `trending.py` and list it in `SOURCES`; to watch another GitHub topic, add it to `WATCH_TOPICS`.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: branch, edit, run `python scripts/check.py` (there is no CI, so this is the gate), open a PR.

## License

MIT. See [LICENSE](LICENSE). Portions are derived from pstack, Copyright (c) 2026 Lauren Tan, and from Matt Pocock's skills (the `grill` technique and `wayfinder` playbook, MIT; notice in `plugins/deep-mode/skills/deep-mode/LICENSE`). Vendored references under `plugins/deep-mode/skills/rasmic-stack/references/` keep their own licenses: `unslop` (MIT, Lauren Tan), `before-and-after` (PolyForm Shield 1.0.0, James Clements).
