# foundational-thinking

Group: core. When: before writing logic — choosing core types and data structures, sequencing scaffold vs feature, asking what concurrent actors share.
- **Rule.** Structural decisions protect option value; code-level decisions protect simplicity. Data structures first: define core types early, trace every access pattern, pick structures that match the dominant paths.
- **Code level.** DRY the structure, not every line. Types and data models converge. Three similar statements beat a premature abstraction. Explicit over clever. Test behavior and edge cases, not line counts.
- **Concurrency corollary.** Before sharing state between actors, ask "what if another actor modifies this concurrently?" If not "nothing", isolate.
- **Scaffold first.** "Does every subsequent phase benefit from this existing?" CI, linting, test infra, shared types are scaffold. Setup before features, tests before fixes. Small, single-purpose commits.
- Each increment lands a coherent abstraction or deepens one. Subtraction comes before scaffolding.
- **Anti-patterns.** Logic before data shape; spreading a new capability across callers as special-case coordination.
