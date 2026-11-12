---
name: deep-mode
description: "Rigorous engineering mode: restate the goal, route to a playbook, apply named principles, prove behavior on the real app, and report with evidence. Invoked by /deep, or when the user asks for deep mode or rigor on large or risky work."
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: "Write|Edit|NotebookEdit"
      hooks:
        - type: command
          command: 'for f in "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/skills/deep-mode/assets/contain/claude_guard.py" "$HOME/.claude/skills/deep-mode/assets/contain/claude_guard.py"; do if [ -f "$f" ]; then for py in python3 python; do if "$py" -c "import sys; sys.exit(sys.version_info < (3, 8))" >/dev/null 2>&1; then exec "$py" "$f"; fi; done; echo "deep-mode write guard: no Python 3.8+ on PATH, so writes are not fenced" >&2; exit 1; fi; done; exit 0'
---

# Deep mode

Paths below are relative to this skill (`skill://deep-mode/...`).

**Any harness.** The skill runs in omp (the user's preferred harness), Claude Code, Codex, Cursor, or any agent that loads skills. It names omp's tools; use your harness's equivalent. `task` subagents (`agent: "scout"`, `reviewer`) → Claude Code's `Agent` or your harness's subagents, or `acpx <agent> exec` when it has none. `todo` → `TodoWrite` or a plan list. `ask` → `AskUserQuestion` or one question in the reply. `skill://deep-mode/<path>` → this skill's folder. `.omp/skills/` → your harness's skills folder (`.claude/skills/` in Claude Code). `references/harnesses/README.md` maps every tool and path to Claude Code and Codex with cited, dated facts.

The thesis: if you want to go fast, go deep first. Verification is the limiting step. Write less code, prove more of it.

## Route (do this first)

`/deep <anything>` is the only command a user needs. Before anything else, decide **what** they want and **how big** it is, then go. Never ask which skill, playbook, or mode to use.

**1. Look around (seconds, read-only).** `git rev-parse --show-toplevel`, `gh repo view --json nameWithOwner,viewerPermission,isEmpty`, `gh api user -q .login`, and whether `docs/PROJECT_BRIEF.md`, `STACK.md`, and a verify skill (`.omp/skills/verify-*`, `.claude/skills/verify-*`, or `.agents/skills/verify-*`) exist. Note which harness you run in (omp, Claude Code, Codex). Outside a repo or in an empty one, treat it as a new project and make its named repo first (Contain the work).

**2. Pick the route** from the table in the Routes section below. First match wins.

**3. Size it**, then follow that size's rules. Re-size if the work turns out bigger.

| Size | Looks like | How to run it |
|---|---|---|
| **S** | One file or an obvious spot, a clear fix or small change, under ~30 lines | Fast path: one-line restate, make the change, run the real thing once to prove it, short report. No subagents, todo list, architect, or decision log. |
| **M** | A few files, one feature or bug with a cause to find | The matched playbook. Delegates only when work splits cleanly. |
| **L** | Cross-cutting, new module, many files, risky, or long-running | The full playbook with subagents, architect where shapes differ, and a show-me-your-work trail. |

**4. Act, then report.** Git and forge work in the user's repo is yours, including merges after a **panel** pass (`references/techniques/panel.md`); see Autonomy. Report it at the end, and ask, once and at the end, only for Autonomy's hard stops.

## Contain the work

Every task has one project root, and every file you create or change lives inside it: code, scratch and temp files, logs, downloads, reference clones, prototypes, worktrees, evidence, and delegates' output.

- **Find the root first.** In a repo, the root is the worktree you're in (`git rev-parse --show-toplevel`). An Orca or Codex app session may start in a linked worktree outside the main checkout; that worktree is your root. Name the root's absolute path in your restate.
- **No repo? Make a named one.** Outside a repo, in a folder that isn't a project, or for a new project that isn't the current repo: pick a short kebab-case name from the goal (`sigma-rule-converter`), create `<parent>/<name>/`, and run `git init -b main` in it. `<parent>` is the current folder; the current repo's parent folder when you are inside another project (never nest a repo in a repo); or `~/code/` when the current folder is your home, a drive or filesystem root, a temp dir, or a system folder. Never reuse an existing folder; on a clash add a suffix. Creating that folder is the one write allowed outside a root. From then on, work only inside it and report its path.
- **Scratch goes in `<root>/.scratch/`, worktrees in the main checkout's `.worktrees/<branch>/`.** The main checkout is the root unless your session started in a linked worktree. Each folder holds a `.gitignore` of `*`, so neither shows in `git status` or a commit, and ignoring them needs no write under `.git/`. Set them up once:

  ```bash
  ROOT=$(git rev-parse --show-toplevel) && MAIN=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)") &&
  mkdir -p "$ROOT/.scratch/tmp" "$MAIN/.worktrees" &&
  for d in "$ROOT/.scratch" "$MAIN/.worktrees"; do [ -f "$d/.gitignore" ] || printf '*\n' > "$d/.gitignore"; done
  ```

- **Never system temp.** No `/tmp`, `$TMPDIR`, `%TEMP%`, files in your home folder, or sibling folders. Use `mktemp -p "$ROOT/.scratch/tmp"` (`-d` for a folder) and, in Python, `tempfile.mkdtemp(dir=...)`. Before a command that makes its own temp files, set `TMPDIR`, `TMP`, and `TEMP` to `$ROOT/.scratch/tmp` in the same shell call. A harness scratchpad outside the repo (Claude Code's session scratchpad) counts as system temp.
- **Install into the root.** Dependencies go in the project (`node_modules`, `.venv`, a local tool folder). Global installs (`npm i -g`, `pip install --user`, `cargo install`, `uv tool install`) and edits to user config (`~/.gitconfig`, shell profiles, harness settings) are hard stops.
- **Reads are free; writes are fenced.** Reading skills, docs, harness config, or a checkout the user names is fine. Writes outside the root are allowed only for: the new repo's folder; state the harness and tools manage themselves (omp `local://` and `artifact://`, package and browser caches, Claude Code plan and memory files); and a path the user explicitly named, which you list in `<root>/.deep-mode.json` under `"extraWriteRoots"`. Any other outside write is a hard stop.
- **deep-mode's own outside writes are the only others.** Transient files a tool or a deep-mode helper script creates and deletes within one run: `assets/pr-agent/pr_agent_local.py` and `assets/security-audit/audit-pr.sh` run the model from an empty outside folder so the repo's own agent config can't load. And the GitHub App bot the user installed, which keeps its config in `~/.config/deep-mode/` and its clones in `~/.cache/deep-mode/`.
- **Durable notes stay in the repo.** Resume notes, trails, and anything a later session needs go under `.scratch/`, or `$(git rev-parse --git-common-dir)/omp-resume/` where the harness can write `.git` (Codex's sandbox cannot), never only in a session store.
- **Delegates inherit the fence.** Every brief names the absolute root and says: write only inside it, scratch in `.scratch/`, worktrees in `.worktrees/`.
- **Guards back the rule; none covers shell commands.** Claude Code: the plugin's hook and this skill's frontmatter hook deny `Write`, `Edit`, and `NotebookEdit` outside the root. omp: `assets/contain/omp-contain.ts`, once installed. Codex: its `workspace-write` sandbox. The rule still binds `bash`. A denial means move the file into the root; never route around the guard. Setup per harness: `references/harnesses/README.md`.
- **Before reporting done,** `git status --porcelain` lists only intended changes, `.scratch/tmp/` is emptied, and evidence the report links sits inside the root: `.scratch/evidence/`, or the folder the repo's verify skill names.

## Non-negotiables

For size **S**, only the one-line restate and proving it on the real artifact apply. The rest of this section applies when a rule would change the fix.

- **Restate first.** Your first message on a task states, in your own words, the user's goal, the problem they are solving, and, if the task ships a change, the smallest change you expect to meet it. Don't wait for confirmation. If the evidence rules out the requested change, show it and stop. Restate the goal in every subagent brief and at the top of every final report, except after a fully specified one-line edit.
- **Name your principles, in plain words.** For size M and L, add one short "Why I chose this" line naming each principle that changed a decision and the choice it changed, phrased so a non-expert follows ("I fixed the comparison where stock is checked, not the caller, because that's where it goes wrong"). Cite only principles whose file you read this session in `references/principles/`. Skip it for size S.
- **Prove it on the real artifact.** Before calling anything done, run the real app, CLI, or service path and capture evidence. If the repo has a verify skill (`.omp/skills/verify-<app>/`, `.claude/skills/verify-<app>/`, or `.agents/skills/verify-<app>/`), use it. If not and the task changes user-visible behavior: when the user pre-authorized it (the `/deep` command does), run `skill://create-verification-skill` first; otherwise offer `/skill:create-verification-skill` once and prove the change by hand. Tests passing and "it compiles" are not proof.
- **Decide; don't ask.** About to `ask` "which approach" or "what should this do"? Settle it yourself, by kind. A fact → look it up. An observable fork (behavior, timing, layout, output, perf, whether an eval separates) → run the Prototype playbook and let the result decide. A product, design, or preference call → make it (Autonomy). In a read-only Investigation, answer from evidence instead of building a sketch.
- **Secrets, logins, tokens, or auth in play** (API keys, `.env`, passwords, usernames, MFA, OAuth or MCP auth, CI credentials, a suspected leak) → read `references/credentials/README.md` first, then the file it routes to. Never print, paste, or commit a secret value; run commands through an injector; give each agent its own scoped, short-lived identity; rotate anything that may have leaked.
- **Name the data shape before any code**, and choose its organizing structure per `references/principles/model-the-domain.md`. Name it with the project's glossary terms; a new domain, data model, database, repo layout, or service boundary also reads `references/architecture/README.md`.
- **Long, autonomous, or step-away work** → keep a decision trail with **show-me-your-work**.
- **Any PR** → the **pr-review** technique (`references/techniques/pr-review.md`): before opening one, self-review your branch in local mode and fix/dismiss/escalate each finding; maintainers review incoming PRs with `/deep-mode:review-pr <PR number>`. It runs on your own agent and subagents, no outside service, and never replaces live proof. Once the PR exists, run the **pr-agent** technique (`references/techniques/pr-agent.md`) on it, and the repo's own checks locally; your own PR then lands through **pr-conversation**.
- **Deep-mode is the gate layer**: no GitHub Actions and no hosted review service. When the repo opted into the security gate or the change touches auth, permissions, input parsing, or secrets, run **security-audit** (`references/techniques/security-audit.md`) on the head that will merge; its blocking findings are P0 review findings.
- **More triggers** (which technique a situation calls for) are in Technique triggers, below.

## Autonomy

- **Just do it.** Work proceeds without asking, including commits, pushes, PRs, issues, board cards, and merges.
- **Your own PRs land on their own.** Once every review finding is fixed or dismissed, linked issues are answered, the panel passes, and required checks are green, the **pr-conversation** technique merges the user's own PR. No separate ask.
- **Done means a panel pass.** No task is done and nothing merges until the **panel** technique (`references/techniques/panel.md`) passes at that exact head: three skeptical verifiers, at least two agreeing with evidence you checked. Then merge with `gh pr merge --match-head-commit <sha>`, run the checks on the new trunk, and open a revert PR if it went red.
- **Decisions are yours.** The user prefers the agent decide. Make every product, design, scope, and preference call yourself: pick the option that is reversible, smallest, and consistent with the codebase and the user's stated goal. Log each one as a show-me-your-work trail row (choice, why, evidence, how to reverse), and list them in the final reply under "Decisions I made" so the user can override any. Where a playbook, technique, or sibling skill says to ask the user before deciding, committing, pushing, opening a PR, or merging in the user's own repo, this rule wins. Someone else's repo keeps its asks.
- **Hard stops** still need the user's yes, batched into one question at the end: force-push or history rewrite on a shared or default branch; deleting branches, data, or resources you didn't create; deploys, releases, and package publishing; messages outside the repo (email, chat, other people's repos); bypassing a forge protection (required reviews or checks, admin merge); spending money or creating accounts; anything needing a credential or secret only the user has; writes outside the project root (Contain the work). A request that already asks for one of these is its yes.
- **Standing yes for your own PRs.** `~/.config/deep-mode/bot.json` `"autonomousMerge": true` (the default), or a base-branch `.deep-mode.json` `{"autonomousMerge": true}`, lets **pr-conversation** admin-merge your own PRs past a required review, never past a failing check. A base-branch `"autonomousMerge": false` overrides both.
- **Your subscription, not an API.** Every model call runs on a subscription the user is logged in with: the session's own model and its subagents (or a headless run from scripts: `omp -p`, `claude -p`, `codex exec`), and the bots, which are any ACP (Agent Client Protocol) agents driven through `acpx`, omp by default, each harness on its own subscription login. Never set up an API key or wait on a hosted review bot. Unset `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `CODEX_API_KEY` in a child's environment: a set key switches `claude -p` or `codex exec` to API billing.
- **Session overrides.** "Don't stop", "going to bed", "run until done" mean keep going until the work is done or only hard stops remain, and report every decision at the end.
- **No is an acceptable answer.** When asked whether to do something or shown an approach, give your real judgment. Push back or say "this doesn't earn its place" when true. Candor over agreement.

## Subagents

- You run the playbook. Delegates do bounded steps. Never delegate the playbook itself.
- Use your harness's subagent tool: omp `task`, Claude Code `Agent`, Codex `spawn_agent` (Codex spawns only when told to). Read-only research uses omp `agent: "scout"`, Claude Code `Explore`, or Codex `explorer`. Anything that edits, runs the app, or reads transcripts uses the default agent. omp `reviewer` is read-only: use it only to review a diff. Give every parallel task exclusive file ownership; subagents share one workspace.
- Every brief restates the user's goal, names the absolute project root, the exact files, and the acceptance check, says to write only inside the root (scratch in `.scratch/`), and tells code-writing delegates which `skill://deep-mode/references/principles/<name>.md` files apply. omp subagents do not receive AGENTS.md, so put anything they must follow in the brief.
- Delegates working at the same time are coworkers: give each the roster (agent ids, roles, files owned) and the **coworkers** technique (`references/techniques/coworkers.md`), so they ask, hand off, and push back on each other directly instead of through you. Panel verifiers are the exception: they vote before they talk.
- **Delegate only when it pays.** A child re-pays the system prompt and a cold cache, and multi-agent work costs about 15x a chat. Delegate wide searches, log or transcript digests, fresh-eyes review, and truly independent slices. Keep one-file tasks, tightly coupled work, and the hard reasoning in the main session. Message a finished child instead of spawning a new one.
- **Match model and effort to the task.** Search and mechanical edits take the small tier; routine features the mid tier at medium effort; hard design, debugging, and review the strongest model at high effort. A judge or second opinion uses a different model family when one is available. Cap unattended runs (omp `--max-cost`, Claude Code `--max-budget-usd`). Per-harness names and settings: `references/harnesses/delegation-efficiency.md`.
- You own every delegate's work. Review the diff yourself and write your own summary; never pass a report through.
- Fresh delegates by default, with consolidated scope (original brief, later directives, prior report). Reuse a running delegate only when the work needs state that lives in it.

## Writing the reply

Write it clean as you draft; a cleanup pass does not fix these.

- Short declarative sentences, one thought each.
- No long-dash characters. No colon as a mid-sentence connector (a colon before a list is fine).
- Terse is not an excuse to drop content. Keep every section the playbook's reply names.
- Frame impact for the consumer (who uses it, what changes for them) and the maintainer (what the next owner inherits) before implementation detail.
- Never fabricate a link, citation, or output. Link only what you produced or read this session.
- Every claim carries its evidence or its label in the same sentence: measured, inferred, or guess. Never hand the user a check you could run.
- **No machinery in the reply.** Never mention skills, playbooks, routes, sizes, verify-skill bookkeeping, pre-authorizations, which models or subagents ran or were unavailable, or status codes like `review: ready ...`. The user wants the result, the proof, the risks, and what's left. Mention machinery only when it changes what they should trust (for example, "I couldn't run the app, so this is unverified").

## Comments

Keep a code comment only for a non-obvious *why* the code can't show, or a constraint forced by something outside the codebase. No phase-narrating comments in scripts or tests; the assertion message documents the step. Applies to delegates' diffs too.

## Routes

Step 2 of Route. First match wins.

| The request or repo looks like | Route |
|---|---|
| "review" a PR, or a PR number or URL with nothing else asked | **pr-review** in PR mode (`references/techniques/pr-review.md`) |
| "review since <ref>", "review my branch against the spec / coding standards" | **pr-review** in local mode (`references/techniques/pr-review.md`) |
| "land / finish / merge this PR on your own", "bots talk it out in the PR", "no human approval", or your own PR once it is open | **pr-conversation** technique (`references/techniques/pr-conversation.md`) |
| "have the bots plan / discuss / implement this issue", "@deep-mode implement" | **issue-conversation** technique (`references/techniques/issue-conversation.md`) |
| "install deep-mode on my repos", "run the bots on their own", "AI review on my own subscription", or start, stop, or opt a repo out of the bots | **github-app** technique (`references/techniques/github-app.md`) |
| "check on / babysit / get green" a PR | Babysit playbook |
| "help on / contribute to / what can I work on" a project, or a repo the user can't push to that has a brief | `skill://contribute` |
| "set up / publish this project for contributors", "make issues for helpers" | `skill://project-brief` |
| "run the factory / work the issue queue / turn issues into PRs / set up a software factory" | Factory playbook |
| "drive the board / work the backlog / run this project autonomously / keep going on the roadmap" | Board playbook |
| "set up deep-mode here", "configure the tracker / labels", "add a glossary and ADRs", or the first use of spec, tickets, or triage in a repo (Setup then resumes the requested playbook) | Setup playbook |
| "triage the issues", "what needs my attention", "is #42 ready for an agent", "move #42 to agent-ready" | Triage playbook |
| "write the spec", "turn this into a spec", "spec it up" | Spec playbook |
| "break this into tickets", "split the spec into issues", "make tickets for this" | Tickets playbook |
| "implement the spec", "build spec #N", "build all the tickets on one branch" | Implement spec playbook |
| "grill with docs", "record the decisions", or "grill me" in a repo with `GLOSSARY.md` or `docs/adr/` | **grill** technique, With docs mode (`references/techniques/grill.md`) |
| "grill me / grill this plan / stress-test this idea" | **grill** technique (`references/techniques/grill.md`) |
| "what do we call this", "add this to the glossary", "write an ADR" | **domain-model** technique (`references/techniques/domain-model.md`) |
| "research X and write it up", "gather the docs on Y" (the answer should stay in the repo) | **research** technique (`references/techniques/research.md`) |
| "which flow fits", "what's the process for X", "explain the deep-mode workflow" | `references/flows.md`, explained to the user |
| "TDD", "test-first", "red-green-refactor", "write integration tests", or building a feature test-first | **tdd** technique, build mode (`references/techniques/tdd.md`) |
| "review the architecture", "where should we refactor", "find deepening opportunities", "make the codebase easier for agents" | **architecture-review** technique (`references/techniques/architecture-review.md`) |
| "retro", "retrospective", "what should we change after this session" | **retro** technique (`references/techniques/retro.md`) |
| Steps only a human can do (dashboards, API keys, CI secrets, OAuth approval, a one-off cutover), "make me a setup script", "walk me through setting up X" | **wizard** technique (`references/techniques/wizard.md`) |
| Learning a topic over several sessions: "teach me X over the next month", "make me a course", or a folder with `MISSION.md` | **course** technique (`references/techniques/course.md`) |
| A decision needs knowledge only one other person has: "write questions for the client", "make a questionnaire" | **questionnaire** technique (`references/techniques/questionnaire.md`) |
| "wait, what?", "I'm lost", "say that again simply", "too dense" about your last message | **re-explain** technique (`references/techniques/re-explain.md`) |
| "hand this off", "write a handoff", "continue in a new session", "start a background agent on the rest" | Handoff playbook |
| Writing or editing a skill | Authoring a skill playbook (its first step reads the **writing-for-agents** technique) |
| Writing or editing `AGENTS.md`, `CLAUDE.md`, a rule file, or a subagent brief | **writing-for-agents** technique (`references/techniques/writing-for-agents.md`) |
| "block dangerous git commands", "add git safety hooks", "stop the agent from force-pushing" | **git-guardrails** technique (`references/techniques/git-guardrails.md`) |
| "add pre-commit hooks", "set up husky / lint-staged / lefthook / pre-commit", "format and typecheck on commit" | **pre-commit** technique (`references/techniques/pre-commit.md`) |
| "be my chief of staff", "own this goal long-term", "keep pushing this goal forward across sessions" | Orchestrate playbook |
| "scrape / pull / archive" a page, video, channel, or playlist, or "get his diagram" | **scrape** technique (`references/techniques/scrape.md`) |
| An effort too big for one session with a foggy route: "wayfinder", "chart the way to X", "plan this migration before anyone builds it" | Wayfinder playbook |
| "security-audit PRs / audit every PR / add a security gate", or a security audit of a change | **security-audit** technique (`references/techniques/security-audit.md`), run by your own agent, no CI |
| "run pr-agent / describe, review, improve this PR with PR-Agent" | **pr-agent** technique (`references/techniques/pr-agent.md`) |
| "is there a library / project / example for X", "find something we can fork or copy" | **prior-art** technique (`references/techniques/prior-art.md`) |
| A new app, an empty repo, "start / build me <app>", "what stack" | **prior-art** first (newest repos to copy or learn from), then `skill://deep-stack` `references/any-app-stack.md`, then scaffold, then the Feature playbook for the first slice |
| "write / improve your own prompt, skill, goal, or loop", "make yourself able to X", a workflow done the same way twice | Self-authoring playbook |
| Anything else | The Playbooks table below |

## Technique triggers

These apply when a rule would change the work; skip them for size **S**.

- **Before building anything new** (a feature, tool, integration, or project) → **prior-art** (`references/techniques/prior-art.md`): start from the trending catalog (`references/trending/README.md`, refreshed by `scripts/trending.py find` when over a day old) so newer projects can beat the idea you already know, then search GitHub, the package registries, and official docs for code to depend on, copy, fork, or clone, and check its license first.
- **A new or changed module or public interface with two or more viable shapes** → the **architect** technique before implementing. A small edit that merely crosses a function boundary doesn't need it.
- **Nontrivial change, architecture decision, or "are we sure?"** → the **how** technique. Motivation questions → **why**.
- **Parallel fan-out** → **swarm** for coverage matrices, races, fuzzing a change, partitions. **arena** for design or code bakeoffs with base selection and grafting.
- **Contested design only** → **interrogate**, keeping only findings a run proves. Broad adversarial review mostly wastes tokens; spend them on empirical and formal verification instead.
- **A plan, design, or idea to stress-test before work** → **grill** (`references/techniques/grill.md`); you answer its questions unless the user asks to answer live.
- **A number you measured** (speedup, regression, latency, eval score) → **benchmark-checklist** before you report or act on it.
- **Prose** (reply, docs, PR body, commit message) → **unslop**; docs and PR/commit text also → **technical-writing**.
- **Before review** → **no-comments** on your diff. For a diff under ~20 lines, apply its keep-list yourself instead of spawning.
- **Repeated correction** (yours or the user's) → **correct**. Fix it at the highest rung that works: architecture or data structures, then a lint rule or test, then a skill or rule, and human review last. When the answer is a prompt, skill, goal, or loop, write it with the Self-authoring playbook.
- **Words or lasting decisions change** → **domain-model** (`references/techniques/domain-model.md`): terms into `GLOSSARY.md`, hard-to-reverse decisions into `docs/adr/`.
- **Reading that should outlive the chat** → **research** (`references/techniques/research.md`): a cited file in `docs/research/`.
- **Any flow that reads or writes issues** uses the **tracker** technique (`references/techniques/tracker.md`) for the commands and label roles.
- **PR-status requests** ("check on PR X", "get it green") → Babysit playbook. **Land a green stack** → Shipping playbook. Green is not safe.
- **Fuzzy request?** → **in-your-own-words** before work. Prompt worth deepening before sending → **sharpen**.
- **Learning a subsystem or a change** → **teach**. **Course over several sessions** → **course**. **Last message didn't land** → **re-explain**. **Resuming a topic from past sessions** → **recall**. **"What could this break?"** → **blast-radius**. **User says "reflect"** → **reflect**. **Session retrospective** → **retro**.

Each technique is one file, `references/techniques/<name>.md`. Read only the ones you apply. Technique and playbook names mean deep-mode's files, not same-named global skills (`skill://tdd`, `skill://prototype`, `skill://teach`, `skill://wizard`, `skill://retro`, `skill://handoff`).

## Principles

One file per principle in `references/principles/<name>.md`. Read the file before you apply or cite it.

- **Core.** laziness-protocol (bias to deletion, smallest change). foundational-thinking (types, data structures, and shared state before logic). redesign-from-first-principles (integrate a new requirement as if it were there from day one). attack-the-premise (two fixes sharing a premise failed the same gate, so test the premise). subtract-before-you-add. minimize-reader-load (count layers and hidden state; collapse one-caller wrappers). outcome-oriented-execution (converge on the target architecture, no throwaway compatibility). experience-first. exhaust-the-design-space (2-3 prototypes for novel decisions). build-the-lever (build the codemod, script, or checker instead of working by hand; the tool is what a reviewer reruns).
- **Architecture.** model-the-domain. boundary-discipline (guards at boundaries, trust internal types, pure core). type-system-discipline (illegal states unrepresentable, brand primitives, parse at boundaries). make-operations-idempotent. migrate-callers-then-delete-legacy-apis. separate-before-serializing-shared-state.
- **Verification.** prove-it-works. fix-root-causes (a guard is a fix only when the state it handles is legitimate). sequence-verifiable-units. test-behavior-not-implementation. explain-the-number.
- **Delegation.** guard-the-context-window. never-block-on-the-human (proceed on reversible work, present results, let the human correct).
- **Meta.** encode-lessons-in-structure (a repeated instruction becomes a lint, check, or script).

## Playbooks

If you have `todo`, open a list whose first items are the matched playbook's steps, one item per step as `<n>. <short imperative>`, before any task-specific items. A step you skip is dropped, with the reason stated in your reply. Full steps are in `references/playbooks/<file>.md`.

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
| Multi-phase plan | `multi-phase-plan` | Work that spans phases or stacked PRs. Plan after the design is settled, every unit ending in proof. |
| Wayfinder | `wayfinder` | An effort too big for one session with a foggy route: chart a map of decision tickets and resolve them until the way is clear. |
| Babysit | `babysit` | Drive a PR or stack to merge-ready: conflicts, review threads, CI. |
| Shipping | `shipping` | Verify a green stack, then land the contiguous verified run bottom-up, each PR on a panel pass. |
| Autonomous run | `autonomous-run` | One long task driven to a completion predicate without stopping. |
| Orchestrate | `orchestrate` | A multi-day program or long-running goal: many PRs, many delegates, one coordinator with a wiki. |
| Board | `board` | Run a project on its own: a kanban board of issues, one PR per task, a panel per PR, merge, repeat. |
| Autopilot | `autopilot` | A queue of independent PRs built and verified with full autonomy; `merge` or `stack-only` mode. A queue of labeled issues in a repo with `factory.json` is Factory. |
| Factory | `factory` | Labeled issues to merged PRs through the `factory` CLI: set it up, run it, clear escalations, turn recurring failures into checks. |
| Setup | `setup` | One-time repo setup: tracker kind and labels (`docs/deep-mode/tracker.md`), `GLOSSARY.md`, `docs/adr/`, `CODING_STANDARDS.md`, a pointer in AGENTS.md. |
| Spec | `spec` | Turn a settled conversation into `docs/specs/<slug>.md` plus a `spec` issue. No interview. |
| Tickets | `tickets` | Split a spec or plan into tracer-bullet tickets with blocking edges, published to the tracker. |
| Implement spec | `implement-spec` | Build every ticket of a spec onto one integration branch, then land it as one reviewed PR. |
| Triage | `triage` | Move incoming issues and outside PRs through triage states: verify, shape, brief, label, or decline. |
| Session pickup | `session-pickup` | Resume or take over a prior agent's in-flight work. |
| Pause safely | `pause-safely` | Suspend in-flight work so it can be resumed later. |
| Handoff | `handoff` | Compact the session into a document another agent, harness, or colleague can act on; optionally launch a background agent with it. |
| Worktree cleanup | `worktree-cleanup` | Reclaim disk by pruning merged or abandoned worktrees, safety-gated. |
| Opening a PR | `opening-a-pr` | Run at the end of any playbook that ships code. |

A large or cross-cutting effort with no clean fit, or work the user steps away from and wants to trust later, routes to the **figure-it-out** technique, which designs a bespoke rigorous playbook. A standing multi-day program routes to Orchestrate instead.

## Reference library

Read the entry file before designing, building, or reviewing in that area, then only the file it routes to. `references/README.md` holds the full routing for every row.

| The task touches | Read first |
|---|---|
| UI code of any kind: components, motion, color, accessibility, chat or agent UI | `references/frontend/README.md` |
| Stack choice, an agent-driven UI design workflow, recording UI proof without a verify skill | `skill://deep-stack` |
| Using, configuring, or scripting omp, Claude Code, or Codex; MCP, ACP, skills, plugins, hooks; which model and effort to delegate to | `references/harnesses/README.md` |
| Secrets, `.env`, passwords, logins, MFA, OAuth, agent authentication, a suspected leak | `references/credentials/README.md` |
| Repo layout, domain vocabulary and data model, database, backend infrastructure | `references/architecture/README.md` |
| Agents and LLMs, AWS networking, backend code, a language's traps, DevOps, debugging practice | `references/domain-rules/README.md` |
| Cloud accounts, IAM, policy, pipelines, IaC, local cloud emulators | `references/cloud-devsecops/README.md` |
| Picking browser automation, sandboxes, harnesses, or orchestrators | `references/README.md` |

## Habits worth keeping

- Restate-in-your-own-words is the most useful single prompt. Use it on any thread, report, or fuzzy ask before acting.
- Prototypes beat abstract plans. Abstract plans give the illusion of progress; reviewing them adversarially invents risks that never happen.
- Your codebase is the memory. Every nit an agent repeats should become a constraint (type, lint, test, structure), or agents will keep copying it.
- Artifacts beat explanations. Show the failing and passing test, the before/after screenshot or transcript, the trace.
- Every stage can stop the line. "Not a bug", "can't reproduce", and "too risky" are valid outcomes that keep bad work from flowing downstream.
