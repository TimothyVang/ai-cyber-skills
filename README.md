![The deepmodebot logo](brand/logo.svg)

# deepmodebot

**deepmodebot** is an open-source MIT plugin for coding agents. It has two halves:

- **PR and issue bots** on your own private GitHub App. Owner-controlled work uses ACP agents through acpx on your machine and subscription login. The bots review your PRs in the thread, fix findings, run a verifier panel, and merge your own PRs behind a gate enforced in code. They also plan and build your issues. Outside-contributor reviews use a separate, tool-free omp process.
- **A software-factory skill set**: one `/deep` command that routes any task to a playbook, plus the flow from idea to merged code (setup, grill, spec, tickets, implement, review, land) and the techniques around it (TDD, triage, domain model, research, architecture review, prototype, board, factory, retro and more).

The skill runs in omp, Claude Code, Codex, Cursor and other harnesses that load `SKILL.md` skills. Built for the Ai Cyber community; anyone can use and improve it.

**Site:** [timothyvang.github.io/deepmodebot](https://timothyvang.github.io/deepmodebot/) · **Docs:** [how the bots work](plugins/deepmodebot/skills/deepmodebot/references/techniques/github-app.md) · [the flow map](plugins/deepmodebot/skills/deepmodebot/references/flows.md)

![The real thread of PR 19: the author bot merges main into the PR, the reviewer posts findings, the author fixes them, the coordinator blocks after three rounds, the owner says continue, two panels fail with evidence, the third passes 2/3, and the bot squash-merges](docs/images/pr-19-thread.gif)

A real run, not a mock-up: the bots took [PR #19](https://github.com/TimothyVang/deepmodebot/pull/19) through 5 cycles. Two failed panels caught real bugs; the third passed 2/3 and the bot merged it.

![How the bots work: a private GitHub App on GitHub, and on your machine a poller that runs ACP agents through acpx and posts each turn as the app](docs/images/how-it-works.svg)

## What you get

| Piece | What it does |
|---|---|
| `/deep <anything>` | One command routes and sizes the task, proves the result on the real app, and reports its decisions. Ordinary local work stays in your starting tree for review. Publishing follows the review and verifier-panel gates. |
| `deepmodebot` skill | 29 playbooks, 24 principles and 43 techniques, indexed in its `SKILL.md`. Every task is proven on the real artifact and merges only on a verifier panel pass. |
| PR and issue bots | Install your own private GitHub App on your repos and a poller on your machine runs the bots: it reviews and lands your own PRs, resolves their merge conflicts, and plans and builds the issues you open. See [GitHub App bots](#github-app-bots). |
| PR review | `/deepmodebot:review-pr <PR number>` reviews correctness, security, spec and standards, keeps findings backed by code or execution, and posts a comment-only review. No hosted review service is required. Prompts and source context still reach your configured model provider. |
| Land a PR | `/deepmodebot:land-pr <PR number>` finishes and merges your own PR with no human: a reviewer bot posts findings in the PR thread, the author bot answers each with a fix or a reason, three verifier bots vote on the final head, and on a pass it merges. It never merges over a failing check. You see each turn in the session as it lands, drawn as an 8-bit frame right in the chat (each bot a sprite, each turn a dialog box), or watch the whole conversation play live as an 8-bit battle screen in your terminal; `/deepmodebot:pr-thread <PR or issue URL>` shows any bot conversation later. |
| `deep-stack` skill | Stack picks and a ship loop: a default software stack and the decision rules behind it for any app (web, CLI, desktop, mobile, AI agent, data/ML, security tooling), an agent-driven UI design workflow, and a per-task loop of worktree, build, recorded evidence and reviewed PR. |
| Verification skills | `create-verification-skill` builds a per-repo `verify-<app>` skill (a control CLI plus a feature map) so agents can drive your app and capture proof. `maintain-verification-skill` keeps it accurate as the app changes. |
| `project-brief` and `contribute` | A maintainer publishes a newcomer brief, claimable tasks as issues, a roadmap and templates. A contributor's agent finds an unclaimed task that doesn't overlap open PRs, claims it, builds it through deepmodebot, and opens a PR. |
| Trending catalog | `plugins/deepmodebot/skills/deepmodebot/scripts/trending.py` keeps a digest of new and trending repos that deepmodebot searches before building anything. |
| Harness references | Cited, dated guides (checked 2026-11-11) for using omp, Claude Code, and Codex, the MCP, ACP, A2A, and WebMCP protocols, and portable AI-native conventions (`AGENTS.md`, Agent Skills, plugin marketplaces). A cross-harness map translates every omp tool and path deepmodebot names into Claude Code and Codex. In `plugins/deepmodebot/skills/agent-harnesses/`. |
| Agent SDK workspace | [Install and use Antigravity, Claude Agent, Codex, and omp SDKs](plugins/deepmodebot/skills/agent-harnesses/references/sdks.md), with pinned optional dependencies and no-model smoke commands. CLI subscription logins and SDK authentication are separate contracts. |
| Contained work | The agent works only inside the project's repo. Scratch and temp files go in `.scratch/`, worktrees in `.worktrees/` (both git-ignored), never system temp or folders outside the repo. With no repo it creates a named one first. A guard enforces this in Claude Code and omp; Codex's sandbox does it natively. |
| Credentials and auth | Cited, free-first guidance (checked 2026-11-11) for sharing API keys and `.env` safely, passwords and usernames, logins and MFA for agents, credential brokers, protecting MCP servers and agent APIs, CI OIDC, secret scanning, and leak response. In `plugins/deepmodebot/skills/secrets-and-auth/`. |
| Architecture | Cited, decision-ready guidance (checked 2026-11-11) for organizing monorepos, naming the domain (glossary, typed models, LinkML, RDF and SHACL, graph databases, Palantir-style ontology for agent actions), choosing and migrating databases with agents working safely against them, and backend infrastructure and system design (reliability, queues and durable workflows, APIs, OpenTelemetry, deployment, IaC). Each file ends with the default stack for a solo dev or small team. In `plugins/deepmodebot/skills/software-architecture/`. |
| Self-authoring | deepmodebot writes and revises its own bounded loop prompts from observed failures. `assets/loop/loop.py` supplies the mutable working plan and latest check diagnostics, with exact prompt snapshots and complete check logs; shortened diagnostics link to their full log. The objective, constraints, acceptance check, protected files and finite caps stay fixed; plan-only edits do not prevent a stall stop. Runs use omp, Claude Code or Codex. Interactive sessions can use native `/goal`. |
| Language ports | A behavior inventory, protected consumer tests and a representative pilot precede bulk translation. Preserve architecture unless the target runtime boundary requires a change; a port need not delete valid branches or reduce reader load. Parity and completeness are checked separately, including release builds, callbacks and lifecycle semantics. Copilot and Bun's Rust migration accounts inform the workflow without prescribing Rust or one cutover strategy. Parallel work has explicit integration and build owners. |
| Efficient delegation | When a subagent pays for itself, which model tier and reasoning effort fits each task (search, mechanical edits, features, hard design, review, long runs, summaries) in omp, Claude Code, and Codex, how subscription limits are metered, and how to cut token use. In `plugins/deepmodebot/skills/agent-harnesses/references/delegation-efficiency.md`, checked 2026-11-11. |

The agent makes reversible product and design decisions and handles commits, PRs and merges when publication is in scope. Ordinary small or medium local work stays uncommitted in the starting tree, with runtime proof and diff review. Publication requires three skeptical verifiers and at least two evidence-backed passes, or one passing verifier for an eligible small change.
It still asks before deploys, deleting things it did not create, rewriting shared history, outside messages, spending money, using secrets only you have, or writing outside the project.

## Measured behavior

[Local delivery experiments](evals/results/local-delivery-2026-11-12.md) exercised one feature fixture with five repetitions per arm.
In the second experiment, the revised command finished 5/5 runs and every artifact passed all 19 CLI checks.
Plain-agent runs also finished 5/5 and passed all 19 checks, with lower median reported usage ($0.9754 versus $1.6271).
Reported usage is a harness estimate, not a subscription invoice. The small, development-known fixture and same-provider judges do not establish general superiority.

[Review quality](evals/review/README.md) uses historical bugs, clean controls and explicit finding adjudication. [Workflow coverage](evals/workflows/README.md) separates mapped routes from executed journeys and unsupported capabilities. No matched hosted-review comparison or complete feature parity has been demonstrated.

Read the [paired review results and label corrections](evals/results/review-quality-2026-11-12.md)
and [captured workflow outcomes](evals/results/workflow-coverage-2026-11-12.md).
The review holdout contains one bug/control pair. The four exercised journeys do not prove the whole mapped inventory.

## The software factory

The main line takes an idea to merged code. Skip the phases a job doesn't need. [The flow map](plugins/deepmodebot/skills/deepmodebot/references/flows.md) has the full table.

Choosing or improving the machinery? The [software-factory GitHub landscape](plugins/deepmodebot/skills/deepmodebot/references/factory-landscape.md) maps 61 projects to dispatch, isolation, review, merge, and recovery patterns. It separates documented mechanisms from runtime proof and flags license and hosted-service limits.

| Phase | Flow | Leaves behind |
|---|---|---|
| 0. Set up the repo once | Setup playbook | A tracker (GitHub issues, local files, or another tracker), mapped labels, `GLOSSARY.md`, `docs/adr/`, `CODING_STANDARDS.md`, an `AGENTS.md` section |
| 1. Sharpen the idea | **grill**, with its With docs mode | A decision table, glossary terms, ADRs |
| 2. Settle a fork by running it | Prototype playbook | A decision backed by an observation |
| 3. Write it down | Spec playbook | `docs/specs/<slug>.md` and a spec issue |
| 4. Cut it up | Tickets playbook | Tickets with their blockers |
| 5. Build it | Phased build (one integration branch) or Work a queue (one PR per ticket), with **tdd** | Merged code |
| 6. Review and land | **pr-review** (spec and standards lenses), **panel**, **pr-conversation** | A merged PR with evidence |

Around the main line:

- **Triage:** Sorts incoming issues and outside PRs into a category and a state, and posts a brief or the questions that block them.
- **Wayfinder:** Charts an effort too big for one session and hands its decisions to a spec.
- **Run a goal:** Drives one goal to a checkable end without you, in one session or as a multi-day program with many PRs and subagents.
- **Work a queue:** Turns a backlog, a queue of PRs, or labeled issues (through the `factory` CLI) into merged PRs, each after a panel pass.
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
- **Self-authoring:** Writes, validates and proves a reusable prompt, skill, goal or loop, and runs a goal unattended until its check passes.

## Install

### omp

```bash
omp plugin marketplace add TimothyVang/deepmodebot
omp plugin install deepmodebot@deepmodebot
```

Then, in any repo:

```text
/deepmodebot:deep <your task>
```

Plugin commands are prefixed with the plugin name. For a bare `/deep`, copy `plugins/deepmodebot/commands/deep.md` to `~/.omp/agent/commands/`.

Optional: append `agents-snippet.md` to `~/.omp/agent/AGENTS.md`. It routes large or risky work to deepmodebot and sets the verification rule for every session.

Updates are automatic while the GitHub App bot runs from the plugin (below). To update by hand, run both commands. `omp plugin upgrade` alone reinstalls omp's local copy of the repo and fetches nothing:

```bash
omp plugin marketplace update deepmodebot
omp plugin upgrade deepmodebot
```

### Claude Code

```text
/plugin marketplace add TimothyVang/deepmodebot
/plugin install deepmodebot@deepmodebot
```

Once any `/deepmodebot:` command runs in a session, the plugin's hook denies `Write`, `Edit`, and `NotebookEdit` outside the project for the rest of that session. Your other sessions are untouched. It needs Python 3.8 or newer (`python3` or `python`) on `PATH`: without it the guard cannot check paths, so it denies those three tools in a deepmodebot session until Python is installed.

The skills name omp tools (`task`, `todo`, `ask`). `plugins/deepmodebot/skills/agent-harnesses/SKILL.md` maps them: `Agent`, `TaskCreate` or `TodoWrite`, and `AskUserQuestion`.

To update, run `claude plugin marketplace update deepmodebot` and `claude plugin update deepmodebot@deepmodebot`, then restart Claude Code.

### Codex

```bash
codex plugin marketplace add TimothyVang/deepmodebot
codex plugin add deepmodebot@deepmodebot
```

Codex loads the skills but not the commands. Start with `$deepmodebot:deepmodebot <your task>`. To keep writes in the project, run with `--sandbox workspace-write` and add this to `~/.codex/config.toml` so temp dirs are fenced too:

```toml
[sandbox_workspace_write]
exclude_tmpdir_env_var = true
exclude_slash_tmp = true
```

### Manual

Copy every folder in `plugins/deepmodebot/skills/` to `~/.omp/agent/skills/` (or `~/.claude/skills/`, or `~/.agents/skills/` for Codex), and the files in `plugins/deepmodebot/commands/` to your commands folder. Cursor and other harnesses that load `SKILL.md` skills take the same folders in their own skills folder. In Claude Code a manual install arms the guard only when you invoke the `deepmodebot` skill itself.

### Turn on the guard in omp

omp has no sandbox, so add deepmodebot's hook. It blocks `write`, `edit`, and `ast_edit` outside the project in every session. With the plugin installed, copy the link file once; it loads the guard from the installed plugin, so upgrades never leave a stale copy:

```bash
mkdir -p ~/.omp/agent/hooks/pre
cp plugins/deepmodebot/skills/deepmodebot/assets/contain/omp-contain-link.ts ~/.omp/agent/hooks/pre/
```

With a manual install, copy `omp-contain.ts` itself to the same folder instead.

For one run only, pass `--hook <path to omp-contain.ts>` instead. To let the agent write to a folder outside the project you named, list it in the project's `.deepmodebot.json` as `{"extraWriteRoots": ["~/some/folder"]}`. The guards don't parse shell commands, so the skill's rule still binds `bash`.

## Use it

The examples use the bare `/deep`. With a plugin install, type `/deepmodebot:deep` in omp and Claude Code, or `$deepmodebot:deepmodebot` in Codex.

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
- It reuses the repo's verification tools or runs the real user path directly. A reusable `verify-<app>` skill is useful for repeated work, not a prerequisite for every local change.
- The direct commands still work: `/deepmodebot:review-pr`, `/deepmodebot:land-pr`, `/deepmodebot:pr-thread`, `/deepmodebot:contribute`, `/deepmodebot:project-brief`.

## GitHub App bots

A private GitHub App gives the bots their own name in threads (`<app>[bot]`). Owner-controlled work uses ACP agents through [acpx](https://github.com/openclaw/acpx), with omp as the default. Each harness needs its own subscription login. Outside-contributor reviews currently require omp's sealed, tool-free path. The poller runs on your machine; no public webhook server is required.

Install in three commands:

```bash
git clone https://github.com/TimothyVang/deepmodebot
cd deepmodebot/plugins/deepmodebot/skills/deepmodebot
py -3 assets/github-app/install.py      # python3 on macOS and Linux
```

With the omp plugin installed, run `install.py` from the plugin instead, so the bot keeps itself up to date: `py -3 ~/.omp/plugins/node_modules/deepmodebot/skills/deepmodebot/assets/github-app/install.py`.

`install.py` checks git, `gh`, openssl and npm, installs acpx when it is missing, finds the ACP agents on your PATH (omp first, then Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode), registers omp with acpx, sends a test prompt over ACP to the agents the bots will use, creates your private app in the browser, waits while you install it on the repos you pick, and writes `~/.config/deepmodebot/bot.json`. Autostart at logon (Task Scheduler or the Startup folder, launchd, systemd or cron) is optional; it registers one on a yes. It asks before each change. `--yes` accepts every default; `--check` changes nothing.

![A real run of install.py --check](docs/images/install.gif)

Installing the app on a repo is the opt-in. Then:

```bash
py -3 assets/github-app/bot.py status
py -3 assets/github-app/bot.py once --repo <owner/repo> --dry-run   # preview a cycle, post nothing
py -3 assets/github-app/bot.py watch                                # poll in the foreground instead
```

- **Your PRs:** the bots merge in the base when it conflicts, review, fix or dismiss each finding, run a 3-verifier panel, and merge once required checks are green.
- **Others' PRs:** review comments only, never merges or code execution. The reviewer receives the diff and a bounded packet of changed source files and direct local imports from Git objects. The packet names omissions; it is not whole-repository analysis.
- **Issues:** the bots plan and critique in the thread. On an issue you opened, or after you comment `@deepmodebot implement`, they build it and open a PR that closes it.
- **Agents and models:** each role in `bot.json` is `{"agent": "omp", "model": "<optional>"}`. Put the author on a Claude model and the reviewer on a GPT model in omp, and one harness gives you cross-family review.
- **Updates:** a bot run from the omp plugin checks between cycles, at most hourly and right after it merges into this repo. When `main` moved it upgrades the plugin, and it restarts itself when its own code changed. `bot.py update` checks now. `"autoUpdate": false` in `bot.json` turns it off. A bot run from a git clone never updates; pull it yourself.
- **Opt out:** a base-branch `.deepmodebot.json` with `"bot": false` skips the repo, and `"autonomousMerge": false` stops it at merge-ready.

![The PR conversation: kickoff, conflict merge, review and answer rounds over ACP mirrored to the thread, a three-verifier panel, and the merge gate](docs/images/pr-conversation.svg)

![The issue conversation: plan, critique, answer, then build and land on the owner's issues](docs/images/issue-flow.svg)

Details: [the github-app technique](plugins/deepmodebot/skills/deepmodebot/references/techniques/github-app.md).

## Collaborate on a project

Maintainer, once per project (and again when it changes):

```text
/deepmodebot:project-brief
```

Contributor, after installing the plugin:

```text
/deepmodebot:contribute I know Python and want to help with detections
```

- **Claims:** a contributor's agent posts a claim comment on the issue (who, plan, files, expiry in 7 days). Other agents read claims and skip claimed work.
- **Overlap check:** before starting and before opening a PR, the agent compares its files with every open PR and active claim. On overlap it picks other work, coordinates on the issue, or builds on top. After opening the PR it runs `scripts/pr-overlap.py comment` so the PR carries an overlap comment; the maintainer's agent re-runs it on open PRs.
- **Limits:** claims are a convention, not a lock. The overlap check catches shared files, not logic conflicts in different files; local checks, review, and the panel catch those.
- **Review:** the maintainer reviews each PR with `/deepmodebot:review-pr <PR number>`; contributors' agents self-review before opening one.

## Trending catalog

`plugins/deepmodebot/skills/deepmodebot/scripts/trending.py` keeps the catalog current with no scheduler. The published copy lives in this repo's `trending/`, outside the plugin, so a daily refresh never changes what installs ship.

`find <terms>` keeps a copy in the user's project at `.scratch/trending/`: a missing or day-old copy is replaced by the published one, or rebuilt with `update` when that is old too (about a minute; uses `GITHUB_TOKEN`, `GH_TOKEN`, or `gh auth token`). `find --no-refresh` skips that.

`catalog.json` keeps every repo seen in the last 120 days with first-seen date and star growth; `README.md` is the digest agents read. Refresh the published copy with `python plugins/deepmodebot/skills/deepmodebot/scripts/trending.py update --out trending` and commit it.

To add a source, write a `source_*` function in `trending.py` and list it in `SOURCES`; to watch another GitHub topic, add it to `WATCH_TOPICS`.

## Make it your own

deepmodebot is MIT licensed, and its brand kit lets you ship it as your own product. One brand file sets the name, logo, colors, command and skill names, bot trigger and URLs. One command builds a complete copy under that brand:

```bash
py -3 scripts/whitelabel.py --brand brand/examples/acme.json --out ../acme-review
```

The build renames the plugin, commands, skills, the bot and its GitHub App, rethemes the site, re-renders the images, and updates the SEO and llms files. It fails if any old name is left. LICENSE and NOTICE stay, with your copyright line added. See [the rebrand guide](docs/rebrand.md).

## Contribute

Want to help build deepmodebot itself? Install the plugin, clone this repo, and run:

```text
/deepmodebot:contribute
```

Your agent reads the [project brief](docs/PROJECT_BRIEF.md), picks an unclaimed task from the [roadmap](ROADMAP.md) (issues labeled [`help wanted`](https://github.com/TimothyVang/deepmodebot/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)) that doesn't overlap open PRs or other claims, claims it after you say yes, and opens a PR with proof.

Full rules, including how to do it by hand: [CONTRIBUTING.md](CONTRIBUTING.md). Short version: claim the issue, branch, edit, run `python scripts/check.py` (there is no CI, so this is the gate), open a PR.

## FAQ

**What is deepmodebot?** An open-source MIT plugin for coding agents. It combines a self-hosted PR and issue bot with workflows for planning, implementation, review and delivery. Local work requires runtime proof; published changes also pass the verifier gate.

**How do the PR bots work?** A poller on your machine checks the repos where your app is installed. An author agent and a reviewer agent, each an ACP agent reached through acpx, keep a session per PR. A coordinator passes each turn between them and posts it to the thread as your app, until no P0 or P1 finding is open. Three verifiers then vote (one, who must pass it, for a small change), and a gate in code merges your own PR at the voted head.

**Does it need an API key?** No. Supported agent CLIs use existing subscription logins, and calls count against their usage. This is not offline inference: prompts and source context can reach the configured model provider.

**Which agents and harnesses does it work with?** Owner-controlled bot roles use ACP agents supported by acpx. Outside-contributor reviews currently require omp. The portable skill instructions target omp, Claude Code, Codex, Cursor and other skill-loading harnesses; that is not a claim that every combination has been tested.

**Will it merge other people's PRs?** No. Only your own PRs merge: your account opened them from your repo, not a fork, and their commits pass the ownership checks in code. Everyone else's PRs get review comments only.

**Has it merged a real PR on its own?** Yes. [PR #19](https://github.com/TimothyVang/deepmodebot/pull/19) went through 5 cycles: a conflict merge, review rounds, two failed panels that caught real bugs, then a 2/3 panel pass and a squash merge by the bot.

**Can I white-label an AI code review GitHub App?** Yes. deepmodebot is MIT licensed and ships a brand kit, so you can sell it as your own product. Write one `brand.json` with your name, slug, command and skill names, bot trigger, colors, logo and URLs, then run `py -3 scripts/whitelabel.py --brand <file> --out <dir>`. It builds a full copy under your brand: the product name and logo, the site colors, the commands and skills, the bot and its GitHub App, the docs site, the README, the images, and the SEO and llms files.
A last check fails the build if any old name is left. LICENSE and NOTICE stay as they are, with your copyright line added. `install.py --brand <name>` is a shortcut that renames only the bots. See [the rebrand guide](docs/rebrand.md).

## License

MIT. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
