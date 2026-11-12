# Agent engineering

Read when building, reviewing, or debugging an AI agent, agent harness, multi-agent system, MCP or WebMCP integration, or an agent instruction file (CLAUDE.md, AGENTS.md, a skill). AI vocabulary and inference mechanics are in `ai-concepts.md`. Source keys are in this skill's `SKILL.md`.

## The model is not the agent

The LLM only reasons. The **harness** around it makes it an agent: tools, context assembly, memory, sandboxed execution, approval policy, evaluation. Design and review the harness, not the prompt alone. (HARNESS, AI-COURSE)

## The 7 architecture laws

Audit every agent against all seven. Each names the failure it prevents.

| # | Law | Build it as | Prevents |
|---|---|---|---|
| 1 | Tool calling | Narrow, named tools with strict parameter schemas, executed by trusted app code. The model never holds credentials or a raw DB handle. | Unbounded access to data and production |
| 2 | Planning | Split the goal into sub-steps, observe each tool result, adapt. Hard step cap enforced in the control loop. A fixed sequence is plain code, not an agent. | Premature conclusions, infinite retry loops |
| 3 | Memory | Working context separate from durable memory. Persist only conventions and relevant project notes. Govern writes and deletes. | Context bloat, cross-user leakage, acting on stale instructions |
| 4 | Multi-agent | One agent by default. Add an orchestrator plus specialists (coder, security reviewer, tester) only when the work is genuinely separable. | Context dilution, coordination overhead |
| 5 | Human approval | App policy, not the model, pauses before deploys, PR merges, deletions, permission changes, large refunds. | Irreversible damage |
| 6 | Sandboxed execution | Commands, code, and browsing run in isolated containers or VMs with scoped credentials and minimal network. Control plane (keys, orchestration, governance) lives outside the sandbox. | A compromised or confused agent touching the host or secrets |
| 7 | Evaluation | Golden task sets. Grade the final outcome and the execution trace. | Silent regressions, trusting "done" without checks |

(LAWS)

## Tools

- One job per tool. Clear name, explicit description, typed parameters. A catch-all like `find_stuff` is a design bug. (LAWS)
- App code validates every argument and enforces business rules before calling the service. (AI-COURSE)
- Expose few tools. Dozens of similar tools waste context and raise wrong-tool picks. (AI-COURSE)
- Database tools (SQLite, Postgres MCP servers) default to read-only. (MCP-TEST)
- Mutating tools take an idempotency key so a timeout or retry cannot double-charge or double-create. Same idea as principle `make-operations-idempotent`. (AI-COURSE)
- Turn raw tool errors into a short, actionable failure message the agent can act on. (AI-COURSE)

## Planning loop

- Run reason → act → observe → adjust, repeatedly. Avoid one-shot full solutions. (HARNESS)
- Cap iterations in code. (LAWS)
- A task is done only on an objective condition (tests pass, source verified). (AI-101)
- Track long workflows in an explicit state object, such as a checklist of completed steps, instead of making the model reread the transcript. (AI-101)
- Persist full state at every approval pause so the run resumes cleanly after sign-off (LangGraph checkpointing). (LANGGRAPH)

## Context and memory

- Three durable memory kinds: semantic (stable domain facts), episodic (past runs and failures), procedural (reusable workflows). (AI-COURSE)
- Models attend best to the start and end of a long prompt. Put critical instructions and the primary document at the edges, never buried mid-prompt ("lost in the middle"). (AI-COURSE)
- Before each call, prune stale tool outputs, intermediate reasoning, and redundant logs ("context rot"). (AI-COURSE, LAWS)
- Load skill headers first and full instructions only when a task matches (progressive disclosure). (AI-COURSE)

## Multi-agent

