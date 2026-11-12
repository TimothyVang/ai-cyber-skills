---
description: "Show what the deep-mode bots said on a PR or issue: a short text digest, 8-bit frames of the turns right here, or the live 8-bit battle screen in your terminal"
argument-hint: "<PR or issue URL | owner/repo> [frames [N] | arena]"
---

Show me the bot conversation for $ARGUMENTS. This only reads threads: post nothing, change nothing.

- A PR or issue URL alone: run `python <deep-mode skill dir>/assets/pr-conversation/show_thread.py <url>` and show me its output as it is. If I ask what one bot said in full, run it again with `--full`.
- With `frames`: run `python <deep-mode skill dir>/assets/pr-conversation/arena.py <url> --frames` (`--last N` when I give a number, `--repo <owner/repo>` for a repo) and show me its output as it is, inside a fenced `text` code block so the columns stay aligned. It prints one 8-bit frame per turn (the newest 3 by default) and ends with the newest comment id.
- With `arena`, or an `owner/repo` without `frames`: the 8-bit display runs full screen in a terminal, so give me the command to run in my own terminal window: `python <deep-mode skill dir>/assets/pr-conversation/arena.py <url>` (or `--repo <owner/repo>`), with the real path filled in. If I ask for it in a browser instead, start it with `--serve --open` as a background service and give me its local URL.

`<deep-mode skill dir>` is the folder `skill://deep-mode` resolves to on disk; python needs that file path, not the `skill://` URL. In Claude Code it is `${CLAUDE_PLUGIN_ROOT}/skills/deep-mode`.

Arguments: $ARGUMENTS
