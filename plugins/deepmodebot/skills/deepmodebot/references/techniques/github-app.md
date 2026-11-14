# github-app

**Use when:** the user wants deepmodebot's bots working their repos without a session: "install deepmodebot on my repos", "run the bots on their own", "AI review on my own subscription". Also to set the bots up, start, stop, check on, or opt a repo out.

## What it is

- **An identity.** A private GitHub App the user creates on their own account. Bot comments show as `<slug>[bot]`, so the thread reads as bots, not as the user. The app never runs a model.
- **A poller, not a service.** `bot.py` runs on the user's machine and polls the installed repos every `interval` seconds. There are no webhooks and no server.
- **Any ACP agent, no API keys.** The models run in agent CLIs that `acpx` reaches over ACP: omp by default, or Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode and others. Each harness uses its own subscription login (Claude.ai, ChatGPT and the like). Each role in `bot.json` picks an agent and an optional model, so omp alone can seat an author on a Claude model and a reviewer on a GPT model for cross-family review. Every call draws on subscription usage.
- **The user's hands for writes.** Pushes, PR creation and merges use the user's own `gh` and git credentials. The app token reads the installed repos' PRs, issues and comments and posts the bots' replies.
- **The conversations.** Each cycle runs the **pr-conversation** (`references/techniques/pr-conversation.md`) and **issue-conversation** (`references/techniques/issue-conversation.md`) techniques. On the user's own PRs that ends in a merge.

## Setup

Run once per machine, from this skill's folder:

```bash
py -3 assets/github-app/install.py            # interactive; asks before each change
py -3 assets/github-app/install.py --check    # report what is missing, change nothing
```

`install.py` walks five steps and skips any already done:

1. **Tools:** git, `gh` logged in as the user, `openssl` (Git for Windows ships one), npm, and `acpx` (installed with npm on a yes).
2. **Agents:** the ACP harnesses on PATH, omp first, then Claude Code, Codex, Gemini CLI, Cursor, Copilot and OpenCode, each on its own subscription login. omp is registered with acpx.
3. **ACP round trip:** one prompt through `acpx` to each agent the bots will use.
4. **The app:** runs `ghapp.py setup` in the browser, then waits while the user installs it. Installing is the opt-in: pick "Only select repositories" to name the repos the bots may work in.
5. **Config and autostart:** writes `~/.config/deepmodebot/bot.json` with the agents found, then runs `bot.py install-autostart` on a yes.

`--yes` accepts every default, `--no-autostart` skips step 5's autostart, and `--brand <name>` renames the bots (below).

**Manual path.** `py -3 assets/github-app/ghapp.py setup` creates the app on its own: a browser page opens; click "Create GitHub App". The app id and private key stay in `~/.config/deepmodebot/`, outside every repo. Pass `--org <org>` to create it under an organization. Install it at the `install` URL it prints, then `py -3 assets/github-app/ghapp.py whoami` lists the bot login and its installations.

The app asks for contents, pull requests and issues (write), and checks, statuses, actions and metadata (read).

## Run

```bash
py -3 assets/github-app/bot.py once --repo <owner/repo> --dry-run   # preview one cycle, post nothing
py -3 assets/github-app/bot.py once --repo <owner>/<name> --item pr:<n>   # one item now; --item needs --repo
py -3 assets/github-app/bot.py watch                                # poll every interval
py -3 assets/github-app/bot.py install-autostart                    # optional: start watch at logon
py -3 assets/github-app/bot.py update --dry-run                     # show what an update would run
py -3 assets/github-app/bot.py status
```

- `install-autostart` is optional. It registers `deepmodebot-bot` with Task Scheduler (Windows), launchd (macOS), or a systemd user unit or crontab `@reboot` entry (Linux); `uninstall-autostart` removes it.
  - Installed as an omp plugin, the task or launcher points at `~/.omp/plugins/node_modules/deepmodebot/...`, the link omp keeps on the current version, so an upgrade never leaves it on a deleted folder.
