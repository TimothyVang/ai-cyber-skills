# Research technique, before and after, 2026-11-13

CONTRIBUTING's "Testing a behavior change" asks for a before and after run of a changed technique on a throwaway repo with a planted bug.
This run covers PR #68's research technique and `social.py`.

## Setup

- Project: a three-file repo, `weatherfetch`, with a `docs/notes/` folder and `fetch.py`.
- Planted bug: `fetch.py` calls `requests.get` with no `timeout` and says "requests gives up after 30 seconds by default". requests has no default timeout.
- Before: skill and `/deep` command at `2e071da` (main, the PR's base).
- After: skill and `/deep` command at `1fe232b` (this branch, with the review fixes to `social.py`).
- Each candidate is a fresh git repo with the snapshot in `.omp/skills/`, started with `evals/outcome/run.py`'s `omp_command`: `omp -p`, no rules, context files or extensions, `--max-cost 4`, `--max-time 25m`.
- Model: `anthropic/claude-opus-5-5` for every run and helper. One run per variant per task, so the counts below are anecdotes, not rates.
- Cost is omp's reported cost summed over every session file, helpers included.
- Raw runs (prompt, command, events, sessions, project folders) are in `.scratch/research-ab/` of the author worktree. They are not committed.

Requests, inside the `/deep` command body:

- `timeout`: "Our fetch.py says requests gives up after 30 seconds by default. Research what timeout requests actually applies by default and what we should set, and write it up for the team."
- `social`: "What are people on Reddit and X saying about Cursor pricing in the last 30 days? Write it up for the team."

## Results

| Run | Exit | Cost | Tool calls (main) | Wall | Note written | Brief | Found the planted bug |
|---|---|---|---|---|---|---|---|
| timeout-before | 0 | $1.12 | 24 | 2.5 min | `docs/notes/requests-default-timeout.md` | no | yes |
| timeout-after | 0 | $0.94 | 18 | 2.5 min | `docs/notes/requests-default-timeout.md` | `.scratch/research/requests-default-timeout/brief.md` | yes |
| social-before | 3 (max cost) | $3.95 | 22 | 7.5 min | none | no | n/a |
| social-after | 0 | $2.48 | 45 | 8.1 min | `docs/notes/cursor-pricing-social.md` | `.scratch/research/cursor-pricing-social/brief.md` | n/a |

No run committed or edited `fetch.py`. Both timeout runs said the comment is wrong and left the fix to the user, since the request asked for a write-up.

### timeout

Both runs reached the same answer from the same evidence:

- The requests docs say "If no timeout is specified explicitly, requests do not time out."
- The installed source has `timeout=None` (`sessions.py:510`).
- A local probe server that never answers was still waiting after 45 s, and a `(3.05, n)` timeout raised `ReadTimeout`.

Both recommend `timeout=(3.05, 10)` and list the API's real latency under Not settled.

The after run wrote the brief first (step 1) and used fewer calls. It did not spawn researchers: this is the one-fact path in step 3, and the before run did not either.

### social

**Before.** The technique had no route to Reddit or X. The main session started one background researcher. Both then scraped directly:

- reddit.com search JSON, RSS feeds and a search RSS that answered 403 (saved as `rss-cursor-search-pricing-FORBIDDEN.xml`).
- X's syndication endpoint for 38 post ids.
- 20 pages of a forum thread.

It hit the $4 cap and wrote no note. Its last reply was "Nothing else needs doing until the researcher's draft arrives."

**After.** The run read the technique and ran `social.py reddit-find` and `x-find` in parallel, then ran `x-find` four more times with narrower queries. No helper agent ran.

- `reddit-find` scanned 500 posts in each of 5 subreddits. It marked 4 titles `verified` (every topic word) and 280 `partial match` or otherwise not verified.
- The agent did not cite partial matches as found. It filtered their titles for pricing terms and re-checked 37 thread ids with `reddit-thread`, which confirms the archive record and the date.
- The note cites 26 Reddit threads. 25 carry a `verified` label from one of the tool's runs. The 26th, a megathread, is named as unread.
- All 4 cited X posts are in the run's `verified` X list.
- Prices and plan terms are cited to cursor.com pages, not to posts.
- After writing the note, the agent ran a script that checks every Reddit and X URL in it against the verified lists.

The run pointed `TMPDIR` into the project, a git repo. `x-find` still started its search children, so `outside_dir` passed over that folder and found a system temp folder that git confirmed is outside every repo.

## Limits

- One run per cell. A second run could size or route differently.
- The planted bug is a factual one. The timeout task exercises steps 1 to 3 and 6 to 7, not the researcher fan-out in steps 4 and 5.
- The social task depends on live archives and search, so a rerun will see different posts.
- At `1fe232b`, `reddit-thread` checked only that a thread exists inside the window, not its topic, so relevance of a re-checked thread was the agent's judgment. 18 of the 25 cited threads were `partial match` leads re-checked this way.
- After this run, `reddit-thread` was changed to require `--topic` and apply the same every-topic-word title rule, and the `partial match` label became `topic unconfirmed`. With `--topic "Cursor pricing"`, those 18 threads would now be `topic unconfirmed`, not `verified`.
