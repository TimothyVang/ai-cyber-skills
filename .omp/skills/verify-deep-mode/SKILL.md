---
name: verify-deep-mode
description: Verifies deep-mode's real agent delivery, sealed review and workflow evaluation CLIs, records evidence, and distinguishes runtime proof from structural tests. Use before changing or verifying these surfaces.
---

# Verify deep-mode

## Launch

This project ships agent procedures and short-lived Python CLIs, not a web server. Run from the repository root with Python 3.12+, Git, Node and omp installed. Keep every run under `.scratch/`. No global configuration changes are needed.

## Doctor

Run `python .omp/skills/verify-deep-mode/control.py doctor` first. It checks local executable availability without logging in, reading credential values, calling a model or contacting GitHub. The model runners separately require a supported subscription login and explicit model IDs. A successful doctor is not proof of authentication or feature behavior.

## Drive

Read [the feature map](features/README.md), then its matching file. `control.py run --id <fresh-slug> <outcome|review|workflows> <arguments>` captures the actual CLI stdout, stderr, command and exit. It forwards no guessed action and refuses an existing evidence directory. Each target's `--help` defines its options.

Model calls consume the user's subscription. Keep model, cap and input constant across comparison arms. Never launch a production watcher, post a review, or merge a PR as an evaluation shortcut. The host's existing watcher may already own those operations.

## Evidence

Command captures go to `.scratch/evidence/<slug>/`. Candidate work, raw transcripts and measurements stay in the directories the runner prints. Keep those artifacts and their pinned source commits. A zero exit only proves the command returned successfully. Check requested behavior in the delivered tree, adjudicate review findings against the source, and inspect workflow artifacts before recording a pass.

Synthetic regression fixtures prove specific boundaries, not product superiority, independent review accuracy, or full harness compatibility. Report failed, blocked and contaminated runs alongside successful ones. A mocked provider response is never a live agent run.

## Cleanup

The CLIs exit on completion. There is no verification service to stop. Terminate only processes this invocation started if it fails, retaining raw output. Remove this invocation's disposable temp files, not earlier runs, candidate outputs or evidence. Do not delete the entire `.scratch` directory. Actual model runners must enforce their own time and usage caps.

## Helpers

`control.py doctor` checks prerequisites. `control.py run` captures a real invocation; it is not a replacement implementation of an evaluator. Use fresh IDs so comparisons and failures remain reproducible.