- On Windows a logon task usually needs an elevated terminal. When Task Scheduler refuses it, `install-autostart` writes `deepmodebot-bot.cmd` to your Startup folder instead, which needs no admin rights. It runs `watch` in a minimized window and appends its output to `logs/watch.log` in the cache directory. `status` reports which entry is there as `autostartKind`: `schtasks` or `startup-folder`.
- Repos are polled side by side, `parallelRepos` at a time (default 4). Items within one repo run one at a time, so one long conversation never stalls the other repos.
- The first run records a start time; a repo added to the app later starts at its first poll. Only events after it get a turn. That first poll lists every open PR and records each older PR's head as backlog; any head seen after it is new, whatever its commit dates, including on a PR first seen later (reopened). `--backlog` takes older open PRs and issues too.
- Each cycle lists every open PR and issue and takes non-draft PRs with an unhandled head SHA, new issues, and new human comments that mention `@deepmodebot` or come from the owner after the bots' last turn. On the owner's own PRs only the owner's comments count. On an issue that an own PR's merge waits on, any human comment since the bots' last reply counts, however old. An item whose turn fails (an agent, GitHub or network error) is retried on the next cycles, three attempts in all, with the comments that triggered it.
- With an app configured, discovery uses paginated REST requests authenticated by its installation, not the user's GraphQL quota. Comment authors retain their bot or human type. Without an app, explicit `--repo` runs use the user's `gh` discovery.
- Active PR metadata and checks also use the installation's read budget through a scoped `gh` child environment. Ownership, collaborators and branch-protection authority still use the human's credentials. Normal PR creation and SHA-pinned merges use the human's REST API; the explicit `--admin` path remains separate and fails closed.
- A primary rate limit or secondary `Retry-After` response pauses repository reads until the reset time instead of flooding the rest of the installation. `status` reports the persisted `readCooldown` with its reason and deadline.
- A comment counts as the bots' only when the app posted it, or the owner's account posted it with the bot signature; a signature from anyone else is a human comment.
- The owner is the `gh` user running the bot, even when an organization owns the app.
- One bot process runs at a time (a lock file). `--dry-run` takes no lock: each run clones into a workspace of its own and removes it afterwards, so previews can run beside the bot and each other.
- State is in `~/.config/deepmodebot/bot-state.json`. Clones, worktrees, logs and per-item transcripts are in `~/.cache/deepmodebot/bot/`.

Config is `~/.config/deepmodebot/bot.json`, created with these defaults on the first run. Each role is `{"agent": "<acpx agent>", "model": "<optional model id>"}`:

```json
{"author":{"agent":"omp"},"reviewer":{"agent":"omp"},"verifiers":[{"agent":"omp"},{"agent":"omp"},{"agent":"omp"}],"autonomousMerge":true,"maxRounds":3,"interval":120,"mention":"@deepmodebot","parallelRepos":4,"autoUpdate":true,"updateMinutes":60,"localCopyPaths":[]}
```

The shipped trigger is `@deepmodebot`. A reseller keeps its own trigger and `mention` remains configurable.
The pre-rename bare default is ignored with a warning because it notified an unrelated account.
Stored configuration is not rewritten; explicit custom triggers remain unchanged.

