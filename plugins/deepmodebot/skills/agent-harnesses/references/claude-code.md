# Claude Code harness reference

Read when deepmodebot runs inside Anthropic Claude Code (CLI `claude`, its IDE extensions, the Agent SDK, or an ACP client driving it), or when you must translate a deepmodebot instruction written for omp into Claude Code tools, files, and flags.

Checked: Claude Code 2.1.322 on Windows, 2026-11-11, against [code.claude.com/docs](https://code.claude.com/docs/en/overview) (canonical docs site; index at [llms.txt](https://code.claude.com/docs/llms.txt)) and local `claude --help`.

## Auth, billing, models

- Credential precedence, first wins: cloud provider (`CLAUDE_CODE_USE_BEDROCK` / `_VERTEX` / `_FOUNDRY`), `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN`, Anthropic profile, then subscription OAuth from `/login` ([authentication](https://code.claude.com/docs/en/authentication)).
- `ANTHROPIC_API_KEY` outranks a Pro/Max/Team login. Interactive mode asks once to approve it. In `-p` mode the key is always used when present, so API billing replaces the subscription silently ([authentication](https://code.claude.com/docs/en/authentication)).
- Subscription in CI: `claude setup-token` creates a long-lived token; export it as `CLAUDE_CODE_OAUTH_TOKEN` ([authentication](https://code.claude.com/docs/en/authentication)). Check with `claude auth status` (claude 2.1.322 --help).
- Credentials file: `~/.claude/.credentials.json` (Linux, Windows `%USERPROFILE%\.claude`), macOS Keychain ([authentication](https://code.claude.com/docs/en/authentication)).
- Models: `--model <alias|full id>`, `/model`, or `model` setting. Aliases include `default`, `best` (= `opus`), `fable`, `opus`, `sonnet`, `haiku` ([model-config](https://code.claude.com/docs/en/model-config)).
- Effort: `--effort low|medium|high|xhigh|max` (claude 2.1.322 --help), `/effort`, env `CLAUDE_CODE_EFFORT_LEVEL`; the keyword `ultrathink` raises effort for one turn ([model-config](https://code.claude.com/docs/en/model-config)).
- Update: `claude update`; install a version: `claude install [stable|latest|<ver>]` (claude 2.1.322 --help). Health: `claude doctor`.

## Memory and context files

| File | Scope |
| - | - |
| Managed: `C:\Program Files\ClaudeCode\CLAUDE.md`, `/etc/claude-code/CLAUDE.md`, `/Library/Application Support/ClaudeCode/CLAUDE.md` | Org, cannot be excluded |
| `~/.claude/CLAUDE.md`, `~/.claude/rules/*.md` | User, all projects |
| `./CLAUDE.md` or `./.claude/CLAUDE.md` | Project, committed |
| `./CLAUDE.local.md` | Personal, gitignore it |
| `.claude/rules/**/*.md` | Modular project rules; `paths:` frontmatter scopes a rule to globs |

Source: [memory](https://code.claude.com/docs/en/memory).

- Files in cwd and every ancestor load at launch, concatenated root-first; `CLAUDE.local.md` follows `CLAUDE.md` in each dir. Subdirectory files load lazily when Claude touches a file there ([memory](https://code.claude.com/docs/en/memory)).
- Imports: `@path/to/file`, relative to the importing file, max depth 4 hops. External imports need one-time approval ([memory](https://code.claude.com/docs/en/memory)).
- AGENTS.md (v2.1.277+): read only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` exists in cwd or above. A `CLAUDE.local.md` alone suppresses AGENTS.md. `AGENTS.override.md`, `AGENTS.local.md`, `.agents/` are never read ([memory](https://code.claude.com/docs/en/memory)).
- Portable fix: put `@AGENTS.md` as the first line of `CLAUDE.md`. Avoid symlinks on Windows ([memory](https://code.claude.com/docs/en/memory)).
- Setting to read both: `pluginConfigs."cc-plugin-agents-md@builtin".options.instructionFiles = "claude-md-and-agents-md"` in user settings or `/config` > Project instructions ([memory](https://code.claude.com/docs/en/memory)).
- Auto memory: `~/.claude/projects/<project>/memory/MEMORY.md` plus topic files, shared across worktrees of one repo ([memory](https://code.claude.com/docs/en/memory)).
- Subagents get the full CLAUDE.md hierarchy and a git status snapshot, but not the conversation, invoked skills, or files already read. Built-in `Explore` and `Plan` skip CLAUDE.md; custom agents can set `omitClaudeMd: true` ([sub-agents](https://code.claude.com/docs/en/sub-agents)).

## Skills and commands

| Location | Invoked as |
| - | - |
| `~/.claude/skills/<name>/SKILL.md` | `/<name>` (personal) |
| `.claude/skills/<name>/SKILL.md` | `/<name>` (project) |
| `<plugin>/skills/<name>/SKILL.md` | `/<plugin-name>:<name>` |
| `.claude/commands/<name>.md`, `~/.claude/commands/` | `/<name>` (legacy format, still works) |

Source: [skills](https://code.claude.com/docs/en/skills). Precedence: enterprise > personal > project; a skill beats a same-named command; plugin skills never collide because they are namespaced.

- Custom commands are merged into skills. Commands accept the same frontmatter except `name` and `paths` ([skills](https://code.claude.com/docs/en/skills)).
- Frontmatter: `name`, `description` (with `when_to_use`, truncated at 1,536 chars in the listing), `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`, `compatibility` ([skills](https://code.claude.com/docs/en/skills)).
- `allowed-tools` pre-approves tools only for the invoking turn; the grant clears on the next user message ([skills](https://code.claude.com/docs/en/skills)).
- Substitutions: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `$name`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}` ([skills](https://code.claude.com/docs/en/skills)).
- Own files: link them with relative markdown links from SKILL.md (`[reference.md](reference.md)`); use `${CLAUDE_SKILL_DIR}` in `` !`cmd` `` injection. For plugin skills it is the skill subdir, not the plugin root ([skills](https://code.claude.com/docs/en/skills)).
- Rendered SKILL.md is injected once and not re-read. After auto-compaction only the first 5,000 tokens of each recent skill survive (25,000 total) ([skills](https://code.claude.com/docs/en/skills)).
- Invocation: user types `/name args`; the model calls the `Skill` tool. Permission rule form: `Skill(name *)` ([tools-reference](https://code.claude.com/docs/en/tools-reference)).

## Plugins and marketplaces

- Layout: `.claude-plugin/plugin.json` (only `name` required) at plugin root; `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` at plugin root, not inside `.claude-plugin/` ([plugins-reference](https://code.claude.com/docs/en/plugins-reference)).
- Marketplace: a repo/dir with `.claude-plugin/marketplace.json` (`name`, `owner`, `plugins[]`) ([plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)).
- In session: `/plugin marketplace add <owner/repo|url|path>`, `/plugin install <plugin>@<marketplace>` ([plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)).
- CLI: `claude plugin marketplace add|list|remove|update`, `claude plugin install|i <plugin>[@marketplace] [-s user|project|local]`, `list`, `enable`, `disable`, `update`, `uninstall`, `validate <path>`, `details <name>` (claude 2.1.322 --help).
- Session-only load without installing: `claude --plugin-dir <path>` (repeatable) or `--plugin-url <zip url>` (claude 2.1.322 --help).
- Plugin components are namespaced: `/plugin-name:skill`, agents `plugin-name:agent`. Plugin subagents ignore `permissionMode`, `hooks`, `mcpServers` ([sub-agents](https://code.claude.com/docs/en/sub-agents)).

## Built-in tools

Exact names from [tools-reference](https://code.claude.com/docs/en/tools-reference): `Agent`, `AskUserQuestion`, `Bash`, `PowerShell`, `Read`, `Edit`, `Write`, `NotebookEdit`, `Glob`, `Grep`, `LSP`, `WebFetch`, `WebSearch`, `Skill`, `EnterPlanMode`, `ExitPlanMode`, `EnterWorktree`, `ExitWorktree`, `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, `TaskStop`, `TodoWrite`, `SendMessage`, `ListAgents`, `Monitor`, `CronCreate`, `CronDelete`, `CronList`, `ToolSearch`, `ListMcpResourcesTool`, `ReadMcpResourceTool`, `Workflow`.

- Subagent tool is `Agent` (older docs and SDK messages say `Task`) ([tools-reference](https://code.claude.com/docs/en/tools-reference)). The ACP adapter handles both names ([claude-agent-acp](https://github.com/agentclientprotocol/claude-agent-acp)).
- Todo: `TaskCreate/TaskGet/TaskList/TaskUpdate` replace `TodoWrite`. They are on by default only for Opus 4.7, Sonnet 4.6, Haiku 4.5 and older. Newer models get none unless `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` or `--allowedTools TaskCreate`. `CLAUDE_CODE_ENABLE_TASKS=0` swaps back to `TodoWrite` ([tools-reference](https://code.claude.com/docs/en/tools-reference)).
- `Glob` and `Grep` are absent by default on macOS, Linux, WSL; Claude uses Bash search there ([tools-reference](https://code.claude.com/docs/en/tools-reference)).
- `Edit` is exact-string replacement; requires a prior read and a unique `old_string` or `replace_all` ([tools-reference](https://code.claude.com/docs/en/tools-reference)).
- Bash: cwd persists inside working dirs; env vars do not persist; default timeout 2 min, max 10 min (`BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS`); output over ~30,000 chars spills to a file; `run_in_background: true` for servers ([tools-reference](https://code.claude.com/docs/en/tools-reference)).

## Subagents

- Files: `.claude/agents/<name>.md` (project), `~/.claude/agents/` (user), `--agents '<json>'` (session), plugin `agents/`. Priority: managed > `--agents` > project > user > plugin ([sub-agents](https://code.claude.com/docs/en/sub-agents)).
- Frontmatter: `name`, `description` (required); `tools`, `disallowedTools`, `model` (`sonnet|opus|haiku|fable|<id>|inherit`), `permissionMode`, `maxTurns`, `skills` (preload full content), `mcpServers`, `hooks`, `memory` (`user|project|local`), `background`, `omitClaudeMd`, `effort`, `isolation: worktree`, `color`, `initialPrompt` ([sub-agents](https://code.claude.com/docs/en/sub-agents)).
- Built-ins: `Explore` and `Plan` (read-only; Write and Edit denied), `general-purpose` (all subagent tools). A user/project agent named `Explore` overrides the built-in ([sub-agents](https://code.claude.com/docs/en/sub-agents)).
- Subagents run in the background by default; nesting allowed up to 3 layers ([sub-agents](https://code.claude.com/docs/en/sub-agents)).
- Restrict which agents may be spawned: permission rule `Agent(Explore)`; omit `Agent` from `tools` to forbid nesting ([sub-agents](https://code.claude.com/docs/en/sub-agents)).
- Resume or message a running subagent with `SendMessage` by agent ID or name ([tools-reference](https://code.claude.com/docs/en/tools-reference)).

## Permissions and settings

- Modes: `default` (shown as Manual; CLI alias `manual`), `acceptEdits`, `plan`, `auto` (classifier), `dontAsk` (deny anything not pre-approved), `bypassPermissions` ([permission-modes](https://code.claude.com/docs/en/permission-modes)). Set via `--permission-mode` or Shift+Tab. `-p` defaults to `default`.
- Rule syntax `Tool(specifier)`: `Bash(npm run *)` (`Bash(ls:*)` equivalent), `Read(~/secrets/**)`, `Edit(/src/**)`, `WebFetch(domain:x.com)`, `Skill(deploy *)`, `Agent(Explore)`, bare `mcp__server__tool` ([tools-reference](https://code.claude.com/docs/en/tools-reference), [permissions](https://code.claude.com/docs/en/permissions)).
- Evaluation order deny > ask > allow; first match wins; an allow cannot carve out of a deny. Deny rules hold even in `bypassPermissions` ([permissions](https://code.claude.com/docs/en/permissions), [permission-modes](https://code.claude.com/docs/en/permission-modes)).
- Path rules: `//abs/path` absolute, `/path` project-relative, `~/` home ([sandboxing](https://code.claude.com/docs/en/sandboxing)).
- Settings precedence, high to low: managed (`managed-settings.json`, MDM, server) > `--settings` > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json` ([settings](https://code.claude.com/docs/en/settings)).
- `--setting-sources user,project,local` picks which files load; `--safe-mode` disables all customizations; `--bare` skips hooks, plugins, MCP, CLAUDE.md discovery (claude 2.1.322 --help).
- Sandbox: `/sandbox` or `sandbox.enabled: true`. Runs on macOS (Seatbelt), Linux, WSL2. Native Windows runs commands unsandboxed ([sandboxing](https://code.claude.com/docs/en/sandboxing)).

## Headless and SDK

- `claude -p "<prompt>"` prints and exits. `--output-format text|json|stream-json`, `--input-format stream-json`, `--json-schema '<schema>'`, `--include-partial-messages` (claude 2.1.322 --help).
- Control: `--allowedTools`, `--disallowedTools`, `--tools "Read,Grep"` (restrict built-in set), `--permission-mode`, `--permission-prompts none` (auto-deny prompts), `--max-budget-usd`, `--max-turns N`, `--fallback-model`, `--append-system-prompt`, `--add-dir` (claude 2.1.322 --help; `--max-turns` in [cli-reference](https://code.claude.com/docs/en/cli-reference), not in local help).
- MCP isolation: `--mcp-config <file|json>` with `--strict-mcp-config` (claude 2.1.322 --help).
- Sessions: `-c/--continue`, `-r/--resume <id|name>`, `--fork-session`, `--session-id <uuid>`, `--no-session-persistence` (claude 2.1.322 --help).
- `-p` skips the workspace-trust dialog and runs project hooks and `.mcp.json` servers. Use `--bare` for scripted calls; Anthropic says it will become the `-p` default ([headless](https://code.claude.com/docs/en/headless)).
- `--bare` reads only `ANTHROPIC_API_KEY` or `apiKeyHelper`, never OAuth, so it cannot use a subscription login (claude 2.1.322 --help).
- Background sessions: `claude --bg "<prompt>"`, then `claude agents`, `attach`, `logs`, `stop`, `rm` (claude 2.1.322 --help).
- Agent SDK: verified package names `@anthropic-ai/claude-agent-sdk` (TypeScript) and `claude-agent-sdk` (Python); both normally bundle the Claude Code binary. Follow [SDK setup and usage](sdks.md) for isolated installs, examples, and authentication/product restrictions. Sources: [TypeScript upstream](https://github.com/anthropics/claude-agent-sdk-typescript), [Python upstream](https://github.com/anthropics/claude-agent-sdk-python), [quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart.md). Checked 2026-11-13.
- GitHub Actions: `uses: anthropics/claude-code-action@v1` ([github-actions](https://code.claude.com/docs/en/github-actions)).

## Hooks

- Config: `"hooks": { "<Event>": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "..." } ] } ] }` in any settings file, plugin `hooks/hooks.json`, or skill/agent frontmatter ([hooks](https://code.claude.com/docs/en/hooks)).
- Events: `SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`, `PostModelSwitch`, `Elicitation`, `ElicitationResult`, `SessionEnd` ([hooks](https://code.claude.com/docs/en/hooks)).
- Input is JSON on stdin. Exit 0: success, stdout JSON applies. Exit 2: blocking error, stderr is the reason. Other codes: non-blocking error ([hooks](https://code.claude.com/docs/en/hooks)).
- PreToolUse deny via JSON: `hookSpecificOutput.permissionDecision: "deny"` plus `permissionDecisionReason`. A hook `allow` never overrides a deny or ask rule ([hooks](https://code.claude.com/docs/en/hooks), [permissions](https://code.claude.com/docs/en/permissions)).
- Matchers use bare tool names, not `Tool(spec)` ([tools-reference](https://code.claude.com/docs/en/tools-reference)).

## MCP

- Add: `claude mcp add [-s local|project|user] [-t stdio|sse|http] [-e K=V] [-H "Header: v"] <name> <cmd|url> [-- args]`; also `add-json`, `list`, `get`, `remove`, `login`, `reset-project-choices` (claude 2.1.322 --help). Default scope `local`.
- Storage: local and user scope in `~/.claude.json`; project scope in `.mcp.json` at repo root (committed, needs per-user approval) ([mcp](https://code.claude.com/docs/en/mcp)).
- `.mcp.json` supports `${VAR}` and `${VAR:-default}`; `type` accepts `stdio`, `sse`, `http` (alias `streamable-http`), WebSocket ([mcp](https://code.claude.com/docs/en/mcp)).
- Tool names: `mcp__<server>__<tool>`. Output warns at 10,000 tokens, caps at 25,000 (`MAX_MCP_OUTPUT_TOKENS`); text over 50,000 chars spills to a file ([mcp](https://code.claude.com/docs/en/mcp)).
- `claude mcp serve` exposes Claude Code's own tools as a stdio MCP server ([mcp](https://code.claude.com/docs/en/mcp)).
- Subagents can scope servers via `mcpServers` frontmatter ([sub-agents](https://code.claude.com/docs/en/sub-agents)).

## ACP

- Claude Code has no native ACP server mode in 2.1.322 (no flag in claude 2.1.322 --help) [inference].
- ACP is provided by the adapter [agentclientprotocol/claude-agent-acp](https://github.com/agentclientprotocol/claude-agent-acp), npm `@agentclientprotocol/claude-agent-acp`, formerly `@zed-industries/claude-code-acp`. It wraps the Claude Agent SDK and supports tool permission requests, TODO lists, slash commands, client MCP servers, terminals, and subagent child sessions ([README](https://github.com/agentclientprotocol/claude-agent-acp)).
- It serves ACP v1 and draft v2; `CLAUDE_AGENT_ACP_PROTOCOL=v1|v2|auto`. `CLAUDE_CODE_EXECUTABLE` points it at an existing `claude` ([README](https://github.com/agentclientprotocol/claude-agent-acp)).
- Under ACP, the client owns permission prompts; settings, CLAUDE.md, skills still load from the Claude Code config [inference].

## Sessions, checkpoints, worktrees

- Transcripts: `~/.claude/projects/<project>/<session>.jsonl`, subagent transcripts under `<session>/subagents/`, spilled outputs under `<session>/tool-results/` ([claude-directory](https://code.claude.com/docs/en/claude-directory)).
- Checkpoints: `/rewind` or Esc twice. Only edits made by file tools are tracked; files changed only by Bash are not restorable. Snapshots in `~/.claude/file-history/<session>/` ([checkpointing](https://code.claude.com/docs/en/checkpointing), [claude-directory](https://code.claude.com/docs/en/claude-directory)).
- Compaction: `/compact` manual; auto window via `--autocompact auto|<tokens>`; `PreCompact`/`PostCompact` hooks (claude 2.1.322 --help, [hooks](https://code.claude.com/docs/en/hooks)).
- Worktrees: `claude -w <name>` creates `.claude/worktrees/<name>/` on branch `worktree-<name>`; add `.claude/worktrees/` to `.gitignore`; `.worktreeinclude` copies gitignored files ([worktrees](https://code.claude.com/docs/en/worktrees)).
- Background shell tasks: `/tasks`; `TaskStop` ends them. `-p` runs cap background commands at 10 min by default ([tools-reference](https://code.claude.com/docs/en/tools-reference)).
- Retention: `cleanupPeriodDays` (default 30) prunes transcripts and file history ([claude-directory](https://code.claude.com/docs/en/claude-directory)).

## Containing writes to the project root

- Working directories = launch dir plus `--add-dir <path>`, `/add-dir`, or `permissions.additionalDirectories` ([permissions](https://code.claude.com/docs/en/permissions)). Do not add dirs outside the repo.
- `permissions.blockWritesOutsideWorkingDirectories: true` (v2.1.314+): `Write`, `Edit`, `NotebookEdit` refuse paths outside working dirs in every mode, including `bypassPermissions`. It does not limit Bash, MCP tools, or hook programs. A repo can set it in `.claude/settings.json`; it also removes `EnterWorktree`/`ExitWorktree` ([settings-reference](https://code.claude.com/docs/en/settings-reference)).
- `acceptEdits` auto-approves edits only inside working dirs; writes elsewhere still prompt ([permissions](https://code.claude.com/docs/en/permissions)).
- Deny rules for outside paths: `"deny": ["Edit(//tmp/**)", "Edit(~/**)"]` [inference from rule syntax]. Deny beats allow and holds in all modes ([permissions](https://code.claude.com/docs/en/permissions)).
- Bash writes: `tee` targets and redirects are checked against working dirs (v2.1.269+), but arbitrary programs are not ([permissions](https://code.claude.com/docs/en/permissions)). Only the sandbox contains them.
- Sandbox writes default to: working dir, a per-user temp dir, added dirs. Sandboxed commands get `$TMPDIR` pointed at that temp dir, so temp files land outside the repo. Tune with `sandbox.filesystem.allowWrite` / `denyWrite`; `sandbox.excludedCommands` escape it ([sandboxing](https://code.claude.com/docs/en/sandboxing)). No documented key removes the temp dir [unverified]; set `TMPDIR` to `<repo>/.scratch/tmp` (deepmodebot's self-ignoring scratch folder) in the settings `env` block instead [inference].
- `CLAUDE_CODE_TMPDIR` overrides the temp dir Claude Code hands unsandboxed commands when `$TMPDIR` is unset, and also moves the session scratchpad ([sandboxing](https://code.claude.com/docs/en/sandboxing), [claude-directory](https://code.claude.com/docs/en/claude-directory)).
- Scratchpad: with a claude.ai login, Claude is given a per-session scratchpad for temp files, used instead of `/tmp`, writable without prompts: `%TEMP%\claude\<hash>\<session>\scratchpad\` on Windows, `/tmp/claude-<uid>/...` on Linux. Hooks get it as `scratchpad_dir`. Turn it off with `enableArtifact: false` ([claude-directory](https://code.claude.com/docs/en/claude-directory), [hooks](https://code.claude.com/docs/en/hooks)).
- The write block still lets through plan files, the scratchpad, and `.md` files under `~/.claude/projects/<project>/memory/`. Keep these inside the repo with `plansDirectory` (relative to the project root) and turn off auto memory with `autoMemoryEnabled: false` ([settings-reference](https://code.claude.com/docs/en/settings-reference), [memory](https://code.claude.com/docs/en/memory)).
- Path-blocking hook: `PreToolUse` with matcher `Write|Edit|NotebookEdit`. Read `tool_input.file_path` from stdin for Write/Edit; it is always absolute, with backslashes on Windows, so normalize before comparing. Compare against the stdin `cwd` field. The NotebookEdit path field name is not in the hooks schema (likely `notebook_path`) [unverified]. Exit 2 with a stderr reason, or emit `permissionDecision: "deny"` ([hooks](https://code.claude.com/docs/en/hooks)). For Bash, parse `tool_input.command` (best-effort only).
- Native Windows has no sandbox, so only the Write/Edit block and hooks apply there ([sandboxing](https://code.claude.com/docs/en/sandboxing)).
- Claude Code's own writes (not yours, never clean them): `~/.claude.json`, `~/.claude/projects/`, `~/.claude/file-history/`, `~/.claude/plans/`, `~/.claude/shell-snapshots/`, `~/.claude/backups/`; in the repo `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/agent-memory*/` ([claude-directory](https://code.claude.com/docs/en/claude-directory), [worktrees](https://code.claude.com/docs/en/worktrees), [sub-agents](https://code.claude.com/docs/en/sub-agents)). `CLAUDE_CONFIG_DIR` relocates `~/.claude`.

## Traps for deepmodebot

- omp `task` with `agent: "scout"` -> call `Agent` with `subagent_type: "Explore"` (read-only). `reviewer` -> define `.claude/agents/reviewer.md` with `tools: Read, Grep, Glob, Bash` or ship it in the plugin `agents/` dir (then `deepmodebot:reviewer`).
- Subagents start blank: put full requirements in the `Agent` prompt. `Explore`/`Plan` do not see CLAUDE.md, so restate deepmodebot rules in the prompt.
- `.omp/RULES.md` is not read. Use `CLAUDE.md`, `.claude/rules/*.md`, or `@.omp/RULES.md` from `CLAUDE.md`. A `CLAUDE.local.md` silently stops `AGENTS.md` from loading.
- omp `todo` -> `TaskCreate`/`TaskUpdate`, or `TodoWrite`. On current models neither exists by default; do not fail, keep a checklist in a repo file or ask the user to set `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`.
- omp `ask` -> `AskUserQuestion` (multiple choice). It does not exist for the model in `-p`/`dontAsk` runs; decide and record the assumption.
- `skill://deepmodebot/...` paths do not resolve. Use relative links from SKILL.md or `${CLAUDE_SKILL_DIR}/...` and open them with `Read`.
- `/skill:<name>` is omp syntax. Claude Code uses `/<name>`; plugin commands are `/deepmodebot:deep` only when installed as plugin `deepmodebot`.
- Project verify skills belong in `.claude/skills/verify-<app>/SKILL.md`, not `.omp/skills/`. Read both if the repo has the omp copy.
- `omp -p` -> `claude -p`. To stay on the subscription, unset `ANTHROPIC_API_KEY` and do not pass `--bare` (bare never reads OAuth). Use `CLAUDE_CODE_OAUTH_TOKEN` for unattended runs.
- `local://` artifacts do not exist. Write scratch files to a gitignored repo dir; Claude's own spills live under `~/.claude/projects/` and are not yours.
- Bash `export` does not persist between calls; chain with `&&`. Bash edits are not checkpointed, so prefer `Edit`/`Write` for reversibility.
