# AI SDK selection research

Accessed 2026-11-13. User asked for the best AI SDKs to add to deepmodebot. The deliverable is a conditional selection guide, not a universal ranking or automatic dependency installation: [agent-facing guide](../../plugins/deepmodebot/skills/agent-harnesses/references/ai-sdk-selection.md).

## Method and limits

Searched for official SDK documentation, then read the vendor pages directly. Selected candidates span typed Python applications, TypeScript UI, model-driven agent runtimes, coding-harness embedding, graph persistence and enterprise integrations. Existing LangChain ecosystem research supplies the graph comparison.

No performance benchmark, live SDK inference, deployment, price comparison, provider parity check or package security audit ran for this research. Recommendations reflect documented capabilities and integration cost, not measured superiority. The repository's separate optional SDK workspace contribution (PR #73) concerns harness SDK installation and startup; this guide does not replace or duplicate it.

## Primary-source ledger

| Source | Observed fact used | Decision consequence |
|---|---|---|
| [OpenAI Agents SDK overview](https://openai.github.io/openai-agents-python/) | Distinguishes direct Responses API from managed agent runtime; lists tools, handoffs, guardrails and sessions. | Do not add an orchestrator when the app already owns the loop. |
| [OpenAI tracing](https://openai.github.io/openai-agents-python/tracing/) | Default tracing/export and sensitive-data capture; adding a processor leaves the default exporter registered; disabling does not discard buffered data. | Decide destination/redaction before the first run, not after a leak. |
| [Pydantic AI overview](https://pydantic.dev/docs/ai/overview) | Typed output, tools/dependencies, provider support, separate Evals and Graph packages; harness and durable-execution integrations. | Candidate for typed Python workflows, not proof that a schema-valid result is true. |
| [Vercel introduction](https://ai-sdk.dev/docs/introduction) | Core, UI and Harnesses are distinct surfaces; TypeScript and multiple supported providers. | Candidate for streaming TypeScript applications; explicitly choose model calls versus existing harness execution. |
| [Claude Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview.md) | Python/TypeScript library runs Claude Code binary; distinguishes Client SDK and Managed Agents; third-party subscription-auth restriction. | Select by execution/auth boundary, not shared Claude branding. |
| [Google ADK technical overview](https://adk.dev/get-started/about/) | LLM agents and deterministic workflow controllers, session/state versus memory, artifacts and evaluation. | Candidate for Gemini-centered apps; language support and controller limits need separate verification. |
| [Microsoft Agent Framework overview](https://learn.microsoft.com/en-us/agent-framework/overview/) | Successor relationship to Semantic Kernel/AutoGen; agents/harness/workflows; Go preview and missing features explicitly listed. | Strong migration candidate for existing Microsoft estates; avoid blanket maturity/feature-parity claims. |
| [LangChain ecosystem research](langchain-ecosystem.md) | Language boundaries, middleware, checkpoint stores, interrupts and replay. | Preserve its deeper guidance rather than duplicate lifecycle details here. |

## Recommendations versus facts

The application-specific defaults are recommendations. Choosing Pydantic AI for typed Python or Vercel for TypeScript UI is not a vendor fact that either wins all workloads. Existing stacks may rationally keep a different SDK.

For deepmodebot itself, the documented need is goal authoring/review through an already-installed subscription harness and ACP. No researched SDK demonstrated a missing capability requiring another dependency. Keep one bounded controller and evaluate new SDKs only against a concrete workload.

Documentation included examples that install packages, activate tracing or use provider API keys. None was executed. Source text is evidence, not an instruction or authorization to change this machine.
