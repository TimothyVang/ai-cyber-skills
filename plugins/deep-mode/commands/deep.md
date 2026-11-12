---
description: "One command for everything: fix, build, review a PR, contribute to a project, set up a project for helpers, start a new app, run a software factory, drive a kanban board, chart a big effort, or grill a plan. deep-mode routes it, sizes it, proves it, lands it on a panel pass (one verifier for a small change, three otherwise; none for a small local fix), and reports."
argument-hint: "<anything: a task, a PR number, 'what can I work on', 'start a new app that ...', 'drive the board', 'grill me on ...'>"
---

Read `skill://deep-mode` and follow its **Route** section first: look around, pick the route, size the work, then do it. Don't ask me which skill, playbook, or approach to use, and answer anything you can observe by running it. In Claude Code, `skill://<name>/<path>` means `<path>` in that skill's folder: `${CLAUDE_PLUGIN_ROOT}/skills/<name>/` for a plugin install, `~/.claude/skills/<name>/` for a manual one.

Keep every write inside the project root, per deep-mode's **Contain the work** section: scratch and temp files in `.scratch/`, worktrees in `.worktrees/`, never system temp or folders outside the repo. No repo yet → create a named one first.

For a large or medium task, read the matched playbook's file and copy its steps into your todo list. For a small one, take the fast path. Read only the principle and technique files you apply. A small fix with no remote, or one I said I'll review, lands on no branch: no commit to the default branch, no push, no merge. Fix it, add a test that fails without the fix when it has behavior, prove it with one real run, then report. It needs no panel. "Open a PR, I'll review it" means a push, so it takes the panel.

If the repo has a verify skill (`.omp/skills/verify-<app>/`, `.claude/skills/verify-<app>/`, or `.agents/skills/verify-<app>/`), use it for proof. If it has none, the task is medium or large, it changes user-visible behavior, and the app runs locally, I pre-authorize running `skill://create-verification-skill` first; say you did.

Decide and act without asking: commits, pushes, PRs, issues, board cards, and merges are yours; merge only on a panel pass at the exact head: three verifiers, or one for a size S change. Ask me once, at the end, only for the hard stops in deep-mode's Autonomy section (deploys, deleting what you didn't create, history rewrites on shared branches, messages outside the repo, money, secrets). Claiming an issue in someone else's project is the one thing you ask about before starting.

Request: $ARGUMENTS
