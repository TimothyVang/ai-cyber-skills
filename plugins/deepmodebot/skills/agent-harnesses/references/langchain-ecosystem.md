# LangChain ecosystem: choose the boundary, not another loop

Read for LangChain, LangGraph, Deep Agents, LangSmith, `create_agent` / `createAgent`, `StateGraph`, middleware tool routing, checkpoint recovery, interrupts, or MCP adapters. **Accessed 2026-11-13.** Vendor facts below cite official pages; **Recommendation** marks deepmodebot design advice. This is documentation research, not an SDK installation, API execution, deployment, or compatibility test.

Use [self-authoring](self-authoring.md) for harness-native prompt/skill/goal syntax, the [bounded self-authoring playbook](../../deepmodebot/references/playbooks/self-authoring.md) for execution and promotion gates, and [protocols](protocols.md) for MCP/ACP/A2A/WebMCP security and wire semantics. This reference adds ecosystem decisions, not replacement rules.

## 1. Select the abstraction

| Requirement | Vendor capability | Recommendation for deepmodebot |
|---|---|---|
| Model chooses tools in a conventional loop | LangChain `create_agent` is a configurable model/tools/prompt/middleware harness; middleware runs inside its compiled LangGraph. [Agents](https://docs.langchain.com/oss/python/langchain/agents.md), [Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware/overview.md) | Keep the existing harness for ordinary coding work. Adopt the design principle of a small task-specific tool surface, not an SDK dependency. |
| Explicit state transitions, deterministic gates, fan-out/join, human pause | LangGraph supplies state, nodes, edges and persistence without prescribing prompts; it does not require LangChain. [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview.md) | Model the existing bounded loop as explicit phases. Select `StateGraph` only when implementing an application that actually needs programmable graph orchestration. |
| Assembled planning, filesystem context, delegation and memory | Deep Agents adds these capabilities over LangChain/LangGraph; SDK self-hosting and Managed Deep Agents are distinct run options. [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview.md) | Borrow progressive disclosure and context isolation. Do not run a second autonomous agent loop inside deepmodebot by default. |
| Traces, datasets, evaluation, production hosting | LangSmith covers observability/evaluation; Agent Server is a separate hosting/runtime concern. [Observability](https://docs.langchain.com/oss/python/langchain/observability.md), [Evaluation](https://docs.langchain.com/langsmith/evaluation.md), [Agent Server](https://docs.langchain.com/langsmith/deployment.md) | Retain local evidence and existing evals. Service activation, telemetry upload and deployment require a separately authorized implementation. |

`create_agent` and `StateGraph` are composable rather than rivals: a middleware-equipped agent can be a graph node/subgraph when surrounding routing is more complex than a tool loop. [Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware/overview.md)

## 2. Language and version gate

Before proposing code, inspect the target project's manifest/lockfile and select its language-specific documentation. The documentation examples below identify API families, not the latest installed versions.

| Boundary | Python documentation | TypeScript documentation |
|---|---|---|
| Core factory | `from langchain.agents import create_agent`; `system_prompt`, `response_format` | `import { createAgent } from "langchain"`; `systemPrompt`, `responseFormat`. [Python agents](https://docs.langchain.com/oss/python/langchain/agents.md), [TS agents](https://docs.langchain.com/oss/javascript/langchain/agents.md) |
| Graph | `StateGraph` from `langgraph.graph`; `.add_node()` | `StateGraph` from `@langchain/langgraph`; `.addNode()`. Current overview uses `StateSchema` / `MessagesValue`; do not assume older schema examples match a pinned package. [Python overview](https://docs.langchain.com/oss/python/langgraph/overview.md), [TS overview](https://docs.langchain.com/oss/javascript/langgraph/overview.md) |
| Deep Agents | `create_deep_agent` from `deepagents` | `createDeepAgent` from `deepagents`; current quickstart awaits factory creation. [Python overview](https://docs.langchain.com/oss/python/deepagents/overview.md), [TS overview](https://docs.langchain.com/oss/javascript/deepagents/overview.md) |
| Middleware | `wrap_model_call`, `wrap_tool_call`, middleware classes/decorators | `createMiddleware`, `wrapModelCall`, `wrapToolCall`; not a mechanical spelling substitution. [Python tools](https://docs.langchain.com/oss/python/langchain/tools.md), [TS middleware](https://docs.langchain.com/oss/javascript/langchain/middleware/custom.md) |
| Runtime requirements documented on access date | Python 3.10+; provider integrations are separate packages | Node.js 22+; Bun section says 1.0.0+; provider integrations separate. [Python install](https://docs.langchain.com/oss/python/langchain/install.md), [TS install](https://docs.langchain.com/oss/javascript/langchain/install.md) |
| MCP adapter generation | `langchain.mcp.MCPAdapter`, `list_tools()`; `langchain[mcp]>=1.4.0`, **beta** | `MCPAdapter` from `@langchain/mcp-adapters`, `listTools()`; docs require **2.0+**. [Python MCP](https://docs.langchain.com/oss/python/langchain/mcp/index.md), [TS MCP](https://docs.langchain.com/oss/javascript/langchain/mcp/index.md) |

Python v1 replaces `langgraph.prebuilt.create_react_agent` with `langchain.agents.create_agent`, moves hooks to middleware, and moves legacy chains/retrievers to `langchain-classic`. Do not silently mix old tutorials with v1 APIs. [v1 migration](https://docs.langchain.com/oss/python/migrate/langchain-v1.md)

The Python versioning page designates LangChain/LangGraph 1.0 as LTS and describes Deep Agents as pre-1.0 with possible minor-version API changes. That is not a claim of feature parity between languages. Recent documented Python feature floors include interrupt response schemas (`langgraph>=1.2.12`), conditional HITL (`langchain>=1.3.3`) and per-call HITL (`langchain>=1.4.6`). Verify each against the target package; do not transpose these floors to TS. [Versioning](https://docs.langchain.com/oss/python/versioning.md), [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts.md), [HITL](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md)

## 3. Route tools, skills and subagents separately

| Need | Choose | Why / boundary |
|---|---|---|
| Execute a capability with structured arguments/results | Tool | Tools are callable functions with defined inputs/outputs. Tool execution is not the same as loading instructions. [Tools](https://docs.langchain.com/oss/python/langchain/tools.md) |
| Teach a procedure or supply domain context while retaining one controller | Skill | Deep Agents loads name/description, then the body and supporting resources on demand. [Skills](https://docs.langchain.com/oss/python/deepagents/skills.md) |
| Isolate a large investigation or specialist execution | Subagent | Supervisor receives the result rather than every intermediate tool response. Defaults and inheritance must be checked, not assumed. [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents.md) |
| Classify once, dispatch independent domains, synthesize | Router | A routing step sends inputs to one or more specialists. [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent/index.md) |
| Change active conversational responsibility as state changes | Handoff | State drives control/configuration changes; this differs from a helper returning to its caller. [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent/index.md) |
| Enforce sequencing or combine deterministic checks with agents | Workflow | Workflows have predetermined paths; agents select their own process. [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents.md) |

**Recommendation:** start with one controller, the minimum applicable skill, and currently available authorized tools. Use the existing delegation gates for genuine independent slices. A skill is neither a new agent nor a permission grant. Routing must consider the requested outcome and current phase, not merely keyword matches.

### Middleware and dynamic tools

Two different cases exist in Python: **filter pre-registered tools** before the model call, or **register newly discovered tools** at runtime. The latter needs both `wrap_model_call` (expose schema) and `wrap_tool_call` (resolve execution). Exposing a name without an executable implementation is incomplete. [Dynamic tool selection](https://docs.langchain.com/oss/python/langchain/tools.md)

**Recommendation:** apply the same separation without SDK code: discover the host's real inventory → read the selected schema/skill → choose the smallest relevant authorized surface → execute through the host → record evidence. Availability filtering improves context; enforcement still belongs at the execution boundary. Neither a tool description nor an LLM selector proves permission.

## 4. State, context and persistence scopes

| Data | Vendor scope | Recommendation for existing loops |
|---|---|---|
| Runtime context | Per-invocation immutable configuration (e.g. verified caller identity); distinct from persisted thread state. [Tools: context](https://docs.langchain.com/oss/python/langchain/tools.md) | Carry fixed root, ownership, permissions and acceptance contract separately from a mutable plan. |
| Thread | Accumulated graph state across runs keyed by `thread_id`; new input can merge into that state. [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers.md) | Give each goal/work unit an unambiguous local identity; unrelated goals must not inherit each other's working evidence. |
| Checkpoint | State snapshot at a super-step boundary; pending writes preserve successful sibling work on failure recovery. [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers.md) | Existing prompt/check logs are an audit trail, **not** a LangGraph checkpointer or exactly-once executor. |
| Store | Cross-thread key-value data in application-defined namespaces; in-memory implementations are not restart-durable. [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence.md), [Stores](https://docs.langchain.com/oss/python/langgraph/stores.md) | Promote only reviewed reusable lessons into maintained project references. Keep per-run diagnostics in the goal trail. |
| Skill / memory files | Skills load progressively; configured memory files can load at startup. Backend/namespace controls persistence and audience. [Skills](https://docs.langchain.com/oss/python/deepagents/skills.md), [Memory](https://docs.langchain.com/oss/python/deepagents/memory.md) | Keep critical invariants in fixed instructions; put task-specific procedures behind precise pointers. Treat learned material as evidence, not new authority. |

Deep Agents distinguishes context compression (offload/summarize) from isolation (delegate heavy context) and long-term memory. A virtual filesystem may be backed by state, disk or a store; the word “filesystem” alone promises neither durable storage nor process isolation. [Context engineering](https://docs.langchain.com/oss/python/deepagents/context-engineering.md), [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview.md)

## 5. Interrupt, resume and replay safely

Python invocation modes are deliberately distinct. Reusing a thread ID alone does not select a resume operation. [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers.md)

| Intent | Python graph input | Critical effect |
|---|---|---|
| New conversational input | `graph.invoke(input, config)` | Applies reducers to saved state, starts at entry point. |
| Recover unfinished work after error | `graph.invoke(None, config)` without old `checkpoint_id` | Retries unfinished work from latest checkpoint. |
| Answer human interrupt | `graph.invoke(Command(resume=answer), config)` | Same thread; interrupted node starts again from its beginning. |
| Replay history | `graph.invoke(None, snapshot.config)` | Executes nodes after the selected checkpoint again, including external calls. |

`interrupt()` needs a checkpointer, thread ID and serializable payload. Code before it may execute again. Time travel is not cached playback or rollback: replay can repeat model/API calls and interrupts; a fork preserves original history. Functional API resume restarts the entrypoint and restores completed task results, but a task that did not finish can run again. Use idempotency keys or reconcile existing effects. [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts.md), [Time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md), [Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api.md)

Human approval middleware offers `approve`, `edit`, `reject`, and `respond`. `respond` supplies a successful synthetic tool response for an ask-user tool; it is **not** denial of a side effect. Default batched decisions follow action order; newer per-call mode keys decisions by interrupt ID. Conditional approval predicates run again on resume and must be stable for the same call. [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md)

**Recommendation:** capture the precise pending action and immutable arguments before an approval boundary; execute only after that action is authorized. On a timeout, inspect evidence before retrying a non-idempotent effect. Never turn “unknown outcome” into “failed, safe to repeat.” Existing deepmodebot approval policy remains authoritative; this research creates no new automatic approval path.

## 6. MCP adapters are not the protocol

Python's current beta adapter replaces the older standalone `MultiServerMCPClient`; migration is not just a rename (`get_tools` → `list_tools`, config/lifecycle changes, old prompt/resource helpers not exposed). TS 2.x still uses the separate `@langchain/mcp-adapters` package. [Python migration](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters.md), [TS MCP](https://docs.langchain.com/oss/javascript/langchain/mcp/index.md)

Python-discovered tools retain the client and can reopen connections after discovery's context exits; keeping the adapter context open holds a connection across calls. TS's documented pattern keeps the adapter open while the agent runs and closes it in `finally`. Do not copy lifecycle assumptions across languages. Python multi-server config prefixes tools; one aggregate config shares a protocol era, while `ClientGroup` supports independently negotiated connections. [Python connections](https://docs.langchain.com/oss/python/langchain/mcp/connections.md), [TS MCP](https://docs.langchain.com/oss/javascript/langchain/mcp/index.md)

**Recommendation:** use the host's already mounted tools when sufficient. Adding an SDK adapter, new server process, remote endpoint, credentials or telemetry is a separate change. Consult [protocols](protocols.md) for trust/auth/transport requirements; a LangChain adapter is an integration layer, not a waiver of them.

## 7. Apply to bounded loops without adopting the stack

**Recommendation — conceptual mapping, not new runner behavior:**

```text
fixed contract + current evidence
    → select phase and relevant skill/tools
    → one bounded authorized work step
    → runner-owned acceptance check
    → pass: finish | fail with new evidence: revise plan | cap/stall: stop
```

Use the existing [self-authoring playbook](../../deepmodebot/references/playbooks/self-authoring.md) unchanged as the authority for goal fields, protected checks, caps, trail and promotion. Borrow graph-style explicit transitions, middleware-style pre-action checks, skill-style progressive disclosure, and trace-style evidence. A working-plan revision can change the method; it cannot alter frontmatter, protected checks, root, permissions or budgets. This mapping installs nothing, enables no API billing, schedules no background service, and gives the local trail no undocumented recovery guarantee.

Suggested routing examples (recommendations):

- “Choose `create_agent` or `StateGraph` for a refund approval workflow” → this reference §§1–5; inspect language/version and side-effect boundaries before suggesting code.
- “Resume a failed graph without sending the email twice” → §§4–5; distinguish failure recovery from historical replay and reconcile the external action.
- “Load skills only when relevant and expose fewer tools” → §3 plus [self-authoring](self-authoring.md); keep policy outside mutable skill content.
- “Keep repairing this project until checks pass” → existing bounded self-authoring playbook; use §7 as design rationale, not as permission to add LangGraph.
- “Port `MultiServerMCPClient` to TypeScript” → §§2,6 plus [protocols](protocols.md); Python's new beta API is not the TS package contract.
- “Add LangSmith tracing/deploy this agent” → §8; separate research from external setup, data upload and paid infrastructure.

## 8. Evaluation, observability and deployment

AgentEvals distinguishes deterministic trajectory matching (`strict`, `unordered`, `subset`, `superset`) from LLM judging. The deterministic comparison can be cost-free; producing a trajectory with a real model need not be. LangSmith distinguishes offline datasets/experiments from online evaluation of live traces, and supports code, human and model evaluators. [Agent Evals](https://docs.langchain.com/oss/python/langchain/test/evals.md), [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation.md)

**Recommendation:** score route choice, required reads, allowed tool use, approval ordering, cap/stall behavior and actual outcome separately. Test the minimal expected constraints rather than freezing harmless read order. Convert real failures into local regression cases. Do not substitute a judge's “done” for the runner's protected acceptance check.

LangSmith tracing captures prompts, inputs/outputs and tool/model interactions; the documented activation needs an account/API key and explicit tracing configuration. [Observability](https://docs.langchain.com/oss/python/langchain/observability.md)

Agent Server offers Cloud, hybrid, self-hosted control plane and standalone hosting. Its overview says Cloud requires Plus or Enterprise; standalone requires PostgreSQL, Redis and a LangSmith license. Running the OSS graph/Deep Agents SDK yourself is not synonymous with running licensed Agent Server. [Agent Server](https://docs.langchain.com/langsmith/deployment.md), [Deep Agents SDK](https://docs.langchain.com/oss/python/deepagents/overview.md)

**Recommendation:** retain local traces by default, redact sensitive data, and obtain explicit scope for external tracing or deployment. No prices, package latest versions, production guarantees or SDK compatibility were verified by this research.
