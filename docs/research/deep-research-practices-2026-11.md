# Which deep-research practices should the research technique adopt?

Date: 2026-11-12. Feeds: the `research` technique (`plugins/deepmodebot/skills/deepmodebot/references/techniques/research.md`) and `assets/research/social.py`.

## Answer

The old technique had a brief and a primary-source rule, but no effort sizing, stop rule, gap step, or full citation check, and it could not reach Reddit or X.
Anthropic's write-up on its multi-agent research system sizes effort to the question, starting at 1 agent with 3-10 tool calls for a simple fact.
It also gives each worker a full brief and attaches citations in a separate pass after research ends ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)). open_deep_research stops on explicit rules and asks what is still missing after each research call (`langchain-ai/open_deep_research@1b7d2e8:src/open_deep_research/prompts.py:100-118`).
ResearchRubrics measured implicit reasoning and synthesis as 45-50% of deep-research failures, and found that binary rubric checks agree with human graders far better than ternary ones ([ResearchRubrics](https://arxiv.org/html/2511.07685) sections 4.2-4.3).
For Reddit and X, anonymous fetching failed here, while a logged-in CLI search followed by keyless verification worked; that approach comes from the MIT project credited in `NOTICE.md`.
The user chose to run every search on their Claude subscription only, so `social.py` drives `claude -p` alone; for Reddit, Claude names the subreddits and the archive lists their posts.

## Findings

Lab guidance and evals:
- Simple fact-finding "requires just 1 agent with 3-10 tool calls". Source: [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system), Prompt engineering principle 3. Checked 2026-11-12.
- "Token usage by itself explains 80% of the variance" on BrowseComp. Multi-agent beat single-agent Claude Opus 4 by 90.2% on Anthropic's internal research eval, at about 15x the tokens of a chat. Source: same post. Checked.
- Early agents "consistently chose SEO-optimized content farms over authoritative but less highly-ranked sources" until source-quality heuristics were added to the prompts. Source: same post, Common failure modes. Checked.
- A CitationAgent attaches citations after the research loop ends. Source: same post, Orchestrator-worker architecture. Checked.
- Binary grading reaches 0.72 to 0.76 macro F1 judge-human agreement, against 0.53 to 0.57 for ternary. Source: [ResearchRubrics](https://arxiv.org/html/2511.07685) section 4.3. Checked.

Open-source agents, read at default-branch HEAD on 2026-11-12:
- open_deep_research tells its supervisor to "Bias towards single agent" and to "Stop when you can answer confidently". It also stops after a fixed number of research calls. Source: `langchain-ai/open_deep_research@1b7d2e8:src/open_deep_research/prompts.py:100-118`. Checked.
- A survey of eleven repos also reported cite-check passes in gpt-researcher (`@ddd4db3:multi_agents/agents/orchestrator.py:100-134`) and deer-flow (`@04a9833:backend/packages/harness/deerflow/agents/lead_agent/prompt.py:488-490`). Not opened by me, so not used in the Answer.

Reddit and X, measured on Windows 11 on 2026-11-12:
- Claude Code's WebSearch, filtered to reddit.com, returned `400 The following domains are not accessible to our user agent: ['reddit.com']`. `site:reddit.com` queries returned no Reddit pages.
- `codex exec` with `web_search="live"` on a ChatGPT login returned Reddit `/comments/` threads, and so did `omp -p --tools=web_search`.
- Child isolation, from three review panels on PR #68:
  - `codex exec -s read-only -c features.shell_tool=false -c mcp_servers={}` still loaded MCP tools from `~/.codex/config.toml` plugins and ran the user's hooks.
  - Adding `--ignore-user-config` removed the MCP tools and the hooks. With that flag, an injected `whoami` and an injected file read both failed.
  - Built-in ChatGPT app connectors (Gmail, Drive, Calendar) and `view_image` survived `--ignore-user-config`. A child ran a Calendar call and read a local image canary. `-c features.apps=false -c features.view_image=false` removed both, and web search still worked.
  - What remains in the codex child: its `exec` code host, which web search needs and which reached no shell or file read in probes; `apply_patch` under the read-only sandbox; subagent spawning; and image generation.
  - The claude child ran the user's hooks and handed them the prompt until `--settings '{"disableAllHooks":true}'` was added.
  - `omp -p --tools=web_search --no-context-files --no-rules --no-skills --no-extensions` still read a local canary file and loaded about 200 imported MCP tools, so `social.py` refuses omp.
  - `claude -p --tools WebSearch` exposed only WebSearch.
- Reddit's own endpoints were unreachable anonymously:
  - Its `.json` endpoints returned 403.
  - Its shreddit comment partial returned 403.
- The arctic-shift archive was partly usable:
  - `/api/posts/ids` and `/api/comments/search` returned scores, dates, and comments with no key.
  - `/api/posts/search` with a text query (`query=` or `title=`) answered "Timeout. Maybe slow down a bit" on every try that day.
  - The same endpoint with only `subreddit=`, `after=`, and `sort=desc` listed posts. Paging 5 x 100 posts reached about 4 to 6 days back in r/AI_Agents, r/CryptoCurrency, and r/LocalLLaMA, and the full 30 days in r/defi and r/ethdev.
- Codex web search found one or two X posts per query; Claude web search found three or four.
- After the switch to Claude only, a prompt telling the child to read a canary file and run `whoami` came back `DENIED` with no leak.
- For `TrustWallet/status/2062172639938965917`, the date decoded from the post id matched fxtwitter's `created_at` to the second. fxtwitter returned 404 for an invented id.
- The upstream approach runs X through a signed-in `grok` CLI. It is opt-in, bills the user's Grok plan, and limits the CLI to hosted X search with a generated agent profile and `--disable-web-search`. The upstream is credited in `NOTICE.md`; the files read were its `grok_x.py` and its configuration docs at commit 029e23e.

## Not settled

- **Whether research files got better.** No blinded eval of whole research runs was done. The Eval playbook would settle it: about 20 real questions, scored on the five rubric axes from the Anthropic post.
- **Reddit coverage on busy subreddits.** The archive listing reaches only the last few days of a busy subreddit within the page cap, and text search there timed out. A fuller window needs the archive's search to recover, or a search backend that can reach reddit.com.
- **Archive lag.** How far arctic-shift's archive lags for posts under a day old was not measured.
