---
name: deep-mode
description: "Rigorous engineering mode: restate the goal, route to a playbook, apply named principles, prove behavior on the real app, and report with evidence. Invoked by /deep, or when the user asks for deep mode or rigor on large or risky work."
disable-model-invocation: true
---

# Deep mode

Paths below are relative to this skill (`skill://deep-mode/...`).

**Any harness.** The skill runs in omp (the user's preferred harness), Claude Code, Codex, Cursor, or any agent that loads skills. It names omp's tools; use your harness's equivalent. `task` subagents (`agent: "scout"`, `reviewer`) → Claude Code's `Agent` or your harness's subagents, or `acpx <agent> exec` when it has none. `todo` → `TodoWrite` or a plan list. `ask` → `AskUserQuestion` or one question in the reply. `skill://deep-mode/<path>` → this skill's folder. `.omp/skills/` → your harness's skills folder (`.claude/skills/` in Claude Code).

The thesis: if you want to go fast, go deep first. Verification is the limiting step. Write less code, prove more of it.

## Route (do this first)

`/deep <anything>` is the only command a user needs. Before anything else, decide **what** they want and **how big** it is, then go. Never ask which skill, playbook, or mode to use.

**1. Look around (seconds, read-only).** `git rev-parse --show-toplevel`, `gh repo view --json nameWithOwner,viewerPermission,isEmpty`, `gh api user -q .login`, and whether `docs/PROJECT_BRIEF.md`, `STACK.md`, and `.omp/skills/verify-*` exist. Outside a repo or in an empty one, treat it as a new project.

**2. Pick the route.** First match wins.

| The request or repo looks like | Route |
|---|---|
| A PR number, a PR URL, or "review" a PR | **pr-review** in PR mode (`references/techniques/pr-review.md`) |
| "review since <ref>", "review my branch against the spec / coding standards" | **pr-review** in local mode (`references/techniques/pr-review.md`) |
| "land / finish / merge this PR on your own", "bots talk it out in the PR", "no human approval", or your own PR once it is open | **pr-conversation** technique (`references/techniques/pr-conversation.md`) |
| "have the bots plan / discuss / implement this issue", "@deep-mode implement" | **issue-conversation** technique (`references/techniques/issue-conversation.md`) |
| "install deep-mode on my repos", "run the bots on their own", "AI review on my own subscription", or start, stop, or opt a repo out of the bots | **github-app** technique (`references/techniques/github-app.md`) |
| "check on / babysit / get green" a PR | Babysit playbook |
| "help on / contribute to / what can I work on" a project, or a repo the user can't push to that has a brief | `skill://contribute` |
| "set up / publish this project for contributors", "make issues for helpers" | `skill://project-brief` |
| "run the factory / work the issue queue / turn issues into PRs / set up a software factory" | Factory playbook |
| "drive the board / work the backlog / run this project autonomously / keep going on the roadmap" | Board playbook |
| "set up deep-mode here", "configure the tracker / labels", "add a glossary and ADRs", or the first use of spec, tickets, or triage in a repo | Setup playbook |
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
| Anything else | The Playbooks table below |

**3. Size it**, then follow that size's rules. Re-size if the work turns out bigger.

| Size | Looks like | How to run it |
|---|---|---|
| **S** | One file or an obvious spot, a clear fix or small change, under ~30 lines | Fast path: one-line restate, make the change, run the real thing once to prove it, short report. No subagents, todo list, architect, or decision log. |
| **M** | A few files, one feature or bug with a cause to find | The matched playbook. Delegates only when work splits cleanly. |
| **L** | Cross-cutting, new module, many files, risky, or long-running | The full playbook with subagents, architect where shapes differ, and a show-me-your-work trail. |

**4. Act, then report.** Git and forge work in the user's repo is yours: branches, commits, pushes, PRs, reviews and comments on your own PRs, issues, labels, board cards, and merges after a **panel** pass (`references/techniques/panel.md`). Do it as the work needs it and report it at the end. Ask, once and at the end, only for the hard stops in Autonomy.

## Non-negotiables

For size **S**, only the one-line restate and proving it on the real artifact apply. The rest of this section applies when a rule would change the fix.

- **Restate first.** Your first message on a task states, in your own words, the user's goal, the problem they are solving, and, if the task ships a change, the smallest change you expect to meet it. Don't wait for confirmation. If the evidence rules out the requested change, show it and stop. Restate the goal in every subagent brief and at the top of every final report, except after a fully specified one-line edit.
- **Name your principles, in plain words.** For size M and L, add one short "Why I chose this" line naming each principle that changed a decision and the choice it changed, phrased so a non-expert follows ("I fixed the comparison where stock is checked, not the caller, because that's where it goes wrong"). Cite only principles whose file you read this session in `references/principles/`. Skip it for size S.
- **Prove it on the real artifact.** Before calling anything done, run the real app, CLI, or service path and capture evidence. If the repo has `.omp/skills/verify-<app>/`, use it. If not and the task changes user-visible behavior: when the user pre-authorized it (the `/deep` command does), run `skill://create-verification-skill` first; otherwise offer `/skill:create-verification-skill` once and prove the change by hand. Tests passing and "it compiles" are not proof.
- **Decide; don't ask.** About to `ask` "which approach" or "what should this do"? Settle it yourself, by kind. A fact → look it up. An observable fork (behavior, timing, layout, output, perf, whether an eval separates) → run the Prototype playbook and let the result decide. A product, design, or preference call → make it (Autonomy). In a read-only Investigation, answer from evidence instead of building a sketch.
- **Before building anything new** (a feature, tool, integration, or project) → **prior-art** (`references/techniques/prior-art.md`): start from the trending catalog (`references/trending/README.md`, refreshed by `scripts/trending.py find` when over a day old) so newer projects can beat the idea you already know, then search GitHub, the package registries, and official docs for code to depend on, copy, fork, or clone, and check its license first.
- **Name the data shape before any code**, and choose its organizing structure per `references/principles/model-the-domain.md`.
- **A new or changed module or public interface with two or more viable shapes** → the **architect** technique before implementing. A small edit that merely crosses a function boundary doesn't need it.
- **Nontrivial change, architecture decision, or "are we sure?"** → the **how** technique. Motivation questions → **why**.
- **Parallel fan-out** → **swarm** for coverage matrices, races, fuzzing a change, partitions. **arena** for design or code bakeoffs with base selection and grafting.
- **Contested design only** → **interrogate**, keeping only findings a run proves. Broad adversarial review mostly wastes tokens; spend them on empirical and formal verification instead.
- **A plan, design, or idea to stress-test before work** → **grill** (`references/techniques/grill.md`); you answer its questions unless the user asks to answer live.
- **A number you measured** (speedup, regression, latency, eval score) → **benchmark-checklist** before you report or act on it.
- **Prose** (reply, docs, PR body, commit message) → **unslop**; docs and PR/commit text also → **technical-writing**.
- **Before review** → **no-comments** on your diff. For a diff under ~20 lines, apply its keep-list yourself instead of spawning.
- **Repeated correction** (yours or the user's) → **correct**. Fix it at the highest rung that works: architecture or data structures, then a lint rule or test, then a skill or rule, and human review last.
- **Long, autonomous, or step-away work** → keep a decision trail with **show-me-your-work**.
- **Words or lasting decisions change** → **domain-model** (`references/techniques/domain-model.md`): terms into `GLOSSARY.md`, hard-to-reverse decisions into `docs/adr/`.
- **Reading that should outlive the chat** → **research** (`references/techniques/research.md`): a cited file in `docs/research/`.
- **Any flow that reads or writes issues** uses the **tracker** technique (`references/techniques/tracker.md`) for the commands and label roles.
- **PR-status requests** ("check on PR X", "get it green") → Babysit playbook. **Land a green stack** → Shipping playbook. Green is not safe.
- **Any PR** → the **pr-review** technique (`references/techniques/pr-review.md`): before opening one, self-review your branch in local mode and fix/dismiss/escalate each finding; maintainers review incoming PRs with `/deep-mode:review-pr <PR number>`. It runs on your own agent and subagents, no outside service, and never replaces live proof. Once the PR exists, run the **pr-agent** technique (`references/techniques/pr-agent.md`) on it, and the repo's own checks locally; your own PR then lands through **pr-conversation**.
- **Deep-mode is the gate layer**: no GitHub Actions and no hosted review service. When the repo opted into the security gate or the change touches auth, permissions, input parsing, or secrets, run **security-audit** (`references/techniques/security-audit.md`) on the head that will merge; its blocking findings are P0 review findings.
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

## Autonomy

- **Just do it.** Work proceeds without asking, including commits, pushes, PRs, issues, board cards, and merges.
- **Your own PRs land on their own.** Once every review finding is fixed or dismissed, linked issues are answered, the panel passes, and required checks are green, the **pr-conversation** technique merges the user's own PR. No separate ask.
- **Done means a panel pass.** No task is done and nothing merges until the **panel** technique (`references/techniques/panel.md`) passes at that exact head: three skeptical verifiers, at least two agreeing with evidence you checked. Then merge with `gh pr merge --match-head-commit <sha>`, run the checks on the new trunk, and open a revert PR if it went red.
- **Decisions are yours.** The user prefers the agent decide. Make every product, design, scope, and preference call yourself: pick the option that is reversible, smallest, and consistent with the codebase and the user's stated goal. Log each one as a show-me-your-work trail row (choice, why, evidence, how to reverse), and list them in the final reply under "Decisions I made" so the user can override any. Where a playbook or technique says to ask the user before deciding, committing, pushing, opening a PR, or merging, this rule wins.
- **Hard stops** still need the user's yes, batched into one question at the end: force-push or history rewrite on a shared or default branch; deleting branches, data, or resources you didn't create; deploys, releases, and package publishing; messages outside the repo (email, chat, other people's repos); bypassing a forge protection (required reviews or checks, admin merge); spending money or creating accounts; anything needing a credential or secret only the user has. A request that already asks for one of these is its yes.
- **Standing yes for your own PRs.** `~/.config/deep-mode/bot.json` `"autonomousMerge": true` (the default), or a base-branch `.deep-mode.json` `{"autonomousMerge": true}`, lets **pr-conversation** admin-merge your own PRs past a required review, never past a failing check. A base-branch `"autonomousMerge": false` overrides both.
- **Your subscription, not an API.** Every model call runs on a subscription the user is logged in with: the session's own model and its subagents (or `omp -p` from scripts), and the bots, which are any ACP (Agent Client Protocol) agents driven through `acpx`, omp by default, each harness on its own subscription login. Never set up an API key or wait on a hosted review bot.
- **Session overrides.** "Don't stop", "going to bed", "run until done" mean keep going until the work is done or only hard stops remain, and report every decision at the end.
- **No is an acceptable answer.** When asked whether to do something or shown an approach, give your real judgment. Push back or say "this doesn't earn its place" when true. Candor over agreement.

## Subagents

- You run the playbook. Delegates do bounded steps. Never delegate the playbook itself.
- Use `task` (or your harness's subagent tool). Read-only research uses `agent: "scout"`. Anything that edits, runs the app, or reads transcripts uses the default agent. `reviewer` is read-only: use it only to review a diff. Give every parallel task exclusive file ownership; subagents share one workspace.
- Every brief restates the user's goal, names the exact files and acceptance check, and tells code-writing delegates which `skill://deep-mode/references/principles/<name>.md` files apply. Subagents do not receive AGENTS.md, so put anything they must follow in the brief.
- Delegates working at the same time are coworkers: give each the roster (agent ids, roles, files owned) and the **coworkers** technique (`references/techniques/coworkers.md`), so they ask, hand off, and push back on each other directly instead of through you. Panel verifiers are the exception: they vote before they talk.
- Tier by difficulty. The hardest changes (cross-cutting design, concurrency, subtle algorithms) go to your strongest judgment model. Mechanical edits go to a fast model. For a second opinion or a judge, use a different model family when one is available. Agreement across families is high signal.
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

**Stack, UI design, and factory tooling** come from `skill://deep-stack` (stack picks and the decision rules behind them); its "With deep-mode" section sets the split. Greenfield web, SaaS, or AI-app framework, backend, auth, payments, or deploy choice → its `references/stack.md`. Any other kind of app (CLI, desktop, mobile, agent, data/ML, security tooling), or "build the stack for me" → its `references/any-app-stack.md`, which writes a cited `STACK.md`. Designing a UI with an agent → its `references/design-workflow.md`; rebuilding to the standard of a named reference app → the Reference rebuild playbook. Recording UI proof with no `verify-<app>` skill → its `references/prove.md`. Your gates and playbooks still govern.

**Agent tooling** (browser automation, agent sandboxes, coding-agent harnesses or multi-agent orchestrators, autoresearch loops) → read the cited landscape in `research/README.md` of a local checkout of `TimothyVang/automation-tools` before picking a tool. No checkout: `gh repo clone TimothyVang/automation-tools` (private; skip if you can't access it). It is a 2026-11-11 snapshot tuned for omp + Orca on Windows, so recheck release dates and licenses of the tool you pick.

**Engineering domain rules** come from `references/domain-rules/` (its `README.md` lists sources). Read only the file the task touches, before designing or reviewing in that area:

- AI agent, agent harness, multi-agent system, MCP or WebMCP, or an agent instruction file (CLAUDE.md, AGENTS.md, a skill) → `references/domain-rules/agent-engineering.md`. Audit agents against all seven of its laws.
- LLM fundamentals, RAG or retrieval, fine-tuning, inference cost or hardware, local models, or model choice → `references/domain-rules/ai-concepts.md`.
- AWS, VPC, cloud connectivity failure, IAM, or cloud cost → `references/domain-rules/aws-networking.md`. A "can't connect" bug starts with its four-step packet check and flow-log table.
- Backend code, API, database, cache, queue, scaling, resilience, observability, security, or language choice → `references/domain-rules/backend-system-design.md`; a specific language's runtime, tooling, or traps → `references/domain-rules/language-ecosystems.md`.
- Linux, shell tools, git, containers, Kubernetes, Terraform, CI/CD, deploy strategy, secrets, or a bug rooted in data structures, complexity, memory, floats, concurrency, or network protocols → `references/domain-rules/devops-and-fundamentals.md`.
- Unfamiliar codebase, stuck on an error, slowness, memory, or race debugging, legacy code, PR or commit text, production incident, estimates, or pushing back on scope → `references/domain-rules/engineering-practice.md`.

**Frontend UI/UX** (building, restyling, or reviewing UI; components; motion and animation; motion graphics or rendered video; color; accessibility; chat or agent UI) → before writing UI code, read `references/frontend/README.md` (always-apply rules, routing, section index), then the `references/frontend/playbook/` section it routes to. `references/frontend/patterns/` holds what the reference images and clips taught, as text: shipped-app layouts, popular pins, 193 animation techniques, the motion-graphics stack. These files are bundled, so they work anywhere deep-mode is installed. Evidence and media live in the private `TimothyVang/frontend`; if `gh` can read it and you need them, shallow-clone to `~/.omp/agent/frontend`, never into the project.

**Cloud security and DevSecOps rules** come from `references/cloud-devsecops/` (cited reports in `TimothyVang/cloud-devsecops`; its `README.md` lists them). They cover securing and wiring up a cloud, where `domain-rules/aws-networking.md` covers how AWS networking works. Read the file the task touches before designing, reviewing, or changing cloud access, policy, or pipelines:

- AWS accounts, Organizations, SCP/RCP, IAM, GuardDuty or Security Hub, KMS, or CI access to AWS → `references/cloud-devsecops/aws.md`.
- Azure subscriptions, management groups, Entra ID, RBAC, Azure Policy, Defender for Cloud, Key Vault, Private Endpoints, AKS, or CI access to Azure → `references/cloud-devsecops/azure.md`.
- Google Cloud orgs or projects, IAM or service accounts, org policy, VPC Service Controls, Security Command Center, Binary Authorization, GKE, or CI access to GCP → `references/cloud-devsecops/gcp.md`.
- A CI/CD pipeline's security stages, supply chain (SBOM, signing, SLSA provenance), scanners, policy as code, container or Kubernetes hardening, or GitHub Actions hardening → `references/cloud-devsecops/devsecops-pipeline.md`.
- Testing cloud or IaC code without a real account (Floci, LocalStack, moto, Azurite, Google emulators) → `references/cloud-devsecops/local-emulators.md`. Run infra changes there first when the emulator covers the service.
- Choosing terminal, container, Kubernetes, Terraform, or code-review tooling → `references/cloud-devsecops/devops-tools.md`.

## Habits worth keeping

- Restate-in-your-own-words is the most useful single prompt. Use it on any thread, report, or fuzzy ask before acting.
- Prototypes beat abstract plans. Abstract plans give the illusion of progress; reviewing them adversarially invents risks that never happen.
- Your codebase is the memory. Every nit an agent repeats should become a constraint (type, lint, test, structure), or agents will keep copying it.
- Artifacts beat explanations. Show the failing and passing test, the before/after screenshot or transcript, the trace.
- Every stage can stop the line. "Not a bug", "can't reproduce", and "too risky" are valid outcomes that keep bad work from flowing downstream.
