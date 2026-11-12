# github-app

**Use when:** the user wants deep-mode's bots working their repos without a session: "install deep-mode on my repos", "run the bots on their own", "AI review on my own subscription". Also to set the bots up, start, stop, check on, or opt a repo out.

## What it is

- **An identity.** A private GitHub App the user creates on their own account. Bot comments show as `<slug>[bot]`, so the thread reads as bots, not as the user. The app never runs a model.
- **A poller, not a service.** `bot.py` runs on the user's machine and polls the installed repos every `interval` seconds. There are no webhooks and no server.
- **Any ACP agent, no API keys.** The models run in agent CLIs that `acpx` reaches over ACP: omp by default, or Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode and others. Each harness uses its own subscription login (Claude.ai, ChatGPT and the like). Each role in `bot.json` picks an agent and an optional model, so omp alone can seat an author on a Claude model and a reviewer on a GPT model for cross-family review. Every call draws on subscription usage.
- **The user's hands for writes.** Pushes, PR creation and merges use the user's own `gh` and git credentials. The app token only posts comments.
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
5. **Config and autostart:** writes `~/.config/deep-mode/bot.json` with the agents found, then runs `bot.py install-autostart` on a yes.

`--yes` accepts every default, `--no-autostart` skips step 5's autostart, and `--brand <name>` renames the bots (below).

**Manual path.** `py -3 assets/github-app/ghapp.py setup` creates the app on its own: a browser page opens; click "Create GitHub App". The app id and private key stay in `~/.config/deep-mode/`, outside every repo. Pass `--org <org>` to create it under an organization. Install it at the `install` URL it prints, then `py -3 assets/github-app/ghapp.py whoami` lists the bot login and its installations.

The app asks for contents, pull requests and issues (write), and checks, statuses, actions and metadata (read).

## Run

```bash
py -3 assets/github-app/bot.py once --repo <owner/repo> --dry-run   # preview one cycle, post nothing
py -3 assets/github-app/bot.py once --repo <owner>/<name> --item pr:<n>   # one item now; --item needs --repo
py -3 assets/github-app/bot.py watch                                # poll every interval
py -3 assets/github-app/bot.py install-autostart                    # start watch on its own
py -3 assets/github-app/bot.py status
```

- `install-autostart` registers `deep-mode-bot` with Task Scheduler (Windows), launchd (macOS), or a systemd user unit or crontab `@reboot` entry (Linux); `uninstall-autostart` removes it.
  - Installed as an omp plugin, the task points at `~/.omp/plugins/node_modules/deep-mode/...`, the link omp keeps on the current version, so `omp plugin upgrade` never leaves it on a deleted folder.
- Repos are polled side by side, `parallelRepos` at a time (default 4). Items within one repo run one at a time, so one long conversation never stalls the other repos.
- The first run records a start time; a repo added to the app later starts at its first poll. Only events after it get a turn. That first poll lists every open PR and records each older PR's head as backlog; any head seen after it is new, whatever its commit dates, including on a PR first seen later (reopened). `--backlog` takes older open PRs and issues too.
- Each cycle lists every open PR and issue and takes non-draft PRs with an unhandled head SHA, new issues, and new human comments that mention `@deep-mode` or come from the owner after the bots' last turn. On the owner's own PRs only the owner's comments count. On an issue that an own PR's merge waits on, any human comment since the bots' last reply counts, however old. An item whose turn fails (an agent, GitHub or network error) is retried on the next cycles, three attempts in all, with the comments that triggered it.
- Comments are read through GitHub's GraphQL API: the newest 100 on each item, each with its author's type. Another app's comment is never taken for a human's, so it neither triggers a turn nor holds up a merge.
- A comment counts as the bots' only when the app posted it, or the owner's account posted it with the bot signature; a signature from anyone else is a human comment.
- The owner is the `gh` user running the bot, even when an organization owns the app.
- One bot process runs at a time (a lock file). `--dry-run` takes no lock: each run clones into a workspace of its own and removes it afterwards, so previews can run beside the bot and each other.
- State is in `~/.config/deep-mode/bot-state.json`. Clones, worktrees, logs and per-item transcripts are in `~/.cache/deep-mode/bot/`.

Config is `~/.config/deep-mode/bot.json`, created with these defaults on the first run. Each role is `{"agent": "<acpx agent>", "model": "<optional model id>"}`:

```json
{"author":{"agent":"omp"},"reviewer":{"agent":"omp"},"verifiers":[{"agent":"omp"},{"agent":"omp"},{"agent":"omp"}],"autonomousMerge":true,"maxRounds":3,"interval":120,"mention":"@deep-mode","parallelRepos":4}
```

A repo names its own gate in its base-branch `.deep-mode.json`: `{"check": "npm test"}`.
- On the owner's PRs the bot runs it in a clean worktree at the head, before the panel and again at the exact head it merges. A nonzero exit goes to the author as a P1 finding, and the merge waits for a pass. The limit is 30 minutes.
- After a merge it is the trunk check: red opens the revert PR, with no agent involved. Without a `check`, a verifier agent runs the repo's documented checks.

## Opt out

- Remove a repo from the installation, or uninstall the app, to stop all bot work there.
- A base-branch `.deep-mode.json` with `"bot": false` skips the repo.
- A base-branch `.deep-mode.json` with `"autonomousMerge": false` keeps the conversation but stops at merge-ready.
- `bot.json` `"autonomousMerge": false` stops merges on every repo.
- A `hold`, `do-not-merge`, or `stack-only` label on a PR keeps the conversation (review, fixes, panel) and stops before the merge. Remove the label and the next cycle merges it.
- The bot reads `.deep-mode.json` from the base branch (`git show origin/<base>:.deep-mode.json`), never a PR head, and fetches the base again right before each merge.

