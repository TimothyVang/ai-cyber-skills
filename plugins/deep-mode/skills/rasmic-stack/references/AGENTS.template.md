# Agent workflow

<!-- From michaelshimeles/rstack AGENTS.md, adapted for omp. Copy into a repo root,
     then replace "Checks in this repo" with that repo's commands. Each
     `skill://rasmic-stack/` path is a file inside the global `rasmic-stack`
     skill; `skill://deep-mode/` paths are inside the `deep-mode` skill. -->

Choose the applicable parts of this workflow for the requested task.

- Read-only reviews, explanations, and investigations need no worktree, commit,
  PR, or PR review run. If an investigation leads to edits, isolate those edits.
- Code changes use isolation, relevant architecture guidance, checks, and
  evidence of the behavior changed. Capture a failure before fixing it.
- Small documentation edits use an isolated branch and relevant content or link
  checks. Do not manufacture runtime evidence or require a PR review for them.
- Ship when the task calls for a PR or a completed repository change. A request
  for a plan, review, or local experiment does not imply publishing it.

## Workflow

1. **Isolate.** Follow `skill://rasmic-stack/references/new-feature/new-feature.md`
   before repository edits. Start from `origin/main`, or preserve a worktree
   already assigned to this task. Never build on `main`.
2. **Build.** Follow `skill://rasmic-stack/references/code-structure/code-structure.md`
   when extracting shared operations or choosing boundaries. Follow the
   project's existing architecture; the service layer pattern is a default for
   projects without a convention.
3. **Prove.** Run relevant checks. Follow
   `skill://rasmic-stack/references/evidence-driven-testing/evidence-driven-testing.md`
   for changed runtime behavior: record the failure before fixing it and the
   success afterward. For documentation, inspect the changed instructions and
   verify runnable examples and links as applicable.
4. **Ship.** Open the PR with evidence appropriate to the change. Use
   `skill://rasmic-stack/references/before-and-after/before-and-after.md` when
   screenshots help; use output pairs for CLI changes. Run the **pr-review**
   technique (`skill://deep-mode/references/techniques/pr-review.md`) for code
   or executable workflow changes, or when requested. It reviews with your own
   read-only subagents; no third-party review service is needed. Stop when no
   P0/P1 finding is open and every P2 is fixed or dismissed with a reason. Stop
   after 3 rounds or on oscillation and report its `review:` line with the open
   findings. Do not claim success or raise the cap automatically. Posting the
   review to GitHub needs the human's yes; never approve or request changes
   unless asked. Present the PR URL.

Ship-beat notes:

- `before-and-after` drives the `@vercel/before-and-after` CLI. `--markdown`
  uploads the pair and prints a PR-ready table; it also accepts existing
  PNGs, so evidence gathered while developing can be reused as-is.
- In containers/VMs where Chrome fails with "No usable sandbox", set
  `AGENT_BROWSER_ARGS="--no-sandbox"` for the capture command.
- The default upload host (0x0.st) is public — fine for ordinary UI shots;
  pass `--upload-url` for anything sensitive.

## Writing for humans

Run `skill://rasmic-stack/references/unslop/unslop.md` over anything a person
will read, before you commit, post, or send it: commit messages, the PR title
and body, README and doc edits, code comments, and the closing reply. Apply it
to text you wrote or changed, not to prose you didn't touch.

## Multi-agent rules

- Never commit directly to `main`.
- One worktree and one branch per task and per agent — never reuse or modify
  another agent's worktree, branch, or uncommitted work.
- **Scope check** before starting: skim open PRs' changed files
  (`gh pr list`, `gh pr diff <n> --name-only`) and look for uncommitted work
  in shared checkouts. Inspect overlapping diffs: independent edits to the same
  file may proceed in your own worktree. Ask only when changes conflict in
  behavior, depend on unfinished work, or ownership is unclear. Do not modify
  another task's checkout.
- Never force-push to `main` — and never plain `--force` anywhere; only
  `--force-with-lease`, only on your own task branch.
- Resolve lockfile conflicts by regenerating, never by hand-merging.
- Worktrees don't isolate shared resources: confirm a dev-server port
  answers *your* process before trusting it, and don't run schema
  experiments against a shared database.
- If a conflict can't be resolved confidently, stop and report instead of
  guessing.

## Completing a task that ships

1. Keep changes limited to the assigned task.
2. Run the applicable checks listed below.
3. Assemble applicable evidence into before/after pairs or content-check results.
4. Commit with a clear message, rebase onto the latest `origin/main`, and
   rerun the checks.
5. Push (`git push -u origin <branch>`; after rebasing an already-pushed
   branch, `--force-with-lease`).
6. Open the PR. The body must explain what changed, how it was tested (every
   claim backed by evidence), before/after proof, and any risks or follow-up
   work. Run the title and body through unslop before posting.
7. Run the pr-review technique when applicable, with the stop rule above.
8. End by presenting the PR URL.

Do not merge the PR unless explicitly instructed. Keep the worktree until
the PR is merged or closed.

## Checks in this repo

Replace this section with the repo's own commands (typecheck, lint, test,
build) and what each one proves. Keep generated evidence under a gitignored
`.artifacts/` directory.
