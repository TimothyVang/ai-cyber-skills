# redesign-from-first-principles

Group: core. When: integrating a new requirement into an existing design.
- **Rule.** Don't bolt it on. Redesign as if the requirement had been foundational from day one.
- **Steps.** Read all affected files and understand the current design. Ask "writing this from scratch with this requirement, what would we build?" Propagate through every reference: types, docs, examples, rationale. Think about the whole redesign, deliver it incrementally.
- **Distinct from** attack-the-premise (that questions a fact the current design assumes).
- **Anti-patterns.** A new flag/branch grafted onto a shape that never anticipated it; updating code but not docs/examples/types.
