# why

**Use when:** "why does X work this way", "why did we pick Y", design rationale, regressions, postmortems, data-backed thresholds. Runtime behavior → **how**.

Posture: careful, cautious, precise investigator. Honest about known vs inferred.

1. **Target and question.** Target = code, pattern, feature, or decision. Vague → best guess from context (open files, recent edits, discussion); state it and proceed.
2. **Code anchor** (inline, before spawning): paths + line ranges, key symbols, recent commits, PR numbers, linked tickets. Run `git blame -L <s>,<e> <file>`, `git log --follow -p -- <file>`, `git log --oneline -20 -- <file>`, `git log -1 --format=%B <sha>`, then `gh pr view <n> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews` for substantive PRs. The anchor goes to every investigator.
3. **Discover sources.** List the MCP servers/tools this omp session exposes (`mcp://` resources, tool list) and map each to one category: (1) source control, (2) issue tracker, (3) long-form docs, (4) team chat, (5) infra observability, (6) error tracking, (7) product analytics warehouse. Source control is always available via git/`gh`; GitHub Issues via `gh`/`issue://` counts for (2). Record ambiguous classifications.
4. **Spawn investigators** in one `task` batch, one per available category, each owning exactly one source. Default to full coverage: document the null, don't skip the search. Each gets the anchor, the user's question, and its category's search focus; if the target looks defensive (null checks, retries, timeouts, rate limits, flags, OOM handlers), add an incident/postmortem search. Investigators write nothing.
   Best-at: source control = review-time rationale; tracker = product/business forcing function; docs = long-form design rationale; chat = deliberation that never reached a doc; observability = runtime reality behind timeouts/retries/limits; error tracking = exceptions behind defensive code; analytics = flag/experiment/data-migration/"where did this number come from".
   - Skip a category only with a written reason in Sources Consulted: no tool available (a *gap*, not a choice), or provably irrelevant (high bar). Answering inline is allowed only for a single-commit target whose PR fully answers it, after confirming every other search would be redundant; say so.
5. **Synthesize** with one subagent given findings (incl. nulls and skips), anchor, question, and the epistemics below. It spot-checks citations and modifies nothing.
6. **Present** without rewriting confidence language.

**Epistemics tiers** (every claim sits in one):
- **Direct** — an author *wrote* why (PR body, ticket, comment, doc, chat). Plain, cited: "This exists because X."
- **Supported** — several indirect items converge. "The evidence points strongly to X: [items]."
- **Inferred** — your reading; chain explicit, hedged: "Given A and B, C seems likely because D."
- **Speculative** — thin; other stories fit. "One possibility is X, but we have no direct evidence."
- **Unknown** — searched, not found; name exactly what was searched with what queries.
Confidence words ("because", "was designed to", "fixes", "the team decided") need an adjacent citation. Banned: "obviously", "clearly", "of course", "just", "I think". Never cite code as evidence of its own intent. Don't rationalize messy history, don't treat absence of evidence as evidence of absence, don't rubber-stamp a hypothesis embedded in the question. Surface contradictions; don't pick the tidier one. A missing "What We Don't Know" is suspicious.

**Output:** The Question · The Code in Question · What We Found (`[Direct]`/`[Supported]`, cited) · What We Can Reasonably Infer (`[Inferred]`, hedged, chain shown) · Competing Hypotheses (for / against-or-missing) · What We Don't Know (specific gaps, unavailable sources, people who'd know) · Sources Consulted (one line per category, incl. empty and skipped with reason) · Confidence Summary (1–2 sentences). If the question precedes a change, add a **Preserve / Change / Avoid / Risk** constraint set.

**Failure mode:** recency bias — the latest commit isn't authoritative; trace back.
