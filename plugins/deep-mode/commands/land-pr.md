---
description: "Land a PR with no human: deep-mode bots review, fix, verify and merge it in the PR thread, on your own subscriptions"
argument-hint: "<PR number or URL>"
---

Read `skill://deep-mode` and then `skill://deep-mode/references/techniques/pr-conversation.md` in full, and follow it to land PR $ARGUMENTS.

I'm asking you to merge it on your own: no owner approval and no human in the loop. That is my yes for `--admin` when the base branch requires a review, as long as the panel passed at that exact head, every required check reported green, and the repo's local gate passed at that head. If the base branch's `.deep-mode.json` sets `"autonomousMerge": false`, stop and ask instead. Never merge over a failing check or someone else's PR, and never delete the branch.

Run the bots as separate ACP agents through `acpx`, with the agent and model each role names in `~/.config/deep-mode/bot.json` (omp by default; any ACP agent works). Each harness uses its own subscription login. Pass each turn between their sessions yourself and mirror it to the PR thread under the deep-mode GitHub App when it is configured, or my `gh` when it isn't. No API keys, and don't wait for hosted review bots.

PR: $ARGUMENTS
