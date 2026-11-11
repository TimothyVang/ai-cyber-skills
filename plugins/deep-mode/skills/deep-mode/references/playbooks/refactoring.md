# Refactoring

Use when: changing structure while behavior stays fixed. You own the contract. Not Feature (adds behavior) or Bug fix (corrects it). Large or cross-cutting structural work → the **figure-it-out** technique (`references/techniques/figure-it-out.md`); this playbook is focused-to-medium.

## Steps

1. Pin the behavior contract: run the **how** technique (`references/techniques/how.md`), then write a characterization test, snapshot, or equivalence harness capturing current behavior before structure moves. No coverage → write the pin first. Type check and lint are not a pin.
2. Name the structure the code is missing (`references/principles/model-the-domain.md`). Boring code stays when its shape is clear and local. The reshape must delete branches or invalid states, not add indirection.
3. Name the target shape: module layout, types, call graph as if built today (`references/principles/foundational-thinking.md`, `references/principles/redesign-from-first-principles.md`). Target crosses a function boundary → run the **architect** technique (`references/techniques/architect.md`) first.
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
