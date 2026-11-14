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

## Ecosystem routing and bounded goals

Run `python scripts/eval_routing.py --cases evals/routing/ecosystems.json --model <explicit-model> --out .scratch/evidence/ecosystem-routes.json`.
Inspect each route and size result; the runner's exit code alone does not assert every route matched.
The cases cover tool selection, self-authoring, LangGraph research/debugging, container research, Kubernetes near-misses, goal consensus, local updates and AI SDK research.
For domain selection and self-prompt changes, run isolated before/after agent sessions with the applicable local references and only local file tools.
Use an organic task that produces a goal file for a LangGraph worker in a named Compose project or Kubernetes namespace.
Inspect opened reference paths, fixed scope/check/caps, retained unknown effect status and the next bounded action in the delivered goal.
Run the emitted goal through `loop.py run <goal.md> --dry-run`; prose review alone misses unsupported YAML lists in the runner's flat frontmatter format.
Keep raw command/events/answers under `.scratch/evidence/`; a live planning run is not proof of SDK execution, container isolation or cluster rollout.

## Gotchas

An inventory mapping is not runtime proof. The collector checks artifacts, but those checks do not establish every claim in a human assessment. Platform-only integrations remain explicit gaps. Do not infer that every upstream workflow or harness works from representative journeys.
