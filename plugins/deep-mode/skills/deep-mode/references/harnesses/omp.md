# omp (oh-my-pi) harness reference

Read when deep-mode runs inside omp, when you must translate a deep-mode instruction into an omp tool, path, or flag, or when you script omp headlessly (`omp -p`, `--mode json|rpc|acp`).

Checked: omp 18.18.9 on 2026-11-11. Sources: bundled docs (`read omp://<file>.md`, mirrored in the repo's [docs/](https://github.com/can1357/oh-my-pi/tree/main/docs) folder) and `omp --help`. Doc links below point at the repo copy; the local `omp://` copy is authoritative for 18.18.9.

## 1. Install, update, auth, models

| Need | Command or key | Source |
| --- | --- | --- |
| Update omp / plugins | `omp update`; `omp update --plugins --check` lists outdated plugins | (omp 18.18.9 --help), [marketplace.md](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md) |
| Log in (subscription OAuth) | `/login [provider]` in session, `omp login [provider]` in terminal | [providers.md](https://github.com/can1357/oh-my-pi/blob/main/docs/providers.md) |
| Show plan quotas | `omp usage` | (omp 18.18.9 --help) |
| Isolated auth/sessions/settings | `--profile <name>` or `OMP_PROFILE`; agent dir becomes `~/.omp/profiles/<name>/agent` | [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md) |
| Shell shortcut for a profile | `omp --profile work --alias omp-work` | (omp 18.18.9 --help) |

- Subscriptions: `anthropic` (Claude Pro/Max) and `openai-codex` (ChatGPT/Codex) are OAuth providers reached through `/login`, not env vars. Each org/workspace counts as its own account; multiple accounts rotate. [providers.md](https://github.com/can1357/oh-my-pi/blob/main/docs/providers.md)
- Credential precedence: `--api-key` > `models.yml` `apiKey` > stored OAuth > `/login`-saved key > extension fallback > env var / `.env` > other stored keys. [providers.md](https://github.com/can1357/oh-my-pi/blob/main/docs/providers.md)
- An exported `ANTHROPIC_API_KEY` loses to stored OAuth, but `--api-key` wins over everything. Never pass `--api-key` when the user wants subscription billing. [inference]
- Model flags: `--model <fuzzy|provider/id>`, `--smol`, `--slow`, `--plan` (env `PI_SMOL_MODEL`, `PI_SLOW_MODEL`, `PI_PLAN_MODEL`), `--models a,b` for Ctrl+P cycling. (omp 18.18.9 --help)
- `--thinking off|minimal|low|medium|high|xhigh|max|auto`. (omp 18.18.9 --help)
- Roles live in `modelRoles` in `config.yml` (`default`, `smol`, `slow`, `plan`, plus custom like `review`, `judge`, `advisor`). Values are selectors with optional `:level`, e.g. `openai/gpt-5.4:high`. Agent frontmatter `model: "@review"` resolves through `modelRoles.review`. [task-agent-discovery.md](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md)

## 2. Context files and rules

- Context files are auto-injected in a `<repo-rules>` block. Do not tell the agent to go read `AGENTS.md`. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- Native: `~/.omp/agent/AGENTS.md` (user) and `.omp/AGENTS.md` in the nearest non-empty `.omp/` walking up from cwd. Discovery stops at that `.omp/`; it does not fall back to a farther one. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- Imported conventions: standalone `AGENTS.md` and `CLAUDE.md` (walk up to repo root), `.claude/CLAUDE.md` (cwd only), `.gemini/GEMINI.md`, `.github/copilot-instructions.md`, `.agent(s)/AGENTS.md`. Foreign user-level files (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, ...) load only if listed in `enabledProviders`. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- Precedence: one user file total; one project file per directory depth; same depth, higher provider priority wins (`native` 100, `claude` 80, `codex` 70, `github` 30, `agents-md`/`claude-md` 10). Closer-to-cwd files inject last (most prominent). [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- `@path` inside a context file inlines another file (relative to that file, max 5 hops, not inside code spans). [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- `RULES.md` (`~/.omp/agent/RULES.md`, nearest `.omp/RULES.md`) is a sticky always-apply rule carried on every request and survives long sessions. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- Subagents: `task` subagents drop every file named `AGENTS.md` but still get `RULES.md`. Put subagent-binding rules in `RULES.md`. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- Other rule sources become rulebook rules: `.omp/rules/*.{md,mdc}`, `.cursor/rules/*.mdc`, `.cursorrules`, `.windsurf/rules`, `.clinerules`, `.github/instructions/**/*.instructions.md` (read as `rule://<name>`). [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md), [config-usage.md](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md)
- Switches: `--no-context-files` (subagents inherit it), `--no-rules`; per-file `disabledExtensions: [context-file:user:CLAUDE.md]`; whole source `disabledProviders: [claude]` (also drops that source's MCP, skills, commands, hooks). [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md), [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- `SYSTEM.md` / `APPEND_SYSTEM.md` customize the system prompt; flags `--system-prompt`, `--append-system-prompt`. [config-usage.md](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md)

## 3. Skills

| Source (priority) | Path |
| --- | --- |
| native (100) | `~/.omp/agent/skills/<name>/SKILL.md`, `<ancestor>/.omp/skills/<name>/SKILL.md` (every ancestor to repo root) |
| skillshare (95) | `omp skill install` packages, pinned in `.omp/skills.lock.json` |
| omp-plugins (90) | `skills/` inside extension packages and `~/.omp/plugins/node_modules` |
| claude (80) | `.claude/skills/`; `~/.claude/skills/` only when `claude` is in `enabledProviders` |
| agent-plugins (75) | root `plugin.json` packages, `skills/<name>/SKILL.md` |
| claude-plugins, agents, codex (70) | Claude marketplace plugins, `.agent(s)/skills`, `.codex/skills` |
| github (30) | `.github/skills/<name>/SKILL.md` |

Sources: [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md), [config-usage.md](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md).

- Layout is one level deep: `skills/<name>/SKILL.md`. Nested groups are not discovered. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- Frontmatter: `name`, `description` (required for native and omp-plugins skills), `globs`, `alwaysApply`, `hide`, `disable-model-invocation` (normalized to `disableModelInvocation`, same as `hide`), `enabled: false`. Hidden skills leave the catalog but stay reachable by `skill://` and `/skill:`. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- `skill://<name>` reads `SKILL.md`; `skill://<name>/<rel>` reads inside the skill dir; `..` and absolute paths are rejected. In `bash`, `skill://<name>` is the directory. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- Name collisions: the loser stays reachable as `skill://<namespace>/<name>` and `/skill:<namespace>/<name>`. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- `/skill:<name> [args]` injects the skill body as a user-invoked message (needs `skills.enableSkillCommands`). [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- Filters: `--skills git-*,docker`, `--no-skills`, `skills.ignoredSkills`, `skills.includeSkills`, `skills.manualSkills`. Subagents inherit the session's skill list. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)

## 4. Commands, plugins, marketplaces

- Slash command files: `.omp/commands/*.md` (project beats user), `~/.omp/agent/commands/*.md`, `.claude/commands/**/*.md` (subdir `foo/bar.md` also registers `foo:bar`), `.codex/commands/*.md`, `.opencode/commands/*.md`, `.agent(s)/commands/*.md`. [slash-command-internals.md](https://github.com/can1357/oh-my-pi/blob/main/docs/slash-command-internals.md)
- Plugin commands are prefixed `<plugin>:<command>`, so a plugin `deep-mode` with `commands/deep.md` is `/deep-mode:deep`. [slash-command-internals.md](https://github.com/can1357/oh-my-pi/blob/main/docs/slash-command-internals.md)
- Marketplaces read `.omp-plugin/marketplace.json`, falling back to `.claude-plugin/marketplace.json` (Claude Code format). [marketplace.md](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md)
- CLI: `omp plugin marketplace add <owner/repo|url|path>`, `omp plugin install [--scope user|project] name@marketplace`, `omp plugin list|enable|disable|uninstall|upgrade|discover`, `--dry-run` previews. TUI: `/marketplace add|install|...`, `/plugins`, `/reload-plugins`. [marketplace.md](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md)
- User installs: `~/.omp/plugins/installed_plugins.json`; project installs: `.omp/plugins/installed_plugins.json`. Project shadows user. [marketplace.md](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md)
- After TUI marketplace installs run `/reload-plugins`; new hooks, tools, and extension modules need a session restart. [marketplace.md](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md)
- One-off: `--plugin-dir <dir>` (repeatable). (omp 18.18.9 --help)

## 5. Agent tools

Default tools: `read bash edit write grep glob lsp python notebook browser task todo web_search ask` (`computer` off by default). `--tools a,b` restricts; `--no-tools` disables built-ins. (omp 18.18.9 --help)

- `task` spawns subagents. Default batch shape `{ context, tasks: [{ name?, agent?, task, solutionSpace, ... }] }`. `agent` goes on each item; a top-level `agent` is rejected. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- Bundled agents: `scout`, `reviewer`, `security-reviewer`, `task`, `sonic`; `seance` when spawnable. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- Custom agents: `.omp/agents/*.md`, `~/.omp/agent/agents/*.md`, extension `agents/`, Claude marketplace plugin agents. `.claude/agents`, `.codex/agents`, `.gemini/agents` are NOT loaded. Export bundled ones with `omp agents unpack [--project]`. [task-agent-discovery.md](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md), (omp 18.18.9 --help)
- Agent frontmatter: `name`, `description` (required), `tools`, `spawns`, `model`, `thinking-level`, `output`, `blocking`, `structured`, `autoloadSkills`, `read-summarize`, `prewalk`, `advisor`. [task-agent-discovery.md](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md)
- Model resolution: `task.agentModelOverrides` > agent frontmatter `model` > task role/session fallback. Per-call `model` only works when `task.perCallModel` is on and the model is operator-approved. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- With `async.enabled` (default true) spawns run in background; results auto-deliver; `wait` blocks; `read proc://<id>` inspects; `write proc://<id>/kill` cancels; `write agent://<id>` messages a live agent. `task.maxConcurrency` default 32. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md), `omp config list`
- Subagents run with `tools.approvalMode: yolo`; any call resolving to `prompt` fails in them. Parent-owned `todo` is stripped from children. Children finish via a hidden `yield` tool. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- `todo`: session todo list (`todo.enabled`). `ask`: structured user questions, interactive only; in `rpc-ui` it emits `extension_ui_request` frames. [tools/todo.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/todo.md), [tools/ask.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/ask.md), [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- `eval`: persistent Python/JS kernels with helpers incl. `agent()`, `workpool()`, `browser`. `lsp`: code intelligence (`--no-lsp` disables). [tools/eval.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/eval.md), [tools/lsp.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/lsp.md)

Internal URLs (work in `read`, `write`, `grep`, `bash`):

| URL | Meaning |
| --- | --- |
| `skill://<name>[/path]` | skill files |
| `rule://<name>` | rulebook rule |
| `local://<file>` | session scratch root, shared with subagents |
| `artifact://<id>` | spilled tool output |
| `agent://<id>` / `history://<id>` | subagent output / concise transcript |
| `proc://<id>` | jobs and services; `/kill` cancels |
| `xd://<tool>` | mounted tool device; write JSON args |
| `mcp://<uri>` | MCP resource |
| `omp://<doc>` | bundled omp docs |

Sources: [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md), [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md), [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md), and the runtime system prompt of omp 18.18.9 [unverified in docs for `xd://` semantics beyond approval-mode.md].

## 6. Permissions, plan mode, goal mode

| `tools.approvalMode` | Auto-approves | Prompts |
| --- | --- | --- |
| `always-ask` | read | write, exec |
| `always-ask-cached` | read without file targets, granted paths | file reads, write, exec |
| `write` | read, write | exec |
| `yolo` (default) | all | none |

Source: [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md).

- Flags: `--approval-mode <mode>`, `--auto-approve` / `--yolo`. Per-tool: `tools.approval.<tool>: allow|deny|prompt`; MCP tools keyed `mcp__<server>_<tool>`. `bash.patterns` rules; project layers can tighten but not loosen operator rules. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [settings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md)
- Approval is not a sandbox: an approved bash command has full ambient filesystem and network access. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md)
- Plan mode is read-only (`plan.enabled`, `plan.defaultOnStartup`; ignored in print mode). `--plan-yolo` starts in plan mode, auto-approves the first plan, then implements on `--plan-yolo-into` (default `smol` role). [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Goal mode: `/goal` or `omp --goal "<objective>"` (interactive only, needs `goal.enabled`; rejects `-p`, stdin, resume, `--plan-yolo`). [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Plan-mode subagents get only `read`, `grep`, `glob`, `web_search` (+ `ast_grep`). [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)

## 7. Headless and scripting

- `omp -p "prompt"` runs once and exits. Piped stdin selects print mode automatically. `@file` attaches files. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- `--mode text|json|rpc|rpc-ui|acp`. `json`: NDJSON events (`message_end` carries full messages). `rpc`: line-delimited JSON commands over stdio, not JSON-RPC 2.0. `--no-ui` makes extensions headless. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md), [rpc.md](https://github.com/can1357/oh-my-pi/blob/main/docs/rpc.md)
- Exit codes: nonzero on terminal turn failure; `3` when `--max-cost` stops the run. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- `--wait-async` keeps print mode alive until background jobs finish and re-wakes the session; pair with `--max-time 2h`. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Isolation for scripted calls: `--no-session`, `--no-context-files`, `--no-rules`, `--no-skills`, `--no-extensions`, `--no-lsp`, `--no-tools`, `--tools`, `--config <overlay.yml>` (repeatable, never persisted), `--cwd`, `--add-dir`. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md), [settings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md)
- Sessions: `-c/--continue`, `-r/--resume <id|path>`, `--restore <path>` (resumes interrupted turn and its subagents), `--fork <session>`, `--session-dir`, `--export <file>` (HTML). [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Import foreign sessions: `--from-claude` or `--from-codex` (mutually exclusive; not with `--continue/--resume/--fork/--no-session`). [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Budget guards: `--max-time`, `--warn-cost`, `--max-cost`. (omp 18.18.9 --help)
- Programmatic embedding: SDK documented in `omp://sdk.md`. [sdk.md](https://github.com/can1357/oh-my-pi/blob/main/docs/sdk.md)

## 8. Hooks and extensions

- Load: `--hook <file>`, `-e/--extension <file>`, `extensions:` setting, plugin packages. `--no-extensions` disables discovery. Native hook dirs: `.omp/hooks/pre/*.{ts,js}`, `.omp/hooks/post/*.{ts,js}`, `~/.omp/agent/hooks/pre|post/`. A file directly in `hooks/` is not found. The factory must still call `pi.on(...)`. [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md)
- Hook module: `export default function (pi: HookAPI) { pi.on("tool_call", async (event, ctx) => ...) }`. [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md)
- `tool_call` (pre) may return `{ block, reason, input, additionalContext }`; `block: true` or a throw stops the tool (fails closed). `tool_result` (post) may override `content`, `details`, `isError`. Other events: `before_agent_start`, `context`, `session_before_*`, `session.compacting`. [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md)
- `before_subagent_spawn` can route or block task spawns. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- The `claude-plugins` provider lists hooks among Claude plugin content, but only `.ts`/`.js` hook factories enter the extension pipeline. Claude command hooks from `hooks/hooks.json` and SKILL.md `hooks:` frontmatter are not documented as executed. [unverified] [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md), [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md)

## 9. MCP

- Native config: `.omp/mcp.json` (project) and `~/.omp/agent/mcp.json` (user; per profile). Also reads `.omp/.mcp.json`, root `mcp.json` / `.mcp.json`. [mcp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md)
- Imported: Claude Code (`~/.claude.json`, `~/.claude/mcp.json`, `.claude/.mcp.json`), Codex (`~/.codex/config.toml`, `.codex/config.toml` `[mcp_servers.*]`), Gemini, OpenCode, Cursor (`.cursor/mcp.json`), Windsurf, VS Code (`.vscode/mcp.json`), plugins. Project entry precedes same-named user entry. [mcp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md)
- Manage with `/mcp` (e.g. `/mcp add`). There is no `omp mcp` subcommand in 18.18.9: `omp mcp --help` falls through to `launch`. [mcp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md), (omp 18.18.9 --help)
- Tools register as `mcp__<server>_<tool>` (lowercased, max 64 chars), approval tier `write`. Large rosters are mounted as `xd://mcp__...` devices: `read xd://<tool>` for schema, then `write` JSON args to it. Server instructions enter the system prompt unless `instructions: false`. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [mcp-config.md](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md)
- Resources: `read mcp://<uri>`; MCP-advertised `skill://` URIs are readable when no local skill owns the name. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)

## 10. ACP

- omp is an ACP **agent** (server): `omp acp` or `omp --mode acp`, stdio. Launch flags before `acp` are forwarded. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Approval in ACP: same settings resolver; no per-session approval field in `session/new`, so set `tools.approvalMode`, or start `omp acp --yolo` / `--approval-mode yolo` / `--config file`. Prompts use `session/request_permission`; `ask` uses form elicitation when the client advertises `elicitation.form`. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [tools/ask.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/ask.md)
- omp emits `_omp/compaction/start|end` ACP extension notifications. [compaction.md](https://github.com/can1357/oh-my-pi/blob/main/docs/compaction.md)
- omp as an ACP **client** (driving other ACP agents): not found in 18.18.9 docs or `--help`. [unverified]

## 11. Settings, sessions, compaction

- Settings layers, high to low: runtime flags > setting env vars > `--config` overlays (and `PI_CONFIG_FILES`) > project `<cwd>/.omp/config.yml` (+ `settings.json`, other providers) > global `~/.omp/agent/config.yml` > defaults. Arrays replace, never merge. Project settings are read from cwd's `.omp/` only (no ancestor walk). [settings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md)
- CLI: `omp config list [--json] [--scope global|project]`, `get <key>`, `set <key> <v>` (writes global), `reset <key>`, `path`. TUI: `/settings`. `cfg://` is a settings internal URL that writes like `cfgX.set` [unverified beyond config-usage.md mention]. [settings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md), [config-usage.md](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md)
- Sessions: JSONL under `~/.omp/agent/sessions/--<cwd-slug>--/`; subagent transcripts and artifacts sit beside the parent session. `omp gc` prunes storage. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md), [session.md](https://github.com/can1357/oh-my-pi/blob/main/docs/session.md)
- Compaction: `/compact [instructions]`, automatic at threshold, on overflow, and on length stops; `compaction.enabled`, `compaction.methodOrder` (incl. `shake`, snapcompact, `handoff`). `/handoff` writes a handoff summary. RULES.md survives compaction; opening context does not stay prominent. [compaction.md](https://github.com/can1357/oh-my-pi/blob/main/docs/compaction.md), [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)

## Containing writes to the project root

- omp has no filesystem sandbox. Approval modes gate whether a call runs, not where it writes; approved `bash`/`eval` keep ambient filesystem access. `/tmp` and `$TMPDIR` are not blocked by any default. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md) [inference for TMPDIR]
- `tools.restrictedFolders: [~/secrets, C:/work/x]` forces an explicit approval for every action inside those folders, even in `yolo`. Without a UI (print mode, subagents) such calls are refused. Path-less tools (`bash`, `eval`, MCP) match only by their `cwd`, not command text. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md)
- `--approval-mode always-ask-cached` prompts before file reads and every write/exec; grants are per file or folder. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md)
- `bash.patterns` `deny` rules match tokenized segments (e.g. a `match` on `rm -rf *` denies `cd /tmp && rm -rf build`); they do not cover the same command run through `eval`, so add `tools.approval.eval: prompt|deny`. [settings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md), [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md)
- Hook enforcement: a `tool_call` handler sees `event.toolName` and `event.input` (e.g. `input.path` for `write`/`edit`, `input.command` for `bash`) and returns `{ block: true, reason }` to deny. A throwing handler also blocks. [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md) [inference for exact `path` field name per tool]
- Extra roots: `--add-dir <dir>` widens the workspace (and its context-file discovery); `--cwd <dir>` pins the start dir. Omit `--add-dir` to keep one root. (omp 18.18.9 --help), [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- Isolated subagents (`task.isolation.enabled`, item `isolated: true`) work in a separate checkout (ovnfs, clone, or reflink backends) and merge back as patches or `omp/task/<id>` branches. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- omp's own state, not the agent's work: `~/.omp/agent/` (`config.yml`, `mcp.json`, `agent.db`, `approval-cache.db`, `sessions/`, `managed-skills/`), `~/.omp/plugins/`, `~/.omp/run/session-owners`, and XDG dirs when initialized. `local://`, `artifact://`, and `agent://` files live in the session artifact dir under `sessions/`, outside the repo [inference]. `omp config path` prints the agent dir. [settings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md), [session.md](https://github.com/can1357/oh-my-pi/blob/main/docs/session.md), [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md)
- `local://` is therefore outside the project root. If deep-mode forbids writes outside the repo, keep durable artifacts in a repo path (gitignored) and treat `local://` as omp-managed scratch only. [inference]

## Traps for deep-mode

- Subagent rules in `AGENTS.md` are invisible to `task` subagents. Put them in `.omp/RULES.md` (nearest non-empty `.omp/` only) or in the task `context`. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- An empty `.omp/` is skipped, but a non-empty nearer `.omp/` without `RULES.md` hides the repo-root `.omp/RULES.md`. Check which `.omp/` wins from the cwd. [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- Batch `task` calls reject a top-level `agent`. Write `tasks: [{ agent: "scout", ... }]`. `solutionSpace` is required per item. [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- Subagents run yolo and headless: any `prompt` policy, `ask`, or restricted-folder access fails there. Keep `ask` and `todo` in the main session; children have no `todo`. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [tools/task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- Custom agents in `.claude/agents/` are ignored; define deep-mode agents in `.omp/agents/*.md` or ship them in the plugin's `agents/`. [task-agent-discovery.md](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md)
- Verify skills must be `.omp/skills/verify-<app>/SKILL.md` with a `description`, or omp skips them; nested `skills/group/x/` is not discovered. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- `skill://deep-mode/...` resolves only if the skill name is exactly `deep-mode`; on a collision it may become `skill://<namespace>/deep-mode`. [skills.md](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)
- Scripted model calls: use `omp -p` with OAuth from `/login`; never add `--api-key` (it outranks OAuth). Add `--no-session` and a `--config` overlay disabling the user context file so the caller's instructions do not leak into the callee. [providers.md](https://github.com/can1357/oh-my-pi/blob/main/docs/providers.md), [context-files.md](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)
- `omp -p` exits when the prompt is answered; background subagents die with it unless `--wait-async`. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- `plan.defaultOnStartup` is ignored in print mode; use `--plan-yolo` for unattended plan-then-build. [cli-reference.md](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md)
- `/deep-mode:deep` exists only after the marketplace plugin is installed and `/reload-plugins` (or a new session) ran. [marketplace.md](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md)
- `local://` artifacts live in the session store, outside the repo [inference]. Use them only for transient handoffs inside one session; anything a later session, the user, or a report needs goes in `<root>/.scratch/`.
- Default approval is `yolo`: nothing stops writes outside the repo unless a `tool_call` hook does. deep-mode ships one, `assets/contain/omp-contain.ts`: copy it to `~/.omp/agent/hooks/pre/` (or `<repo>/.omp/hooks/pre/`) or pass `--hook <path>`. It blocks `write`, `edit`, and `ast_edit` outside the root and allows session stores; `bash` and `eval` stay uncovered, so pair it with `bash.patterns` deny rules if needed. [approval-mode.md](https://github.com/can1357/oh-my-pi/blob/main/docs/approval-mode.md), [hooks.md](https://github.com/can1357/oh-my-pi/blob/main/docs/hooks.md)
