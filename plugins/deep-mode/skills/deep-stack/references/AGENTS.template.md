# How agents work in this repo

<!-- Template from the deep-stack skill. Copy to the repo root as AGENTS.md,
     then replace "Checks in this repo" with this repo's commands.
     `skill://deep-stack/` and `skill://deep-mode/` paths are files inside
     those globally installed skills. -->

Use only the parts a task needs.

- Reviews, explanations, and investigations that change nothing need no branch, commit, or PR. If one turns into edits, isolate the edits first.
- Code changes get isolation, checks, and evidence of the changed behavior. Show the failure before fixing it.
- Small doc edits get an isolated branch and a link or content check. They need no runtime evidence and no PR review.
- Publish a PR only when the task asks for one or for a finished repository change.

## Steps

1. **Isolate.** Follow `skill://deep-stack/references/isolate.md` before editing. Branch from `origin/main`, or keep the worktree already assigned to this task. Never build on `main`.
2. **Build.** Follow the project's existing architecture. With no convention, use `skill://deep-stack/references/structure.md` for shared operations.
3. **Prove.** Run the checks below. For changed runtime behavior follow `skill://deep-stack/references/prove.md`: capture before and after. For docs, check the changed links and runnable examples.
4. **Ship.** Open the PR with evidence that fits the change: screenshot pairs for UI, output pairs for CLI. For code or executable workflow changes, run the pr-review technique (`skill://deep-mode/references/techniques/pr-review.md`). Stop when no P0/P1 finding is open and each P2 is fixed or dismissed with a reason. Stop after 3 rounds or on oscillation, and report its `review:` line with the open findings. Post the review as a PR comment; never approve or request changes. Present the PR URL.

## Writing for people

Run `skill://deep-stack/references/unslop/unslop.md` over text a person will read before you commit, post, or send it: commit messages, PR title and body, docs, code comments, and the final reply. Apply it only to text you wrote or changed.

## Working beside other agents

- No direct commits to `main`.
- One worktree and branch per task and per agent. Never touch another agent's worktree, branch, or uncommitted work.
- Before starting, list open PRs and their changed files (`gh pr list`, `gh pr diff <n> --name-only`). Edits to the same file that do not conflict may proceed. Ask only when behavior conflicts, work depends on something unfinished, or ownership is unclear.
- Push with `--force-with-lease` and only to your own branch. Never `--force`, never to `main`.
- Regenerate lockfiles to resolve their conflicts. Do not merge them by hand.
- Worktrees share ports and databases. Check that a dev server port belongs to your process, and keep schema experiments off shared databases.
- When a conflict has no confident resolution, stop and report it.

## Finishing a task that ships

1. Keep the diff to the assigned task.
2. Run the checks below.
3. Collect the before and after evidence.
4. Commit, rebase onto the latest `origin/main`, and run the checks again.
5. Push: `git push -u origin <branch>`.
6. Open the PR. The body states what changed, how it was tested with evidence for each claim, the before and after proof, and any risks.
7. Run pr-review when it applies.
8. Present the PR URL.

Merge only on a deep-mode panel pass at the PR's exact head (`skill://deep-mode/references/techniques/panel.md`). Keep the worktree until the PR merges or closes.

## Checks in this repo

Replace this section with the repo's commands (typecheck, lint, test, build) and what each proves. Keep generated evidence in a gitignored `.artifacts/` directory.
