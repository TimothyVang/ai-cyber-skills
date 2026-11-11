---
name: deep-stack
description: "Stack picks and ship loop: a 2026 default software stack and the decision rules behind it, applied to any app (web, CLI, desktop, mobile, AI agent, data/ML, security tooling), plus an agent-driven UI design workflow and a per-task ship loop (worktree, service-layer build, recorded evidence, reviewed PR). Use when the user asks to pick a stack, \"what stack\", or to build a tech stack for a new app; designs a UI with an agent via a design system; or wants one change shipped as an evidence-backed, reviewed PR. An issue queue run as a software factory is deep-mode's Factory playbook."
---

# Stack picks and ship loop

The references hold dated decision rules distilled from 2026 public talks on building software with agents. Source transcripts are not shipped. Paths below are relative to this skill (`skill://deep-stack/...`). When two rules conflict, the newer date wins.

## Route

Read only the reference for the branch in front of you.

| Branch | Read |
|---|---|
| Choosing a framework, backend, auth, payments, deploy, sandbox, analytics, or model for a web, SaaS, or AI app | `references/stack.md` |
| Building a stack for any other kind of app (CLI, desktop, mobile, agent, data/ML, security tooling, infra), or "build the stack for me" | `references/any-app-stack.md`, which applies `references/philosophy.md` |
| Designing or restyling a UI with an agent | `references/design-workflow.md` |
| Planning work, running agents in parallel or in loops, writing skills / AGENTS.md | `references/agentic-workflow.md` |
| Shipping a repository change | The ship loop below |
| Setting a repo up for the ship loop | Copy `references/AGENTS.template.md` to the repo root as `AGENTS.md`; replace its "Checks in this repo" section with the repo's real commands |

An existing project's architecture and stack beat every default here. The picks are defaults for greenfield work, or when the user asks for the default.

## The ship loop

Pick the steps the task needs. Read-only reviews and investigations skip all of them. A plan, review, or local experiment does not imply publishing a PR. Each step ends on its completion check.

1. **Isolate.** Follow `references/isolate.md`. One worktree and branch per task (and per subagent), from `origin/main`.
   Done when `git branch --show-current` inside the worktree prints the new task branch.
2. **Plan.** For anything bigger than one PR, follow `agentic-workflow.md` §1: talk the design through first, then write the plan as a Markdown file under `plan/` with phases, riskiest integrations first, and to-dos. Split work into small PRs (a few hundred lines; stack them only when they truly depend on each other).
   Done when the plan file exists and each to-do maps to one PR-sized unit.
3. **Build.** Follow `references/structure.md` when extracting shared operations or choosing boundaries: entry points own the product rules (whether and when), services own the reusable operations (how), with explicit inputs and structured results. Pull fresh dependency source with `npx opensrc <package>` when the library is new or recently changed (`stack.md` §11).
   Done when no operation is duplicated across callers and the repo's typecheck and lint pass.
4. **Prove.** Follow `references/prove.md`. Capture the failure before the fix and the success after it: screenshots or video for UI, output pairs for CLI and API changes, measurements for performance.
   Done when every test target has a `passed`/`failed`/`untested` result backed by an artifact under `.artifacts/<task>/`.
5. **Ship.** Open the PR with that evidence as a before and after table. Run every human-facing text through `references/unslop/unslop.md`. Then run deep-mode's **pr-review** technique (`skill://deep-mode/references/techniques/pr-review.md`) on the PR. It reviews with your own subagents, so no third-party review service is needed.
   Done when no P0/P1 finding is open and every P2 is fixed or dismissed with a reason, or the technique hit its 3-round cap or oscillated, and you report its `review:` line with the open findings. Present the PR URL, then merge it on a deep-mode panel pass (`skill://deep-mode/references/techniques/panel.md`).

## Running it from omp

- Parallel slices: give each `task` subagent its own worktree and branch from step 1. Never share a checkout.
- Browser QA for step 4: the `browser` tool drives the app and takes the screenshots; `ffmpeg` records video when a sequence matters.
- Prerequisites by step: `gh` authenticated (PRs, pr-review); a browser or Playwright for UI captures; `ffmpeg` for video. A missing prerequisite stops that step. Report it and the evidence you have instead of substituting a weaker check.

## With deep-mode

When `deep-mode` is active (`/deep` or "deep mode"), it owns the process and this skill supplies the parts:

- deep-mode's playbooks, autonomy rules, and reply rules win. Commits, pushes, PRs, and merges follow deep-mode's Autonomy section: merges need its panel pass.
- `stack.md` and `design-workflow.md` feed its Feature and Prototype playbooks as the default picks on greenfield work.
- `prove.md` is the evidence step for its "prove it on the real artifact" rule when no `verify-<app>` skill exists.
- Ship step: its Opening a PR playbook, then its pr-review technique (`skill://deep-mode/references/techniques/pr-review.md`). The review posts as a comment and never approves. Merging takes a deep-mode panel pass.