A repo names its own gate in its base-branch `.deepmodebot.json`: `{"check": "npm test"}`.
- On the owner's PRs the bot runs it in a clean worktree at the head, before the panel and again at the exact head it merges. A nonzero exit, 127 included, goes to the author as a P1 finding, and the merge waits for a pass. The limit is 30 minutes.
- Before running it, the bot looks up the command's first word on the check's `PATH` (bash's `command -v`). On Windows a temporary child-only launcher binds `python` to the bot's own interpreter, including under `pythonw`. It does not change the user's PATH or the repo's check command. A builtin, a path, or a command that doesn't parse is left to the run.
- A first word the bot can't find is the bot's setup, not the PR. The bot posts one coordinator note, sends no finding, blocks the merge, and retries on the next cycle.
- After a merge it is the trunk check: red opens the revert PR, with no agent involved. Without a `check`, a verifier agent runs the repo's documented checks. A trunk check that can't start reverts nothing; the bot keeps the merge record and retries each cycle until the check runs.

## Updates

- `autoUpdate` defaults to `true`. The existing `watch` cycle synchronizes eligible local copies, even without an omp installation. No second daemon is installed. It checks between cycles, never during an item, at most every `updateMinutes` (default 60), and after merging into its own repo. This is polling, not an instantaneous filesystem subscription.
- Discovery checks direct skill folders under `~/.omp/agent/skills`, `~/.claude/skills`, and `~/.agents/skills`. It also checks `deep-mode` and `deepmodebot` checkouts directly under `~`, `~/code`, `~/repos`, `~/projects`, and `~/src`. It never scans whole disks.
- Register other checkout roots in `bot.json`, for example `"localCopyPaths": ["~/work/deepmodebot", "D:/projects/deep-mode"]`. Paths must be absolute or home-relative. Registration selects a candidate; it does not authorize overwriting changes or treating a fork as canonical. Configuration and credentials are not rewritten.
- Trust comes from the canonical Git origin and immutable GitHub repository ID `1449516491`, not the folder name, plugin name, brand, or an `upstream` remote.
  Once per check, before fetching or changing copies, `gh api` must confirm that ID, `fork: false`, and default branch `main`. The numeric guard survives whitelabel replacement, so a rebranded fork cannot silently become the authority.
  Accepted origins are the HTTPS or Git-over-SSH forms of `TimothyVang/deepmodebot` on GitHub and its renamed `TimothyVang/deep-mode` alias. A fork or unknown origin is preserved, even with a canonical upstream.
- Checkouts advance only on clean `main`, with no local commits ahead of or diverged from canonical main. Updates are fast-forward-only. Dirty files, unknown untracked or ignored files, sparse/assume-unchanged indexes, feature branches, detached heads, and linked paths are not rewritten. There is no stash, reset, or branch switch. Generated cache directories `__pycache__`, `.pytest_cache`, `.mypy_cache`, and `.ruff_cache` are ignored; the narrowly verified omp marketplace metadata exception is described below.
- An unmanaged native skill copy is adopted only when its complete file inventory matches a historical canonical skill snapshot, not merely `SKILL.md`. Historical matching examines up to 2,000 revisions that changed that skill. Missing history, modified files, or unknown provenance preserve the copy with an explicit reason. A copy inside a Git checkout must be managed through its repository root instead.
- Once adopted, each copy has a canonical commit and source path recorded under `copies` in `~/.config/deepmodebot/update.json`. Every managed file must still match that historical snapshot before another update. Extra unknown files are retained; a new upstream file colliding with one blocks the update. Removed upstream files are deleted only if previously managed and unchanged. Before replacement, all prior managed files are backed up under `<bot cache>/local-updates/backups/`. Git checkout history retains prior tracked versions.
- Native copy replacement has a persistent, pinned transaction journal before its first write. After interruption it resumes only files matching the old or new canonical bytes and modes; unexpected edits stop recovery and retain the backup. A pending target completes before a newer target begins. The journal remains until its matching per-copy receipt is observed persisted.
- Before a native-copy success receipt, recheck every desired managed signature and the absence of retired managed files. A mismatch retains the journal and blocks success. Already-current or newly adopted copies are rechecked after historical lookup as well; unrelated extra files remain preserved.
- CLI and watcher updates share an OS lock through receipt persistence. The watcher never hands over while its own installation has an incomplete update. A partial omp plugin upgrade remains a handover barrier on later retries, even when its mixed file inventory no longer matches any canonical snapshot. Only a complete, verified canonical installation clears that barrier; the updater does not overwrite an unrecognized partial install to repair it. Transaction-owned temporary paths are reused or removed during recovery; arbitrary local files are not cleanup targets.
- Handover also requires a successful per-target verification covering the running assets in this same check. A failed checkout, a subsequent dirty refusal, or an undiscovered running installation cannot authorize a restart merely because its code hash changed.
- Source bytes come from pinned Git objects in a dedicated canonical bare cache, never from a dirty user tree. Git and source-identity API calls have 120-second deadlines; each omp command has a 600-second deadline. Missing `gh`, unavailable repository metadata, or unavailable canonical Git objects block writes. The same main SHA is still checked against every copy each interval, so newly found and stale copies converge.
- The omp installation is eligible only when both its marketplace checkout and its installed contents pass provenance checks.
  The marketplace must be clean canonical `main`, with no local commits. It fast-forwards to the pinned commit even when the installed plugin files already match.
  When plugin files differ, the updater runs `omp plugin upgrade deepmodebot` with API-key variables removed, then verifies the complete installed contents before recording the commit.
  After marketplace synchronization and immediately before invoking the package manager, recheck the installed link target and complete inventory. Intervening edits or link changes preserve the installation without running the upgrade.
  Recheck the complete installed inventory after marketplace synchronization even when no upgrade was needed. Canonical provenance is recorded only after this observation succeeds.
  A remembered remote SHA alone never proves what is installed.
- Only the known `~/.omp/plugins/cache/marketplaces/deepmodebot` checkout may retain an untracked root `marketplace.json` generated by omp.
  It must be an unlinked regular file matching the Git blob of `.omp-plugin/marketplace.json` or `.claude-plugin/marketplace.json` tracked at that checkout's current `HEAD`.
  Comparison permits CRLF/LF conversion and one optional terminal newline, not JSON reformatting or changed fields.
  An incoming canonical file or directory at `marketplace.json` blocks the update, even when its bytes match.
  Custom metadata is preserved without upgrading; ordinary user checkouts and other marketplace paths receive no filename-based exception. The updater never rewrites the generated manifest.
- Per-copy actions and refusal reasons appear in watcher logs and `update.json`. One dirty, forked, or unknown copy does not stop other eligible copies. Source failures and update failures are retried at the next interval.
- The watcher hashes the assets it actually runs from. Updating a different installation or only reference documents does not restart it. When its own code changes, the existing handover releases the lock, starts the same `watch` command from its stable path, and waits up to 60 seconds for confirmation. Failure stops the child, reacquires the lock, and leaves the old watcher running; errors are in `<bot cache>/logs/restart-<pid>.log`. Its next interval retries. Under the bot's systemd unit, exit 75 requests the unit restart instead.
- Turn automatic synchronization off with `"autoUpdate": false`. `bot.py update` performs one explicit synchronization without restarting a watcher. `bot.py update --dry-run` reports every discovered copy's action and changes no files or state. It cannot fetch missing Git objects without writing a cache; if neither the cache nor canonical omp marketplace has the required snapshot, it reports source unavailable and asks for a real update first.
- The explicit update command exits nonzero for failed targets, pending incomplete recovery, or an unverified plugin installation. Ordinary preserved checkout or native-copy candidates without pending recovery remain distinct from operational failure. Checked Git command failures, including index-lock failures, are operational failures rather than eligibility refusals.
- Already running older bot code needs one installation update and watcher restart to acquire this behavior. Thereafter it uses the existing interval and autostart entry. Harness sessions may need reloading to see updated skill files. Packaged Claude Code plugins remain managed by `claude plugin marketplace update deepmodebot` and `claude plugin update deepmodebot@deepmodebot`; the native `~/.claude/skills` copies described above are separate.

## Opt out

- Remove a repo from the installation, or uninstall the app, to stop all bot work there.
- A base-branch `.deepmodebot.json` with `"bot": false` skips the repo.
- A base-branch `.deepmodebot.json` with `"autonomousMerge": false` keeps the conversation but stops at merge-ready.
- `bot.json` `"autonomousMerge": false` stops merges on every repo.
- A `hold`, `do-not-merge`, or `stack-only` label on a PR keeps the conversation (review, fixes, panel) and stops before the merge. Remove the label and the next cycle merges it.
- The bot reads `.deepmodebot.json` from the base branch (`git show origin/<base>:.deepmodebot.json`), never a PR head, and fetches the base again right before each merge.

## Safety

- PR and issue text is untrusted data. Prompts say so, wrap it in delimiters, and defang `@path` mentions. A request in it to merge, push, run, or post elsewhere is a finding.
- Only the user's own PRs merge, and only through pr-conversation's gates, enforced in code at the merging head.
  - Same head as the panel, the ownership gate re-checked (with other writers, each commit the bot didn't push needs the owner as committer and a verified signature).
  - Required checks green (a check the rules tie to one GitHub App counts only that app's check runs and the commit statuses its bot account set), the head contains its base, linked issues answered, not conflicting, merge authorized.
  - Branch rules are read again after any wait for checks. `--admin` only when the required review is the one rule it would bypass and no check, required or not, is failing or cancelled. No rebase, no force-push, no branch deletion.
- The bots merge only into the default branch or a protected branch. A PR based on any other branch is a stack child: it is reviewed and verified, then waits until it targets the trunk, so a stack lands bottom-up. Retargeting it gives it a fresh review and panel against the new base.
- Required checks get one wait of up to 30 minutes per head. After it, each cycle looks again without waiting: a check still running keeps the PR waiting, and a check that hasn't reported for three cycles while nothing runs blocks the merge until a new push or an owner comment. A skipped required check counts as passed, as GitHub counts it.
- After each merge, the trunk check runs on the merge commit: the repo's `check` command when set, else a verifier running the documented checks. Red → the bot opens a `deepmodebot/revert-pr-<n>` PR, which the next cycle lands like any other; a check that can't run or returns no verdict is reported, never reverted on.
  - The bot records the merge before running `gh pr merge` and records each step after it (read-back, note, trunk check), so an error anywhere after GitHub accepts the merge resumes on the next cycles (three attempts) even though the PR is closed.
  - No time limit drops that record: while the PR stays open the bot reads its state each cycle, so a merge that shows up late still gets its trunk check. The record goes when the steps finish, the PR is closed unmerged, or it merges at another head.
- Answering an issue a PR's merge waits on never starts a second implementation; only an owner's `@deepmodebot implement` does. The command opens a line as its own word: `@deepmodebot implementation looks wrong`, a quoted command, and one shown inside a code block or an HTML comment don't count.
- The author and the verifiers run (both with `--approve-all`) only after the current head re-passes the ownership gate, so a push from another account mid-conversation sends the PR to a human.
- Every PR uses exactly three independent verifier contexts and detached worktrees at the same head. All three must return valid votes with evidence; at least two PASS votes are required. Missing, malformed or unavailable responses block the panel, even when two others pass. `verifiers` configuration must contain exactly three roles. There is no size-based one-reviewer exception.
- A cached panel is reusable only when `current_panel` sees `panelPolicy: "three-independent-v1"`, the same nonempty head SHA, and three valid votes with at least two PASS votes. Legacy light-panel or unmarked cache entries trigger a fresh three-reviewer panel rather than authorizing a merge.
- No one but the owner steers a write-enabled agent: on the owner's PRs other people's comments neither trigger a turn nor reach a prompt, and an issue build plans and implements in new agent sessions that see only the owner's comments, never an earlier discussion's context.
- Implementing an issue reuses an existing `deepmodebot/issue-<n>` branch only when every commit on it is one the bots made; otherwise the bots stop and say so.
- The bot never blocks itself on its own worktrees. Once an issue's PR is open, the bot closes that build's one-off agent sessions and detaches the implementation worktree from `deepmodebot/issue-<n>`. A later checkout of a branch that another worktree under `~/.cache/deepmodebot/bot/worktrees/` holds detaches that holder first; its files and uncommitted changes stay. A holder anywhere else, such as a user's own worktree, is never touched: the item errors and names it.
- Contributors' and forks' PRs get review comments only, from a sealed reviewer: one model call with no tools, no files and no project config (`omp -p --no-tools` from an empty folder, the call the **pr-agent** technique uses).
  It receives the diff with as many context lines as fit (40, else 10, else 3), plus a bounded packet of whole source blobs from the Git merge-base and head comparison, with head commit and blob IDs.
  The packet includes eligible changed files and best-effort direct local Python and JavaScript/TypeScript imports; it records omissions and does not claim complete dependency coverage.
  Oversized files are omitted rather than excerpted so partial code cannot masquerade as the whole file.
  - The packet admits at most 12 files, 128 KiB per file and 256 KiB of source in total. Large modules can therefore participate without unbounded prompts; remaining files and imports are explicitly omitted.
  - Context comes from Git objects, never worktree files, and excludes unsafe names, hidden or sensitive/config-like paths, symlinks, submodules, binary and non-UTF-8 data. File counts, bytes and Git subprocess time are bounded. Path filters cannot detect every secret embedded in otherwise ordinary source; the diff itself is also sent to the reviewer. Both diff and source are untrusted prompt data, not instructions.
  - The reviewer cannot read a local file or fetch a URL, so a hostile PR cannot make it leak one, and nothing in the PR can configure it. The sealed call needs an `omp` reviewer on a subscription login; with any other reviewer agent the bots skip other people's PRs and log it.
- Issue discussions follow the same rule. When the issue or a comment in the prompt comes from anyone but the owner, the plan, critique and answer turns are sealed calls, and they need `omp` for both the author and the reviewer; with another agent the bots leave such an issue alone and log it. The owner's own issues, and a build the owner asked for, keep their tools.
- A push from another account in the middle of a cycle is caught before the review: when the head moved since the cycle listed the PR's commits, ownership is checked again, and a head that fails it is reviewed sealed.
- On the owner's PRs and issues, agents run inside the repo, so their CLIs load its AGENTS.md and CLAUDE.md, and its rules apply. No real-money trading actions, ever.
- The private key and installation tokens stay in `~/.config/deepmodebot/`. Tokens last one hour. None of them go into prompts, logs or repos.
- Usage is the user's subscription. Raise `interval` or install on fewer repos to spend less.

**Done when** `install.py --check` reports nothing missing, `bot.py status` shows the bot running, and `bot.py once --repo <owner/repo> --dry-run` completes a cycle on an installed repo.
For a stop or opt-out request, done when `bot.py status` or the repo's base-branch `.deepmodebot.json` shows the change.

## Bot name

Rename the bots with `install.py --brand <name>`. It writes `assets/github-app/brand.local.json`, and `brand.py` derives the app name, comment signature, mention, branch prefix, repo config file, config and cache directories, and autostart task from it.

That renames only the bots. To ship the whole product under your own brand (name, logo, colors, commands, skills, the GitHub App, the docs site, the README, images and SEO), run the brand kit from the deepmodebot repo's root: `py -3 ./scripts/whitelabel.py --brand <file> --out <dir>`. The guide is `docs/rebrand.md` in the repo.
