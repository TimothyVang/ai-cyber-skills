# OpenAI Codex (CLI, IDE extension, desktop app, cloud)

Read when deepmodebot is running inside OpenAI Codex (CLI `codex`, the IDE extension, Codex in the ChatGPT desktop app, or `codex exec` in CI), or when you must translate deepmodebot's omp instructions (task subagents, todo, ask, `skill://`, `.omp/`, `omp -p`) into Codex equivalents.

Checked 2026-11-11 against codex-cli 0.163.0 (local `--help`), learn.chatgpt.com/docs (Codex docs moved there from developers.openai.com/codex), and github.com/openai/codex. Upstream is already at 0.167.0 per the [changelog](https://learn.chatgpt.com/docs/changelog); re-check `codex --help` if flags differ.

## 1. Install, update, auth, models

- Install: `npm install -g @openai/codex`, `brew install --cask codex`, or the install.sh / install.ps1 scripts ([README](https://github.com/openai/codex)). Update: `codex update`. Health check: `codex doctor` (codex 0.163.0 --help).
- Sign in with ChatGPT: `codex login` (browser flow, default). Usage draws on the ChatGPT plan ([auth](https://learn.chatgpt.com/docs/auth)).
- API key: `printenv OPENAI_API_KEY | codex login --with-api-key`. API-key auth bills at standard API rates on the Platform account, not plan credits ([auth](https://learn.chatgpt.com/docs/auth)).
- `CODEX_API_KEY=<key> codex exec ...` overrides the key for one run; works with `codex exec`, `codex review`, the TS SDK, `codex exec-server --remote` ([non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode)). Never export it job-wide in CI that runs repo code (same source).
- `codex login status` shows the active method; `codex logout` clears stored creds ([auth](https://learn.chatgpt.com/docs/auth)). Creds live in `~/.codex/auth.json` or the OS keyring ([config-advanced](https://learn.chatgpt.com/docs/config-file/config-advanced)).
- Model: `-m/--model`, config `model`. Effort: `model_reasoning_effort` = `low|medium|high|xhigh|max|ultra`, availability depends on model ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)). Docs recommend `gpt-6.1-sol` when the account has access; `gpt-6-luna` for fast scans ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)). `codex debug models` dumps the catalog (codex 0.163.0 --help).
- Profiles: `-p/--profile NAME` layers `~/.codex/NAME.config.toml` (top-level keys, not `[profiles.NAME]`) over `~/.codex/config.toml` ([config-advanced](https://learn.chatgpt.com/docs/config-file/config-advanced)).
- `CODEX_HOME` relocates the whole home (default `~/.codex`) ([AGENTS.md doc](https://learn.chatgpt.com/docs/agent-configuration/agents-md)).

## 2. AGENTS.md

- Global: `$CODEX_HOME/AGENTS.override.md` if non-empty, else `$CODEX_HOME/AGENTS.md`; first non-empty only ([AGENTS.md doc](https://learn.chatgpt.com/docs/agent-configuration/agents-md)).
- Project: walk from project root (Git root, or `project_root_markers`) down to cwd. Per directory take at most one of `AGENTS.override.md`, `AGENTS.md`, then names in `project_doc_fallback_filenames` (same source; [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)).
- Concatenated root to leaf; deeper files appear later and win. Empty files skipped. Stops at `project_doc_max_bytes` (default 32 KiB) combined ([AGENTS.md doc](https://learn.chatgpt.com/docs/agent-configuration/agents-md)).
- Built once per run / TUI session. Edit AGENTS.md, then start a new session ([AGENTS.md doc](https://learn.chatgpt.com/docs/agent-configuration/agents-md)).
- `CLAUDE.md` is NOT read unless listed in `project_doc_fallback_filenames`, and fallbacks only apply where no `AGENTS.md` exists in that directory [inference from the per-directory order above].
- `## Code Review Rules` sections in AGENTS.md steer Codex GitHub review ([AGENTS.md doc](https://learn.chatgpt.com/docs/agent-configuration/agents-md)).
- Subagents are spawned threads of the same session and inherit the parent's skills, MCP servers, sandbox and approvals ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)). Whether they re-read AGENTS.md is not documented [unverified]; restate critical rules in the spawn prompt.

## 3. Skills

- Format: folder with `SKILL.md` (frontmatter `name`, `description` required), optional `scripts/`, `references/`, `assets/`, `agents/openai.yaml`. Follows [agentskills.io](https://agentskills.io/specification) ([skills](https://learn.chatgpt.com/docs/build-skills)).
- Locations: `.agents/skills` in every dir from cwd up to repo root (REPO), `$HOME/.agents/skills` (USER), `/etc/codex/skills` (ADMIN), bundled SYSTEM skills `skill-creator`, `skill-installer` ([skills](https://learn.chatgpt.com/docs/build-skills)). Symlinked folders followed.
- `.codex/skills` and `~/.codex/skills` are not in the current location table; do not rely on them [unverified whether still scanned as legacy].
- Invoke: `$skill-name` in the prompt, or `/skills` picker. Implicit invocation matches `description` ([skills](https://learn.chatgpt.com/docs/build-skills)).
- Plugin skills are namespaced `plugin:skill`, e.g. `deepmodebot:deepmodebot` (observed via `codex debug prompt-input`, codex 0.163.0).
- No `disable-model-invocation` frontmatter. Equivalent: `agents/openai.yaml` with `policy: allow_implicit_invocation: false`; explicit `$skill` still works ([skills](https://learn.chatgpt.com/docs/build-skills)).
- Initial skills list uses at most 2% of context (8,000 chars if unknown); descriptions get shortened first. `skills.max_context_tokens` raises it to 10,000 ([skills](https://learn.chatgpt.com/docs/build-skills)). Front-load trigger words.
- Disable: `[[skills.config]]` with one selector (`path = ".../SKILL.md"` or `name = "..."`) and `enabled = false`; `[skills.bundled] enabled = false` drops system skills ([skills](https://learn.chatgpt.com/docs/build-skills)).
- Changes are picked up automatically; restart if not ([skills](https://learn.chatgpt.com/docs/build-skills)).

## 4. Slash commands, custom prompts, plugins, marketplaces

- Custom prompts are deprecated. They live in `~/.codex/prompts/*.md` (top level only), invoked as `/prompts:<name>`, with `$1..$9`, `$ARGUMENTS`, named `$KEY` placeholders ([custom prompts](https://learn.chatgpt.com/docs/custom-prompts)). Not repo-shareable. Use skills instead.
- Useful built-ins: `/skills`, `/plugins`, `/subagents`, `/agents`, `/plan`, `/review`, `/compact`, `/fork`, `/resume`, `/permissions`, `/status`, `/mcp`, `/hooks`, `/init`, `/goal`, `/diff` ([developer commands](https://learn.chatgpt.com/docs/developer-commands)).
- Plugins bundle skills, MCP servers, hooks; IDE extension does not support plugins; CLI uses `/plugins` browser ([plugins](https://learn.chatgpt.com/docs/plugins)). Start a new session after install.
- CLI (codex 0.163.0 --help): `codex plugin marketplace add <path|owner/repo[@ref]|git-url> [--ref R] [--sparse PATH]`, `marketplace list|upgrade [name]|remove <name>`, `codex plugin list`, `codex plugin add PLUGIN@MARKETPLACE`, `codex plugin remove`.
- Marketplace files read: `$REPO_ROOT/.agents/plugins/marketplace.json`, legacy-compatible `$REPO_ROOT/.claude-plugin/marketplace.json`, `~/.agents/plugins/marketplace.json` ([build plugins](https://developers.openai.com/plugins/build/plugins)).
- Manifests: portable root `plugin.json` (Agent Plugins schema) preferred; `.codex-plugin/plugin.json` is a fallback; "legacy and Claude-compatible manifests" accepted ([build plugins](https://developers.openai.com/plugins/build/plugins)).
- Installed copies go to `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`; enablement in config as `[plugins."<plugin>@<marketplace>"] enabled = true` ([build plugins](https://developers.openai.com/plugins/build/plugins)).
- Verified for this repo (codex 0.163.0, throwaway `CODEX_HOME`): `codex plugin marketplace add <deepmodebot checkout>` registers marketplace `deepmodebot` from `.claude-plugin/marketplace.json`; `codex plugin add deepmodebot@deepmodebot` installs 0.3.0 and all six skills load as `deepmodebot:<skill>`.
- GitHub form, same flow: `codex plugin marketplace add TimothyVang/deepmodebot` then `codex plugin add deepmodebot@deepmodebot` [inference: shorthand documented, not run against GitHub].
- Claude `commands/*.md` inside the plugin (e.g. `/deepmodebot:deep`) are copied but are not surfaced as Codex slash commands [inference: no Codex doc maps plugin `commands/`; not seen in prompt input]. Use `$deepmodebot:deepmodebot` instead.
- Plugin hooks get `PLUGIN_ROOT`, `PLUGIN_DATA`, plus `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`; they must be trusted before they run ([build plugins](https://developers.openai.com/plugins/build/plugins)).

## 5. Agent tools

| Need | Codex tool / mechanism | Source |
| --- | --- | --- |
| Shell | shell command tool; hooks see it as `Bash` | [hooks](https://learn.chatgpt.com/docs/hooks) |
| Edit files | `apply_patch` (hook matcher aliases `Edit`, `Write`) | [hooks](https://learn.chatgpt.com/docs/hooks) |
| Plan / todo | plan tool; exec JSON emits plan-update items; `/plan` mode | [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode); tool name `update_plan` [unverified] |
| Ask user | `request_user_input`, only when listed for the turn (mainly Plan mode) | codex 0.163.0 `debug prompt-input` |
| Web search | `web_search`; config `web_search = "cached"` (default), `"live"` (= `--search`), `"indexed"`, `"disabled"` | [approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security) |
| Images | `-i/--image FILE` on launch; view-image tool | codex 0.163.0 --help |
| Subagents | `spawn_agent`, `followup_task`, `send_message`, `wait_agent`, `interrupt_agent`, `list_agents` | codex 0.163.0 `debug prompt-input` |

- Subagents spawn only on explicit request from the user, AGENTS.md, or a skill ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)). So a skill saying "spawn a read-only explorer" is enough to trigger them.
- Built-in agents: `default`, `worker`, `explorer` (read-heavy) ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Custom agents: one TOML per agent in `~/.codex/agents/` or `.codex/agents/`; required `name`, `description`, `developer_instructions`; optional `model`, `model_reasoning_effort`, `model_reasoning_summary`, `model_verbosity`, `features.shell_tool = false` etc., `skills.config` ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- `sandbox_mode`, `approval_policy`, `mcp_servers` in an agent file are ignored. A custom agent cannot be made read-only by sandbox; only by instructions or `features.shell_tool = false` ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- `[agents]` config: `enabled`, `max_concurrent_threads_per_session` (legacy `max_threads`), `default_subagent_model`, `default_subagent_reasoning_effort` ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Prefer long `wait_agent` waits over polling; file edits by one agent are visible to all (codex 0.163.0 `debug prompt-input`).

## 6. Sandbox and approvals

- `-s/--sandbox read-only|workspace-write|danger-full-access`; `-a/--ask-for-approval on-request|never` (codex 0.163.0 --help). `untrusted` policy is retired and can block startup ([approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)).
- `--full-auto` and `--yolo` are absent from 0.163.0 `--help`. Use `-s workspace-write -a on-request` ("Auto" preset) or `--approve-for-me` (auto-review in workspace-write) (codex 0.163.0 --help; [approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)).
- `--dangerously-bypass-approvals-and-sandbox`: no prompts, no sandbox; only inside external isolation (codex 0.163.0 --help).
- `approvals_reviewer = "user" | "auto_review"`; `approval_policy = { granular = {...} }` for per-category prompts ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference); [approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)).
- Network off by default in workspace-write; enable with `[sandbox_workspace_write] network_access = true` or a permission profile with `network.enabled = true` (+ `features.network_proxy = true` to enforce domains) ([approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)).
- Unversioned folders default to read-only; untrusted dirs may start read-only until trusted via `/permissions` ([approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)).
- Windows native sandbox: `windows.sandbox = "mxc" | "elevated" | "unelevated"`; MXC recommended, `unelevated` has weaker network isolation and no denied read paths ([Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox); [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)). `codex sandbox [CMD]` runs a command under it (codex 0.163.0 --help).
- Subagents inherit the parent's live sandbox and approvals, including `/permissions` changes; a subagent needing new approval fails back to the parent ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).

## 7. Headless and automation

- `codex exec [PROMPT|-]` (alias `e`); stdin appended as `<stdin>` when both given (codex 0.163.0 --help). Default sandbox for exec is read-only ([non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode)).
- Flags: `--json` (JSONL events `thread.started`, `turn.started|completed|failed`, `item.*`, `error`), `-o/--output-last-message FILE`, `--output-schema FILE`, `--ephemeral`, `--skip-git-repo-check`, `--ignore-user-config`, `--ignore-rules`, `-C DIR`, `--add-dir`, `--worktree` (codex 0.163.0 --help; [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode)).
- Chain runs: `codex exec resume --last "next step"` or `codex exec resume <SESSION_ID>`; `codex exec fork` (same sources).
- Git repo required unless `--skip-git-repo-check` ([non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode)).
- Review: `codex review [--uncommitted | --base BRANCH | --commit SHA] [instructions]`; also `codex exec review` (codex 0.163.0 --help).
- Subscription billing in scripts: `codex exec` reuses the saved ChatGPT login by default; do not set `CODEX_API_KEY`/`OPENAI_API_KEY` ([non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode)).
- GitHub Action: `openai/codex-action@v1` with `openai-api-key`, `prompt` or `prompt-file`, `output-file`, `codex-args`, `safety-strategy` (Windows runners need `unsafe`) ([GitHub Action](https://learn.chatgpt.com/docs/github-action)).
- SDK: `npm install @openai/codex-sdk`; `new Codex().startThread().run(prompt)`, `resumeThread(id, { sandboxMode })` ([SDK](https://learn.chatgpt.com/docs/codex-sdk)).
- Cloud: `codex cloud exec --env ENV_ID [--attempts N] [--branch B] "task"`, `codex cloud list|status|diff|apply` (codex 0.163.0 --help).

## 8. config.toml

- User `~/.codex/config.toml`; project `.codex/config.toml` from root down to cwd (trusted projects only); precedence: CLI flags and `-c key=value` > project > profile > user > cloud-managed > `/etc/codex/config.toml` > defaults ([config-basic](https://learn.chatgpt.com/docs/config-file/config-basic)).
- Trust: `[projects."/abs/path"] trust_level = "trusted" | "untrusted"`; untrusted skips project `.codex/` config, hooks, rules ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)).
- Project-local config ignores provider, `notify`, `profile(s)`, `otel` keys; put them in user config ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)).
- Features: `[features] name = true` or `--enable/--disable NAME`; list with `codex features list` (0.163.0 shows `multi_agent`, `hooks`, `plugins`, `goals`, `worktrees`, `memories` stable+on). `--strict-config` rejects unknown keys (codex 0.163.0 --help).
- `notify = ["cmd", ...]` gets a JSON payload ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)).
- Hooks: `~/.codex/hooks.json`, `<repo>/.codex/hooks.json`, or inline `[hooks]` in either config.toml; all layers load; non-managed hooks need trust review. Events include `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop` ([hooks](https://learn.chatgpt.com/docs/hooks)).

## 9. MCP and app server

- Add: `codex mcp add NAME [--env K=V] -- CMD ARGS` or `--url URL [--bearer-token-env-var VAR]`; also `list`, `get`, `remove`, `login`, `logout` (codex 0.163.0 --help). This writes user config; agents must not run it unasked.
- Config: `[mcp_servers.NAME]` with `command`, `args`, `env`, or `url`; `startup_timeout_sec` (10), `tool_timeout_sec` (60), `enabled`, `required`, `enabled_tools`, `disabled_tools`, `default_tools_approval_mode = auto|prompt|writes|approve` ([MCP](https://learn.chatgpt.com/docs/extend/mcp)).
- MCP tool names in hooks: `mcp__<server>__<tool>` ([hooks](https://learn.chatgpt.com/docs/hooks)).
- `codex mcp-server` is removed; Codex is no longer an MCP server ([MCP server removal](https://learn.chatgpt.com/docs/mcp-server)).
- Integrations use `codex app-server` (experimental): JSON-RPC 2.0 over stdio JSONL (default), `ws://`, or `unix://`; `generate-ts`, `generate-json-schema` emit bindings ([app server](https://learn.chatgpt.com/docs/app-server); codex 0.163.0 --help).

## 10. ACP

- Codex has no native ACP mode. Use the adapter `@agentclientprotocol/codex-acp` ([agentclientprotocol/codex-acp](https://github.com/agentclientprotocol/codex-acp)), built on the app server; the older `@zed-industries/codex-acp` repo points there ([zed-industries/codex-acp](https://github.com/zed-industries/codex-acp)).
- Adapter maps model, effort, approval, sandbox, permission profiles, plan, MCP, subagent sessions; auth via ChatGPT, `CODEX_API_KEY`, or `OPENAI_API_KEY` (same sources). Zed: Agent Panel, "New Codex Thread".

## 11. Sessions

- Resume: `codex resume [ID|name] [--last] [--all] [--include-non-interactive]`; fork: `codex fork [ID] [--last]`; `codex archive|unarchive|delete <id|name>`; `codex queue` posts to a running session (codex 0.163.0 --help).
- TUI: `/resume`, `/fork`, `/compact` (summarize to free context), `/new` ([developer commands](https://learn.chatgpt.com/docs/developer-commands)).
- Worktrees: `--worktree` starts in a new managed Git worktree; TUI command offers "Browse worktrees" (codex 0.163.0 --help; [developer commands](https://learn.chatgpt.com/docs/developer-commands)). Managed worktree path is not documented [unverified].
- `codex apply` git-applies the latest agent diff; `codex cloud apply` applies a cloud task diff (codex 0.163.0 --help).

## Containing writes to the project root

- Write boundary: `workspace-write` permits writes in the workspace, which by default ALSO includes temp dirs like `/tmp` ([approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)). `/status` lists the writable dirs.
- Exclude temp: `[sandbox_workspace_write] exclude_tmpdir_env_var = true` and `exclude_slash_tmp = true` ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)). Windows `%TEMP%` handling is not documented [unverified]; check `/status`.
- Extra roots: `--add-dir DIR` (codex 0.163.0 --help) and `sandbox_workspace_write.writable_roots = [...]` ([config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)). Do not add any for contained work.
- Permission profiles (alternative to `sandbox_mode`, don't combine): `default_permissions = "contained"`, `[permissions.contained] extends = ":workspace"`, then `[permissions.contained.filesystem.":workspace_roots"]` path rules `"." = "write"`, `"**/*.env" = "deny"` ([permissions](https://learn.chatgpt.com/docs/permissions); [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference)).
- Special path keys: `:workspace_roots`, `:tmpdir`, `:slash_tmp`, `:minimal`, `:root`, absolute and `~/` paths. Narrower `deny` wins inside the profile ([permissions](https://learn.chatgpt.com/docs/permissions)). Whether `:workspace` already grants `:tmpdir` write is not stated [unverified]; set temp keys to `"read"` explicitly.
- Protected even inside roots: `.git` (and resolved gitdir), `.agents`, `.codex`, `.aws` are read-only under workspace-write ([approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)). Commits from inside the sandbox need approval [inference].
- Outside-root writes under `-a on-request` trigger an approval prompt; under `-a never` they fail ([approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)).
- Hook guard: `PreToolUse` with matcher `apply_patch` (aliases `Edit`, `Write`) or `Bash`; target path is inside `tool_input.command` (the patch text or shell string), not a separate field. Parse `*** Add/Update/Delete File:` lines [inference on patch format].
- Deny by stdout `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`, or exit code 2 with reason on stderr ([hooks](https://learn.chatgpt.com/docs/hooks)). `"ask"` is unsupported and lets the call through.
- Codex's own state, not yours: `$CODEX_HOME` (`~/.codex`) holds `config.toml`, `auth.json`, `history.jsonl`, `log/` (`log_dir`), SQLite state (`sqlite_home`), `sessions/YYYY/...`, `plugins/cache/`, `.tmp/`, `tmp/` ([config-advanced](https://learn.chatgpt.com/docs/config-file/config-advanced); [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference); local listing). `--ephemeral` skips session files (codex 0.163.0 --help).

## Traps for deepmodebot

- `task` with `agent: "scout"` / `reviewer`: no such tool. Say in prose "spawn an explorer subagent" (built-in `explorer`) or define `.codex/agents/reviewer.toml`. Read-only is instruction-only; sandbox is inherited, so a "read-only scout" can still write.
- `todo`: use the plan tool / `/plan`. `ask`: `request_user_input` exists only in Plan mode; in Default mode end the turn with the question. In `codex exec` nobody answers: decide and record the assumption.
- `skill://deepmodebot/...` paths do not resolve. Read files by real path relative to the skill folder; Codex shows each skill's file path in its skill list.
- `/skill:<name>` and `/deepmodebot:deep` do not exist. Use `$deepmodebot:deepmodebot` (plugin install) or `$deepmodebot` (folder in `.agents/skills`).
- `.omp/skills/verify-<app>/` is not discovered. Put project verify skills in `.agents/skills/verify-<app>/`. Note `.agents` is read-only to the sandbox, so creating one needs approval.
- `.omp/RULES.md` is never loaded. Put subagent rules in AGENTS.md and restate them in each spawn prompt.
- `omp -p` scripted calls: use `codex exec -s read-only --ephemeral -o out.txt "..."` on the saved ChatGPT login. Never set `OPENAI_API_KEY`/`CODEX_API_KEY` (switches to API billing).
- `local://` artifacts do not exist. Write to a gitignored dir inside the repo (not `/tmp`, which deepmodebot forbids even though Codex allows it).
- Spawning: Codex only spawns on explicit instruction, and slots are capped (4 observed). Fan out in waves; do not assume omp's 32.
- Plugin install edits `~/.codex/config.toml`; never run `codex plugin add`, `codex mcp add`, `codex login` on the user's behalf.
- `CLAUDE.md`-only repos give Codex no project instructions. Add `AGENTS.md` (or `project_doc_fallback_filenames = ["CLAUDE.md"]` in user config, with consent).
- Hooks in `.codex/hooks.json` do not run until the user trusts them; do not assume a containment hook is active. Check `/hooks`.
