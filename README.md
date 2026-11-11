# deep-mode

**deep-mode** brings rigorous engineering habits to [omp](https://github.com/can1357/oh-my-pi), Claude Code, and Codex agents. It ships the `/poteto` command, verification skills, its own PR review loop, a guard that keeps every write inside the project, and `rasmic-stack`. Built for the Ai Cyber community; anyone can use and improve it.

deep-mode is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT). Her idea is "if you want to go fast, go deep first": agents prove their work instead of claiming it.

## What you get

| Piece | What it does |
|---|---|
| `/poteto <anything>` | The one command. It reads your request and the repo, routes it (fix, feature, review a PR, drive a kanban board, chart a big effort, grill a plan, contribute to a project, set up a project for helpers, start a new app and pick its stack), sizes it (fast path for small jobs, full playbook for big ones), proves the result on the real app, lands it on a 3-agent panel pass, and reports what it decided. |
| `deep-mode` skill | 26 playbooks (bug fix, feature, board, wayfinder, factory, perf, refactor, prototype, babysit, shipping, autopilot, and more), 24 principles, and 28 techniques, including the verdict panel, grill, coworkers, prior-art search (GitHub, package registries, docs) before building, a CI security audit of every PR, and PR-Agent run locally on the subscription your omp is logged into (Claude or Codex). |
| Harness references | Cited, dated guides (checked 2026-11-11) for using omp, Claude Code, and Codex, the MCP, ACP, A2A, and WebMCP protocols, and portable AI-native conventions (`AGENTS.md`, Agent Skills, plugin marketplaces). A cross-harness map translates every omp tool and path deep-mode names into Claude Code and Codex. In `plugins/deep-mode/skills/deep-mode/references/harnesses/`. |
| Contained work | The agent works only inside the project's repo. Scratch and temp files go in `.scratch/`, worktrees in `.worktrees/` (both git-ignored), never system temp or folders outside the repo. With no repo it creates a named one first. A guard enforces this in Claude Code and omp; Codex's sandbox does it natively. |
| `create-verification-skill` | Builds a per-repo `verify-<app>` skill: a control CLI plus a feature map, so agents can drive your app and capture proof. |
| `maintain-verification-skill` | Keeps that verify skill accurate as the app changes. |
| `rasmic-stack` skill | Ras Mic's stack picks and the philosophy behind them: 57 cited decision rules from 166 of his videos. For web and SaaS apps it uses his exact picks. For any other app (CLI, desktop, mobile, AI agent, data/ML, security tooling) it applies his rules, labels those picks **inferred**, prototypes the risky ones, and writes a cited `STACK.md`. It also carries his UI design workflow and rstack software factory. |
| PR review | `/deep-mode:review-pr <PR number>` reviews a PR with your own agent and parallel reviewer subagents, keeps only findings a code read or run proves, posts one comment-only GitHub review (on your own repo without asking), and re-reviews new commits until clean. Agents also self-review before opening a PR. No outside review service; code stays where the agent runs. |
| Land a PR | `/deep-mode:land-pr <PR number>` finishes and merges your own PR with no human: reviewer bots post findings in the PR thread, the author bot answers each with a fix or a reason, three verifier bots vote on the final head, and on a pass it merges. Where the branch requires an approving review, it admin-merges only on your request or when the base branch's `.deep-mode.json` sets `"autonomousMerge": true`, and never over a failing check. Every bot runs on your own subscription in omp; no API keys. |
| `project-brief` (maintainer) | Publishes a project for contributors: a newcomer brief (`docs/PROJECT_BRIEF.md`), small claimable tasks as GitHub Issues, a generated `ROADMAP.md`, PR and issue templates, `CONTRIBUTING.md`, and two GitHub Actions: one flags PRs that touch the same files, one keeps the roadmap current. |
| `contribute` (contributor) | `/deep-mode:contribute <what you'd like to work on>` briefs a newcomer's agent on the project, finds an unclaimed task that doesn't overlap open PRs or other claims, claims it, builds and proves it through deep-mode, and opens a PR that closes the issue. |

The agent works on its own: it makes product and design calls, commits, pushes, opens PRs, keeps a kanban board, and merges. A task is done, and a PR merges, only when a panel of three skeptical verifier agents runs it and at least two agree, with evidence the agent has checked. Parallel agents talk to each other directly, like coworkers. It still asks you before deploys, deleting things it didn't create, rewriting shared history, messaging people outside the repo, spending money, using secrets only you have, or writing anywhere outside the project.

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

Once any `/deep-mode:` command runs in a session, the plugin's hook denies `Write`, `Edit`, and `NotebookEdit` outside the project for the rest of that session. Your other sessions are untouched. It needs `python` or `python3` on `PATH`.

The skills name omp tools (`task`, `todo`, `ask`). `plugins/deep-mode/skills/deep-mode/references/harnesses/README.md` maps them: `Agent`, `TaskCreate` or `TodoWrite`, and `AskUserQuestion`.

### Codex

```bash
codex plugin marketplace add TimothyVang/deep-mode
codex plugin add deep-mode@deep-mode
```

Codex loads the skills but not the commands. Start with `$deep-mode:deep-mode <your task>`. To keep writes in the project, run with `--sandbox workspace-write` and add this to `~/.codex/config.toml` so temp dirs are fenced too:

```toml
[sandbox_workspace_write]
exclude_tmpdir_env_var = true
exclude_slash_tmp = true
```

### Manual

Copy every folder in `plugins/deep-mode/skills/` to `~/.omp/agent/skills/` (or `~/.claude/skills/`, or `~/.agents/skills/` for Codex), and the files in `plugins/deep-mode/commands/` to your commands folder. In Claude Code a manual install arms the guard only when you invoke the `deep-mode` skill itself.

### Turn on the guard in omp

omp has no sandbox, so add deep-mode's hook. It blocks `write`, `edit`, and `ast_edit` outside the project in every session:

```bash
mkdir -p ~/.omp/agent/hooks/pre
cp plugins/deep-mode/skills/deep-mode/assets/contain/omp-contain.ts ~/.omp/agent/hooks/pre/
```

For one run only, pass `--hook <path to omp-contain.ts>` instead. To let the agent write to a folder outside the project you named, list it in the project's `.deep-mode.json` as `{"extraWriteRoots": ["~/some/folder"]}`. The guards don't parse shell commands, so the skill's rule still binds `bash`.

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
- **Overlap check:** before starting and before opening a PR, the agent compares its files with every open PR and active claim. On overlap it picks other work, coordinates on the issue, or builds on top. A GitHub Action also comments on any PR that touches the same files as another.
- **Limits:** claims are a convention, not a lock. The overlap check catches shared files, not logic conflicts in different files; CI and review catch those.
- **Review:** the maintainer reviews each PR with `/deep-mode:review-pr <PR number>`; contributors' agents self-review before opening one.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: branch, edit, run `python scripts/check.py`, open a PR. CI runs the same check.

## License

MIT. See [LICENSE](LICENSE). Portions are derived from pstack, Copyright (c) 2026 Lauren Tan, and from Matt Pocock's skills (the `grill` technique and `wayfinder` playbook, MIT; notice in `plugins/deep-mode/skills/deep-mode/LICENSE`). Vendored references under `plugins/deep-mode/skills/rasmic-stack/references/` keep their own licenses: `unslop` (MIT, Lauren Tan), `before-and-after` (PolyForm Shield 1.0.0, James Clements).
