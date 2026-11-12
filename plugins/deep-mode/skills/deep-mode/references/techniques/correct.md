# correct

**Use when:** agents keep repeating the same mistakes in this repo, or each time the operator corrects you. Make each mistake impossible. Assume every contributor is an agent that sees only files it opened, copies the nearest example, takes the shortest path that compiles.

1. Read recent commits, reverts, review comments, agent instruction files (AGENTS.md, CLAUDE.md, `.omp/`), and workaround comments. Group mistakes into classes; a class counts once it happened twice.
   Done when each class is listed with at least two cited occurrences.
2. Fix each class at the highest level that works:
   - **Architecture:** one owner per state, one supported way per task, hidden internals so the wrong import fails, one source of truth instead of hand-synced lists, delete old ways and dead code agents would copy.
   - **Types** so the bad state can't be written; if it still compiles, a **lint/CI check** whose error names the file, type, or function to use instead; if the pattern is already common, fail only when a change adds more.
   - **Tests** of behavior; fix or delete tests that pass when behavior breaks or fail when only internals change.
   - **Docs/agent rules last**, only for judgment calls (nothing fails when skipped).
   - Done when each class has a chosen level and a reason no higher level works.
3. Fix the most frequent classes now, one unit per class (one commit each). Prove each new check fails on a real past mistake. Same command locally and in CI. Exceptions go on the offending line with reason, expiry, and a decision-trail row.
   Done when each fixed class has its own commit and a run showing its check failing on a past mistake.
4. Keep a rule table in the agent instruction file pairing each rule with its enforcer. On a correction: fix the mistake, add the rule; an existing unenforced rule is a repeat → enforce it at the highest level in the same change. Drop rules whose mistake can no longer happen.
   Done when every rule in the table names an enforcer, or is a judgment call marked as docs-only.

**Output:** each class with its evidence, the level picked, and why a higher level didn't work.

**Done when** every class found is fixed or listed as deferred, and the rule table matches the enforcers in the repo.
