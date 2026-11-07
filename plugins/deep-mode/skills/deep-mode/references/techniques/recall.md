# recall

**Use when:** "catch me up", "where did I leave off", "recall my work on X", before starting or resuming work.

1. Classify. Resuming one specific chat or turning habits into a skill is a different task. Given a full state capsule already (paths, branch, change)? Use it, skip mining.
2. Lock scope: window (default last 7 days), topic, workspace (active only; never another project's history unasked). State it back. Never quietly turn "all" into "recent N".
3. Mine your own history. omp: `archive` in `eval` (recent sessions, recaps, prompt history) and `history://`. For many sessions, fan out `scout`s by slice; order by real modification time, grep the topic first, read only matching regions, skip the current chat and subagent/eval/test noise. Each returns per session: topic, goal, decisions, open threads, struggles/corrections, artifacts (PRs, tickets, branches), cited by session id. One or two sessions → search directly. Raw transcripts stay in subagents.
4. Sweep the shared record whenever a feature, file, subsystem, area, or bug is named — default, and "my work on X" doesn't exempt it. Run **why**'s investigators in parallel with step 3, question reframed to "current state, what's been tried and didn't hold, what users still report". Null results are findings; unavailable sources are named. Skip only for pure activity recall with no target.
5. Verify surfaced PRs, branches, tickets against live state with `git` and `gh`. When the answer hinges on what an agent actually did, read the full transcript.
6. Write the brief.

**Output:** **Capsule** (≤5 bullets) → **Threads** (one line each, exactly one tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, `[planned, not started]`) → **Problems** (≤5 recurring, incl. user-reported symptoms and reverted fixes) → **Next move** (one concrete action).

**Hard rules.** Read only what in-scope threads need. Adjacent work stays out unless blocking. Cut detail before threads. Through **unslop**; cite chat findings by session id and shared-record findings by source; sanitize private context before public output.
