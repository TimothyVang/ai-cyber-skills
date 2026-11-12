---
description: "Show what the deep-mode bots said on a PR or issue: a short text digest, or the 8-bit battle-screen display of the whole conversation"
argument-hint: "<PR or issue URL | owner/repo> [arena]"
---

Show me the bot conversation for $ARGUMENTS. This only reads threads: post nothing, change nothing.

- A PR or issue URL alone: run `python skill://deep-mode/assets/pr-conversation/show_thread.py <url>` (the script sits in the deep-mode skill's `assets/pr-conversation/`) and show me its output as it is. If I ask what one bot said in full, run it again with `--full`.
- With `arena`, or an `owner/repo` instead of a URL: start the 8-bit display, `python skill://deep-mode/assets/pr-conversation/arena.py <url> --serve --open` (or `--repo <owner/repo> --serve --open`), as a background service, and give me its local URL.

Arguments: $ARGUMENTS
