# Agent-assisted Rust migrations

Read when assessing a language rewrite or planning a behavior-preserving port with coding agents. These are two project-specific accounts, not evidence that every codebase should move to Rust.
Sources checked 2026-11-12. Outcomes below are reported by the authors, not independently reproduced here. Existing playbooks and approval gates still govern.

## GitHub Copilot runtime

Stephen Toub, [Migrating the GitHub Copilot runtime to Rust, using Copilot](https://github.blog/ai-and-ml/generative-ai/migrating-the-github-copilot-runtime-to-rust-using-copilot/), GitHub Blog, 2026-09-16 (updated 2026-09-23).

- Motivation was an embeddable runtime with low startup and memory overhead, including a C ABI, rather than a blanket preference for Rust over TypeScript.
- The team shipped component-by-component atomic replacements while development continued. Pure leaf components came first; state ownership and orchestration followed. Temporary internal interop disappeared as callers migrated.
- Existing CLI and SDK end-to-end tests provided the behavioral oracle. Compilation still admitted serialization, cancellation, lifecycle, omitted-feature, dependency-semantic and performance regressions.
- Separate worktrees isolated parallel edits, but shared build resources needed coordination. Human oversight caught an agent attempting to waive a compatibility failure rather than restore the missing API.

## Bun

Jarred Sumner, [Rewriting Bun in Rust](https://bun.com/blog/bun-in-rust), Bun, 2026-07-08.

- Motivation was recurring lifetime and cleanup bugs at the boundary between garbage-collected JavaScript and manually managed memory. The initial port deliberately retained the Zig architecture rather than redesigning it.
- The author prepared `PORTING.md` and a field-lifetime inventory (`LIFETIMES.tsv`), trialled three files, then scaled translation with separate implementer and reviewer contexts. Compiler failures and runtime failures became subsequent work queues.
- Bun chose an all-at-once port, unlike Copilot's incremental replacements. The author reports 11 days to merge, all-platform tests with none skipped or deleted, and manual CLI checks; merge was explicitly not release readiness.
- Reported regressions included side effects erased by `debug_assert!` in release builds, changed slice-casting behavior, and placeholder constants. Rust compilation and extensive tests did not establish complete parity.

## Applying the comparison

[inference] Choose the cutover strategy from coupling, concurrent development and the available behavioral oracle, not either project's headline. Pilot the full path before scaling; preserve behavior before redesigning; assign edit ownership and a build coordinator; verify real consumer paths and release builds. Keep test oracles and compatibility gates independent of implementation edits. Treat benchmark and cost figures as workload-specific reports, not forecasts.
