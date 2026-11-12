# minimize-reader-load

Group: core. When: reviewing or shaping code that's hard to trace.
- **Rule.** Maintainability = reader work, on two independent axes: **layers to trace** and **state to hold**. LOC, cyclomatic complexity, "clean architecture" are proxies. Human analog of guard-the-context-window.
- **Moves.** Collapse layers that cost more than they save (one-caller wrappers, adapters with no second implementation, speculative indirection). Adjacent layers must change the abstraction; collapse pass-throughs. Demand interface compression: prefer boundaries hiding meaningful decisions. Shrink state scope: pure functions > locals > fields > module state > globals; derive instead of sync. Name the invariant once at the boundary. Before adding a layer or state, ask whether it reduces load elsewhere by at least as much.
- **Test.** Can a new reader answer "where does X come from?" and "what can change X?" in under 30 seconds? If not, cut layers or cut state.
- **Anti-patterns.** 6-layer adapter stacks; flat files with 50 globals.
