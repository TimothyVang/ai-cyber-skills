# Workflow coverage

A maintainer can distinguish a documented route from a workflow that an agent actually completed.

## Sub-features

- Pinned upstream inventories account for mappings and explicit gaps.
- Planning, review, architecture and handoff journeys produce inspectable artifacts.
- Bug-fix and feature delivery reuse the outcome corpus instead of a second implementation.
- Collection reruns trusted artifact checks in a fresh `collected-checks-*` directory instead of accepting supplied success flags.
- Every phase's input tree is bound to prepare or the preceding successful capture, rejecting intervening edits.
- Agent and artifact-probe subprocesses scrub credential variables and use project-local temp directories.
- Handoff regression checks reject zero discovered tests, entirely skipped suites and failing tests.

## How to get to it (user POV)

Read `evals/workflows/README.md`, choose a journey and invoke deepmodebot through the installed harness in the prepared disposable project.

## Driving it with control-deepmodebot

Preconditions: doctor passes; no real issues, PRs, deployments or credentials are required by the chosen journey.

Run `python .omp/skills/verify-deepmodebot/control.py run --id workflows-help workflows --help`. Follow the documented validate/prepare/capture/collect/report sequence. Use explicit models, isolated context and a fresh run ID. Independently read the resulting artifacts and attach evidence to the assessment before marking a scenario passed.
Inspect the newly collected `checks.json`, its capture and scenario bindings, and its retained evidence. A prewritten passing receipt must not rescue a failing artifact. The independent assessment remains required.
Verify capture `input_snapshot` chains and schema-version-2 result metadata. Older unbound passes remain invalid.
Inspect candidate code before executing probes; environment scrubbing is not a host sandbox.

## Source-backed procedure probes

For changes motivated by video research, attach the affected procedure to an isolated `omp -p` planning request with explicit model and time/usage caps.
Exercise nested delegation without enforceable child limits, an unknown migration outcome at handoff, tenant-scoped request design, load-test write limits, and incomplete integration consent.
Keep raw events, command, exit, and full answer under `.scratch/`; inspect the answer against each intended decision before marking it passed.
These planning probes show instruction following only. They do not prove child cancellation, migration recovery, cloud setup, load capacity, or a productivity improvement.
For compaction-pointer changes, start with only the workflow map loaded and allow local read/write tools. Confirm the raw trace opens Handoff through that pointer and a real checkpoint preserves unknown work without publishing, launching, or pausing.


## Software-factory source-map probes

For changes to the software-factory source map (`factory-landscape.md` in the main deepmodebot skill's reference library) or its pointers, run a bounded, tool-less planning probe with the actual reference attached.
Ask for local subscription-authenticated candidates, stale-worker fencing and holdout-isolation experiments, a no-Actions decision about `gh-aw`, a correction of Attractor-as-runtime claims, and whether upstream deployment permissions transfer.
Keep the prompt, raw events, command, exit, and full answer under `.scratch/`.
Pass only when candidates match the source map, the answer requests runtime/license verification, Attractor remains a specification, and existing merge/deployment permissions remain unchanged.
This demonstrates use of the guidance, not candidate functionality or automatic retrieval through the new pointers.

## Gotchas

An inventory mapping is not runtime proof. The collector checks artifacts, but those checks do not establish every claim in a human assessment. Platform-only integrations remain explicit gaps. Do not infer that every upstream workflow or harness works from representative journeys.
