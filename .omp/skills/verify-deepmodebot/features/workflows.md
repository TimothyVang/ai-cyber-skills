# Workflow coverage

A maintainer can distinguish a documented route from a workflow that an agent actually completed.

## Sub-features

- Pinned upstream inventories account for mappings and explicit gaps.
- Planning, review, architecture and handoff journeys produce inspectable artifacts.
- Bug-fix and feature delivery reuse the outcome corpus instead of a second implementation.

## How to get to it (user POV)

Read `evals/workflows/README.md`, choose a journey and invoke deepmodebot through the installed harness in the prepared disposable project.

## Driving it with control-deepmodebot

Preconditions: doctor passes; no real issues, PRs, deployments or credentials are required by the chosen journey.

Run `python .omp/skills/verify-deepmodebot/control.py run --id workflows-help workflows --help`. Follow the documented validate/prepare/capture/collect/report sequence. Use explicit models, isolated context and a fresh run ID. Independently read the resulting artifacts and attach evidence to the assessment before marking a scenario passed.

## Gotchas

An inventory mapping is not runtime proof. A validator checks evidence structure, not the truth of an assessment. Platform-only integrations remain explicit gaps. Do not infer that every upstream workflow or harness works from representative journeys.
