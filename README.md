# deep-mode

**deep-mode** brings rigorous engineering habits to [omp](https://github.com/can1357/oh-my-pi) and Claude Code agents. It ships the `/poteto` command, verification skills, a Greptile PR loop, and `rasmic-stack`. Built for the Ai Cyber community; anyone can use and improve it.

deep-mode is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT). Her idea is "if you want to go fast, go deep first": agents prove their work instead of claiming it.

## What you get

| Piece | What it does |
|---|---|
| `/poteto <task>` | Runs a task through deep-mode. The agent restates your goal, picks a playbook, applies named principles, proves the change on the real app, and reports with evidence. |
| `deep-mode` skill | 22 playbooks (bug fix, feature, perf, refactor, prototype, babysit, shipping, autopilot, and more), 24 principles, and 21 techniques. |
| `create-verification-skill` | Builds a per-repo `verify-<app>` skill: a control CLI plus a feature map, so agents can drive your app and capture proof. |
| `maintain-verification-skill` | Keeps that verify skill accurate as the app changes. |
| `rasmic-stack` skill | Ras Mic's stack picks and the philosophy behind them: 57 cited decision rules from 166 of his videos. For web and SaaS apps it uses his exact picks. For any other app (CLI, desktop, mobile, AI agent, data/ML, security tooling) it applies his rules, labels those picks **inferred**, prototypes the risky ones, and writes a cited `STACK.md`. It also carries his UI design workflow and rstack software factory. |
| Greptile loop | On repos with the Greptile app, the PR playbooks wait for Greptile's review of the current commit, triage each finding (fix, dismiss, or ask), and loop until clean. Greptile is evidence, never a gate. |
| `project-brief` (maintainer) | Publishes a project for contributors: a newcomer brief (`docs/PROJECT_BRIEF.md`), small claimable tasks as GitHub Issues, a generated `ROADMAP.md`, PR and issue templates, `CONTRIBUTING.md`, and two GitHub Actions: one flags PRs that touch the same files, one keeps the roadmap current. |
| `contribute` (contributor) | `/deep-mode:contribute <what you'd like to work on>` briefs a newcomer's agent on the project, finds an unclaimed task that doesn't overlap open PRs or other claims, claims it, builds and proves it through deep-mode, and opens a PR that closes the issue. |

The agent never commits, pushes, opens a PR, or merges unless you ask.

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

Copy the three folders in `plugins/deep-mode/skills/` to `~/.omp/agent/skills/` (or `~/.claude/skills/`), and `plugins/deep-mode/commands/poteto.md` to your commands folder.

## Use it

```text
/poteto checkout total is wrong with a coupon. repro first, then fix and show proof
/poteto add CSV export to the reports page
/poteto why is the dashboard slow
/poteto check on PR 42
/poteto build the tech stack for this project using Ras Mic's philosophy
```

- On a new repo, the first run builds a `verify-<app>` skill. Later runs reuse it.
- Say "commit it", "open a PR", or "merge it" when you want git writes.
- Start fuzzy work with "restate in your own words what my goal is".

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
- **Overlap check:** before starting and before opening a PR, the agent compares its files with every open PR and active claim. On overlap it picks other work, coordinates on the issue, or builds on top. A GitHub Action also comments on any PR that touches the same files as another.
- **Limits:** claims are a convention, not a lock. The overlap check catches shared files, not logic conflicts in different files; CI and review catch those.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: branch, edit, run `python scripts/check.py`, open a PR. CI runs the same check.

## License

MIT. See [LICENSE](LICENSE). Portions are derived from pstack, Copyright (c) 2026 Lauren Tan. Vendored references under `plugins/deep-mode/skills/rasmic-stack/references/` keep their own licenses: `greploop` (MIT, Greptile AI), `unslop` (MIT, Lauren Tan), `before-and-after` (PolyForm Shield 1.0.0, James Clements).
