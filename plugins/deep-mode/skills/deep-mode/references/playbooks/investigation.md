# Investigation

Use when: the user wants a cited explanation or a recommendation (how/why/are-we-sure), not a code change. Read-only. You own the answer: plan, route, write.

## Steps
1. Route through the **how** technique (`references/techniques/how.md`); for motivation questions also the **why** technique (`references/techniques/why.md`). Delegate unknown-code mapping to `task` with `agent: "scout"`.
   Done when every claim you plan to make has a file/symbol citation.
2. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only investigation`.
3. Produce the how-shaped output: Overview / Key Concepts / How It Works / Where Things Live / Gotchas. For a choice between alternatives, produce a recommendation with a tradeoffs table instead.
   Done when every section is present, or the recommendation and table are.
4. Apply the **unslop** technique (`references/techniques/unslop.md`) to the reply. Done when unslop's own `Done when` holds for the reply.

## Gates
- Read-only: no edits, no PR, no babysitting, no **architect** unless the investigation precedes a code change.
- If it precedes a code change: hand back to the user and re-route to Bug fix (`references/playbooks/bug-fix.md`) or Feature.
- Wrong premise → push back with reasons; don't answer around it.

## Evidence
- The investigation output with file/symbol citations.
- For "are we sure?" questions: your real judgment and the reasons.
