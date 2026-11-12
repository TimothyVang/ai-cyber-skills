# Worktree cleanup

Use when: the user asks to prune git worktrees or reclaim disk space from agent work. This is the one playbook that deletes user state with no code review to catch a slip, so its gates are the review.

## Steps

1. Snapshot free disk space (`df -h` on the repo's volume, or the platform equivalent) and record it. Done when the free space number is in your notes.
2. Audit every worktree, reading paths from `git worktree list --porcelain`. Never hand-type them, since agent worktrees can live outside the repo's sibling directory (`references/principles/encode-lessons-in-structure.md`). Skip the main worktree. Per worktree record:
   - size (`du -sh`) and age (`git log -1 --format=%ct`)
   - merged: `git merge-base --is-ancestor HEAD <base>`, base = the branch PRs target (fetch it first; not necessarily `origin/HEAD`). Squash merges fail this check, so PR state is the real signal.
   - dirty: `git status --porcelain --ignored` → `clean`, `wip:N` (N tracked edits), `scratch:N` (N untracked non-ignored files, `??` lines), or `ignored-only` (only `!!` lines: build artifacts)
   - remote: pushed / ahead N / no-remote / detached
   - PR: `gh pr list --author @me --state all --json number,state,headRefName` (fetch once, match by branch)
   - last agent session that worked in it (session history/`archive`, scanned in a background subagent, since it's slow)
   Done when every non-main worktree has a row with all six fields.
3. Suggest a bucket: `hold-wip` (any `wip`), `hold-open-pr` (open or draft PR), `verify-recent-chat` (a session touched it within ~4 days), `safe` (merged or PR closed/merged), else `review`. If you'll do this again, make the audit a script (`references/principles/build-the-lever.md`). Done when every row has one bucket.
4. Treat the bucket as advice, not permission. Get the user's set of active/pinned sessions and cross-check every candidate; the pinned set wins over `safe` (`references/principles/prove-it-works.md`). Done when every candidate is marked pinned or not pinned.
5. Verify usage before deleting: for every `verify-recent-chat` row or doubtful one, fan out `scout` subagents to read those sessions and report whether each is active and which worktrees it touches (`references/principles/guard-the-context-window.md`). An active session's background subagents may own sibling worktrees whose names never appear anywhere visible. Those are in use. Done when every such row is marked in use or not in use.
6. Pause on irreversible loss: for `wip:N`, show the diff and get a decision first. A clean worktree is recoverable from its branch; uncommitted work is gone. A scratch worktree is safe to drop only if `git status --porcelain --ignored` shows no untracked non-ignored files (`??`); any `scratch:N` → hold it for the user and name the files. Done when every `wip` and `scratch` row has the user's decision or is held.
7. Prune the confirmed set, per path: `git worktree remove --force <path>`; if the directory survives on ignored build artifacts, delete it; then `git worktree prune`. Branch refs survive, so no commits are lost. Done when no pruned path exists on disk or in `git worktree list`.
8. Other reclaimers when needed: package caches (pnpm, npm, yarn, uv, pip, cargo) and build outputs. Clear only caches the user hasn't said to keep. Done when each cleared cache is named with its size.
9. Re-measure disk space and re-list worktrees. Done when the report has both free space numbers and the new worktree list.

## Gates

- Clean (or ignored-only) + merged + not in use → proceed. `wip`, `scratch`, or in-use → hold for the user.
- The user's active/pinned set overrides any bucket.
- Never delete a branch ref as part of cleanup.
- Never clear a cache the user said to keep.

## Evidence

- Disk space before and after, with space reclaimed.
- Worktrees pruned (paths).
- Each one held back, with a one-line reason (in use by which session, open PR, or uncommitted work).
