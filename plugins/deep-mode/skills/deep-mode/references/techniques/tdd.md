# tdd

**Use when:** user asks for TDD, a failing test, or a regression test, or the bug has an obvious cheap local test target. Skip when the test path is unclear, expensive, integration-heavy, or unrequested.

1. Understand the bug: intended vs current behavior, affected path, smallest observable repro.
2. Choose the narrowest executable check already used for that codepath. None practical → don't build one from scratch.
3. Write the smallest failing test that would have caught it, encoding intended behavior (test-behavior-not-implementation).
4. Run it before fixing; confirm it fails *for the intended reason*. Passes or fails otherwise → fix the test/repro first.
5. Make the smallest production fix preserving nearby contracts.
6. Rerun; confirm pass.

Impractical test (broad harness, brittle mocks, slow e2e, prod-only state, vague repro, fixture churn) → closest executable check: targeted script, repro command, browser automation, snapshot, log assertion. No new test beats a bad test (mostly mocks, implementation-pinned, timing-dependent, expensive, throwaway).

**Hard rules.** Never change tests to match a wrong implementation. Never weaken assertions unless behavior genuinely changed, with reason. No unrelated coverage expansion. Flaky → make deterministic, document the signal. Broader failure class → land the focused regression first.

**Output:** failing-before check and its failure; passing-after run plus nearby validation; if failing-before couldn't be shown, why and what check replaced it.
