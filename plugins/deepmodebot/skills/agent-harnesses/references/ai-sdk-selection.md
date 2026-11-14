# Choose an AI SDK by the missing capability

**Checked 2026-11-13 against the primary documentation below.** These are use-case recommendations, not measured speed, quality or cost rankings. No SDK inference, deployment or compatibility matrix was exercised. Recheck the language-specific docs and lockfile before implementation.

## Choose the layer first

1. **A model call:** use the application's existing provider client. A multi-agent framework is unnecessary for extraction or one response when the application already owns state and tool dispatch.
2. **A coding harness:** retain the installed CLI/SDK and its permission model. ACP drives an agent; MCP exposes tools. Neither protocol creates a sandbox. Read `references/protocols.md`.
3. **An application agent:** choose one owner for the model/tool loop. Add a graph or durable engine only for explicit transitions, parallel coordination, persisted waiting or recovery that the existing runtime cannot supply.
4. **Evaluation or tracing:** choose those independently. A trace is evidence, not acceptance; sending traces to a vendor is a separate data/authorization decision.

For deepmodebot's own subscription-backed goal drafting and review, **keep the existing harness and ACP**. An SDK comparison is not permission to install packages, introduce API keys, enable external tracing or nest another autonomous repair loop.

## Shortlist by application

| Need | Default candidate to evaluate | Documented reason | Important limit |
|---|---|---|---|
| Typed Python extraction and agent outputs, provider flexibility | **Pydantic AI** | Typed output validation, function tools/dependencies, model providers; separate Evals and Graph packages. [Overview](https://pydantic.dev/docs/ai/overview) | Type/schema validity does not prove the answer, business metric or permission is correct. Provider feature parity still needs a test. |
| TypeScript application with streaming chat UI | **Vercel AI SDK** | Core covers generation, structured output, tools and agents; UI covers chat hooks; Harnesses wraps existing coding harnesses. [Introduction](https://ai-sdk.dev/docs/introduction) | Choose Core versus Harnesses explicitly; do not run two competing loops or assume every provider supports every surface. |
| Small code-first agent runtime around OpenAI-oriented tools, handoffs and sessions | **OpenAI Agents SDK** | Agents, function tools, handoffs, guardrails, sessions and tracing; direct Responses API remains an alternative when the app owns the loop. [Overview](https://openai.github.io/openai-agents-python/) | Tracing is enabled by default and may include model/tool inputs and outputs. Review data destinations before the first call. |
| Explicit durable graph state, approval pauses or replay | **LangGraph**, with LangChain only where useful | Low-level graph execution, persistence and interrupt/resume semantics; LangChain supplies higher-level agent middleware. | Read `references/langchain-ecosystem.md`; checkpoints do not make external effects exactly-once. |
| Python/TypeScript application embedding Claude Code's execution harness | **Claude Agent SDK** | Runs the Claude Code binary with built-in tools, permissions, hooks and sessions. [Overview](https://code.claude.com/docs/en/agent-sdk/overview.md) | This is not just the Claude API client. Third-party products cannot assume claude.ai subscription authentication is permitted. |
| Gemini-centered agent app needing explicit workflows, developer UI and evaluation | **Google ADK** | LLM agents plus sequential/parallel/loop workflow agents, sessions/state, artifacts and evaluation tools. [Technical overview](https://adk.dev/get-started/about/) | Verify the selected language's feature support and model adapter. A `LoopAgent` is another controller to bound, not a reason to bypass the host's limits. |
| Existing Microsoft/.NET estate or migration from Semantic Kernel/AutoGen | **Microsoft Agent Framework** | Agents, harness, explicit workflows, providers and middleware; documented successor to Semantic Kernel and AutoGen. [Overview](https://learn.microsoft.com/en-us/agent-framework/overview/) | Language maturity differs: the inspected page marks Go public preview and lists missing features. Check the chosen package, not a framework-wide GA claim. |

These candidates overlap. Existing dependencies and demonstrated failure modes win over novelty. Keep an older framework when it meets the contract and migration cost exceeds a proven benefit; a vendor's successor announcement is not a migration mandate.

## Apply the choice without guessing

Record a small decision packet:

- User outcome, current language/runtime and existing dependencies.
- Missing primitive: typed result, streaming UI, tools, coordination, durable state or harness embedding.
- Exact package/version and authoritative language-specific page; separate feature floor from installed version.
- Authentication mode, data destinations and who owns tools, retries, state, approvals and shutdown.
- One consumer-visible proof, one denial case and one timeout/recovery case; same workload and model when comparing SDKs.
- Baseline, target, observed result, adoption/rejection and rollback. Do not manufacture benchmark numbers.

Use the smallest adapter that passes those checks. If a material deployment, data-residency or budget preference is unknown, ask that question; discover repo facts yourself. Never substitute a different model or provider merely to make the sample work.

## Data and execution traps

- OpenAI Agents SDK's [tracing guide](https://openai.github.io/openai-agents-python/tracing/) documents default export and sensitive-data capture. Disable or replace tracing before a run when external export is not approved. Turning tracing off later does not erase buffered records; adding a redaction processor does not remove the default exporter.
- Claude's [SDK overview](https://code.claude.com/docs/en/agent-sdk/overview.md) distinguishes local Agent SDK, direct Client SDK and hosted Managed Agents. Their execution and authentication boundaries are not interchangeable.
- Provider fallback, automatic retries and multi-agent calls must stay inside the user's selected model, spend and side-effect contract. Documentation advertising a fallback is not approval to use it.
- Tool arguments and structured model outputs are untrusted input. Validate types and domain constraints before effects; apply permissions at execution, not merely by hiding a tool from the model.
- Persisted sessions, checkpoint stores and durable queues preserve different things. Reconcile an unknown external outcome before replay. A successful SDK return is not proof of the human's goal.
- A local SDK initialization/import check proves startup only. Stub/offline models are useful tests, not evidence of live inference, tool enforcement or production reliability.

**Done when** the decision names the application-specific winner, the rejected alternative and evidence for the tradeoff; implementation claims include a pinned-package live proof. Research-only work must say that proof has not run.
