# Pause safely

Use when: the user explicitly asks to pause or stop for now. Explicit only: on "keep going", "going to bed, keep going", or "don't stop", do not pause. Compaction is automatic and never a reason to pause. You own a clean stop: leave a checkpoint a cold-start agent can resume from.

## Steps

1. Stop at a safe boundary: finish the current atomic step or back out of it. Start nothing new.
2. Cancel nested subagents and background jobs you started (`write proc://<id>/kill`); note any whose results you still need.
3. Take no irreversible action to pause: no new PR, no push unless you already had one out.
4. Make the work durable: save `git diff --binary` (plus untracked files via `git add -N` first, or list them) as a patch next to the resume note, and make one clear `wip:` commit on the current branch; if the tree is broken, say so in one line of its body.
5. Write the resume note off-context at `$(git rev-parse --git-common-dir)/omp-resume/<slug>.md` (never committed, shared by worktrees, visible to a cold-start session; `local://` is not) and print its absolute path: intent, what you were doing, progress and what's verified, current state, next steps, key files, gotchas, patch path. If a show-me-your-work trail exists, point at it instead of duplicating it.

## Gates

- Never pause on "keep going"-type instructions.
- No push, PR, merge, deploy, or deletion as part of pausing.
- Nothing may live only in context: every needed fact is on disk or in the note.

## Evidence

This is a pause, not a final report:
- Where you are in the loop.
- What's on disk versus what was only in your head (paths, no diff dumps).
- Patch path, the `wip:` commit SHA, and whether the tree is clean.
- The resume note's path and the first action on resume.
