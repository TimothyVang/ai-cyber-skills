---
name: create-verification-skill
description: "Generate a project-local verification skill (.omp/skills/verify-<app>/) that drives the app the way a user does and captures proof: control CLI, launch/doctor/drive/evidence/cleanup, and a feature map. Any language or platform. Use for /skill:create-verification-skill, \"make a verify skill for this repo\", or when a repo has no scripted way to prove UI/CLI/service behavior."
disable-model-invocation: true
---

# Create a verification skill

Adapted for omp from pstack's `create-verification-skill` (MIT, Lauren Tan / Cursor; see `LICENSE`).

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, exercise a feature the way a user would, and capture evidence. This skill generates that as a project-local omp skill at `<repo>/.omp/skills/verify-<app>/`, which omp discovers automatically for every session in the repo. Write the output for the next agent, not for a human: it will be read cold, mid-task, by an agent that has never seen the app.

Outside omp, write the same skill to the folder your harness discovers and substitute that path for `.omp/skills/` below: Claude Code reads `.claude/skills/verify-<app>/`, and Codex and most other agents read `.agents/skills/verify-<app>/` (`skill://deep-mode/references/harnesses/README.md` has the map). Codex's sandbox makes `.agents/` read-only, so creating it there needs the user's approval.

## 1. Interview the repo, not the user

Answer these from the codebase. Ask the user (via `ask`) only what you cannot observe:

- **Surface:** what does a user actually touch? Web UI, CLI/TUI, desktop app, API, mobile app, library? A repo can have several; pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent interact with it programmatically? Existing harnesses first: Playwright/Cypress specs, expect scripts, PTY helpers, curl-able endpoints, a debug port. Only then pick a generic recipe:
  - Web or Electron: Playwright or Chrome DevTools Protocol (CDP).
  - CLI/TUI: tmux where available; on Windows, a Node script using `child_process` or `node-pty`.
  - Service: plain HTTP.
- **Observe:** what evidence can be captured? Screenshots, accessibility snapshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to double-drive a shared instance beats corrupting the user's session.

If the checkout doesn't build or start as-is, fix that first (or report it precisely) before generating. A skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, clearly marked as verification scaffolding, and remove it in cleanup.

## 2. Build the control CLI

Ship one executable helper, `.omp/skills/verify-<app>/control-<app>.<ext>`, in the repo's own language/runtime. Agents run commands instead of writing throwaway scripts, which saves tokens and makes runs reproducible. Required commands:

| Group | Commands |
|---|---|
| Lifecycle | `launch` (empty data dir → migrations → seed → ready means *usable*, not just "port open"), `cleanup` |
| Health | `doctor` (read-only: process up, right build/version, port owned by this run, auth valid) |
| Inspect | `snapshot` (a11y tree or equivalent), `screenshot <path>`, `logs` |
| Drive | whatever the surface needs: `goto`, `click`, `type`, `press`, `send`, `run -- <cmd>` |

Add `trace`, `wait-settle`, `feature-flag <name> on|off`, `network-log` when the stack supports them. Design rules:

- Output machine-readable JSON.
- Errors say what to do instead.
- Anything with destructive side effects takes `--dry-run`.
- Subcommands disclose functionality gradually; `--help` is complete.
- Commands compose; no command does two jobs.

## 3. Write the skill

Write `.omp/skills/verify-<app>/SKILL.md`. Frontmatter is required: omp skips project skills without a `description`. Use `name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it. Body sections, each grounded in what the interview found (no placeholders left):

- **Launch:** the exact command that starts the app for verification, and how to tell it's ready (a log line, a prompt, a doctor pass). Launch must reach a usable state from an empty data dir, including migrations and seed data. A database health check can pass while its init scripts are still running. Include teardown. For a short-lived CLI or TUI there is no server to keep alive: build once, then start each drive in its own isolated session.
- **Doctor:** one read-only check answering "is this instance worth driving?" An agent runs it first, and again whenever anything looks off.
- **Drive:** the harness recipe with real selectors and commands from this repo, not examples. Prefer stable handles (ARIA roles and names, `data-testid`, prompt strings, route paths) over coordinates and tab order.
- **Evidence:** what to capture and where it goes. Proof standards:
  - Exercise the real user path, not internal setters or test-only endpoints.
  - Capture the action and the resulting state, not just the final screen.
  - Verify side effects (files written, rows inserted, messages sent) alongside what's visible.
  - Mocks only where a production boundary already isolates the external system.
  - When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name.
- **Cleanup:** tear down what the run started. Never kill by process name; kill what you started. Cleanup removes instances and scratch state, never evidence: proof artifacts survive in a location the skill names.
- **Helpers:** every script the skill ships is executable and its invocation is shown in the skill body. Reference files with paths relative to the skill directory (or `skill://verify-<app>/...`).

## 4. Seed the feature map

Create `.omp/skills/verify-<app>/features/README.md` plus one file per user-facing feature you can identify (top 3–5 to start, from routes, commands, menus, or docs). Follow the shape in `references/feature-map-example/`: a README index (baseline preconditions, driving conventions, proof and skip reporting, entry contract, feature list) and one file per feature.

Each feature file: H1 title, one paragraph of user-visible behavior, then exactly these four H2s in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with control-<app>`, `Gotchas`. The driving section starts with `Preconditions:` and pairs each user action with an exact command and its observable result.

If the seed data lacks a precondition a journey needs, the journey reports a failure and the reason goes in that feature's `Gotchas`. Never weaken a journey to make it pass. A proof that drives one convenient entry point is incomplete when the map lists others. Keep implementation details out of the map.

## 5. Wire it into the repo's instructions

omp loads `AGENTS.md` into main sessions only; task subagents do not receive it but do receive `.omp/RULES.md`. So:

- Add a short `## Verification` section to the repo's existing context file (root `AGENTS.md`, or `.omp/AGENTS.md` if the repo uses that). Create root `AGENTS.md` only if the repo has none. Use the template below, filled in. Do not paste the skill's contents into it.
- Add one line to `.omp/RULES.md` (create it if absent; append if present) so subagents verify too:
  `Prove behavior changes with skill://verify-<app> before reporting done; include the evidence paths.`

AGENTS.md template:

```markdown
## Verification

Every behavior change must be proven on the running app before it's done. Passing tests are not proof.

- Use the `verify-<app>` skill (`.omp/skills/verify-<app>/SKILL.md`). Read it before launching, driving, or debugging the app.
- Find the feature in `.omp/skills/verify-<app>/features/README.md` and follow its "Driving it" recipe.
- Run `<doctor command>` first, and again whenever anything looks off. Never drive an instance you didn't launch.
- Report evidence: commands run, screenshots/snapshots, observed end state. "Fixed" without artifacts is not done.
- Adding or changing a user-facing feature? Update its feature-map file in the same change.
- Missing a CLI command you need? Add it to `control-<app>`; don't write a throwaway script.
```

## 6. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive ONE mapped feature, capture evidence, clean up. After cleanup, confirm the evidence still exists at the named location; a cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts don't strand processes and ports. A generated skill that was never executed is a draft, not a deliverable.

If you proved it in a stand-in for the real target (a container instead of a fresh VM, a local stack instead of a remote one), list every setup step the stand-in did that the target will not. Those steps stay unverified until a run on the real target covers them.

## 7. Hand off

Report: files created, the proof run (commands, evidence paths), anything unverified. Point the user at `/skill:maintain-verification-skill` to keep the map honest as the app changes. Suggest a cadence only if asked.
