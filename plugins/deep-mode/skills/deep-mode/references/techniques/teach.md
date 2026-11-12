# teach

**Use when:** "teach me this", "help me really understand X", explain a change or subsystem. Goal is understanding, not changes. Learning a topic over several sessions (a course, lessons, quizzes, a learning workspace) is the **course** technique (`references/techniques/course.md`) instead.

1. Decide the few things they should walk away understanding, chosen from why they're asking (changing, reviewing, debugging, new) and what they know — read from the conversation, not quizzed. Depth goes where their question is.
2. Orient yourself in the code, then run **how** and **why** in parallel; don't redo their work. Size to the question. Keep **why** narrow by default (scoped question, git plus a source or two) so it records skipped categories; widen only when reasons are the point.
3. Start with a plain definition (common name if it has one), tie it to this case ("in X, we use this to…"), then how it works, deeper reasons, edge cases. Each part: the problem it solves and the actual mechanism. Smallest complete answer first (a sentence or two), then stop; add layers when asked.
4. Keep it a conversation: offer to go deeper, follow their lead. No quizzes, no "Pause", no "say it back", no flagging parts as tricky. One-shot with no live human → deliver cleanly, offer depth at the end.
5. Show, don't only tell. Open the diff/code/debugger when fastest. For 3+ moving parts, draw a *series* of diagrams, each redrawing the last and adding one part (A→B; then +C; then the return edge). Mermaid when labels carry the meaning; for spatial ideas (layout, overlap, before/after) use an image tool if the session has one. A single simple point needs no figure.

**Hard rules.** Write through **unslop**: plain spoken English, tight not terse, concrete mechanism over metaphor or preview. Sentence case, no em dashes, prefer periods, ≤2 commas per sentence, one name per concept, no mirror sentences, no framing labels ("key insight", "at its core", "TL;DR"). Keep **why**'s confidence hedges intact.

**Output:** the explanation itself, never a report about it. Lead with the main point; end with threads worth chasing via how/why.
