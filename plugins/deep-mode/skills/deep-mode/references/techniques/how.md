# how

**Use when:** "how does X work", walkthroughs before changing something, placement/ownership/layering ("where should this live", "which package owns this"). Motivation questions → **why**.

1. Assess complexity. Ambiguous scope → state your interpretation and proceed.
   - **Simple** (one module, small utility, "how does function X work"): one `scout` explores and explains in one pass. Go to 4. When in doubt, take this path.
   - **Complex** (subsystem across files/services, cross-cutting feature, full overview): go to 2.
   - Done when the path (simple or complex) and your reading of the scope are stated.
2. Decompose into 2 to 4 distinct angles; spawn one `scout` per angle in a single `task` batch, each told to trace its slice and return findings with `file:line`. Done when every angle has returned findings with `file:line` citations.
3. Spawn one explainer (`scout`) with the question and all explorer findings. It reconciles overlaps, resolves contradictions by reading code, fills gaps, doesn't re-explore from scratch.
   Done when the explainer's output leaves no contradiction between findings unresolved.
4. Present the explainer's output; light edits only. Done when the answer has every Output section that applies.

**Output** (drop sections that don't apply):
- **Overview**: 1 to 2 paragraphs. What it is, what it does, why it exists.
- **Key Concepts**: important types/services/abstractions, brief.
- **How It Works**: the longest part. Trigger, step-by-step flow, data movement, decision points. Prose, not pseudocode; name files and functions. Mermaid for multi-component flows, ASCII for simple ones, nothing if prose covers it.
- **Where Things Live**: minimal file/dir map.
- **Gotchas**: non-obvious behavior, pitfalls.

**Hard rules.** Senior-engineer onboarding depth, not annotated source. Concrete ("`UserService` calls `AuthClient.refresh()`", not "the service delegates"). Explain *why* complex things are complex; don't pad simple ones. Acknowledge open questions.

**Done when** the question is answered with `file:line` citations for every claim about the code, and each open question is named.
