---
description: "Land a PR with no human: deep-mode bots review, fix, verify and merge it in the PR thread, on your own subscription"
argument-hint: "<PR number or URL>"
---

Read `skill://deep-mode` and then `skill://deep-mode/references/techniques/pr-conversation.md` in full, and follow it to land PR $ARGUMENTS. In Claude Code, `skill://<name>/<path>` means `${CLAUDE_PLUGIN_ROOT}/skills/<name>/<path>`.

I'm asking you to merge it on your own: no owner approval and no human in the loop. That is my yes for `--admin` when the base branch requires a review, as long as the panel passed at that exact head, every required check reported green, and the repo's local gate passed at that head. If the base branch's `.deep-mode.json` sets `"autonomousMerge": false`, stop and ask instead. Never merge over a failing check or someone else's PR.

Run every bot as yourself or an omp `task` subagent, so all model calls use my subscription in omp; no API keys, and don't wait for hosted review bots.

PR: $ARGUMENTS
