# Isolate a task

Every task that edits the repository gets its own git worktree and branch. Parallel agents then never edit the same checkout.

## Steps

1. Fetch: `git fetch origin`.
2. Pick a short branch name from the task: `<type>/<slug>`, for example `fix/login-redirect`.
3. Create the worktree inside the repo's self-ignored `.worktrees/` folder, never beside the repo: `mkdir -p .worktrees && { [ -f .worktrees/.gitignore ] || printf '*\n' > .worktrees/.gitignore; } && git worktree add .worktrees/<slug> -b <type>/<slug> origin/main`.
4. Work only inside that directory. Install dependencies there; worktrees do not share `node_modules` or virtualenvs.
5. Copy any untracked local config the task needs (for example `.env.local`). Never commit it.

A worktree already assigned to this task is reused as is. Never build on `main`.

## Done when

`git branch --show-current` inside the worktree prints the task branch, and `git status` shows a clean tree based on `origin/main`.

## Cleanup

After the PR merges or closes: `git worktree remove .worktrees/<slug>`, then delete the branch.
