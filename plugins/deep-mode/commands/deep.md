---
description: "One command for fixing, building, reviewing, planning and shipping. deep-mode routes and sizes the task, proves it on the real artifact, and reports. Ordinary local work stays uncommitted for review; publication uses an exact-head verifier gate."
argument-hint: "<anything: a task, a PR number, 'what can I work on', 'start a new app that ...', 'drive the board', 'grill me on ...'>"
---

Read `skill://deep-mode` and follow its **Route** section first: look around, pick the route, size the work, then do it. Don't ask me which skill, playbook, or approach to use, and answer anything you can observe by running it. In Claude Code, `skill://<name>/<path>` means `<path>` in that skill's folder: `${CLAUDE_PLUGIN_ROOT}/skills/<name>/` for a plugin install, `~/.claude/skills/<name>/` for a manual one.

Keep every write inside the project root, per deep-mode's **Contain the work** section: scratch and temp files in `.scratch/`, worktrees in `.worktrees/`, never system temp or folders outside the repo. No repo yet → create a named one first.

Read the matched playbook for a medium or large task; small tasks use the fast path. Follow its local-delivery or publication path and read only references that change the work. With no remote or an explicit request for local review, ordinary small and medium work stays uncommitted in the starting tree. Prove it through the real app or CLI and review the diff. Risky work keeps the full checks. "Open a PR, I'll review it" is publication and needs the panel.

Reuse an existing project verification skill when present. Otherwise exercise the real app or CLI directly and retain its output. Create a reusable verification skill only when I ask for one or repeated journeys justify it, not as a prerequisite for an ordinary local task. Do not replace runtime proof with unit tests alone.

Decide and act without asking within the requested delivery target. Publication includes commits, pushes, PRs and merges on an exact-head panel pass. Local delivery does not silently become publication. Ask once at the end only for deep-mode's hard stops. Claiming an issue in someone else's project still needs permission before starting.

Request: $ARGUMENTS
