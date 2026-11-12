---
description: "Show what the deep-mode bots said on a PR or issue: a short text digest, or the 8-bit battle-screen display of the whole conversation in your terminal"
argument-hint: "<PR or issue URL | owner/repo> [arena]"
---

Show me the bot conversation for $ARGUMENTS. This only reads threads: post nothing, change nothing.

- A PR or issue URL alone: run `python skill://deep-mode/assets/pr-conversation/show_thread.py <url>` (the script sits in the deep-mode skill's `assets/pr-conversation/`) and show me its output as it is. If I ask what one bot said in full, run it again with `--full`.
- With `arena`, or an `owner/repo` instead of a URL: the 8-bit display runs full screen in a terminal, so give me the command to run in my own terminal window: `python <path to the deep-mode skill>/assets/pr-conversation/arena.py <url>` (or `--repo <owner/repo>`), with the real path filled in. If I ask for it in a browser instead, start it with `--serve --open` as a background service and give me its local URL.

Arguments: $ARGUMENTS
