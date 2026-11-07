# outcome-oriented-execution

Group: core. When: planned rewrites and migrations with explicit phase boundaries.
- **Rule.** Optimize for the verifiable end state, not smooth intermediate states. Intermediate breakage is acceptable when planned, scoped, and reversible.
- **Guardrails.** Only for planned rewrites/migrations with phase boundaries. Declare where temporary breakage is acceptable. Keep high-signal checks on actively touched areas while migrating. Require full static and runtime verification at plan completion.
- **Anti-patterns.** Temporary compatibility code that becomes long-lived debt.
