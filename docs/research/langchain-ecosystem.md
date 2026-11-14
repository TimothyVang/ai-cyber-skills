# LangChain ecosystem research

**Access date: 2026-11-13.** Scope: official documentation for LangChain, LangGraph, Deep Agents and LangSmith, with Python/TypeScript boundaries and transferable patterns for deepmodebot. Started at the official `llms.txt` and followed its Python/TypeScript indexes and linked pages. Primary documentation only; no packages installed, API/model calls executed, servers started, accounts configured, or deployment/telemetry enabled.

The agent-facing decision reference is [langchain-ecosystem.md](../../plugins/deepmodebot/skills/agent-harnesses/references/langchain-ecosystem.md). That file owns the compact selection tables and routing instructions. This file preserves source provenance, deeper implications, failure scenarios and unresolved facts. **Vendor fact** means documented behavior, not independently tested behavior; **Recommendation** means a proposed application to deepmodebot.

## Findings that change decisions

### LC-1: One ecosystem, several independent decisions

**Vendor fact:** LangChain supplies the configurable agent harness (`create_agent`); LangGraph is the lower-level state/control-flow runtime and does not require LangChain; Deep Agents assembles filesystem context, subagents, memory and planning over that stack. Middleware stays with a `create_agent` agent embedded in a larger graph. [S01](https://docs.langchain.com/oss/python/langchain/agents.md), [S03](https://docs.langchain.com/oss/python/langgraph/overview.md), [S05](https://docs.langchain.com/oss/python/deepagents/overview.md), [S07](https://docs.langchain.com/oss/python/langchain/middleware/overview.md)

**Recommendation:** ask which boundary is actually missing: a capability, procedure, isolated context, explicit transition, persistent state, or production operations. “Multi-step” alone does not justify a graph dependency, and “multi-agent” alone does not justify subagents. A local coding harness already supplies a tool loop; importing a second autonomous harness creates another controller to bound and another permission surface to audit.

**Example:** generating and reviewing a migration can remain one bounded host iteration with deterministic acceptance. A customer-service application with authenticated users, durable waiting approvals and parallel business workflows may warrant a graph. The distinction is the application's runtime requirements, not the length of the prompt.

### LC-2: Pin the language and package generation before translating an example

**Vendor fact:** Python's v1 migration changes the factory, prompt parameters, middleware hooks and legacy package namespace. Python documentation describes Deep Agents as pre-1.0. The current install pages say Python 3.10+, Node.js 22+, with a separate Bun requirement. [S11](https://docs.langchain.com/oss/python/migrate/langchain-v1.md), [S09](https://docs.langchain.com/oss/python/versioning.md), [S10](https://docs.langchain.com/oss/python/langchain/install.md), [S12](https://docs.langchain.com/oss/javascript/langchain/install.md)

Current Python MCP docs require `langchain[mcp]>=1.4.0` and mark the namespace beta; TypeScript's counterpart requires `@langchain/mcp-adapters>=2.0`. [S26](https://docs.langchain.com/oss/python/langchain/mcp/index.md), [S27](https://docs.langchain.com/oss/javascript/langchain/mcp/index.md)

**Recommendation:** record `(language, package, pinned version, requested feature, source page)` before proposing code. Copy only the language's actual import/signature example, not shared prose. The TS Agents page inspected contains Python-oriented prose such as `system_prompt` and “Python callable,” while its TS code uses `systemPrompt` and `tool(...)`. This is a documentation consistency limitation, not evidence that those Python spellings work in TS. [S02](https://docs.langchain.com/oss/javascript/langchain/agents.md)

No “latest” version was established. A feature floor is not an installed version, and a shared page title is not parity evidence. Exact production support and lockfile compatibility remain implementation-time checks.

### LC-3: Selection and authorization are separate boundaries

**Vendor fact:** Python tools documentation distinguishes filtering already registered tools from adding runtime-discovered tools. Runtime registration needs model-call wrapping to expose tools and tool-call wrapping to execute them. Middleware can also transform prompts, inspect behavior, apply limits and interrupt sensitive tool calls. [S08](https://docs.langchain.com/oss/python/langchain/tools.md#dynamic-tool-selection), [S07](https://docs.langchain.com/oss/python/langchain/middleware/overview.md)

**Recommendation:** adopt the sequence `inventory → applicability → permission → schema → execution → evidence`. Model-facing selection reduces distraction; the actual execution gate still validates scope and authority. A generated skill or remote tool's description cannot authorize a new subprocess, credential, filesystem root or mutation.

**Example:** a research phase may choose search/read tools; an implementation phase may choose edit tools for owned files. Merely hiding a deployment tool from the prompt is not an access control system. Conversely, loading a “deployment” skill must not mount new servers or grant production access. If the selected capability is unavailable, report that boundary or use an authorized equivalent; do not invent a tool implementation.

### LC-4: A skill is context; a subagent is execution

**Vendor fact:** skills use progressively disclosed metadata, body and resources. Deep Agents' default isolated subagent receives the delegated task; fork mode can inherit parent context. Custom isolated subagents do not inherit the parent's custom middleware or system prompt; tools/model have documented defaults, and custom subagent skills have separate loading rules. These are feature-specific inheritance rules, not a universal “all children inherit everything” contract. [S23](https://docs.langchain.com/oss/python/deepagents/skills.md), [S25](https://docs.langchain.com/oss/python/deepagents/subagents.md)

**Recommendation:** use skills for reusable procedures and subagents only for execution isolation or independent work that repays delegation overhead. A brief must explicitly carry ownership, fixed constraints, result format and evidence requirements. Main-agent permissions and memory do not safely transfer just because a child has a familiar name.

**Portability trap:** the Deep Agents skills page describes skill-specific tools carried in metadata as a Deep Agents feature, not the Agent Skills standard, and distinguishes this from `allowed-tools`. Do not add those fields to deepmodebot's portable skill conventions by analogy. Existing [self-authoring reference](../../plugins/deepmodebot/skills/agent-harnesses/references/self-authoring.md) remains the source for portable layouts and harness-specific syntax. [S23](https://docs.langchain.com/oss/python/deepagents/skills.md#add-tools-to-skills)

### LC-5: Durable state, audit logs and memory are not interchangeable

**Vendor fact:** checkpointers persist thread state at super-step boundaries; stores hold cross-thread key-value data. A thread ID selects saved state, while invocation input determines new work versus resume versus replay. Successful pending writes in a failed super-step can be retained. In-memory implementations do not supply restart durability. Runtime context is separate per-run configuration. [S15](https://docs.langchain.com/oss/python/langgraph/persistence.md), [S16](https://docs.langchain.com/oss/python/langgraph/checkpointers.md), [S17](https://docs.langchain.com/oss/python/langgraph/stores.md), [S08](https://docs.langchain.com/oss/python/langchain/tools.md#context)

**Recommendation:** deepmodebot's existing `.scratch/goals/<slug>/` trail is evidence for subsequent decisions, not a resumable execution engine. Use it to establish what happened; inspect current files/external state before retrying. A reviewed project lesson belongs in a maintained reference; an unfinished hypothesis belongs in the mutable working plan. Never copy user-specific memory into an agent-wide/shared namespace by default.

Store namespaces are application-defined and searches may match namespace prefixes; they are not by themselves an authentication or tenant-isolation guarantee. Use a verified caller and explicit access enforcement in real applications. [S17](https://docs.langchain.com/oss/python/langgraph/stores.md), [S24](https://docs.langchain.com/oss/python/deepagents/memory.md)

### LC-6: Resume can repeat work, and approval can be invalidated by unstable predicates

**Vendor fact:** an interrupted node starts from its beginning on resume; Functional API entrypoints replay while completed task outputs are restored. Started-but-unfinished tasks can execute again. Historical replay re-executes downstream LLM/API calls and interrupts; forks do not roll back prior effects. [S18](https://docs.langchain.com/oss/python/langgraph/interrupts.md), [S19](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md), [S20](https://docs.langchain.com/oss/python/langgraph/functional-api.md)

**Recommendation:** distinguish `proposed`, `authorized`, `attempted`, `confirmed`, and `unknown outcome` in evidence for non-idempotent operations. “Connection lost” is not proof that sending, charging, publishing or deleting failed. Use stable operation identity and external reconciliation before retry; checkpointing cannot create exactly-once behavior at an external service by itself.

**Example:** `send message → interrupt for approval` is unsafe because approval comes after the effect and the prefix may run again. Prefer `prepare immutable request → approve that request → perform with operation key → record receipt`. If arguments change after review, approval no longer covers the same action. This is a conceptual design example, not tested code.

**Vendor fact:** HITL supports `approve`, `edit`, `reject`, and `respond`; `respond` is a synthetic successful result for ask-user tools, not a rejection. Conditional predicates execute again on resume. The docs warn a predicate changing to false can execute the tool and ignore the reviewer's rejection; batched inconsistencies can raise errors. Per-call mode is documented with a Python version floor. [S21](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md)

**Recommendation:** freeze review-relevant inputs, use explicit action identity, and ensure conditional approval checks are deterministic for the pending action. General graph interrupts, tool-approval middleware and the host harness's permission prompts are different mechanisms; none replaces the others' authorization contract.

### LC-7: MCP migration crosses lifecycle and feature boundaries

**Vendor fact:** Python's new `MCPAdapter` returns tools that retain/reopen the client after discovery closes. Keeping its context open permits one connection across calls. TS documents keeping its adapter open while the agent runs and closing it in `finally`. [S26](https://docs.langchain.com/oss/python/langchain/mcp/index.md), [S27](https://docs.langchain.com/oss/javascript/langchain/mcp/index.md)

Python migration removes public `get_prompt`, `get_resources` and `session` counterparts; old interceptor/config behavior needs translation. Aggregated Python `MCPConfig` shares protocol negotiation, whereas `ClientGroup` isolates connection eras. [S28](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters.md), [S29](https://docs.langchain.com/oss/python/langchain/mcp/connections.md)

**Recommendation:** a migration inventory must include prompts/resources, transport, stateful sessions, authentication, tool naming, result errors and cleanup, not only imports. Do not describe adapter support as complete MCP support. Preserve the existing [protocols reference](../../plugins/deepmodebot/skills/agent-harnesses/references/protocols.md) as the wire/security authority. This research does not authorize starting or connecting an MCP server.

### LC-8: Measure routes and outcomes separately; services stay optional

**Vendor fact:** AgentEvals provides deterministic strict/unordered/subset/superset trajectory matching and model judging. LangSmith provides offline dataset experiments and online live-traffic evaluation; traces can become regression cases. LangSmith tracing records inputs, model interactions and tool calls when enabled. [S30](https://docs.langchain.com/oss/python/langchain/test/evals.md), [S31](https://docs.langchain.com/langsmith/evaluation.md), [S32](https://docs.langchain.com/oss/python/langchain/observability.md)

**Recommendation:** borrow dataset/evidence discipline in the existing local eval suite. Route labels should not substitute for task completion. Assert necessary ordering (read policy before mutation), permit harmless parallel read ordering, and forbid unauthorized extra actions. Deterministic comparison does not imply the model run that produced a trajectory is free. Redact logs and keep external telemetry disabled unless separately authorized.

**Vendor fact:** Agent Server hosting is distinct from where the LangSmith observability/evaluation platform runs. Cloud requires Plus or Enterprise; self-hosted control-plane hosting is Enterprise; standalone hosting brings PostgreSQL, Redis and a LangSmith license. Managed Deep Agents, OSS SDK self-hosting and licensed Agent Server are different options. [S34](https://docs.langchain.com/langsmith/deployment.md), [S05](https://docs.langchain.com/oss/python/deepagents/overview.md)

**Recommendation:** neither “OSS” nor “self-hosted” means zero-cost execution, no operational burden, or no licensing conditions. No billing, deployment or network-facing service is introduced by applying these patterns to deepmodebot.

## Bounded-loop transfer contract

This section is **Recommendation**, not an implemented SDK integration. The existing [self-authoring playbook](../../plugins/deepmodebot/skills/deepmodebot/references/playbooks/self-authoring.md) owns immutable goal frontmatter, protected checks, iteration/time/cost caps, stall handling, evidence and promotion. Keep those semantics unchanged.

| Ecosystem pattern | Transfer to existing deepmodebot | Preserve / reject |
|---|---|---|
| Graph state and transitions | Explicitly identify the current phase, observed failure, next bounded action and evidence path in the working plan | Preserve the fixed contract; reject rewriting acceptance to make a result pass. |
| Middleware | Check selected tool availability, ownership and approval before action; inspect result afterward | Host enforcement remains authoritative; prose is not a security sandbox. |
| Dynamic tool selection | Load only the relevant tool schema and skill branch | No silent installation, new SDK dependency or extra service. |
| Progressive skill disclosure | Precise trigger → small skill body → task-specific reference | Keep always-loaded instructions compact; do not paste a documentation corpus into every prompt. |
| Subagent context isolation | Independent owned slices return bounded findings and evidence | No second unbounded goal loop; use existing delegation and integration rules. |
| Checkpoint/replay thinking | Identify completed versus uncertain effects before another attempt | Local trails do not supply LangGraph persistence or exactly-once execution. |
| Store / memory | Promote a validated reusable lesson at the existing review gate | Diagnostics and retrieved pages remain untrusted; do not silently edit shared policy or global harness config. |
| Evaluation feedback | Add a failure-derived local regression and compare behavior before promotion | Protected acceptance remains the completion oracle; external judge/service is not required. |

A useful next-action record is `{phase, observed_failure, hypothesis, next_action, selected_reference, evidence_path}` inside the existing mutable plan, not a new goal schema. No new runner fields or execution guarantees are claimed. Outcome paths remain `pass → finish`, `new failure evidence → bounded revision`, `cap/stall/policy violation → existing stop/report behavior`.

## Failure-mode and routing cases for the integration owner

These are proposed evaluation cases, not executed results.

| Prompt / situation | Expected decision | Failure to catch |
|---|---|---|
| “Use LangGraph to keep fixing this test until green” in a plain repo | Existing self-authoring loop; this reference for design only | Installing LangGraph or spawning an unbounded nested loop without need. |
| “`create_react_agent` example fails in my Python v1 project” | Language/version gate, migration docs, debugging workflow | Copying legacy hook names or using TS APIs. |
| “Should this approval flow use `create_agent` or `StateGraph`?” | Determine whether standard tool loop plus HITL suffices; graph for surrounding explicit topology | Treating the factories as mutually exclusive. |
| “MCP tools appear but cannot execute” | Separate schema exposure from runtime execution registration; inspect pinned adapter generation | More prompt text instead of completing execution wiring. |
| “Resume this interrupted email node” | Same thread, interrupt resume, inspect pre-interrupt side effects and pending action | New thread, plain new input, or blind resend. |
| “Replay an old successful graph” | Warn that downstream effects execute again; scope replay to authorized effects | Claiming replay is read-only playback or rollback. |
| “Reviewer rejected the operation” | Preserve `reject` semantics and stable predicate | Using `respond` as denial or changing a predicate to skip review. |
| “Remember this customer secret for all future tasks” | Scope/auth/data-policy check; no default shared memory promotion | Agent-global memory leakage. |
| “Port our MCP client to TS” | TS package/lifecycle docs, inventory prompts/resources/session use | Transplanting Python beta `langchain.mcp` or context-manager behavior. |
| “Add a LangSmith dashboard” | Separate research from external account/key/trace upload authorization | Turning tracing on or assuming subscription covers API/service cost. |

## Source manifest

All entries below were accessed **2026-11-13**. Titles are the returned page titles; Py/TS labels disambiguate pages with the same title. Long pages were read in topic-relevant sections; this is not a claim that every example on every page was audited. IDs are stable citation anchors for this research, not package versions.

| ID | Page title and actual URL read | Evidence scope |
|---|---|---|
| I00 | [Docs by LangChain — llms.txt](https://docs.langchain.com/llms.txt) | Entry point and recursive index discovery. |
| I01 | [Docs by LangChain: AGENT DEVELOPMENT LIFECYCLE Build Python](https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.txt) | Official page inventory, including migration/versioning links. |
| I02 | [Docs by LangChain: AGENT DEVELOPMENT LIFECYCLE Build TypeScript](https://docs.langchain.com/_llms/agent-development-lifecycle/build/type-script.txt) | TS counterpart inventory through graph/frontend sections. |
| S01 | [Agents — Python](https://docs.langchain.com/oss/python/langchain/agents.md) | Factory, core arguments, tool definition. |
| S02 | [Agents — TypeScript](https://docs.langchain.com/oss/javascript/langchain/agents.md) | CamelCase factory/options; shared-prose limitation. |
| S03 | [LangGraph overview — Python](https://docs.langchain.com/oss/python/langgraph/overview.md) | Runtime boundary, graph imports, LangChain independence. |
| S04 | [LangGraph overview — TypeScript](https://docs.langchain.com/oss/javascript/langgraph/overview.md) | Package/imports and current schema example. |
| S05 | [Deep Agents overview — Python](https://docs.langchain.com/oss/python/deepagents/overview.md) | Harness, managed vs SDK, filesystem backends/capabilities. |
| S06 | [Deep Agents overview — TypeScript](https://docs.langchain.com/oss/javascript/deepagents/overview.md) | `createDeepAgent` quickstart and run options. |
| S07 | [Middleware overview — Python](https://docs.langchain.com/oss/python/langchain/middleware/overview.md) | Hooks, limits, graph composition. |
| S08 | [Tools — Python](https://docs.langchain.com/oss/python/langchain/tools.md) | Schemas, runtime context, dynamic selection and registration. |
| S09 | [Versioning — Python](https://docs.langchain.com/oss/python/versioning.md) | Stability, LTS, pre-1.0 caveats. |
| S10 | [Install LangChain — Python](https://docs.langchain.com/oss/python/langchain/install.md) | Runtime floor and provider package separation. |
| S11 | [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1.md) | Factory/hook/package migration. |
| S12 | [Install LangChain — TypeScript](https://docs.langchain.com/oss/javascript/langchain/install.md) | Node/Bun requirements and packages. |
| S13 | [Multi-agent — Python](https://docs.langchain.com/oss/python/langchain/multi-agent/index.md) | Subagents, handoffs, skills, routers; illustrative tradeoffs. |
| S14 | [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents.md) | Predetermined vs agentic paths, chaining/parallel/routing examples. |
| S15 | [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence.md) | Checkpointer/store distinction, in-memory caveat. |
| S16 | [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers.md) | Threads, super-steps, pending writes, invocation modes. |
| S17 | [Stores](https://docs.langchain.com/oss/python/langgraph/stores.md) | Namespaced data, prefix search, ordering/limit caveats. |
| S18 | [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts.md) | Pause/resume, restart boundary, response-schema floor. |
| S19 | [Use time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md) | Replay, fork, repeated effects/interrupts. |
| S20 | [Functional API overview](https://docs.langchain.com/oss/python/langgraph/functional-api.md) | Task result restoration, entrypoint replay, idempotency. |
| S21 | [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md) | Decision types, predicate stability, batched/per-call floors. |
| S22 | [Context engineering in Deep Agents](https://docs.langchain.com/oss/python/deepagents/context-engineering.md) | Context types, input/runtime context, compression/isolation. |
| S23 | [Skills](https://docs.langchain.com/oss/python/deepagents/skills.md) | Progressive disclosure, source directories, skill-tool extension. |
| S24 | [Memory](https://docs.langchain.com/oss/python/deepagents/memory.md) | Agent/user scopes, backend persistence, update permissions. |
| S25 | [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents.md) | Isolation/fork, default child, inheritance boundaries. |
| S26 | [Model Context Protocol (MCP) — Python](https://docs.langchain.com/oss/python/langchain/mcp/index.md) | Beta adapter floor, imports, discovery, target types. |
| S27 | [Model Context Protocol (MCP) — TypeScript](https://docs.langchain.com/oss/javascript/langchain/mcp/index.md) | Adapter 2.x, lifecycle and transports. |
| S28 | [Migrate from langchain-mcp-adapters](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters.md) | Old/new names, removed public methods, lifecycle/config changes. |
| S29 | [Connections](https://docs.langchain.com/oss/python/langchain/mcp/connections.md) | Reentrant lifetime, multiple servers, protocol-era scope. |
| S30 | [Agent Evals](https://docs.langchain.com/oss/python/langchain/test/evals.md) | Trajectory comparison modes and judge distinction. |
| S31 | [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation.md) | Offline/online evaluation and failure-to-dataset loop. |
| S32 | [LangSmith Observability](https://docs.langchain.com/oss/python/langchain/observability.md) | Data captured and activation/account boundary. |
| S33 | [Deployment](https://docs.langchain.com/oss/python/langgraph/deploy.md) | Hosting choices and Cloud workflow; no deployment performed. |
| S34 | [LangSmith Agent Server](https://docs.langchain.com/langsmith/deployment.md) | Hosting/platform separation, plan/license prerequisites. |
| S35 | [Custom middleware — TypeScript](https://docs.langchain.com/oss/javascript/langchain/middleware/custom.md) | Hook names and creation API. |

## Unresolved facts and refresh triggers

- **Installed compatibility unverified:** no target SDK application was executed. Pin and inspect actual packages, provider integrations and checkpoint backends before implementing any example. Current docs are moving pages, not immutable release snapshots.
- **Language parity unverified:** Python-specific feature floors, middleware semantics, interrupt response schemas, skill-tool extensions and subagent inheritance were not exhaustively checked against TS. The reference labels the observed language rather than claiming parity.
- **Documentation quality:** TS Agents prose contains Python spellings; some official examples use toy tool bodies. Neither should be copied as production validation, permission enforcement or security design. We retained concepts and signatures, not runnable sample implementations.
- **Operations unverified:** no prices, quotas, tenant entitlements, regional availability, data retention contracts, scaling guarantees or package release registry “latest” values were checked. Hosting prerequisites are vendor documentation observations, not a service quote.
- **Durability unverified:** no crash/replay tests, persistence migrations, external idempotency tests or authorization tests were run. Exactly-once side effects are not established by the documentation.
- **Scope of ecosystem:** Managed Deep Agents is recorded as a distinct hosting choice from its linked overview descriptions; its full API, Fleet, Engine, OpenWiki and provider-specific integrations were not independently researched here.
- **Refresh on** changed manifest/lockfile, beta/minor Deep Agents upgrade, adapter migration, new replay/approval behavior, changed tracing destination, or deployment proposal. Re-enter through `llms.txt`; read the feature's language-specific page and version note before revising the reference.
- **Verification hand-off:** parent should run repository documentation/routing checks after integration. This worker deliberately ran no builds, tests, linters, formatters, model evals or SDK smoke runs.
