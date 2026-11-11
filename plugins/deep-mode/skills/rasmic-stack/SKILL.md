---
name: rasmic-stack
description: "Ras Mic's (@rasmic, Michael Shimeles) 2026 software stack and the decision philosophy behind it, applied to any app (web, CLI, desktop, mobile, AI agent, data/ML, security tooling), plus his AI UI design workflow and rstack per-task workflow (worktree → service-layer build → recorded evidence → reviewed PR). Use when the user names rasmic, Ras Mic, or rstack; asks to pick or build a tech stack for any new app; designs a UI with an agent via a design system; or wants one change shipped as an evidence-backed, reviewed PR. An issue queue run as a software factory is deep-mode's Factory playbook."
---

# Ras Mic stack and software factory

Distilled from all 166 @rasmic videos (the source transcripts are not shipped) and his [rstack](https://github.com/michaelshimeles/rstack) skills, vendored under `references/` with their licenses. His Greptile review loop is not vendored: deep-mode uses its pr-review technique instead. Paths below are relative to this skill (`skill://rasmic-stack/...`). Citations in the references carry video dates; the newest video wins conflicts.

## Route

Read only the reference for the branch in front of you.

| Branch | Read |
|---|---|
| Choosing a framework, backend, auth, payments, deploy, sandbox, analytics, or model for a web, SaaS, or AI app | `references/stack.md` |
| Building a stack for any other kind of app (CLI, desktop, mobile, agent, data/ML, security tooling, infra), or "build the stack for me" | `references/any-app-stack.md`, which applies `references/philosophy.md` |
| Designing or restyling a UI with an agent | `references/design-workflow.md` |
| Planning work, running agents in parallel or in loops, writing skills / AGENTS.md | `references/agentic-workflow.md` |
| Shipping a repository change | The factory below |
| Setting a repo up for the factory | Copy `references/AGENTS.template.md` to the repo root as `AGENTS.md`; replace its "Checks in this repo" section with the repo's real commands |

An existing project's architecture and stack beat every default here. His picks are defaults for greenfield work or when the user asks for "his" choice.

## The factory

Pick the beats the task needs. Read-only reviews and investigations skip all of them; a plan, review, or local experiment does not imply publishing a PR. Each beat ends on its completion check.

1. **Isolate** — follow `references/new-feature/new-feature.md`. One worktree and branch per task (and per subagent), from `origin/main`.
   Done when `git branch --show-current` inside the worktree prints the new task branch.
2. **Plan** — for anything bigger than one PR, follow `agentic-workflow.md` §1: talk the design through first, then write the plan as a Markdown file under `plan/` with phases, riskiest integrations first, and to-dos. Split work into small PRs (a few hundred lines; stack them only when they truly depend on each other).
   Done when the plan file exists and each to-do maps to one PR-sized unit.
3. **Build** — follow `references/code-structure/code-structure.md` when extracting shared operations or choosing boundaries: actions own the product rules (why and when), services own the reusable operations (how), with explicit inputs and structured results. Pull fresh dependency source with `npx opensrc <package>` when the library is new or recently changed (`stack.md` §11).
   Done when no operation is duplicated across callers and the repo's typecheck and lint pass.
4. **Prove** — follow `references/evidence-driven-testing/evidence-driven-testing.md`. Capture the failure before the fix and the success after it: recorded UI session, scripted headless captures, or measured output pairs for non-UI changes.
   Done when every test target has a `passed`/`failed`/`untested` result backed by an artifact under `.artifacts/<task>/`.
5. **Ship** — open the PR with that evidence (`references/before-and-after/before-and-after.md` for screenshot tables). Run every human-facing text through `references/unslop/unslop.md`. Then run deep-mode's **pr-review** technique (`skill://deep-mode/references/techniques/pr-review.md`) on the PR; it reviews with your own subagents, so no third-party review service is needed.
   Done when no P0/P1 finding is open and every P2 is fixed or dismissed with a reason, or the technique hit its 3-round cap or oscillated, and you report its `review:` line with the open findings. Present the PR URL, then merge it on a deep-mode panel pass (`skill://deep-mode/references/techniques/panel.md`).

## Running it from omp

- Parallel slices: give each `task` subagent its own worktree and branch from beat 1; never share a checkout.
- Browser QA for beat 4: the `browser` tool is the computer-use driver; the bundled recorder (`evidence.py`, gdigrab on Windows) records the session.
- On Windows, run the `.sh` helpers with Git Bash (`"C:/Program Files/Git/bin/bash.exe"`); a bare `bash` may resolve to WSL.
- Prerequisites by beat: `gh` authenticated (PRs, pr-review); `ffmpeg`/`ffprobe` with libx264 and the ass filter (recorder; check with `python3 references/evidence-driven-testing/scripts/evidence.py doctor`); `npx @vercel/before-and-after` (screenshot tables). A missing prerequisite stops that beat: report it and the evidence you have instead of substituting a weaker check.

## With deep-mode

When `deep-mode` is active (`/poteto`, deep-mode, or poteto-mode), it owns the process and this skill supplies the parts:

- deep-mode's playbooks, autonomy rules, and reply rules win. Commits, pushes, PRs, and merges follow deep-mode's Autonomy section: merges need its panel pass.
- `stack.md` and `design-workflow.md` feed its Feature and Prototype playbooks as the default picks on greenfield work.
- `evidence-driven-testing` is the recorder for its "prove it on the real artifact" step when no `verify-<app>` skill exists.
- Ship beat → its Opening a PR playbook, then its pr-review technique (`skill://deep-mode/references/techniques/pr-review.md`). The review posts as a comment and never approves; merging takes a deep-mode panel pass.