## Safety

- PR and issue text is untrusted data. Prompts say so, wrap it in delimiters, and defang `@path` mentions. A request in it to merge, push, run, or post elsewhere is a finding.
- Only the user's own PRs merge, and only through pr-conversation's gates, enforced in code at the merging head.
  - Same head as the panel, the ownership gate re-checked (with other writers, each commit the bot didn't push needs the owner as committer and a verified signature).
  - Required checks green (a check the rules tie to one GitHub App counts only that app's check runs and the commit statuses its bot account set), the head contains its base, linked issues answered, not conflicting, merge authorized.
  - Branch rules are read again after any wait for checks. `--admin` only when the required review is the one rule it would bypass and no check, required or not, is failing or cancelled. No rebase, no force-push, no branch deletion.
- The bots merge only into the default branch or a protected branch. A PR based on any other branch is a stack child: it is reviewed and verified, then waits until it targets the trunk, so a stack lands bottom-up. Retargeting it gives it a fresh review and panel against the new base.
- Required checks get one wait of up to 30 minutes per head. After it, each cycle looks again without waiting: a check still running keeps the PR waiting, and a check that hasn't reported for three cycles while nothing runs blocks the merge until a new push or an owner comment. A skipped required check counts as passed, as GitHub counts it.
- After each merge, the trunk check runs on the merge commit: the repo's `check` command when set, else a verifier running the documented checks. Red → the bot opens a `deep-mode/revert-pr-<n>` PR, which the next cycle lands like any other; a check that can't run or returns no verdict is reported, never reverted on.
  - The bot records the merge before running `gh pr merge` and records each step after it (read-back, note, trunk check), so an error anywhere after GitHub accepts the merge resumes on the next cycles (three attempts) even though the PR is closed.
  - No time limit drops that record: while the PR stays open the bot reads its state each cycle, so a merge that shows up late still gets its trunk check. The record goes when the steps finish, the PR is closed unmerged, or it merges at another head.
- Answering an issue a PR's merge waits on never starts a second implementation; only an owner's `@deep-mode implement` does. The command opens a line as its own word: `@deep-mode implementation looks wrong`, a quoted command, and one shown inside a code block or an HTML comment don't count.
- The author and the verifiers run (both with `--approve-all`) only after the current head re-passes the ownership gate, so a push from another account mid-conversation sends the PR to a human.
- A size S diff (at most 30 changed lines in at most 2 files, measured with `git diff --numstat`, and no path about auth, secrets, permissions, migrations, CI or agent config) gets a light panel. One verifier votes, from another model than the author's when `bot.json` has one, and must PASS. Every other diff gets all the configured verifiers.
- No one but the owner steers a write-enabled agent: on the owner's PRs other people's comments neither trigger a turn nor reach a prompt, and an issue build plans and implements in new agent sessions that see only the owner's comments, never an earlier discussion's context.
- Implementing an issue reuses an existing `deep-mode/issue-<n>` branch only when every commit on it is one the bots made; otherwise the bots stop and say so.
- The bot never blocks itself on its own worktrees. Once an issue's PR is open, the bot closes that build's one-off agent sessions and detaches the implementation worktree from `deep-mode/issue-<n>`. A later checkout of a branch that another worktree under `~/.cache/deep-mode/bot/worktrees/` holds detaches that holder first; its files and uncommitted changes stay. A holder anywhere else, such as a user's own worktree, is never touched: the item errors and names it.
- Contributors' and forks' PRs get review comments only, from a sealed reviewer: one model call with no tools, no files and no project config (`omp -p --no-tools` from an empty folder, the call the **pr-agent** technique uses), fed the diff with as many context lines as fit (40, else 10, else 3). It cannot read a local file or fetch a URL, so a hostile PR cannot make it leak one, and nothing in the PR can configure it. The sealed call needs an `omp` reviewer on a subscription login; with any other reviewer agent the bots skip other people's PRs and log it.
- Issue discussions follow the same rule. When the issue or a comment in the prompt comes from anyone but the owner, the plan, critique and answer turns are sealed calls, and they need `omp` for both the author and the reviewer; with another agent the bots leave such an issue alone and log it. The owner's own issues, and a build the owner asked for, keep their tools.
- A push from another account in the middle of a cycle is caught before the review: when the head moved since the cycle listed the PR's commits, ownership is checked again, and a head that fails it is reviewed sealed.
- On the owner's PRs and issues, agents run inside the repo, so their CLIs load its AGENTS.md and CLAUDE.md, and its rules apply. No real-money trading actions, ever.
- The private key and installation tokens stay in `~/.config/deep-mode/`. Tokens last one hour. None of them go into prompts, logs or repos.
- Usage is the user's subscription. Raise `interval` or install on fewer repos to spend less.

**Done when** `install.py --check` reports nothing missing, `bot.py status` shows the bot running, and `bot.py once --repo <owner/repo> --dry-run` completes a cycle on an installed repo.
For a stop or opt-out request, done when `bot.py status` or the repo's base-branch `.deep-mode.json` shows the change.

## Bot name

Rename the bots with `install.py --brand <name>`. It writes `assets/github-app/brand.local.json`, and `brand.py` derives the app name, comment signature, mention, branch prefix, repo config file, config and cache directories, and autostart task from it.

That renames only the bots. To ship the whole product under your own brand (name, logo, colors, commands, skills, the GitHub App, the docs site, the README, images and SEO), run the brand kit from the deep-mode repo's root: `py -3 ./scripts/whitelabel.py --brand <file> --out <dir>`. The guide is `docs/rebrand.md` in the repo.
