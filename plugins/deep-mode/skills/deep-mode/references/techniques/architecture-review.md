# architecture-review

**Use when:** "review the architecture", "where should we refactor", "find deepening opportunities", "make this codebase easier for agents to work in", or a codebase-wide look for structural friction. One change whose shape is open is the **architect** technique (`references/techniques/architect.md`) instead. This technique finds candidates across the codebase, reports them visually, then settles one.

**Words.** Use these terms exactly in the report and the follow-up. A **module** is anything with an interface and an implementation (a function, class, package). Its **interface** is everything a caller must know to use it. A module is **deep** when a small interface hides a lot of behavior, **shallow** when the interface is almost as big as what it hides. A **seam** is where one module meets another and where a test or a second implementation can plug in. An **adapter** is one implementation behind a seam; a seam with one adapter is speculative, a seam with two (production and test) is real.

**Leverage** is how many callers one interface serves. **Locality** is how much of one change, bug, or concept lives in one place. The **deletion test**: imagine deleting the module and inlining it into its callers. If complexity collapses into one place, the module was shallow. If the same complexity reappears in every caller, the module earns its keep.

1. **Scope.** If the user named an area, use it. Otherwise find the hot spots, because deepening pays off where code keeps changing: `git log --since=6.months --format= --name-only | sort | uniq -c | sort -rn | head -40`. Group the top paths by directory. Changes scattered with no cluster → widen the window. Read `GLOSSARY.md` and every ADR in `docs/adr/` that touches the scope; ADRs are settled unless the friction is strong enough to reopen one.
2. **Explore.** Spawn one `scout` with a fresh context, the scope, the vocabulary above, and the red flags from the **architect** technique. Ask it to note where it felt friction, with file paths:
   - one concept spread across many small modules a reader has to hop between;
   - shallow modules, pass-through layers, wrappers with one caller;
   - pure helpers pulled out for testing while the bugs live in how they are wired together;
   - one internal decision known by several modules (leak);
   - code that is untested, or hard to test through its current interface.
   It runs the deletion test on every suspect and returns candidates, each with files, problem, proposed change, and deletion-test result.
3. **Screen.** Drop candidates that only move complexity (deletion test fails), that an ADR forbids without strong new evidence, or that sit in code nobody has touched in a year. Rate the rest **Strong**, **Worth exploring**, or **Speculative**, and tag each with the kind of dependency behind the seam: in-process, swappable dependency (database, filesystem), ports and adapters, or external service.
4. **Report.** Copy `assets/architecture-review/report-template.html` to `docs/deep-mode/architecture-<YYYY-MM-DD>.html` and fill one card per candidate:
   - title, badges, files, and a before and after diagram side by side;
   - one sentence each for problem and change, gains in locality, leverage, and test terms, the deletion-test line, and an ADR callout when one conflicts.
   Use `GLOSSARY.md` names for domain concepts. Vary the diagrams (dependency graph, layer stack, call tree collapsing into one box); a card that needs a paragraph to explain needs a better diagram. End with the top recommendation. Open the file (`start`, `open`, or `xdg-open`) and print its absolute path. Propose no interfaces yet. The report is a working artifact: leave it uncommitted unless the user wants it kept.
5. **Pick.** Take the top recommendation and say so. In live mode (the user asked to choose), ask which card to explore and wait.
6. **Grill the pick** with the **grill** technique (`references/techniques/grill.md`): constraints, callers, the shape of the deepened module, what sits behind its seam, which tests survive and which move to the new interface. Keep the docs current as answers land, per the **domain-model** technique (`references/techniques/domain-model.md`):
   - a new module name for a concept missing from `GLOSSARY.md` → add the term;
   - a term that gets sharper in the discussion → update its entry;
   - the candidate rejected for a reason a future review would need → write an ADR in `docs/adr/` so the next review does not suggest it again. Skip ADRs for "not now" reasons.
7. **Hand off.** An accepted candidate with two or more viable interfaces → **architect** (its arena step designs it at least twice). One clear shape → the Refactoring playbook (`references/playbooks/refactoring.md`).

**Hard rules.** Scope before you scan. Every candidate cites files and passes the deletion test. Diagrams carry the argument; prose stays one sentence per field. No candidate re-argues an ADR without naming it.

**Output:** the report path, the candidates as a one-line-each list with their ratings, the pick and its grill decisions, and every `GLOSSARY.md` and ADR change made.
