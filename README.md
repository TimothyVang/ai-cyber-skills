# deep-mode

**deep-mode** is an open-source MIT plugin for coding agents. It has two halves:

- **PR and issue bots** on your own private GitHub App. Any ACP agent (omp by default, or Claude Code, Codex, Gemini CLI and others) runs on your machine with your own subscription login, not an API key. The bots review your PRs in the thread, fix their own findings, vote on a 3-agent verifier panel, and merge your own PRs behind a gate enforced in code. They plan and build the issues you open.
- **A software-factory skill set**: one `/deep` command that routes any task to a playbook, plus the flow from idea to merged code (setup, grill, spec, tickets, implement, review, land) and the techniques around it (TDD, triage, domain model, research, architecture review, prototype, board, factory, retro and more).

The skill runs in omp, Claude Code, Codex, Cursor and other harnesses that load `SKILL.md` skills. Built for the Ai Cyber community; anyone can use and improve it.

**Site:** [timothyvang.github.io/deep-mode](https://timothyvang.github.io/deep-mode/) · **Docs:** [how the bots work](plugins/deep-mode/skills/deep-mode/references/techniques/github-app.md) · [the flow map](plugins/deep-mode/skills/deep-mode/references/flows.md)

![The real thread of PR 19: the author bot merges main into the PR, the reviewer posts findings, the author fixes them, the coordinator blocks after three rounds, the owner says continue, two panels fail with evidence, the third passes 2/3, and the bot squash-merges](docs/images/pr-19-thread.gif)

A real run, not a mock-up: the bots took [PR #19](https://github.com/TimothyVang/deep-mode/pull/19) through 5 cycles. Two failed panels caught real bugs; the third passed 2/3 and the bot merged it.

![How the bots work: a private GitHub App on GitHub, and on your machine a poller that runs ACP agents through acpx and posts each turn as the app](docs/images/how-it-works.svg)

## What you get

| Piece | What it does |
|---|---|
| `/deep <anything>` | The one command. It reads your request and the repo, routes it (fix, feature, review a PR, write a spec, cut tickets, drive a board, run a factory, chart a big effort, grill a plan, contribute to a project, start a new app and pick its stack), sizes it (fast path for small jobs, full playbook for big ones), proves the result on the real app, lands it on a 3-agent panel pass, and reports what it decided. |
| `deep-mode` skill | 32 playbooks, 24 principles and 43 techniques, listed below. Every task is proven on the real artifact and merges only on a verifier panel pass. |
| PR and issue bots | Install your own private GitHub App on your repos and a poller on your machine runs the bots: it reviews and lands your own PRs, resolves their merge conflicts, and plans and builds the issues you open. See [GitHub App bots](#github-app-bots). |
| PR review | `/deep-mode:review-pr <PR number>` reviews a PR with your own agent and parallel reviewer subagents through correctness, security, spec and standards lenses, keeps only findings a code read or run proves, posts one comment-only review, and re-reviews new commits until clean. No outside review service; code stays where the agent runs. |
| Land a PR | `/deep-mode:land-pr <PR number>` finishes and merges your own PR with no human: a reviewer bot posts findings in the PR thread, the author bot answers each with a fix or a reason, three verifier bots vote on the final head, and on a pass it merges. It never merges over a failing check. You see each turn in the session as it lands, or watch the whole conversation play as an 8-bit battle screen (each bot a sprite, each turn a dialog box); `/deep-mode:pr-thread <PR or issue URL>` shows any bot conversation later. |
| `deep-stack` skill | Stack picks and a ship loop: a default software stack and the decision rules behind it for any app (web, CLI, desktop, mobile, AI agent, data/ML, security tooling), an agent-driven UI design workflow, and a per-task loop of worktree, build, recorded evidence and reviewed PR. |
| Verification skills | `create-verification-skill` builds a per-repo `verify-<app>` skill (a control CLI plus a feature map) so agents can drive your app and capture proof. `maintain-verification-skill` keeps it accurate as the app changes. |
| `project-brief` and `contribute` | A maintainer publishes a newcomer brief, claimable tasks as issues, a roadmap and templates. A contributor's agent finds an unclaimed task that doesn't overlap open PRs, claims it, builds it through deep-mode, and opens a PR. |
| Trending catalog | `scripts/trending.py` keeps a digest of new and trending repos that deep-mode searches before building anything. |
| Harness references | Cited, dated guides (checked 2026-11-11) for using omp, Claude Code, and Codex, the MCP, ACP, A2A, and WebMCP protocols, and portable AI-native conventions (`AGENTS.md`, Agent Skills, plugin marketplaces). A cross-harness map translates every omp tool and path deep-mode names into Claude Code and Codex. In `plugins/deep-mode/skills/deep-mode/references/harnesses/`. |
| Contained work | The agent works only inside the project's repo. Scratch and temp files go in `.scratch/`, worktrees in `.worktrees/` (both git-ignored), never system temp or folders outside the repo. With no repo it creates a named one first. A guard enforces this in Claude Code and omp; Codex's sandbox does it natively. |
| Credentials and auth | Cited, free-first guidance (checked 2026-11-11) for sharing API keys and `.env` safely, passwords and usernames, logins and MFA for agents, credential brokers, protecting MCP servers and agent APIs, CI OIDC, secret scanning, and leak response. In `plugins/deep-mode/skills/deep-mode/references/credentials/`. |
| Architecture | Cited, decision-ready guidance (checked 2026-11-11) for organizing monorepos, naming the domain (glossary, typed models, LinkML, RDF and SHACL, graph databases, Palantir-style ontology for agent actions), choosing and migrating databases with agents working safely against them, and backend infrastructure and system design (reliability, queues and durable workflows, APIs, OpenTelemetry, deployment, IaC). Each file ends with the default stack for a solo dev or small team. In `plugins/deep-mode/skills/deep-mode/references/architecture/`. |
| Self-authoring | deep-mode writes, validates, and proves its own prompts, skills, goals, and loops: project-local first, a deep-mode PR next, user-level only with your yes. `assets/loop/loop.py` runs a goal file headless in omp, Claude Code, or Codex until its check command passes, with an iteration cap, cost cap, stall stop, and a stop if the agent edits its own goal or the files its check runs, or the harness fails. Interactive sessions use each harness's native `/goal`. |
| Efficient delegation | When a subagent pays for itself, which model tier and reasoning effort fits each task (search, mechanical edits, features, hard design, review, long runs, summaries) in omp, Claude Code, and Codex, how subscription limits are metered, and how to cut token use. In `plugins/deep-mode/skills/deep-mode/references/harnesses/delegation-efficiency.md`, checked 2026-11-11. |

The agent works on its own: it makes product and design calls, commits, pushes, opens PRs, keeps a board, and merges. A task is done, and a PR merges, only when a panel of three skeptical verifier agents runs it and at least two agree, with evidence the agent has checked. It still asks you before deploys, deleting things it didn't create, rewriting shared history, messaging people outside the repo, spending money, using secrets only you have, or writing anywhere outside the project.

## The software factory

The main line takes an idea to merged code. Skip the phases a job doesn't need. [The flow map](plugins/deep-mode/skills/deep-mode/references/flows.md) has the full table.

| Phase | Flow | Leaves behind |
|---|---|---|
| 0. Set up the repo once | Setup playbook | A tracker (GitHub issues, local files, or another tracker), mapped labels, `GLOSSARY.md`, `docs/adr/`, `CODING_STANDARDS.md`, an `AGENTS.md` section |
| 1. Sharpen the idea | **grill**, with its With docs mode | A decision table, glossary terms, ADRs |
| 2. Settle a fork by running it | Prototype playbook | A decision backed by an observation |
| 3. Write it down | Spec playbook | `docs/specs/<slug>.md` and a spec issue |
| 4. Cut it up | Tickets playbook | Tickets with their blockers |
| 5. Build it | Implement spec (one integration branch) or Board (one PR per ticket), with **tdd** | Merged code |
| 6. Review and land | **pr-review** (spec and standards lenses), **panel**, **pr-conversation** | A merged PR with evidence |

Around the main line:

- **Triage:** Sorts incoming issues and outside PRs into a category and a state, and posts a brief or the questions that block them.
- **Wayfinder:** Charts an effort too big for one session and hands its decisions to a spec.
- **Board:** Runs a project on GitHub issues with status labels. Every task ends in a merge after a panel pass.
- **Factory:** Runs a queue of labeled issues through the `factory` CLI: spec, hidden tests, code, reviews and merge for each job.
- **Orchestrate:** Runs a multi-day program with many stacked PRs and subagents from one coordinator.
- **domain-model:** Keeps `GLOSSARY.md` and ADRs current as names and decisions change.
- **research:** Writes an answer that later sessions will cite into the repo.
- **architecture-review:** Finds structural friction across the codebase and settles which refactors to make.
- **security-audit:** Audits a PR's security before it merges, run by your own agent.
- **retro:** Improves the repo's files, checks and docs after a session, so the next agent works faster.
- **Handoff and Pause safely:** A portable doc for another session, harness or person, or a resume note for later in this repo.
- **questionnaire:** Writes the questions for the one person who holds a fact nobody else has.
- **wizard:** A guided script for steps only a human can do: dashboards, credentials, irreversible clicks.
- **teach and course:** Explains a change or subsystem, or runs a course on a topic over many sessions.
- **pre-commit:** Runs the repo's own lint, typecheck and tests at commit time.
- **git-guardrails:** Turns the git hard stops into a hook the harness enforces before a destructive command runs.
- **deep-stack:** Stack picks and decision rules for any app, an agent-driven UI design workflow, and a per-task ship loop.
- **Verification skills:** Build and maintain a per-repo `verify-<app>` skill so agents can drive your app and capture proof.

## Install

### omp

```bash
omp plugin marketplace add TimothyVang/deep-mode
omp plugin install deep-mode@deep-mode
```

Then, in any repo:

```text
/deep-mode:deep <your task>
```

Plugin commands are prefixed with the plugin name. For a bare `/deep`, copy `plugins/deep-mode/commands/deep.md` to `~/.omp/agent/commands/`.

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

Copy every folder in `plugins/deep-mode/skills/` to `~/.omp/agent/skills/` (or `~/.claude/skills/`, or `~/.agents/skills/` for Codex), and the files in `plugins/deep-mode/commands/` to your commands folder. Cursor and other harnesses that load `SKILL.md` skills take the same folders in their own skills folder. In Claude Code a manual install arms the guard only when you invoke the `deep-mode` skill itself.

### Turn on the guard in omp

omp has no sandbox, so add deep-mode's hook. It blocks `write`, `edit`, and `ast_edit` outside the project in every session:

```bash
mkdir -p ~/.omp/agent/hooks/pre
cp plugins/deep-mode/skills/deep-mode/assets/contain/omp-contain.ts ~/.omp/agent/hooks/pre/
```

For one run only, pass `--hook <path to omp-contain.ts>` instead. To let the agent write to a folder outside the project you named, list it in the project's `.deep-mode.json` as `{"extraWriteRoots": ["~/some/folder"]}`. The guards don't parse shell commands, so the skill's rule still binds `bash`.

## Use it

```text
/deep the coupon total is wrong. fix it
/deep add CSV export to the reports page
/deep grill me on this plan, then write the spec and cut tickets
/deep implement spec #12
/deep triage the open issues
/deep review PR 42
/deep start a new app: a CLI that converts Sigma rules for our SIEM
/deep check on PR 42, and ship it when it's green
```

- You never pick a skill or playbook. `/deep` routes, sizes, and runs it.
- Small jobs take the fast path. Big ones get the full playbook, subagents, and a decision log.
- It decides and acts without asking: commits, pushes, PRs, board cards, and merges after a panel pass. It asks once at the end only for hard stops (deploys, deletions, shared-history rewrites, outside messages, money, secrets), and lists every decision it made so you can reverse any.
- On a new repo, medium and large jobs first build a `verify-<app>` skill so the agent can prove changes. Later runs reuse it.
- The direct commands still work: `/deep-mode:review-pr`, `/deep-mode:land-pr`, `/deep-mode:pr-thread`, `/deep-mode:contribute`, `/deep-mode:project-brief`.

## GitHub App bots

A private GitHub App you create gives the bots their own name in threads (`<app>[bot]`). The bots are any ACP agent reached through [acpx](https://github.com/openclaw/acpx): omp by default, or Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode and others. Each harness uses its own subscription login. No API keys, no webhooks, no server; the bot polls.

Install in three commands:

```bash
git clone https://github.com/TimothyVang/deep-mode
cd deep-mode/plugins/deep-mode/skills/deep-mode
py -3 assets/github-app/install.py      # python3 on macOS and Linux
```

`install.py` checks git, `gh`, openssl and npm, installs acpx when it is missing, finds the ACP agents on your PATH (omp first, then Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode), registers omp with acpx, sends a test prompt over ACP to the agents the bots will use, creates your private app in the browser, waits while you install it on the repos you pick, writes `~/.config/deep-mode/bot.json`, and registers autostart (Task Scheduler, launchd, systemd or cron). It asks before each change. `--yes` accepts every default; `--check` changes nothing.

![A real run of install.py --check](docs/images/install.gif)

Installing the app on a repo is the opt-in. Then:

```bash
py -3 assets/github-app/bot.py status
py -3 assets/github-app/bot.py once --repo <owner/repo> --dry-run   # preview a cycle, post nothing
py -3 assets/github-app/bot.py watch                                # poll in the foreground instead
```

- **Your PRs:** the bots merge in the base when it conflicts, review, fix or dismiss each finding, run a 3-verifier panel, and merge once required checks are green.
- **Others' PRs:** review comments only. They never merge.
- **Issues:** the bots plan and critique in the thread. On an issue you opened, or after you comment `@deep-mode implement`, they build it and open a PR that closes it.
- **Agents and models:** each role in `bot.json` is `{"agent": "omp", "model": "<optional>"}`. Put the author on a Claude model and the reviewer on a GPT model in omp, and one harness gives you cross-family review.
- **Opt out:** a base-branch `.deep-mode.json` with `"bot": false` skips the repo, and `"autonomousMerge": false` stops it at merge-ready.

![The PR conversation: kickoff, conflict merge, review and answer rounds over ACP mirrored to the thread, a three-verifier panel, and the merge gate](docs/images/pr-conversation.svg)

![The issue conversation: plan, critique, answer, then build and land on the owner's issues](docs/images/issue-flow.svg)

Details: [the github-app technique](plugins/deep-mode/skills/deep-mode/references/techniques/github-app.md).

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

## FAQ

**What is deep-mode?** An open-source MIT plugin for coding agents. It ships PR and issue bots that run on your own GitHub App and subscription, and a skill set that takes work from idea to spec, tickets, code and a merged PR, with every result proven and checked by a 3-agent panel.

**How do the PR bots work?** A poller on your machine checks the repos where your app is installed. An author agent and a reviewer agent, each an ACP agent reached through acpx, keep a session per PR. A coordinator passes each turn between them and posts it to the thread as your app, until no P0 or P1 finding is open. Three verifiers then vote, and a gate in code merges your own PR at the voted head.

**Does it need an API key?** No. Each agent CLI uses its own subscription login, for example Claude Code with Claude.ai or Codex with ChatGPT. Every call counts against that subscription's usage.

**Which agents and harnesses does it work with?** The bots use any agent acpx reaches over ACP: omp by default, or Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode and others. Each role can pick its own model. The skill runs in omp, Claude Code, Codex, Cursor and other harnesses.

**Will it merge other people's PRs?** No. Only your own PRs merge: your account opened them from your repo, not a fork, and their commits pass the ownership checks in code. Everyone else's PRs get review comments only.

**Has it merged a real PR on its own?** Yes. [PR #19](https://github.com/TimothyVang/deep-mode/pull/19) went through 5 cycles: a conflict merge, review rounds, two failed panels that caught real bugs, then a 2/3 panel pass and a squash merge by the bot.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
