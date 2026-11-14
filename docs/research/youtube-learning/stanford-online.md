# Stanford Online: engineering agents beyond the model loop

## Scope and provenance

Canonical channel: [Stanford Online, @stanfordonline](https://www.youtube.com/@stanfordonline), channel ID `UCBa5G_ESCn8Yd4vw5U-gIcg`. Anonymous, sequential flat discovery captured **3,026 videos, 112 shorts, and 1 stream: 3,139 unique public discoverable items**. The three tab requests succeeded with empty error logs. This does not include a guarantee about private, deleted, unlisted, inaccessible, or later-added content.

A reproducible, **title-based** relevance rule identified **1,668 CS/AI candidates: 1,603 videos and 65 shorts**. These candidates have local catalog pages and a field-status CSV.
The full 3,139-item machine-readable catalog retains matches and non-matches, original tab/rank, and exact regex rules. This is **not full-content classification**, proof of exhaustive topical recall, or a claim that 1,668 videos were watched.
Explicit CS course codes, AI/ML/LLM techniques, software/computing/data-science terms, robotics, and selected formal/safety/learning-based control terms drive matching.
Ambiguous titles can produce false positives, while vague titles can hide relevant material. Broad AI-business items can match without being technical engineering lectures.

The deep read deliberately stops at the requested lecture and three CS329Z companions from the [official course schedule](https://cs329z.stanford.edu/):

| Source | Captured records / nonempty speech | Duration | Final speech starts | Final panel record starts |
|---|---:|---|---|---|
| [DSPy vs. LangGraph: AI Agent Frameworks Explained — Lecture 5, Michael Ryan](https://www.youtube.com/watch?v=q0Q-Hy8TTps) | 590 / 590 | 1:17:14 | 1:17:05 | 1:17:05 |
| [What Are AI Agents? Agentic Systems Explained — Lecture 1, Diyi Yang](https://www.youtube.com/watch?v=DGI4vucR71w) | 588 / 587 | 1:09:36 | 1:09:21 | 1:09:31, timestamp only |
| [LLMs for Agent Builders: Context Engineering — Lecture 2, Michael Ryan](https://www.youtube.com/watch?v=Vr1NzH8bT44) | 595 / 595 | 1:17:53 | 1:17:37 | 1:17:37 |
| [How AI Agents Use Tools: Function Calling & MCP — Lecture 4, Diyi Yang](https://www.youtube.com/watch?v=s0S38lz6O7M) | 596 / 596 | 1:19:16 | 1:19:04 | 1:19:04 |

All **2,369 captured panel records / 2,368 speech segments** were read. Start times are available, not segment ends: the final speech begins 9, 15, 16, and 12 seconds before the respective durations, so complete ending coverage is unverified. The foundations transcript's final timestamp-only record is retained without invented speech. The other three transcripts begin at 0:05, leaving opening coverage unverified too. Auto-captions can misrecognize names, model identifiers, and numbers.

Discovery and transcript captures are dated **2026-11-14 UTC**; no local-date conversion is assumed. Watch date texts are Nov 13, Nov 9, Nov 10, and Nov 12 respectively. The official schedule places these classroom sessions on Oct 7, Sep 23, Sep 28, and Oct 5; classroom and upload dates are separate fields, not a fabricated date correction.

Only **four watch-detail fetches and four transcript reads** were performed. Other items were not probed for captions. Raw responses, captions, timed renderings, fuller lessons, and catalog artifacts remain local under `.scratch/youtube-learning/stanford-online/`; this document is original paraphrase. No target-content commands, notebook execution, paid model calls, signed-in browser session, or independent source-code/production audit formed part of this research. The [official Lecture 5 notebook repository](https://github.com/cs329z/lecture5-frameworks) is a source reference, not a reproduced experiment.

## Findings

### 1. Choose control flow before choosing a framework

Ryan separates three engineering inputs: **system, data, and evaluation**. A model loop can exist without a dataset or metric; evidence-driven improvement cannot ([Lecture 5, 2:54–4:12](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=174)). His agency spectrum distinguishes application-controlled workflows from model-selected actions ([4:29–5:25](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=269)). Yang makes the same distinction and shows that fixed workflows can still be powerful ([Lecture 1, 56:00–57:55](https://www.youtube.com/watch?v=DGI4vucR71w&t=3360)).

**Transfer:** start with the smallest sufficient control surface. Extracting event details into a calendar can be a bounded workflow; managing a calendar in an open-ended conversation may justify more agentic decisions ([Lecture 5, 1:08:05–1:08:46](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=4085)). “Agent” is not an automatic quality upgrade.

The foundations diagram separates model, reasoning/planning, memory, tools, and environment. Yang explicitly describes it as conceptual, cautioning against treating its arrows as authoritative wiring ([Lecture 1, 23:20–26:16](https://www.youtube.com/watch?v=DGI4vucR71w&t=1400)). It is a diagnostic map, not an implementation specification.

### 2. A typed contract constrains shape, not meaning or permission

The first DSPy sentiment example produces inconsistent casing; a typed literal narrows the permitted labels ([Lecture 5, 12:00–14:36](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=720)). Signatures, descriptions, and prompt-bearing docstrings convey semantic requirements; an ambiguous date is not resolved merely by assigning a date type ([16:03–18:35](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=963)). The lecture explicitly discusses the surprising boundary where documentation affects execution ([21:32–23:25](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1292)).

Ryan describes deterministic adapter formatting, output parsing, fallback, and eventual errors, but does not exercise every failure path ([14:44–15:49](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=884); [19:52–20:04](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1192)). Structured decoding is also explained in Lecture 2 ([1:05:21–1:10:03](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=3921)).

**Transfer:** test semantic correctness, missing-value policy, and authorization separately from serialization. A valid JSON object is not proof of a correct event, a calibrated confidence score, or permission to write it.

### 3. DSPy and LangGraph offer different, composable seams

The same toy-calendar task appears in both frameworks. DSPy composes signatures/modules with ordinary Python policy; LangGraph expresses shared state, nodes, and conditional edges. Both can exit without writing when required event details are missing ([Lecture 5, 23:36–26:19](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1416); [42:20–50:02](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=2540); [51:10–51:18](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=3070)). The one-hour duration default is the demonstrator's application choice, not a library guarantee.

Ryan emphasizes DSPy's program/optimization orientation and LangGraph's explicit orchestration, and says a DSPy call can be a graph node ([50:05–50:52](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=3005); [52:38–53:28](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=3158)). He discloses prior DSPy work and less LangGraph familiarity ([9:12–9:29](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=552); [46:12–46:22](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=2772)). His uncertain answer about LangGraph optimizers is not treated as a verified current API limitation.

**Transfer:** choose a seam that makes policy and state inspectable, rather than declaring a universal framework winner. A rendered graph does not itself establish persistence, distributed execution, correct retries, or exactly-once effects.

### 4. The optimization result is useful precisely because its limits are visible

The lecture uses **50 synthetic labeled emails: 30 train, 20 test**. Its exact-match metric checks date, start time, and duration, deliberately not event-name quality ([Lecture 5, 27:04–29:57](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1624)). The displayed smaller-model result rises from **11/20 (55%) to 20/20 (100%)** after prompt optimization ([30:31–32:22](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1831)).

The optimization is **cached**, not a freshly completed subsecond training run. Ryan estimates minutes and potentially substantial token consumption, without reporting a measured token count ([31:26–32:53](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1886)). He retains train/dev/test discipline and explains cache replay versus nondeterministic uncached generation ([33:04–34:12](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=1984)). He also warns that a hackable evaluation can reward unwanted prompts ([34:27–35:37](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=2067)).

**Transfer:** freeze held-out domain cases, record prompt/model/data/cache versions, and measure cost and latency alongside correctness. Twenty perfect synthetic cases do not establish production generalization or broad equivalence between models. Exact model names are not promoted from uncertain auto-captions into verified identifiers.

### 5. Context and memory are constrained, policy-bearing resources

Lecture 2 contrasts full-attention and fixed-state linear-attention tradeoffs, including hybrid designs ([28:37–35:55](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=1717)). Its pedagogical diagrams are not a numerical implementation or a universal ranking of architectures. An advertised context limit is not evidence that a model will reliably retrieve or aggregate information throughout it.

Ryan distinguishes prefill, sequential decode, and growing KV state, connecting these to first-token and output-token latency ([52:46–57:25](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=3166)). The compute-bound/memory-bound split is a workload explanation, not a hardware-independent guarantee. Inserting evidence at the front can change positional computation and invalidate a reusable prefix; appending in order is generally friendlier to reuse ([1:13:58–1:14:39](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=4438)). This is not a verified hosted API cache/billing contract.

Yang distinguishes episodic logs, semantic summaries, and procedural skills ([Lecture 1, 43:11–46:36](https://www.youtube.com/watch?v=DGI4vucR71w&t=2591)). Both introductory lectures recount the same email-deletion anecdote in which a confirm-before-action constraint was allegedly lost in compression ([Lecture 1, 51:20–53:24](https://www.youtube.com/watch?v=DGI4vucR71w&t=3080); [Lecture 2, 1:15:12–1:15:56](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=4512)). This is not two independent incidents or an independently established root cause.

**Analyst inference:** keep durable authorization outside lossy model-written summaries, recheck it at execution, and evaluate context/memory choices for task quality and constraint preservation. Retrieval and compaction are selection policies, not interchangeable ways to retain everything.

RLMs instead expose input as data in a programmatic environment for selective code/subcall inspection ([Lecture 2, 1:16:06–1:17:20](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=4566)). Lecture 5's demonstration uses roughly 50 emails; a million-email scenario is hypothetical ([38:01–39:36](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=2281)). Neither establishes unlimited context, bounded recursion, or safe code execution.

### 6. Tools require selection, validation, authorization, execution, and evidence

Lecture 4 treats tools as external function interfaces: the model proposes a name and arguments; a separate program executes the operation ([20:53–26:58](https://www.youtube.com/watch?v=s0S38lz6O7M&t=1253)). Hallucinated parameters and wrong-but-existing APIs remain possible ([28:36–29:41](https://www.youtube.com/watch?v=s0S38lz6O7M&t=1716); [56:12–57:25](https://www.youtube.com/watch?v=s0S38lz6O7M&t=3372)).

Toolformer's candidate-call execution and continuation-loss filtering are explained as a learning method, not a runtime safety check ([31:39–40:57](https://www.youtube.com/watch?v=s0S38lz6O7M&t=1899)). Syntax-tree checks later distinguish nonexistent API hallucination from incorrect use of a real API; validity still does not prove correct intent or authorized effects ([59:50–1:01:21](https://www.youtube.com/watch?v=s0S38lz6O7M&t=3590)). These are narrated paper methods, not reproduced training runs.

The MCP discussion explains hosts, per-server client connections, servers, discovery schemas, and invocation arguments ([1:09:18–1:12:32](https://www.youtube.com/watch?v=s0S38lz6O7M&t=4158)). The lecture's REST/function-calling/MCP taxonomy is not a claim that these are mutually exclusive replacements, that MCP eliminates JSON schemas, or that protocol conformance provides authorization automatically. Host/runtime code handles protocol execution; a model-proposed call is not the transport implementation.

A course-LMS illustration separates inbound access checks from outbound backend credentials, with posting grades requiring different authority from reading assignments ([1:13:07–1:15:01](https://www.youtube.com/watch?v=s0S38lz6O7M&t=4387)). **Transfer:** enforce least privilege and credential separation in executable boundaries. The illustration does not establish that every MCP server—or the actual course LMS—implements these protections correctly.

### 7. Observation is not recovery, and recovery is not exactly-once execution

Ryan distinguishes surfacing failures from automatically handling them while acknowledging overlap ([Lecture 5, 8:13–8:57](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=493)). Temporal is explained through activities, workflows, workers, queues, and history. The lecture shows an existing server UI/history with emoji-selection retries before a calendar write; it explicitly skips the code walkthrough ([1:03:15–1:06:18](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=3795)).

**Transfer:** trace model/tool calls, state changes, errors, and outcomes; bound timeouts, retries, and execution budgets ([1:09:29–1:10:11](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=4169)). The UI is not a verified crash/restart test. Durable orchestration alone does not prove external side-effect deduplication or exactly-once writes; safe replay, idempotency, and authority need separate evidence.

The harness tour likewise describes tool surfaces, context histories, terminal lifetime, and memory policies rather than auditing implementations ([55:38–59:31](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=3338)). Task-specialized harness optimization and general-purpose coding-assistant benchmarks have different exposure, which Ryan explicitly cautions about ([59:39–1:00:51](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=3579)). Evaluate the model–harness pair, not just the model or a headline chart.

### 8. Reliability requires more than one successful attempt

Yang separates consistency, perturbation robustness, and legible/recoverable failure from completion accuracy ([Lecture 1, 1:02:06–1:03:41](https://www.youtube.com/watch?v=DGI4vucR71w&t=3726)). Lecture 4 contrasts **pass@k**, at least one success among attempts, with **pass^k**, all k attempts succeeding ([1:17:42–1:18:46](https://www.youtube.com/watch?v=s0S38lz6O7M&t=4662)). They answer different questions; neither substitutes for authorization or privacy testing.

Retrieval coverage, answer correctness, and citation support also differ. More documents can increase retrieval recall without improving the reader, and citations can themselves be wrong ([Lecture 4, 3:38–11:28](https://www.youtube.com/watch?v=s0S38lz6O7M&t=218)). Retrieved documents/tool results remain untrusted evidence, not instructions.

**Transfer:** include missing tools, invalid arguments, wrong-but-valid calls, stale descriptions, denied permissions, conflicting evidence, dependency failures, repeated runs, and representative cost/latency. Ryan's closing recommendation is a custom-domain evaluation with diverse and failure cases, not optimizing an unrelated public benchmark ([Lecture 5, 1:11:28–1:13:40](https://www.youtube.com/watch?v=q0Q-Hy8TTps&t=4288)).

## Visual evidence boundaries

The local archive contains **22 selected actual video-frame PNGs across these four lectures**, captured and visually inspected by the capturing agent, plus **12 official slide-page exports and 3 notebook graph PNGs** as separate source-image exports. These are selected views, not all diagrams/screenshots from the channel, complete lecture recordings, or exhaustive animation traces. Raw third-party visual material remains local; no reuse license is inferred.

Companion scenes have specific limits:

| Source scene | Captured interpretation |
|---|---|
| [Foundations, 26:08](https://www.youtube.com/watch?v=DGI4vucR71w&t=1568) | Conceptual agent components, not authoritative arrow-level wiring. |
| [Foundations, 45:46](https://www.youtube.com/watch?v=DGI4vucR71w&t=2746) | **Episodic-memory slide**, not a semantic-summary diagram; the nearby narration discusses semantic memory. |
| [LLM builders, 33:43](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=2023) | Full versus linear attention tradeoffs. |
| [LLM builders, 56:29](https://www.youtube.com/watch?v=Vr1NzH8bT44&t=3389) | One animated decode-architecture state, not a complete KV-cache execution trace. |
| [Tool use, 38:14](https://www.youtube.com/watch?v=s0S38lz6O7M&t=2294) | Toolformer filtering/objective explanation; paper method, not runtime MCP. |
| [Tool use, 1:10:37](https://www.youtube.com/watch?v=s0S38lz6O7M&t=4237) | MCP host/client/server topology; clients denote connections, not users. |

The [official Lecture 5 slides](https://web.stanford.edu/class/cs329z/slides/lecture05.pdf) and [notebook repository](https://github.com/cs329z/lecture5-frameworks) are distinct source artifacts from video frames. A selected slide or stored graph is not proof of live execution, correctness, security, or benchmark reproducibility.

## Practical synthesis

1. Define task boundaries and executable authority before adding autonomy.
2. Keep durable policy separate from compressed working context.
3. Make model proposals, validation, authorization, actual effects, and recovery observable.
4. Evaluate held-out domain behavior, repeated reliability, failure paths, cost, and latency.
5. Add framework layers or parallel/agentic control only when measured needs justify them.

These are analyst recommendations derived from four bounded reads. The evidence supports the demonstrated toy-calendar expressibility, an illustrative cached optimization result, and explained design tradeoffs—not a complete secure production architecture or universal framework ranking.
