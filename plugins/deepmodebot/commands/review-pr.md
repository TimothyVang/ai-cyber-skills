---
description: "Review a PR the deepmodebot way: parallel reviewer subagents, findings verified against the code, one comment-only review (asks first on someone else's repo)"
argument-hint: "<PR number>"
---

Read `skill://deepmodebot/references/techniques/pr-review.md` in full and follow it to review PR $ARGUMENTS in PR mode on this repo. In Claude Code, `skill://<name>/<path>` means `<path>` in that skill's folder: `${CLAUDE_PLUGIN_ROOT}/skills/<name>/` for a plugin install, `~/.claude/skills/<name>/` for a manual one.

Run every step yourself, including the parallel `reviewer` subagents and the verification checks. Don't ask me which lenses or models to use. Post the review as a comment on my repo's PR without asking; on someone else's repo, show me the body and ask first. Never approve or request changes. Fix-ups and merges follow deepmodebot's Autonomy section: merge only on a panel pass.

PR: $ARGUMENTS
