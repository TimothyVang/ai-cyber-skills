# Refactoring

Use when: changing structure while behavior stays fixed, including a language port. You own the contract. Not Feature (adds behavior) or Bug fix (corrects it). Language ports follow the section below before the general steps. Other large or cross-cutting structural work → the **figure-it-out** technique (`references/techniques/figure-it-out.md`).

## Language ports

Use the two accounts in `references/rust-migration-case-studies.md` as evidence, not a mandate to choose Rust or one cutover strategy.

1. **Freeze the oracle.** Record the source revision and run existing consumer-facing tests against it. Keep fixtures, snapshots, schemas, test selection and compatibility thresholds outside implementers' write scope. An intended contract change is a separate decision, not a way to turn a port green. Done when baseline commands, results and protected paths are recorded.
2. **Inventory behavior, not just files.** Map each public entrypoint, callback, I/O path, state owner, cancellation/disposal pair and packaging target to its destination and proof. Record numeric serialization, missing/empty values, ordering, ambient inputs, dependency semantics and release-only behavior. Done when every source surface has an owner, destination and acceptance case; unknowns stay open.
3. **Pilot before scaling.** Choose incremental closed slices or an all-at-once cutover from coupling, live churn and rollback needs. Translate behavior before redesigning algorithms. Run a small representative slice through compile, link, startup and its consumer path. Done when the pilot proves the recipe; a compiler-only pass is not sufficient.
4. **Turn failures into work.** Group compiler/runtime failures by owning slice; use Self-authoring (`references/playbooks/self-authoring.md`) for bounded repair loops. A repeated translation mistake changes the shared porting recipe and gets a regression case, not another one-off workaround. For parallel work, follow **coworkers** (`references/techniques/coworkers.md`). Done when each queue item has a reproduced failure, owner and closure evidence.
5. **Check parity and completeness separately.** Exercise the unchanged oracle in supported release configurations and compare externally visible results. Independently reconcile the inventory against current source, including changes that arrived during the port. Compilation cannot detect an omitted callback. Done when every row is proven or explicitly blocked; stubs, skipped tests and lowered baselines never close rows.
6. **Close the migration.** Migrate callers and remove superseded implementations in each closed slice. Remove temporary scaffolding before declaring the port complete. Record real consumer runs and workload-matched resource measurements; keep merge, rollout and release readiness distinct. Done when the requested native/runtime boundary holds end to end, not merely on the hot path.

Then use the general steps for each slice. A port earns its place by the stated migration objective; the ordinary refactor's reader-load reduction gate does not replace that objective.

## Steps

1. Pin the behavior contract: run the **how** technique (`references/techniques/how.md`), then write a characterization test, snapshot, or equivalence harness capturing current behavior before structure moves. No coverage → write the pin first. Type check and lint are not a pin.
2. Name the structure the code is missing (`references/principles/model-the-domain.md`). Boring code stays when its shape is clear and local. The reshape must delete branches or invalid states, not add indirection.
3. Name the target shape: module layout, types, call graph as if built today (`references/principles/foundational-thinking.md`, `references/principles/redesign-from-first-principles.md`). Target changes a module or public interface with two or more viable shapes → run the **architect** technique (`references/techniques/architect.md`) first.
4. Subtract before you add (`references/principles/subtract-before-you-add.md`): delete dead code, collapse one-caller wrappers, drop redundant validators, remove orphan references. Ship the smallest change reaching the target (`references/principles/laziness-protocol.md`); revert speculative "might help" cleanups.
5. Move in small behavior-preserving steps, each keeping the pin green.
   - API reshapes: migrate every caller and delete the old API in the same wave (`references/principles/migrate-callers-then-delete-legacy-apis.md`). No shims, no parallel old/new paths.
   - Spot-check every rename against the files; renames miss usages in strings, prose, back-references.
   - Delegate mechanical edits to a default `task` agent with scope: file paths, names being moved, behavior to hold, exclusive file ownership.
6. Prove behavior unchanged on the real artifact, not "it compiles" (`references/principles/prove-it-works.md`). Larger reshapes: equivalence check (old-vs-new output diff script, recorded baseline replay, or smoke run on the matching surface via the project `verify-<app>` skill).
7. Confirm it is worth keeping: the diff must lower reader load somewhere (`references/principles/minimize-reader-load.md`); else revert.
8. Sequence commits: subtraction, then reshape, then follow-on cleanup, each green (`references/principles/sequence-verifiable-units.md`). Commit and run **Opening a PR** (`references/playbooks/opening-a-pr.md`).

## Gates

- No structure moves before the pin exists and is green.
- Cleanup reveals a missing feature or real bug → split it out; ship the structural change first against the pinned contract. A redesign is allowed only when named and routed to Feature.
- Any step turns the pin red → stop and fix before the next step.
- No reader-load reduction → revert.

## Evidence

- The structure that changed.
- The pin it was held against.
- The equivalence proof (run path and outcome).
- The reader-load delta.
- What shipped and what got reverted. No new behavior.
