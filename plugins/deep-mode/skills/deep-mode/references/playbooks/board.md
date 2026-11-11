# Board

Use when: the agent should run a project on its own ("drive the board", "work the backlog", "run this project autonomously", "keep going on the roadmap"), or a goal bigger than one PR that the user wants planned, built, and landed without them. You own the board, the tasks, the PRs, and the merges. Every task ends in a merge, and only after a panel pass.

The board lives on the repo's GitHub issues: one issue per task, and one status label each: `board:todo`, `board:in-progress`, `board:review`, `board:blocked`, `board:done`. When the user keeps a GitHub Projects board, mirror each status change there too (`gh project item-edit`). No GitHub remote → `plan/board.md`, one checklist line per task with its status.

## Steps

1. **Set up** the labels once (`gh label create <name> --force`). Done when `gh issue list --label board:todo` runs.
2. **Fill the board.**
   - Turn the goal into tasks, each one PR. Every task issue has acceptance criteria a verifier can run, and a `Blocked by: #<n>` line for each dependency.
   - Open issues that fall inside the goal join the board.
   - A goal whose route is foggy → run the Wayfinder playbook (`references/playbooks/wayfinder.md`) first, then fill the board from its decisions.
3. **Pick** the oldest unblocked `board:todo` task. Assign yourself and move it to `board:in-progress` before any work.
4. **Build** it with the matching playbook (Feature, Bug fix, Refactoring, Perf issue), after the **prior-art** technique (`references/techniques/prior-art.md`) for anything new. Give the build to an owner subagent in its own worktree, following the shared-`.git` rules in Orchestrate step 3 (`references/playbooks/orchestrate.md`). Open the PR per Opening a PR (`references/playbooks/opening-a-pr.md`), with `Closes #<n>` in the body. Move the task to `board:review`.
5. **Judge** it with the **panel** technique (`references/techniques/panel.md`) at the PR head. Merge needs both a panel pass and green required checks (including the security gate when the repo has it).
   - Pass → `gh pr merge <pr> --match-head-commit <sha>` with the repo's merge method, then run the checks on the new trunk. Red trunk → open a revert PR at once (Autopilot step 11, `references/playbooks/autopilot.md`). Green → `board:done`.
   - Fail → the owner fixes the findings, pushes, and a fresh panel runs. The third failed panel → `board:blocked` with the findings in a comment.
6. **Loop.** Run up to three tasks at once when they touch different files. After each merge, re-read the board: re-plan tasks the merge changed, unblock dependents, and add the panel's dissent tasks.

## Gates

- Every merge has a panel pass at the exact head it merges.
- The forge's protections stand: never bypass required reviews or checks, never admin-merge, never force-push the default branch.
- The hard stops in SKILL.md Autonomy still need the user.
- One PR per task; a task that grows past one PR splits into new tasks.

## Evidence

- Board state: done, in review, blocked (each blocked task with what it needs).
- Per merged task: PR link, panel line (`references/techniques/panel.md` Output), merge SHA, and the trunk check after the merge.
- Decisions made on the user's behalf, each with how to reverse it.
- Done when no task is `board:todo`, `board:in-progress`, or `board:review`, or every one left is blocked on something only the user can supply.
