# tdd

**Use when:** user asks for TDD, test-first, red-green-refactor, integration tests, a failing test, or a regression test, or the bug has an obvious cheap local test target. Skip when the test path is unclear, expensive, integration-heavy, or unrequested. Two modes share one set of rules: **bug mode** pins one defect, **build mode** grows a feature test-first.

Before the first test, read `GLOSSARY.md` if it exists so test names use the project's terms, and read the ADRs in `docs/adr/` that touch the area.

## Bug mode

1. Understand the bug: intended vs current behavior, affected path, smallest observable repro.
   Done when intended behavior, current behavior, and a repro command are written down.
2. Choose the narrowest executable check already used for that codepath. None practical → don't build one from scratch.
   Done when the check is named by file or command, or recorded as impractical.
3. Write the smallest failing test that would have caught it, encoding intended behavior (test-behavior-not-implementation).
4. Run it before fixing; confirm it fails *for the intended reason*. Passes or fails otherwise → fix the test/repro first.
   Done when the run output shows the test failing on the intended assertion.
5. Make the smallest production fix preserving nearby contracts.
6. Rerun; confirm pass. Done when the new test and the nearby existing tests pass in one run.

## Build mode

1. **Seams.** A seam is the public surface a test drives: an exported function, an HTTP route, a CLI command, a component's props and rendered output. List the seams for the feature, each with one line on what a test there catches and what it misses.
   Prefer the outermost seam that runs in seconds (integration first): it exercises real collaborators and survives refactors. Pick the seams yourself and log them as decision trail rows; in live mode (the user asked to choose), present the list with your pick and wait.
   Tests go only at listed seams. A seam whose shape is still open goes to the **architect** technique (`references/techniques/architect.md`) first.
   Done when every seam is logged as a decision trail row with its catches and misses line.
2. **Slice.** Order the behaviors as thin vertical slices, each one observable end to end through a seam. The first slice is the tracer: the simplest path through every layer the feature touches.
   Done when the slices are an ordered list and the first is the tracer.
3. **Red.** Write one test for the next slice only. Run it. It must fail, and fail on the missing behavior (an assertion), not on a typo, import error, or missing fixture.
   Done when the run output shows an assertion failure for the missing behavior.
4. **Green.** Write the least production code that passes it. No code for later slices, no options nobody asked for. Run the whole file or package, not only the new test.
   Done when the whole file or package passes.
5. **Refactor.** With everything green, remove the duplication and naming debt this slice added. Tests stay untouched and green after every step. A refactor that needs a test change is a behavior change: go back to red.
   Done when the suite is green with no test file changed in this step.
6. Commit the slice (test and code together), then return to step 3 with what this slice taught you. Stop when every listed behavior has a passing test.
   Done when the slice's commit exists with its test and code together.

## What makes a test worth keeping

- It drives a seam and asserts what a caller can observe. It never reads private state, queries the database behind the interface, or asserts call counts on internal collaborators.
- Its expected value comes from somewhere independent of the code: a literal, a worked example, the spec. An expectation computed the same way the code computes it passes by construction (tautological) and can never catch a bug.
- Its name states the behavior ("rejects a cart with no items"), not the mechanism ("calls validateCart").
- Mocks sit only at the system's edge: third-party APIs, payment, email, the clock, randomness, sometimes the filesystem or database (a real test database is better). Never mock a module the repo owns. Make the edge easy to replace by passing the client in, and give it one function per operation (`getUser`, `createOrder`) so each fake returns one shape with no branching.

## Anti-patterns

- **Implementation-coupled:** the test breaks on a refactor that kept behavior.
- **Tautological:** the assertion repeats the implementation.
- **Horizontal:** all tests first, then all code. Tests written ahead of the code test imagined behavior and lock in a structure before the code exists. Work one slice at a time.

Impractical test (broad harness, brittle mocks, slow e2e, prod-only state, vague repro, fixture churn) → closest executable check: targeted script, repro command, browser automation, snapshot, log assertion. No new test beats a bad test (mostly mocks, implementation-pinned, timing-dependent, expensive, throwaway).

**Hard rules.** Never change tests to match a wrong implementation. Never weaken assertions unless behavior genuinely changed, with reason. No unrelated coverage expansion. Flaky → make deterministic, document the signal. Broader failure class → land the focused regression first. Passing tests are not proof the feature works; still prove it on the real artifact.

**Output:** bug mode: failing-before check and its failure, passing-after run plus nearby validation; if failing-before couldn't be shown, why and what check replaced it. Build mode: the seams chosen and why, then one line per slice (test name, red failure message, green run).

**Done when** bug mode has a failing-before and passing-after run (or the stated replacement check), and build mode has a passing test per listed behavior, each committed with its code.
