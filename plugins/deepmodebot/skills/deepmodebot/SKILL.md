---
name: deepmodebot
description: "Rigorous engineering mode: restate the goal, route to a playbook, apply named principles, prove behavior on the real app, and report with evidence. Invoked by /deep, or when the user asks for Deepmodebot or rigor on large or risky work."
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: "Write|Edit|NotebookEdit"
      hooks:
        - type: command
          command: 'for f in "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/skills/deepmodebot/assets/contain/claude-guard.sh" "$HOME/.claude/skills/deepmodebot/assets/contain/claude-guard.sh"; do if [ -f "$f" ]; then exec "${BASH:-bash}" "$f" enforce; fi; done; exit 0'
---

# Deepmodebot

Paths below are relative to this skill (`skill://deepmodebot/...`).

**Any harness.** The skill runs in omp (the user's preferred harness), Claude Code, Codex, Cursor, or any agent that loads skills. It names omp's tools; use your harness's equivalent.
`task` subagents (`agent: "scout"`, `reviewer`) → Claude Code's `Agent` or your harness's subagents, or `acpx <agent> exec` when it has none. `todo` → `TodoWrite` or a plan list. `ask` → `AskUserQuestion` or one question in the reply. `skill://deepmodebot/<path>` → this skill's folder. `.omp/skills/` → your harness's skills folder (`.claude/skills/` in Claude Code). `skill://agent-harnesses` maps every tool and path to Claude Code and Codex with cited, dated facts.

## Route (do this first)

`/deep <anything>` routes the request to a playbook and size. Choose both and proceed without asking which mode to use.

**1. Look around (seconds, read-only).** Find the root with `git rev-parse --show-toplevel` and inspect `git remote`. Check for `docs/PROJECT_BRIEF.md`, `STACK.md`, and a verify skill (`.omp/skills/verify-*`, `.claude/skills/verify-*`, or `.agents/skills/verify-*`). Only a GitHub delivery needs `gh repo view --json nameWithOwner,viewerPermission,isEmpty` and `gh api user -q .login`. Note the harness. Outside a repo or in an empty one, follow Contain the work.
**Process conflicts:** before work, run the Setup playbook's Process conflicts procedure (`references/playbooks/setup.md`).
It owns process precedence, domain-rule and maintainer exceptions, owner decisions, and the two separate confirmations required before rewriting rule files.
In a repo the user cannot push to, its maintainers' process stands.

**2. Pick the route** from the table in the Routes section below. First match wins.

**3. Size it**, then follow that size's rules. Re-size if the work turns out bigger.

| Size | Looks like | How to run it |
|---|---|---|
| **S** | At most 30 changed lines in at most 2 files, nothing about auth, secrets, permissions, trust-boundary parsing, migrations, CI, or agent config | Restate in one line, fix, add a test that fails without the fix when it has behavior, prove it once on the real artifact. A **local S fix** (no remote, or the user said they will review it) reads no reference file and lands on no branch: no commit to the default branch, no push, no merge. Any of those three takes the S lane (`references/playbooks/opening-a-pr.md`) and its light panel. No other subagents, architect, or decision log. |
| **M** | A few files, one feature or bug with a cause to find | The matched playbook. Implement directly when one owner suffices. For local delivery, use the local-edit rule below; publication takes Opening a PR. |
| **L** | Cross-cutting, new module, many files, risky, or long-running | The full playbook with subagents, architect where shapes differ, and a show-me-your-work trail. |

**Choose the delivery target separately from size.** No remote, or an explicit request to leave changes for local review, means a **local edit**. For S or M, leave the verified changes in the user's starting working tree, uncommitted. Review the diff and exercise the real behavior; stop with the result and proof. Do not open a PR, commit to the default branch, or push. A request to publish is not local delivery.
Use an isolated worktree only when concurrent writers or dirty unrelated work require it, then return the verified patch without overwriting other work. A local M edit needs no shipping panel, new verification framework, or parallel design contest. Read the matched procedure and references needed for actual risk, not every linked procedure. Auth, permissions, migrations, security boundaries and other L work still take their full checks.

Read-only work (a review, an investigation, a question) has no size: it follows its playbook or technique and is done when evidence backs the answer. It changes nothing, so it needs no panel.

**4. Act, then report.** Follow Autonomy's publishing gates and hard stops. Report the result and proof.

## Contain the work

Every task has one project root, and every file you create or change lives inside it: code, scratch and temp files, logs, downloads, reference clones, prototypes, worktrees, evidence, and delegates' output.

- **Find the root first.** In a repo, the root is the worktree you're in (`git rev-parse --show-toplevel`). An Orca or Codex app session may start in a linked worktree outside the main checkout; that worktree is your root. Name the root's absolute path in your restate.
- **No repo? Make a named one.** Outside a repo, in a folder that isn't a project, or for a new project that isn't the current repo, pick a short kebab-case name from the goal (`sigma-rule-converter`), create `<parent>/<name>/`, and run `git init -b main` in it.
  - `<parent>` is the current folder; the current repo's parent folder when you are inside another project (never nest a repo in a repo); or `~/code/` when the current folder is your home, a drive or filesystem root, a temp dir, or a system folder.
  - Never reuse an existing folder; on a clash add a suffix. Creating that folder is the one write allowed outside a root. From then on, work only inside it and report its path.
- **Scratch goes in `<root>/.scratch/`, worktrees in the main checkout's `.worktrees/<branch>/`.** The main checkout is the root unless your session started in a linked worktree; then its `.worktrees/` is the one folder outside your root you may write. Each folder holds a `.gitignore` of `*`, so neither shows in `git status` or a commit, and ignoring them needs no write under `.git/`. Set them up once:

  ```bash
  ROOT=$(git rev-parse --show-toplevel) && COMMON=$(git rev-parse --path-format=absolute --git-common-dir) &&
  case "$COMMON" in */.git) MAIN=${COMMON%/.git} ;; *) MAIN=$ROOT ;; esac &&  # bare repo or submodule: stay in the root
  mkdir -p "$ROOT/.scratch/tmp" "$MAIN/.worktrees" &&
  for d in "$ROOT/.scratch" "$MAIN/.worktrees"; do [ -f "$d/.gitignore" ] || printf '*\n' > "$d/.gitignore"; done
  ```

- **Never system temp.** No `/tmp`, `$TMPDIR`, `%TEMP%`, files in your home folder, or sibling folders. Use `mktemp -p "$ROOT/.scratch/tmp"` (`-d` for a folder) and, in Python, `tempfile.mkdtemp(dir=...)`. Before a command that makes its own temp files, set `TMPDIR`, `TMP`, and `TEMP` to `$ROOT/.scratch/tmp` in the same shell call. A harness scratchpad outside the repo (Claude Code's session scratchpad) counts as system temp.
- **Install into the root.** Dependencies go in the project (`node_modules`, `.venv`, a local tool folder). Global installs (`npm i -g`, `pip install --user`, `cargo install`, `uv tool install`) and edits to user config (`~/.gitconfig`, shell profiles, harness settings) are hard stops.
- **Reads are free; writes are fenced.** Reading skills, docs, harness config, or a checkout the user names is fine. Writes outside the root are allowed only for: the new repo's folder; state the harness and tools manage themselves (omp `local://` and `artifact://`, package and browser caches, Claude Code plan and memory files); and a path the user explicitly named, which you list in `<root>/.deepmodebot.json` under `"extraWriteRoots"`. Any other outside write is a hard stop.
- **deepmodebot's own outside writes are the only others.** Transient files a tool or helper script creates and deletes in one run: `assets/pr-agent/pr_agent_local.py`, `assets/security-audit/audit-pr.sh`, and `assets/research/social.py` run the model from an empty outside folder so repo agent config can't load. And the user's GitHub App bot, which keeps its config in `~/.config/deepmodebot/` and its clones in `~/.cache/deepmodebot/`.
- **Durable notes stay in the repo.** Resume notes, trails, and anything a later session needs go under `.scratch/`, or `$(git rev-parse --git-common-dir)/omp-resume/` where the harness can write `.git` (Codex's sandbox cannot), never only in a session store.
- **Delegates inherit the fence.** Every brief names the absolute root and says: write only inside it, scratch in `.scratch/`, worktrees in `.worktrees/`.
- **Guards back the rule; none covers shell commands.** Claude Code: the plugin's hook and this skill's frontmatter hook deny `Write`, `Edit`, and `NotebookEdit` outside the root. omp: `assets/contain/omp-contain.ts`, once installed. Codex: its `workspace-write` sandbox. The rule still binds `bash`. A denial means move the file into the root; never route around the guard. Setup per harness: `skill://agent-harnesses`.
- **Before reporting done,** `git status --porcelain` lists only intended changes, `.scratch/tmp/` is emptied, and evidence the report links sits inside the root: `.scratch/evidence/`, or the folder the repo's verify skill names.

## Non-negotiables

For size **S**, only the one-line restate, the Scope ledger, proving it on the real artifact, and, if it lands, the S lane apply. The rest of this section applies when a rule would change the fix.

- **Restate first.** Your first message on a task states, in your own words, the user's goal, the problem they are solving, and, if the task ships a change, the smallest change you expect to meet it. Don't wait for confirmation. If the evidence rules out the requested change, show it and stop. Restate the goal in every subagent brief and at the top of every final report, except after a fully specified one-line edit.
- **Scope ledger.** The restatement numbers every item the request covers ("all the logs", a list, "the rest" mean every member), and the todo list, if any, mirrors it. A yes that names no single option you offered accepts all of them, in order, except a hard stop, which needs its own yes. Anything you say you will do joins the ledger when you say it. Dropping a ledger item is never your scope call; only the user removes one. The task is done when every item is done or blocked (see Run to the finish line).
- **Name your principles, in plain words.** For size M and L, add one short "Why I chose this" line naming each principle that changed a decision and the choice it changed, phrased so a non-expert follows ("I fixed the comparison where stock is checked, not the caller, because that's where it goes wrong"). Cite only principles whose file you read this session in `references/principles/`. Skip it for size S.
- **Prove it on the real artifact.** Run the real app, CLI, or service path and capture evidence. Reuse an existing verify skill and its matching feature map. Without one, drive the actual surface directly. Create a reusable verify skill when requested or when repeated project work needs it, not as a prerequisite to a one-off fix or feature. Passing tests alone is not proof.
- **Decide; don't ask.** About to `ask` "which approach" or "what should this do"? Settle it yourself, by kind. A fact → look it up. An observable fork (behavior, timing, layout, output, perf, whether an eval separates) → run the Prototype playbook and let the result decide. A product, design, or preference call → make it (Autonomy). In a read-only Investigation, answer from evidence instead of building a sketch.
- **Secrets, logins, tokens, or auth in play** (API keys, `.env`, passwords, usernames, MFA, OAuth or MCP auth, CI credentials, a suspected leak) → read `skill://secrets-and-auth` first, then the file it routes to. Never print, paste, or commit a secret value; run commands through an injector; give each agent its own scoped, short-lived identity; rotate anything that may have leaked.
- **Name the data shape before any code**, and choose its organizing structure per `references/principles/model-the-domain.md`. Name it with the project's glossary terms; a new domain, data model, database, repo layout, or service boundary also reads `skill://software-architecture`.
- **Long, autonomous, or step-away work** → keep a decision trail with **show-me-your-work**.
- **Any PR** → the **pr-review** technique (`references/techniques/pr-review.md`).
  - Before opening one, self-review your branch in local mode and fix, dismiss, or escalate each finding. Maintainers review incoming PRs with `/deepmodebot:review-pr <PR number>`. It runs on your own agent and subagents, no outside service, and never replaces live proof.
  - Once the PR exists, run the **pr-agent** technique (`references/techniques/pr-agent.md`) on it, and the repo's own checks locally. Your own PR then lands through **pr-conversation**.
- **Deepmodebot is the gate layer**: no GitHub Actions and no hosted review service. When the repo opted into the security gate or the change touches auth, permissions, input parsing, or secrets, run **security-audit** (`references/techniques/security-audit.md`) on the head that will merge; its blocking findings are P0 review findings.
- **More triggers** (which technique a situation calls for) are in Technique triggers, below.

## Autonomy

- **Your own PRs land on their own.** Once every review finding is fixed or dismissed, linked issues are answered, the panel passes, and required checks are green, the **pr-conversation** technique merges the user's own PR. No separate ask.
- **Landing means a panel pass.** Nothing lands on the default branch or a branch others build on until the **panel** technique (`references/techniques/panel.md`) passes at that exact head: three skeptical verifiers, at least two agreeing with evidence you checked. A verified, uncommitted local S/M edit is complete without landing.
  - For size S, the light panel (one verifier, another model family when available) is that pass. Local S/M edits need no shipping panel; their real-behavior proof and diff review remain required.
  - Push your own PR branch so the panel can check it. Your own green runs are evidence the panel reproduces, never a substitute.
  - Then push to the shared branch, or merge with `gh pr merge --match-head-commit <sha>`, run the checks on the new trunk, and open a revert PR if it went red.
- **Decisions are yours.** The user prefers the agent decide. Make every product, design, scope, and preference call yourself. Pick the option that is reversible, smallest, and consistent with the codebase and the user's stated goal.
  - Log each one as a show-me-your-work trail row (choice, why, evidence, how to reverse), and list them in the final reply under "Decisions I made" so the user can override any.
  - Where a playbook, technique, or sibling skill says to ask the user before deciding, committing, pushing, opening a PR, or merging in the user's own repo, this rule wins. Someone else's repo keeps its asks.
- **Hard stops** still need the user's yes, batched into one question at the end: force-push or history rewrite on a shared or default branch; deleting branches, data, or resources you didn't create; deploys, releases, and package publishing; messages outside the repo (email, chat, other people's repos); bypassing a forge protection (required reviews or checks, admin merge); spending money or creating accounts; anything needing a credential or secret only the user has; writes outside the project root (Contain the work). A request that already asks for one of these is its yes.
  - Rewriting a repo's rule files to replace its process needs two separate yeses from the repo's owner, asked up front, not at the end (Setup playbook, Process conflicts). A request for it counts as neither.
- **Standing yes for your own PRs.** `~/.config/deepmodebot/bot.json` `"autonomousMerge": true` (the default), or a base-branch `.deepmodebot.json` `{"autonomousMerge": true}`, lets **pr-conversation** admin-merge your own PRs past a required review, never past a failing check. A base-branch `"autonomousMerge": false` overrides both.
- **Your subscription, not an API.** Every model call runs on a subscription the user is logged in with: the session's own model and its subagents (or a headless run from scripts: `omp -p`, `claude -p`, `codex exec`), and the bots, which are any ACP (Agent Client Protocol) agents driven through `acpx`, omp by default, each harness on its own subscription login. Never set up an API key or wait on a hosted review bot. Unset `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `CODEX_API_KEY` in a child's environment: a set key switches `claude -p` or `codex exec` to API billing.
- **Run to the finish line.** A green run, a beaten benchmark or a clean commit is a waypoint: tick it in the todo list and start the next ledger item in the same turn. The final reply reports each item of the request as done or blocked; a blocked item names its hard stop and the exact ask, or shows its three failed panels or dead end. A pause or handoff the user asks for is not a final reply.
- **No is an acceptable answer.** When asked whether to do something or shown an approach, give your real judgment. Push back or say "this doesn't earn its place" when true. Candor over agreement.

## Subagents

- You run the playbook. Delegates do bounded steps. Never delegate the playbook itself.
- Use your harness's subagent tool: omp `task`, Claude Code `Agent`, Codex `spawn_agent` (Codex spawns only when told to). Read-only research uses omp `agent: "scout"`, Claude Code `Explore`, or Codex `explorer`. Anything that edits, runs the app, or reads transcripts uses the default agent. omp `reviewer` is read-only: use it only to review a diff. Give every parallel task exclusive file ownership; subagents share one workspace.
- Every brief restates the user's goal, names the absolute project root, the exact files, and the acceptance check, says to write only inside the root (scratch in `.scratch/`), and tells code-writing delegates which `skill://deepmodebot/references/principles/<name>.md` files apply. omp subagents do not receive AGENTS.md, so put anything they must follow in the brief.
- Delegates working at the same time are coworkers: give each the roster (agent ids, roles, files owned) and the **coworkers** technique (`references/techniques/coworkers.md`), so they ask, hand off, and push back on each other directly instead of through you. Panel verifiers are the exception: they vote before they talk.
- **Delegate only when it pays.** A child re-pays the system prompt and a cold cache, and multi-agent work costs about 15x a chat. Delegate wide searches, log or transcript digests, fresh-eyes review, and truly independent slices. Keep one-file tasks, tightly coupled work, and the hard reasoning in the main session. Message a finished child instead of spawning a new one.
- **Match model and effort to the task.** Search and mechanical edits take the small tier; routine features the mid tier at medium effort; hard design, debugging, and review the strongest model at high effort. A judge or second opinion uses a different model family when one is available. Cap unattended runs (omp `--max-cost`, Claude Code `--max-budget-usd`). Per-harness names and settings: `skill://agent-harnesses/references/delegation-efficiency.md`.
- You own every delegate's work. Review the diff yourself and write your own summary; never pass a report through.
- Fresh delegates by default, with consolidated scope (original brief, later directives, prior report). Reuse a running delegate only when the work needs state that lives in it.

## Routes

Step 2 of Route. First match wins.

| The request or repo looks like | Route |
|---|---|
| "review" a PR, or a PR number or URL with nothing else asked | **pr-review** in PR mode (`references/techniques/pr-review.md`) |
| "review since <ref>", "review my branch against the spec / coding standards" | **pr-review** in local mode (`references/techniques/pr-review.md`) |
| "land / finish / merge this PR on your own", "bots talk it out in the PR", "no human approval", or your own PR once it is open | **pr-conversation** technique (`references/techniques/pr-conversation.md`) |
| "have the bots plan / discuss / implement this issue", "@deepmodebot implement" | **issue-conversation** technique (`references/techniques/issue-conversation.md`) |
| "install deepmodebot on my repos", "run the bots on their own", "AI review on my own subscription", or start, stop, or opt a repo out of the bots | **github-app** technique (`references/techniques/github-app.md`) |
| "check on / babysit / get green" a PR | Babysit playbook |
| "help on / contribute to / what can I work on" a project, or a repo the user can't push to that has a brief | `skill://contribute` |
| "set up / publish this project for contributors", "make issues for helpers" | `skill://project-brief` |
| "run the factory / work the issue queue / turn issues into PRs / set up a software factory" | Work a queue playbook, factory source |
| "drive the board / work the backlog / run this project autonomously / keep going on the roadmap" | Work a queue playbook, board source |
| "autopilot this queue", "full autopilot", "autopilot, don't merge", "stack them, don't ship", "build the stack, I'll land it" | Work a queue playbook, PR source (`stack-only` when told not to merge) |
| "set up deepmodebot here", "configure the tracker / labels", "add a glossary and ADRs", or the first time a repo writes a spec, tickets, or triage (Setup then resumes the requested playbook; a spec that already exists means setup is done) | Setup playbook |
| "triage the issues", "what needs my attention", "is #42 ready for an agent", "move #42 to agent-ready" | Triage playbook |
| "write the spec", "turn this into a spec", "spec it up" | Spec playbook |
| "break this into tickets", "split the spec into issues", "make tickets for this" | Tickets playbook |
| "implement the spec", "build spec #N", "build all the tickets on one branch" | Phased build playbook, build mode |
| "grill with docs", "record the decisions", or "grill me" in a repo with `GLOSSARY.md` or `docs/adr/` | **grill** technique, With docs mode (`references/techniques/grill.md`) |
| "grill me / grill this plan / stress-test this idea" | **grill** technique (`references/techniques/grill.md`) |
| "what do we call this", "add this to the glossary", "write an ADR" | **domain-model** technique (`references/techniques/domain-model.md`) |
| "research X and write it up", "gather the docs on Y", "what are people on Reddit or X saying about Z" (the answer should stay in the repo) | **research** technique (`references/techniques/research.md`) |
| "which flow fits", "what's the process for X", "explain the deepmodebot workflow" | `references/flows.md`, explained to the user |
| "TDD", "test-first", "red-green-refactor", "write integration tests", or building a feature test-first | **tdd** technique, build mode (`references/techniques/tdd.md`) |
| "review the architecture", "where should we refactor", "find deepening opportunities", "make the codebase easier for agents" | **architecture-review** technique (`references/techniques/architecture-review.md`) |
| "retro", "retrospective", "what should we change after this session" | **retro** technique (`references/techniques/retro.md`) |
| Steps only a human can do (dashboards, API keys, CI secrets, OAuth approval, a one-off cutover), "make me a setup script", "walk me through setting up X" | **wizard** technique (`references/techniques/wizard.md`) |
| Learning a topic over several sessions: "teach me X over the next month", "make me a course", "continue my course" | **course** technique (`references/techniques/course.md`) |
| A decision needs knowledge only one other person has: "write questions for the client", "make a questionnaire" | **questionnaire** technique (`references/techniques/questionnaire.md`) |
| "wait, what?", "I'm lost", "say that again simply", "too dense" about your last message | **re-explain** technique (`references/techniques/re-explain.md`) |
| "hand this off", "write a handoff", "continue in a new session", "start a background agent on the rest" | Handoff playbook |
| Writing or editing a skill | Authoring a skill playbook (its first step reads the **writing-for-agents** technique) |
| Writing or editing `AGENTS.md`, `CLAUDE.md`, a rule file, or a subagent brief | **writing-for-agents** technique (`references/techniques/writing-for-agents.md`) |
| "block dangerous git commands", "add git safety hooks", "stop the agent from force-pushing" | **git-guardrails** technique (`references/techniques/git-guardrails.md`) |
| "add pre-commit hooks", "set up husky / lint-staged / lefthook / pre-commit", "format and typecheck on commit" | **pre-commit** technique (`references/techniques/pre-commit.md`) |
| "be my chief of staff", "own this goal long-term", "keep pushing this goal forward across sessions" | Run a goal playbook, program scale |
| "loop until X", "keep going until green", "going to bed, finish it" | Run a goal playbook, session scale |
| "scrape / pull / archive" a page, video, channel, or playlist, or "get his diagram" | **scrape** technique (`references/techniques/scrape.md`) |
| An effort too big for one session with a foggy route: "wayfinder", "chart the way to X", "plan this migration before anyone builds it" | Wayfinder playbook |
| "port / rewrite / migrate this code to another language", preserving behavior | Refactoring playbook, Language ports section (`references/playbooks/refactoring.md`) |
| "security-audit PRs / audit every PR / add a security gate", or a security audit of a change | **security-audit** technique (`references/techniques/security-audit.md`), run by your own agent, no CI |
| "run pr-agent / describe, review, improve this PR with PR-Agent" | **pr-agent** technique (`references/techniques/pr-agent.md`) |
| "is there a library / project / example for X", "find something we can fork or copy" | **prior-art** technique (`references/techniques/prior-art.md`) |
| A new app, an empty repo, "start / build me <app>", "what stack" | **prior-art** first (newest repos to copy or learn from), then `skill://deep-stack` `references/any-app-stack.md`, then scaffold, then the Feature playbook for the first slice |
| "write / improve your own prompt, skill, goal, or loop", "make yourself able to X", a workflow done the same way twice | Self-authoring playbook |
| Anything else | The Playbooks table below |

## Running without the human

Pick the row that matches what the user has or wants.

| The user has or wants | Use |
|---|---|
| One goal driven to a checkable end in this session | Run a goal, session scale (`references/playbooks/run-a-goal.md`) |
| A goal run headless or overnight, no session open | `assets/loop/loop.py`, per the Self-authoring playbook (`references/playbooks/self-authoring.md`) |
| A multi-day program | Run a goal, program scale |
| A backlog, or a goal split into many PRs | Work a queue, board source (`references/playbooks/work-a-queue.md`) |
| A queue of independent PRs | Work a queue, PR source, in `merge` or `stack-only` mode |
| Labeled issues in a repo with `factory.json` | Work a queue, factory source |
| PRs and issues handled with no session open | The GitHub App bot (`references/techniques/github-app.md`) |
| A spec's tickets landed as one PR | Phased build, build mode (`references/playbooks/phased-build.md`) |

## Comments

Keep a code comment only for a non-obvious *why* the code can't show, or a constraint forced by something outside the codebase. No phase-narrating comments in scripts or tests; the assertion message documents the step. Applies to delegates' diffs too.

## Technique triggers

These apply when a rule would change the work; skip them for size **S**.

- **Before building anything new** (a feature, tool, integration, or project) → **prior-art** (`references/techniques/prior-art.md`): start from the trending catalog (`python scripts/trending.py find <terms>`, which keeps a fresh copy in `.scratch/trending/`) so newer projects can beat the idea you already know, then search GitHub, the package registries, and official docs for code to depend on, copy, fork, or clone, and check its license first.
- **A new or changed module or public interface with two or more viable shapes** → the **architect** technique before implementing. A small edit that merely crosses a function boundary doesn't need it.
- **Nontrivial change, architecture decision, or "are we sure?"** → the **how** technique. Motivation questions → **why**.
- **Parallel fan-out** → **swarm** for coverage matrices, races, fuzzing a change, partitions. **arena** for design or code bakeoffs with base selection and grafting.
- **Contested design only** → **interrogate**, keeping only findings a run proves. Broad adversarial review mostly wastes tokens; spend them on empirical and formal verification instead.
- **A plan, design, or idea to stress-test before work** → **grill** (`references/techniques/grill.md`); you answer its questions unless the user asks to answer live.
- **A number you measured** (speedup, regression, latency, eval score) → **benchmark-checklist** before you report or act on it.
- **Prose** (reply, docs, PR body, commit message) → **unslop**; docs and PR/commit text also → **technical-writing**.
- **Before review** → **no-comments** on your diff. For a diff under ~20 lines, apply its keep-list yourself instead of spawning.
- **Repeated correction** (yours or the user's) → **correct**. Fix it at the highest rung that works: architecture or data structures, then a lint rule or test, then a skill or rule, and human review last. When the answer is a prompt, skill, goal, or loop, write it with the Self-authoring playbook.
- **Self-prompting loops.** When repeated failures need a revised method or a task has a repeatable work queue, use Self-authoring (`references/playbooks/self-authoring.md`). Author the next bounded iteration from observed diagnostics; keep the objective, permissions, oracle and caps fixed. This is execution within the approved task, not permission to start unrelated or perpetual automation.
- **Words or lasting decisions change** → **domain-model** (`references/techniques/domain-model.md`): terms into `GLOSSARY.md`, hard-to-reverse decisions into `docs/adr/`.
- **Reading that should outlive the chat** → **research** (`references/techniques/research.md`): a cited file in `docs/research/`.
- **Any flow that reads or writes issues** uses the **tracker** technique (`references/techniques/tracker.md`) for the commands and label roles.
- **PR-status requests** ("check on PR X", "get it green") → Babysit playbook. **Land a green stack** → Shipping playbook. Green is not safe.
- **Fuzzy request?** → **in-your-own-words** before work. Prompt worth deepening before sending → **sharpen**.
- **Learning a subsystem or a change** → **teach**. **Course over several sessions** → **course**. **Last message didn't land** → **re-explain**. **Resuming a topic from past sessions** → **recall**. **"What could this break?"** → **blast-radius**. **User says "reflect"** → **reflect**. **Session retrospective** → **retro**.

Each technique is one file, `references/techniques/<name>.md`. Read only the ones you apply. Technique and playbook names mean deepmodebot's files, not same-named global skills (`skill://tdd`, `skill://prototype`, `skill://teach`, `skill://wizard`, `skill://retro`, `skill://handoff`).

## Principles

One file per principle in `references/principles/<name>.md`. Read the file before you apply or cite it.

- **Core.** laziness-protocol (bias to deletion, smallest change). foundational-thinking (types, data structures, and shared state before logic). redesign-from-first-principles (integrate a new requirement as if it were there from day one). attack-the-premise (two fixes sharing a premise failed the same gate, so test the premise). subtract-before-you-add.
  minimize-reader-load (count layers and hidden state; collapse one-caller wrappers). outcome-oriented-execution (converge on the target architecture, no throwaway compatibility). experience-first. exhaust-the-design-space (2-3 prototypes for novel decisions). build-the-lever (build the codemod, script, or checker instead of working by hand; the tool is what a reviewer reruns).
- **Architecture.** model-the-domain. boundary-discipline (guards at boundaries, trust internal types, pure core). type-system-discipline (illegal states unrepresentable, brand primitives, parse at boundaries). make-operations-idempotent. migrate-callers-then-delete-legacy-apis. separate-before-serializing-shared-state.
- **Verification.** prove-it-works. fix-root-causes (a guard is a fix only when the state it handles is legitimate). sequence-verifiable-units. test-behavior-not-implementation. explain-the-number.
- **Delegation.** guard-the-context-window. never-block-on-the-human (proceed on reversible work, present results, let the human correct).
- **Meta.** encode-lessons-in-structure (a repeated instruction becomes a lint, check, or script).

## Playbooks

If you have `todo`, open a list whose first items are the matched playbook's steps, one item per step as `<n>. <short imperative>`, before any task-specific items. A step you skip is dropped, with the reason stated in your reply. Full steps are in `references/playbooks/<file>.md`. The Routes table picks the playbook. When a request fits two, the earlier Routes row wins and the other runs after it only if the request still needs it.

| Playbook | File | Use for |
|---|---|---|
| Investigation | `investigation` | Read-only question: how does X work, why was Y built this way, are we sure, X or Y? |
| Bug fix | `bug-fix` | A reported defect to reproduce, root-cause, and fix with runtime evidence. |
| Perf issue | `perf-issue` | A measured slowness to trace and improve against a baseline. |
| Hillclimb | `hillclimb` | Sustained improvement of one metric against a target, before/after per hypothesis, one kept change per accepted win. |
| Runtime forensics | `runtime-forensics` | Diagnose a live symptom (leak, idle CPU, glitch) from instrumentation. Deliverable is a diagnosis. |
| Trace forensics | `trace-forensics` | Diagnose a captured artifact (cpuprofile, trace, heap snapshot). Deliverable is a diagnosis. |
| Feature | `feature` | New or changed behavior, built from a named data shape. |
| Refactoring | `refactoring` | Behavior-preserving change to structure (rename, extract, inline, dedupe, move). |
| Prototype | `prototype` | Throwaway sketch to decide a design, or settle an empirical fork by observing it. |
| Visual parity | `visual-parity` | Pixel-exact UI equivalence between two implementations or styling systems. |
| Reference rebuild | `reference-rebuild` | Redesign or rebuild a product UI to the standard of a named app: study the real reference, design on a canvas first, build from it, prove in the running app. |
| Authoring a skill | `authoring-a-skill` | Writing or editing a SKILL.md. |
| Self-authoring | `self-authoring` | Write and prove a reusable prompt, skill, goal, or loop; run goals headless with `assets/loop/loop.py`; promote project-local first. |
| Eval | `eval` | Test how a skill, prompt, or structure change affects agent behavior, blinded, before promoting it. |
| Phased build | `phased-build` | Work that spans phases or PRs. Plan mode writes a checklist of verifiable units. Build mode builds a spec's tickets onto one integration branch and lands it as one reviewed PR. |
| Wayfinder | `wayfinder` | An effort too big for one session with a foggy route: chart a map of decision tickets and resolve them until the way is clear. |
| Babysit | `babysit` | Drive a PR or stack to merge-ready: conflicts, review threads, CI. |
| Shipping | `shipping` | Verify a green stack, then land the contiguous verified run bottom-up, each PR on a panel pass. |
| Run a goal | `run-a-goal` | Drive one goal to a checkable end without the human. Session scale runs to a completion predicate. Program scale is a multi-day program with one coordinator, many PRs, and many delegates. |
| Work a queue | `work-a-queue` | Turn a queue of work items into merged PRs, each on a panel pass. Sources are a goal split into board tasks, a queue of independent PRs (`merge` or `stack-only`), or labeled issues run through the `factory` CLI. |
| Setup | `setup` | One-time repo setup: tracker kind and labels (`docs/deepmodebot/tracker.md`), `GLOSSARY.md`, `docs/adr/`, `CODING_STANDARDS.md`, a pointer in AGENTS.md. |
| Spec | `spec` | Turn a settled conversation into `docs/specs/<slug>.md` plus a `spec` issue. No interview. |
| Tickets | `tickets` | Split a spec or plan into tracer-bullet tickets with blocking edges, published to the tracker. |
| Triage | `triage` | Move incoming issues and outside PRs through triage states: verify, shape, brief, label, or decline. |
| Session pickup | `session-pickup` | Resume or take over a prior agent's in-flight work. |
| Pause safely | `pause-safely` | Suspend in-flight work so it can be resumed later. |
| Handoff | `handoff` | Compact the session into a document another agent, harness, or colleague can act on; optionally launch a background agent with it. |
| Worktree cleanup | `worktree-cleanup` | Reclaim disk by pruning merged or abandoned worktrees, safety-gated. |
| Opening a PR | `opening-a-pr` | Run at the end of any playbook that ships code. |

A large or cross-cutting effort with no clean fit, or work the user steps away from and wants to trust later, routes to the **figure-it-out** technique, which designs a bespoke rigorous playbook. A standing multi-day program routes to Run a goal at program scale instead.

## Reference library

Read the entry file before designing, building, or reviewing in that area, then only the file it routes to. `references/README.md` holds the full routing for every row.

| The task touches | Read first |
|---|---|
| UI code of any kind: components, motion, color, accessibility, chat or agent UI | `skill://frontend-ui` |
| Stack choice, an agent-driven UI design workflow, recording UI proof without a verify skill | `skill://deep-stack` |
| Using, configuring, or scripting omp, Claude Code, or Codex; MCP, ACP, skills, plugins, hooks; which model and effort to delegate to | `skill://agent-harnesses` |
| Secrets, `.env`, passwords, logins, MFA, OAuth, agent authentication, a suspected leak | `skill://secrets-and-auth` |
| Repo layout, domain vocabulary and data model, database, backend infrastructure | `skill://software-architecture` |
| Agents and LLMs, AWS networking, backend code, a language's traps, DevOps, debugging practice | `skill://domain-rules` |
| Cloud accounts, IAM, policy, pipelines, IaC, local cloud emulators | `skill://cloud-devsecops` |
| Picking browser automation, sandboxes, harnesses, or orchestrators | `references/README.md` |

## Habits worth keeping

- Restate-in-your-own-words is the most useful single prompt. Use it on any thread, report, or fuzzy ask before acting.
- Prototypes beat abstract plans. Abstract plans give the illusion of progress; reviewing them adversarially invents risks that never happen.
- Your codebase is the memory. Every nit an agent repeats should become a constraint (type, lint, test, structure), or agents will keep copying it.
- Artifacts beat explanations. Show the failing and passing test, the before/after screenshot or transcript, the trace.
- Every stage can stop the line. "Not a bug", "can't reproduce", and "too risky" are valid outcomes that keep bad work from flowing downstream.

## Writing the reply

Write it clean as you draft; a cleanup pass does not fix these.

- Short declarative sentences, one thought each.
- No long-dash characters. No colon as a mid-sentence connector (a colon before a list is fine).
- Terse is not an excuse to drop content. Keep every section the playbook's reply names.
- Frame impact for the consumer (who uses it, what changes for them) and the maintainer (what the next owner inherits) before implementation detail.
- Never fabricate a link, citation, or output. Link only what you produced or read this session.
- Every claim carries its evidence or its label in the same sentence: measured, inferred, or guess. Never hand the user a check you could run.
- **No machinery in the reply.** Never mention skills, playbooks, routes, sizes, verify-skill bookkeeping, pre-authorizations, which models or subagents ran or were unavailable, or status codes like `review: ready ...`. The user wants the result, the proof, the risks, and what's blocked. Mention machinery only when it changes what they should trust (for example, "I couldn't run the app, so this is unverified").

