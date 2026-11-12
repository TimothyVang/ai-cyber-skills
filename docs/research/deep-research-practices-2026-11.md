# Which deep-research practices should the research technique adopt?

Date: 2026-11-12. Feeds: the `research` technique (`plugins/deepmodebot/skills/deepmodebot/references/techniques/research.md`) and `assets/research/social.py`.

## Answer

The old technique had a good brief and a primary-source rule. It had no effort sizing, stop rule, gap step, or full citation check, and it could not reach Reddit or X.

Lab write-ups and the leading open-source agents agree on six missing practices:
- Size effort to the question ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system), Prompt engineering principle 3).
- Split work by independent facet, with a full brief per worker.
- Stop on explicit rules (`langchain-ai/open_deep_research@1b7d2e8:src/open_deep_research/prompts.py:103-110`).
- Reflect on gaps after each batch.
- Write findings to files.
- Verify that each citation supports its claim. Factual accuracy and citation quality are the weakest axes in measured deep-research output ([ResearchRubrics](https://arxiv.org/html/2511.07685) section 4.2).

For Reddit and X, anonymous fetching fails. Search through a logged-in CLI, then verify each hit against a keyless public source. This is the approach of `mvanhorn/last30days-skill@029e23e`.

## Findings

Lab guidance and evals:
- Simple fact-finding "requires just 1 agent with 3-10 tool calls". Source: [Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), Prompt engineering principle 3 (checked 2026-11-12).
- "Token usage by itself explains 80% of the variance" on BrowseComp. Multi-agent beat single-agent Claude Opus 4 by 90.2% on Anthropic's internal research eval, at about 15x the tokens of a chat. Source: same post (checked).
- Early agents "consistently chose SEO-optimized content farms over authoritative but less highly-ranked sources" until source-quality heuristics were added to the prompts. Source: same post, Common failure modes (checked).
- A separate CitationAgent attaches citations after the research loop ends. Source: same post, Orchestrator-worker architecture (checked).
- Binary rubric grading reaches 0.72 to 0.76 macro F1 judge-human agreement, against 0.53 to 0.57 for ternary. Implicit reasoning and synthesis account for 45 to 50% of failures. Source: [ResearchRubrics](https://arxiv.org/html/2511.07685) sections 4.2 and 4.3 (checked). This is why the answer test is written as yes/no checks and the brief states implicit constraints.

Open-source agents (read at default-branch HEAD on 2026-11-12):
- open_deep_research tells its supervisor to "Bias towards single agent", "Stop when you can answer confidently", and to stop after a fixed number of research calls. It also pauses after each call to ask what is still missing. Source: `langchain-ai/open_deep_research@1b7d2e8:src/open_deep_research/prompts.py:100-118` (checked).
- A standalone brief that every worker re-reads, compressed per-worker notes, and a cite-check pass recur across open_deep_research, gpt-researcher, deer-flow, and hyperresearch.
  - Reported by the survey, not opened by me: `gpt-researcher@ddd4db3:multi_agents/agents/orchestrator.py:100-134` and `deer-flow@04a9833:backend/packages/harness/deerflow/agents/lead_agent/prompt.py:488-490`.
  - Only the open_deep_research lines were opened directly.

Reddit and X, measured in this session on Windows 11, 2026-11-12:
- Claude Code's WebSearch cannot return reddit.com. A domain-filtered search returned `400 The following domains are not accessible to our user agent: ['reddit.com']`, and `site:reddit.com` queries returned no Reddit pages.
- `codex exec` with `web_search="live"` on a ChatGPT login found Reddit `/comments/` threads. `omp -p --tools=web_search` did too.
- Reddit's own `.json` endpoints returned 403 to anonymous clients, and the shreddit comment partial returned 403 here.
  - The arctic-shift archive (`/api/posts/ids`, `/api/comments/search`) returned scores, dates, and comments with no key.
  - Its `/api/posts/search` timed out ("Timeout. Maybe slow down a bit") on every try that day.
- Codex web search found few X posts: 1 or 2 per query.
  - An X post id's snowflake timestamp matched fxtwitter's `created_at` to the second, for `TrustWallet/status/2062172639938965917`.
  - fxtwitter returned 404 for an invented id.
- last30days runs X through a signed-in `grok` CLI. It is opt-in, uses the user's Grok plan, and limits the CLI to hosted X search with a generated agent profile and `--disable-web-search`. Source: `mvanhorn/last30days-skill@029e23e:skills/last30days/scripts/lib/grok_x.py:745-870` and `CONFIGURATION.md:223-225`.

## Not settled

- Whether the new technique produces better research files than the old one. No blinded eval was run. The Eval playbook is the way to settle it: about 20 real questions, scored with the five rubric axes from the Anthropic post.
- The grok path is untested here, because `grok login` has not been run on this machine. last30days audits each grok build against a fake endpoint before trusting it. `social.py` checks only the version floor (1.0.46).
- Arctic-shift's archive lag for posts under a day old was not measured.
