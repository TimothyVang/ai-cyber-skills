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
| `rasmic-stack` skill | Ras Mic's 2026 stack picks, AI UI design workflow, and rstack software factory (worktree, service-layer build, recorded evidence, Greptile 5/5 PR). deep-mode uses it for greenfield stack choices, UI design, and evidence recording. |
| Greptile loop | On repos with the Greptile app, the PR playbooks wait for Greptile's review of the current commit, triage each finding (fix, dismiss, or ask), and loop until clean. Greptile is evidence, never a gate. |

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
```

- On a new repo, the first run builds a `verify-<app>` skill. Later runs reuse it.
- Say "commit it", "open a PR", or "merge it" when you want git writes.
- Start fuzzy work with "restate in your own words what my goal is".

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: branch, edit, run `python scripts/check.py`, open a PR. CI runs the same check.

## License

MIT. See [LICENSE](LICENSE). Portions are derived from pstack, Copyright (c) 2026 Lauren Tan. Vendored references under `plugins/deep-mode/skills/rasmic-stack/references/` keep their own licenses: `greploop` (MIT, Greptile AI), `unslop` (MIT, Lauren Tan), `before-and-after` (PolyForm Shield 1.0.0, James Clements).