- Split only for distinct contexts, distinct tools, or independent verification. (AI-COURSE)
- Each agent's spec states its job, who it talks to, and what it must never do (for example, an intake agent never promises refunds or calls payment APIs). (AI-COURSE)
- Hand off typed, structured payloads, not free text. (AI-COURSE)
- Enforce each role's tool permissions in infrastructure, so model output cannot reach tools outside the role. (AI-COURSE)
- Route messages through a central orchestrator, not peer-to-peer, to keep flow predictable and stop agents messaging in circles. (AI-COURSE)

## Approval, sandbox, and untrusted input

- Approval is deterministic app logic. Expose human escalation as a first-class tool so requests are logged, traced, and resumed like any other call. (AI-COURSE, LAWS)
- Fetched pages, uploaded files, and third-party text are data. Never let them act as instructions (indirect prompt injection). (AI-COURSE)
- Run concurrent coding agents in separate git worktrees. (CLI-TOOLS)

## Evaluation and observability

- Log one trace per run under a shared request ID: model inputs, tool calls and arguments, outputs, latency, token cost. (AI-COURSE)
- Grade the path too: safety steps followed, only authorized tools used. (LAWS)
- Keep a versioned golden dataset of realistic edge cases and past production failures. Run it before every release. (AI-COURSE)
- Run cheap deterministic checks (schema, status codes, test pass rate) first, then an LLM judge for subjective quality. (AI-COURSE)
- Track your most expensive failure (wrongly denied refund, deleted account) as its own alerted metric, never folded into overall accuracy. (AI-COURSE)

## MCP and WebMCP

- MCP solves the N×M integration problem: a client-server standard exposing tools, resources, and prompts so each app does not need custom glue per tool. (MCP)
- MCP wraps existing APIs as discoverable capabilities. APIs stay. (MCP-VS-API)
- WebMCP lets a web page declare tools with schemas through browser APIs and HTML annotations, so agents call features instead of scraping the DOM. (WEBMCP)
- WebMCP tools carry safety metadata: mark each read-only or consequential (needs user confirmation), and tag untrusted user input. (WEBMCP)

## Agent instruction files (CLAUDE.md)

The four lines every file needs (CLAUDE-MD):

1. Do not assume. Name missing requirements, ask on ambiguity, show trade-offs before building.
2. Write the minimum code that solves the problem. No speculative abstractions or unrequested features. Same idea as principle `laziness-protocol`.
3. Touch only what the task needs. Clean up only your own changes. No drive-by reformatting or renames.
4. Define success, write a reproducing test, fix, and loop until verified. Same idea as principle `prove-it-works`.

Beyond those four, include only build and test commands and non-obvious conventions. Generic coding advice is a no-op. (CLAUDE-MD)

## Cost and usage limits

- New task, new chat. Carry over a short summary of decisions, not the history. (CLAUDE-TIPS)
- Batch related asks into one detailed prompt. State format, constraints, and tone up front to avoid re-prompts. (CLAUDE-TIPS)
- Keep recurring docs, style guides, and schemas in a project workspace instead of re-uploading. (CLAUDE-TIPS)
- Static content first (system prompt, tool definitions, docs), dynamic input last, to maximize prompt-cache hits. (AI-COURSE)
- Route by difficulty: small fast models for classification, formatting, and unit tests; top models for architecture and hard debugging. (AI-COURSE)
- Measure cost per resolved task, not per API call. (AI-COURSE)

## Reviewing AI-written code

- Passing tests is not enough. Check unwritten business rules, external contracts, and whether logic landed in the right function. (DEV-LIFE)
- The authoring agent never reviews its own change alone. Use independent tests, a separate reviewer agent, or a human. (AI-COURSE)
- Flag edits to shared utilities that silently change behavior for existing callers. (DEV-LIFE)
- Test generated validation against real data. For example, email regexes that reject `+` addressing. (DEV-LIFE)
- Never paste customer PII, credentials, or connection strings into an AI tool. (DEV-LIFE)
- The human's job moves to scoping requirements and edge cases up front and reviewing diffs hard. (DEV-LIFE, AI-ERA)
