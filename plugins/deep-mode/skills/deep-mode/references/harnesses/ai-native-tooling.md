# AI-native tooling across harnesses

Read when a task touches the conventions every coding agent now shares (AGENTS.md, Agent Skills, Agent Plugins and marketplaces, llms.txt), when deep-mode runs in a harness other than omp, Claude Code or Codex (Gemini CLI, Antigravity CLI, Cursor, Copilot, OpenCode, Amp, Goose, Zed, Devin, Kiro), or when you pick browser automation, docs lookup, worktree, sandbox or orchestrator tooling for agents. MCP and ACP wire details live in the protocols file of this folder.

Checked 2026-11-11 against the linked primary docs. Local probes: omp 18.18.9, codex-cli 0.163.0, Claude Code 2.1.322. Specs: Agent Skills (agentskills.io), Agent Plugins 1.0.0 and 1.1.0, llms.txt v2.

## Portable defaults

- Instructions: one `AGENTS.md` at the repo root, nested ones per package. It is the only context file every harness below reads.
- Skills: canonical copy in `.agents/skills/<name>/SKILL.md`. Mirror to `.claude/skills/<name>/` for Claude Code and `.kiro/skills/<name>/` for Kiro (neither documents reading `.agents/skills`).
- Frontmatter: stay inside the six spec fields unless one harness needs an extension; extensions are ignored or rejected elsewhere.
- Plugins: a Claude-format plugin (`.claude-plugin/plugin.json`) loads in Claude Code, omp, Codex, Copilot CLI, VS Code and Devin. A root Agent Plugins `plugin.json` is the format Cursor, Codex, Copilot, VS Code, Kiro and Antigravity all list as portable.
- Docs: fetch `/llms.txt` or the `.md` twin of a docs page before trusting model memory.

## AGENTS.md

- Plain Markdown, no required fields or frontmatter. Nearest file to the edited file wins; explicit user prompts override all. Monorepos nest one per package ([agents.md](https://agents.md)).
- Stewarded by the Agentic AI Foundation under the Linux Foundation ([agents.md](https://agents.md)).
- Migration rule from the standard: rename the old file to `AGENTS.md` and symlink the old name to it ([agents.md](https://agents.md)).
- Claude Code 2.1.277+ reads `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in cwd or above. Adding a `CLAUDE.local.md` silently turns AGENTS.md off ([memory](https://code.claude.com/docs/en/memory)).
- Claude Code never reads `AGENTS.local.md`, `AGENTS.override.md`, or anything under `.agents/` as instructions ([memory](https://code.claude.com/docs/en/memory)).
- Safe bridge for Claude Code: a `CLAUDE.md` whose first line is `@AGENTS.md`. Prefer it over `ln -s AGENTS.md CLAUDE.md` on Windows: symlinks need admin or Developer Mode and Git checks them out as one-line text files unless `core.symlinks` is on ([memory](https://code.claude.com/docs/en/memory)).
- Codex reads `AGENTS.override.md` then `AGENTS.md` per directory from git root down to cwd, at most one per directory, capped at 32 KiB total (`project_doc_max_bytes`) ([Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md)).
- Gemini CLI reads `GEMINI.md` by default; set `{"context": {"fileName": "AGENTS.md"}}` in `.gemini/settings.json` ([agents.md](https://agents.md), [GEMINI.md docs](https://geminicli.com/docs/cli/gemini-md/)).
- Zed loads only the first match of `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`. A stray `.cursorrules` hides `AGENTS.md` ([Zed instructions](https://zed.dev/docs/ai/instructions)).
- Amp and OpenCode fall back to `CLAUDE.md` only where no `AGENTS.md` exists ([Amp](https://ampcode.com/docs/customize/agents-md), [OpenCode](https://opencode.ai/docs/rules/)). Copilot CLI loads `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md` and `GEMINI.md` together ([Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)).
- `@path` imports work in Claude Code, Amp and Copilot CLI. Copilot refuses imports outside the repo, absolute paths and `~/`, and does not expand them in `GEMINI.md` ([Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)).

## Agent Skills (SKILL.md)

Format ([spec](https://agentskills.io/specification)):

- A skill is a directory with `SKILL.md`: YAML frontmatter, then Markdown. Optional `scripts/`, `references/`, `assets/`.
- Required: `name` (1-64 chars, `a-z0-9-`, no leading, trailing or double hyphen, must equal the parent directory name) and `description` (1-1024 chars, what it does and when to use it).
- Optional: `license`, `compatibility` (max 500 chars), `metadata` (string map), `allowed-tools` (space-separated, experimental).
- Progressive disclosure: catalog (`name` + `description`, about 100 tokens) at startup; full body on activation (keep under 500 lines, under 5000 tokens); resources only when read. Relative paths resolve from the skill root.
- Validate: `skills-ref validate ./my-skill` ([spec](https://agentskills.io/specification)).
- Cross-client discovery convention: `<project>/.agents/skills/` and `~/.agents/skills/`; project overrides user on name collision; gate project skills on folder trust ([client guide](https://agentskills.io/client-implementation/adding-skills-support)).

Where each harness looks (project | user | explicit invoke):

| Harness | Project dirs | User dirs | Invoke |
|---|---|---|---|
| Claude Code | `.claude/skills/` in cwd and parents to repo root; nested dirs load on first file touch | `~/.claude/skills/` | `/name` ([skills](https://code.claude.com/docs/en/skills)) |
| Codex | `.agents/skills/` in cwd and each parent to repo root; `/etc/codex/skills` admin | `~/.agents/skills/` | `$name` ([skills](https://developers.openai.com/codex/skills)) |
| omp | `.omp/skills/` up the tree, plus `.claude`, `.agents`, `.codex`, `.opencode`, `.github/skills` providers | `~/.omp/agent/skills/` | `/skill:name` ([skills](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)) |
| Gemini CLI | `.gemini/skills/`, `.agents/skills/` (alias wins) | `~/.gemini/skills/`, `~/.agents/skills/` | `activate_skill` tool, `/skills` ([skills](https://geminicli.com/docs/cli/skills/)) |
| Antigravity CLI | `.agents/skills/` up to repo root; `.gemini/skills/` NOT read | `~/.gemini/config/skills/` (+ legacy) | `/name` ([skills](https://antigravity.google/docs/skills), [migration](https://antigravity.google/docs/cli/gcli-migration)) |
| Cursor | `.cursor/skills/`, `.agents/skills/` anywhere in repo (scoped to subtree), `.claude/skills/`, `.codex/skills/` | `~/.cursor/skills/`, `~/.agents/skills/`, `~/.claude/skills/`, `~/.codex/skills/` | `/name` ([skills](https://cursor.com/docs/skills)) |
| GitHub Copilot (CLI, cloud agent, VS Code, app) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/`, `~/.agents/skills/` | `/name` ([skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)) |
| OpenCode | `.opencode/skills`, `.claude/skills`, `.agents/skills`, cwd up to root | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` | `skill` tool, `@id` ([skills](https://opencode.ai/docs/skills/)) |
| Amp | `.agents/skills/`, `.claude/skills/` in project and parents | `~/.config/agents/skills/`, `~/.agents/skills/`, `~/.config/amp/skills/`, `~/.claude/skills/` | ask, `amp skills list` ([skills](https://ampcode.com/docs/customize/skills)) |
| Goose | `.agents/skills/` (+ `.goose/skills/`, `.claude/skills/`) | `~/.agents/skills/` (+ `~/.claude/skills/`) | `/skills name` ([skills](https://goose-docs.ai/docs/guides/context-engineering/using-skills/)) |
| Zed agent | `.agents/skills/` | `~/.agents/skills/` | `/name`, `@skill` ([skills](https://zed.dev/docs/ai/skills)) |
| Devin Desktop / CLI (ex-Windsurf) | `.devin/skills/`, `.agents/skills/`, `.windsurf/skills/` | `~/.config/devin/skills/`, `~/.agents/skills/` | `/name` ([customizations](https://docs.devin.ai/desktop/devin-local/customizations)) |
| Kiro | `.kiro/skills/` | `~/.kiro/skills/` | `/name` ([skills](https://kiro.dev/docs/skills/)) |

Frontmatter beyond the spec:

- `disable-model-invocation: true` (slash-only) is honored by Claude Code, Cursor, VS Code/Copilot, OpenCode and Zed ([Cursor](https://cursor.com/docs/skills), [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills), [OpenCode](https://opencode.ai/docs/skills/), [Zed](https://zed.dev/docs/ai/skills)).
- Codex docs do not list it [inference: Codex ignores it]. Codex uses `agents/openai.yaml` with `policy: allow_implicit_invocation: false` inside the skill folder ([Codex skills](https://developers.openai.com/codex/skills)).
- Cursor adds `paths` globs; VS Code adds `user-invocable`, `argument-hint`, `context: fork` ([Cursor](https://cursor.com/docs/skills), [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills)).
- claude.ai uploads, the Skills API and `package_skill.py` hard-fail on any non-spec key ([Claude skills](https://code.claude.com/docs/en/skills)).
- Never put `/` or `:` in `name`. VS Code silently drops the skill; plugins add the `plugin:` prefix themselves ([VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills)).
- OpenCode derives the skill ID from the path, not `name` ([OpenCode](https://opencode.ai/docs/skills/)).

Installers: `npx skills add <owner/repo>` (project by default, `-g` global, `-a <agent>`) ([vercel-labs/skills](https://github.com/vercel-labs/skills)); `gh skill` ([Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)); `gemini skills install <git-url>` ([Gemini](https://geminicli.com/docs/cli/skills/)); `amp skill add <source>` ([Amp](https://ampcode.com/docs/customize/skills)). Each writes files: under deep-mode that is a config change, so install into the repo or ask.

## Plugins and marketplaces

Agent Plugins 1.0 / 1.1 ([spec](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md), [site](https://agent-plugins.org)):

- Root `plugin.json` with `"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"`. Closed top-level fields: `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`.
- Fixed component paths: `skills/<name>/SKILL.md` (immediate children only, no recursion) and root `mcp.json` with its own `$schema`. No inline components, no path overrides.
- stdio MCP `command` is one token (bare name or `./` path). `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` expand in `args`, `env`, `cwd` only.
- Commands, agents, hooks, rules and LSP are client-specific. Put them under `extensions` keyed by reverse domain and a same-named top-level directory (e.g. `com.github.copilot/`) ([Copilot plugin ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)).
- The spec defines no marketplace catalog [inference: no catalog section in spec 1.0.0 or 1.1.0].
- Listed clients: VS Code, Cursor, GitHub Copilot, ChatGPT and Codex, Kiro, Hermes Agent, OpenClaw, Grok Bot, NanoClaw, OpenHands, Perplexity Computer, Google Antigravity. Claude Code is not listed ([compatible clients](https://agent-plugins.org/compatible-clients)).

Claude-format plugins: `<plugin>/.claude-plugin/plugin.json` plus `skills/`, `commands/`, `agents/`, `hooks/`, `.mcp.json`. Repo catalog `.claude-plugin/marketplace.json` needs `name` (kebab-case), `owner`, `plugins[]` with each `name` and `source` (`./` relative, no `..`). Check with `claude plugin validate <dir>` ([Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Copilot plugin ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)).

| Client | Plugin manifests read | Catalogs read | Add / install |
|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `.claude-plugin/marketplace.json` | `claude plugin marketplace add <owner/repo>`, `/plugin install p@m` ([docs](https://code.claude.com/docs/en/plugin-marketplaces)) |
| omp | Claude format, root Agent Plugins `plugin.json`, `package.json` `omp.extensions` | `.omp-plugin/marketplace.json`, else `.claude-plugin/marketplace.json` | `/marketplace add <owner/repo>`, `omp plugin install` ([docs](https://github.com/can1357/oh-my-pi/blob/main/docs/marketplace.md)) |
| Codex / ChatGPT | root `plugin.json`, `.codex-plugin/plugin.json` fallback, Claude-compatible manifests | `.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`, `~/.agents/plugins/marketplace.json` | `codex plugin marketplace add <src>`, `codex plugin add` ([docs](https://developers.openai.com/codex/plugins/build), codex-cli 0.163.0 --help) |
| Copilot CLI | root Agent Plugins; legacy `.plugin/`, `plugin.json`, `.github/plugin/`, `.claude-plugin/` | `marketplace.json`, `.plugin/`, `.github/plugin/`, `.claude-plugin/` | `copilot plugin marketplace add <owner/repo>`, `copilot plugin install p@m` ([ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)) |
| VS Code | Agent Plugins, Copilot, Claude, legacy OpenPlugin | `chat.plugins.marketplaces` setting | Chat: Install Plugin From Source ([ref](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference)) |
| Cursor | root `plugin.json` or `.cursor-plugin/plugin.json` only | `.cursor-plugin/marketplace.json` | Customize page, team marketplaces, `~/.cursor/plugins/local` ([docs](https://cursor.com/docs/plugins)) |
| Devin | `.devin-plugin/` > `.claude-plugin/` > root `plugin.json` | team marketplace | `devin plugins` ([docs](https://docs.devin.ai/cli/extensibility/plugins/overview)) |
| Goose | `plugin.json`, `.plugin/`, `.goose-plugin/`, `gemini-extension.json` | none documented | ([docs](https://goose-docs.ai/docs/guides/context-engineering/plugins/)) |
| Gemini / Antigravity CLI | `gemini-extension.json` / Antigravity plugins | official marketplace | `gemini extensions install <url>`, `agy plugin install <url or path>` ([Gemini](https://geminicli.com/docs/extensions/), [Antigravity](https://antigravity.google/docs/skills)) |

- A root Agent Plugins `plugin.json` outranks `.claude-plugin/plugin.json` in Copilot CLI, and Agent Plugins components load only from fixed paths ([Copilot plugin ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)). [inference: root `commands/` then stops loading in Copilot.]
- `${CLAUDE_PLUGIN_ROOT}` expands in Cursor, VS Code and Copilot. Cursor does not expand `${PLUGIN_ROOT}` or `${PLUGIN_DATA}` ([Cursor ref](https://cursor.com/docs/reference/plugins), [VS Code ref](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference)).
- Installed plugins run from a cache, not your checkout. Reinstall after editing (Copilot: `~/.copilot/installed-plugins/`; Codex: `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`) ([Copilot](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating), [Codex](https://developers.openai.com/codex/plugins/build)).

## Other harnesses at a glance

| Harness | Context files | Headless | MCP config | ACP |
|---|---|---|---|---|
| Gemini CLI | `GEMINI.md` (user `~/.gemini/GEMINI.md` + project tree), `context.fileName` | `gemini -p "..." --output-format json` | `mcpServers` in `settings.json` | `gemini --acp` ([headless](https://geminicli.com/docs/cli/headless/), [ACP](https://geminicli.com/docs/cli/acp-mode/), [MCP](https://geminicli.com/docs/tools/mcp-server/)) |
| Antigravity CLI `agy` | workspace `GEMINI.md` and `AGENTS.md`, `~/.gemini/GEMINI.md` | `agy -p "..." --output-format json` or `stream-json` | `.agents/mcp_config.json`, `~/.gemini/config/mcp_config.json` | [unverified] ([headless](https://antigravity.google/docs/cli/headless), [migration](https://antigravity.google/docs/cli/gcli-migration)) |
| Cursor IDE + CLI `agent` | `AGENTS.md` root and nested, `.cursor/rules/*.mdc` (plain `.md` ignored) | `agent -p "..."`; `--force` runs unapproved actions; `--output-format json` | `.cursor/mcp.json`, `~/.cursor/mcp.json` | `agent acp` ([rules](https://cursor.com/docs/rules), [headless](https://cursor.com/docs/cli/headless), [ACP](https://cursor.com/docs/cli/acp)) |
| Copilot CLI | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.github/instructions/**`, `.claude/rules/**` | `copilot -p "..." -s`; `--allow-all-tools` or `--yolo` | `~/.copilot/mcp-config.json`; repo `.mcp.json` needs trust | `copilot --acp` ([CLI ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)) |
| OpenCode | `AGENTS.md`, `CLAUDE.md` fallback, `~/.config/opencode/AGENTS.md` | `opencode run "..."` | `mcp` in `opencode.json(c)` | `opencode acp` ([rules](https://opencode.ai/docs/rules/), [CLI](https://opencode.ai/docs/cli/), [ACP](https://opencode.ai/docs/acp/)) |
| Amp | `AGENTS.md` cwd, parents, subtrees; `~/.config/amp/AGENTS.md` | `amp -x "..."`, `--stream-json`; `amp -ox` runs in a cloud orb | `amp.mcpServers`, `--mcp-config`, skill-bundled `mcp.json` | third-party `amp-acp` only ([execute](https://ampcode.com/docs/cli/execute-mode), [MCP](https://ampcode.com/docs/customize/mcp), [registry](https://agentclientprotocol.com/get-started/registry)) |
| Goose | `AGENTS.md`, `.goosehints`; `CONTEXT_FILE_NAMES` | `goose run -t "..."` | extensions in `~/.config/goose/config.yaml` | `goose acp` ([hints](https://goose-docs.ai/docs/guides/context-engineering/using-goosehints/), [CLI](https://goose-docs.ai/docs/guides/goose-cli-commands/)) |
| Zed agent | first match list above; `~/.config/zed/AGENTS.md` | none, editor only [inference] | `context_servers` in settings | ACP client; hosts Claude, Codex, Gemini, OpenCode, Copilot, Cursor ([external agents](https://zed.dev/docs/ai/external-agents)) |
| Devin Desktop / CLI | `AGENTS.md`, `AGENTS.local.md`, `AGENT.md` per dir; `.devin/rules/`; legacy `.windsurf/rules/` | `devin -p "..."` | `.devin/mcp_config.json`, `~/.config/devin/mcp_config.json` | `devin acp` ([customizations](https://docs.devin.ai/desktop/devin-local/customizations), [commands](https://docs.devin.ai/cli/essential-commands), [Zed](https://docs.devin.ai/cli/acp/zed)) |
| Kiro IDE + `kiro-cli` | `.kiro/steering/*.md`, `AGENTS.md` | `kiro-cli chat --no-interactive "..."`; `--trust-all-tools` | `.kiro/settings/mcp.json`, `~/.kiro/settings/mcp.json` | `kiro-cli acp` ([steering](https://kiro.dev/docs/steering/), [headless](https://kiro.dev/docs/cli/headless/), [ACP](https://kiro.dev/docs/cli/acp/)) |

- Gemini CLI stopped serving Google AI Pro, Ultra and free users on 2026-06-18; they move to Antigravity CLI. Paid API keys and Code Assist Standard or Enterprise keep Gemini CLI ([Google blog](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli)).
- Antigravity ignores `.gemini/skills/`; move workspace skills to `.agents/skills/`. `agy plugin import gemini` migrates extensions and MCP ([migration](https://antigravity.google/docs/cli/gcli-migration)).
- Windsurf docs now redirect to Devin Desktop; rule and skill dirs moved from `.windsurf/` to `.devin/`, legacy still read ([customizations](https://docs.devin.ai/desktop/devin-local/customizations)).
- Copilot CLI in `-p` mode skips workspace MCP, repo hooks and project extensions unless the folder is trusted or `GITHUB_COPILOT_PROMPT_MODE_WORKSPACE_MCP=true` / `_REPO_HOOKS=true` / `_EXTENSIONS=true` ([CLI ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)).
- Cursor `agent -p` writes workspace files even without `--force` ([headless](https://cursor.com/docs/cli/headless)).
- Amp CI needs an `AMP_API_KEY` access token (`sgamp_...`); the `amp login` session token is rejected ([execute](https://ampcode.com/docs/cli/execute-mode)).

## Browser automation for agents

- Playwright: `npx @playwright/mcp@latest`. Its README tells coding agents to prefer the CLI plus skills, which skips large tool schemas: `npm install -g @playwright/cli@latest`, then `playwright-cli install --skills` ([playwright-mcp](https://github.com/microsoft/playwright-mcp), [playwright-cli](https://github.com/microsoft/playwright-cli)).
- Playwright MCP flags: `--headless`, `--isolated` (profile in memory), `--user-data-dir`, `--storage-state`, `--output-dir`, `--caps=vision,pdf,devtools`. A persistent profile serves one browser at a time; parallel agents need `--isolated` or distinct `--user-data-dir` ([playwright-mcp](https://github.com/microsoft/playwright-mcp)).
- `playwright-cli` sessions: `-s=<name>` or `PLAYWRIGHT_CLI_SESSION=<name>` per agent; headless sessions exit after an hour idle ([playwright-cli](https://github.com/microsoft/playwright-cli)).
- Chrome DevTools MCP: `npx -y chrome-devtools-mcp@latest` for perf traces, network, console with source-mapped stacks. Flags `--headless`, `--isolated`, `--browser-url`, `--autoConnect`, `--slim`. Also ships a `chrome-devtools` CLI and skills ([repo](https://github.com/ChromeDevTools/chrome-devtools-mcp), [config](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md)).
- agent-browser (Vercel, Rust): `npm install -g agent-browser`, `agent-browser install`, then `open <url>`, `snapshot -i`, `click @e1`. One daemon and browser per `--session`. `agent-browser skills get core` prints usage that matches the installed CLI ([repo](https://github.com/vercel-labs/agent-browser)).
- Proof rule: screenshots and traces are artifacts; name the file inside the repo (see containment section).

## Docs for agents

- `llms.txt`: at `/llms.txt` or any subpath (`/docs/llms.txt`); the most specific file wins. Only an H1 is required; then a blockquote summary and H2 link lists. `## Optional` links are skippable. Pages may offer `page.md` or `page.html.md` twins ([llmstxt.org](https://llmstxt.org)).
- Observed 2026-11-11: agentskills.io, opencode.ai, code.claude.com and code.visualstudio.com serve `.md` page twins; cursor.com returns Markdown for `Accept: text/markdown`; ampcode.com serves `/docs/markdown/<page>`.
- Context7: remote MCP `https://mcp.context7.com/mcp` with `Authorization: Bearer <key>`; tools `resolve-library-id` then `query-docs`. CLI: `ctx7 library <name> <query>`, `ctx7 docs <libraryId> <query>`. `npx ctx7 setup` edits agent config ([context7](https://github.com/upstash/context7)).
- Prefer the vendor's own docs or changelog over a docs MCP when they disagree; cite the vendor page.

## Isolation and orchestration

- Git worktrees give each agent its own checkout and branch. Fresh worktrees lack gitignored deps and `.env`; `.worktreeinclude` at the repo root lists gitignored files to copy (Claude Code and Orca) ([Claude worktrees](https://code.claude.com/docs/en/worktrees), [Orca worktrees](https://www.onorca.dev/docs/model/worktrees)).
- Orca (stablyai/orca): desktop ADE running Claude Code, Codex and other agents in parallel worktrees, local, SSH or cloud ([repo](https://github.com/stablyai/orca)). Share big gitignored dirs with `worktree.sharedDirectories` in `orca.yaml` ([worktrees](https://www.onorca.dev/docs/model/worktrees)).
- Orca CLI: `orca worktree create --repo id:<id> --name <n> --json`; `orca orchestration run-create --objective "..."`, `task-create --spec "..."`, `worker-start --task <id> --worktree new-child --agent codex|claude|antigravity`, `check --wait` ([CLI](https://www.onorca.dev/docs/cli/overview), [orchestration](https://www.onorca.dev/docs/cli/orchestration)).
- Conductor kept workspaces under `~/conductor/workspaces/<repo>/<name>`. Conductor Cloud shuts down 2026-11-20 per Orca's migration guide; conductor.build says it is joining Meta ([migration](https://www.onorca.dev/docs/migrate-from-conductor), [conductor.build](https://www.conductor.build)).
- Claude Code agent teams: experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Teammates share a task list and message each other; token cost is much higher than subagents ([agent teams](https://code.claude.com/docs/en/agent-teams)).
- Cloud sandboxes: Codex Cloud environments, Amp orbs, Cursor Cloud Agents, Copilot cloud agent, Kiro web, Devin Cloud. Only repo-level skills travel. User skills (`~/.agents/skills`, `~/.cursor/skills`) stay local unless synced ([client guide](https://agentskills.io/client-implementation/adding-skills-support), [Cursor](https://cursor.com/docs/skills), [Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [Codex Cloud](https://developers.openai.com/codex/cloud)).
- Devcontainers: `.devcontainer/devcontainer.json`; `npm install -g @devcontainers/cli`, `devcontainer up --workspace-folder .`, `devcontainer exec`. Override the mount with `workspaceMount` plus `workspaceFolder` (each requires the other) ([spec](https://containers.dev/implementors/json_reference/), [CLI](https://github.com/devcontainers/cli)).

## Containing writes to the project root

Worktree placement:

| Tool | Default worktree path | Inside repo? | Change it |
|---|---|---|---|
| Claude Code `--worktree` | `.claude/worktrees/<name>/`, branch `worktree-<name>` | yes; add `.claude/worktrees/` to ignores | default is fine ([worktrees](https://code.claude.com/docs/en/worktrees)) |
| Codex app | `$CODEX_HOME/worktrees` | no | Settings > Worktrees ([Codex worktrees](https://developers.openai.com/codex/app/worktrees)) |
| Orca | `~/orca/workspaces/<repo>/<name>` (nested) or flat `<dir>/<name>` | no | per-project Worktree Location ([issue #27015](https://github.com/stablyai/orca/issues/27015), user-filed [unverified in Orca docs]) |
| Conductor | `~/conductor/workspaces/<repo>/<name>`; older `.conductor/` in repo | no / yes | ([migration](https://www.onorca.dev/docs/migrate-from-conductor)) |
| plain git | wherever `git worktree add <path>` points | your choice | use `<repo>/.worktrees/<name>` ([git-worktree](https://git-scm.com/docs/git-worktree)) |

- Inside-repo worktrees must be ignored or they show as untracked ([Claude worktrees](https://code.claude.com/docs/en/worktrees)). deep-mode puts a `.gitignore` of `*` inside `.worktrees/` and `.scratch/`, which needs no write under `.git/` (Codex's sandbox makes `.git` read-only). The local-only alternative is `echo '/.worktrees/' >> "$(git rev-parse --git-common-dir)/info/exclude"`.
- `$GIT_COMMON_DIR/info/exclude` is per-repo, uncommitted, shared by every linked worktree, and its patterns anchor at the repo root ([gitignore](https://git-scm.com/docs/gitignore)). Linked worktree admin data lives in `$GIT_DIR/worktrees/<id>` inside `.git` ([git-worktree](https://git-scm.com/docs/git-worktree)).
- ripgrep honors `.gitignore`, `.ignore`, `.rgignore`, `$GIT_DIR/info/exclude` and `core.excludesFile` ([ripgrep guide](https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md)). Watchers, build tools and test runners may still walk a nested worktree ([issue #27015](https://github.com/stablyai/orca/issues/27015)). Add it to each tool's own exclude (tsconfig `exclude`, test ignore patterns) [inference].
- Sibling layouts (`../app.worktrees/`, `~/orca/workspaces`, `$CODEX_HOME/worktrees`) sit outside the project root. Under deep-mode, repoint them inside the repo or ask before using them.
- Temp files: Python `tempfile` uses `TMPDIR`, then `TEMP`, then `TMP`, before platform defaults like `/tmp` or `C:\TEMP` ([tempfile](https://docs.python.org/3/library/tempfile.html)). Export `TMPDIR`, `TEMP` and `TMP` as `<repo>/.scratch/tmp`. Other runtimes may ignore these variables [inference].
- Devcontainer: bind only the repo (`workspaceMount` `source=${localWorkspaceFolder},target=/workspaces/<name>,type=bind`). Container writes outside the mount never reach the host and vanish on rebuild [inference] ([spec](https://containers.dev/implementors/json_reference/)).
- Browser artifacts: Playwright MCP `--output-dir <repo>/.scratch/pw` covers auto-named files; explicit filenames resolve against the workspace root ([playwright-mcp](https://github.com/microsoft/playwright-mcp)). chrome-devtools-mcp `--isolated` puts its profile in a temp dir; pass `--user-data-dir <repo>/.scratch/chrome` instead ([config](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md)).
- Agent Plugins path containment covers package files only. It does not sandbox plugin subprocesses ([spec](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md)).

Tool-owned state outside the repo (not yours; do not clean it, do not report it as a leak):

- Playwright MCP profile: `%USERPROFILE%\AppData\Local\ms-playwright\mcp-{channel}-{workspace-hash}`, `~/.cache/ms-playwright/...` on Linux ([playwright-mcp](https://github.com/microsoft/playwright-mcp)).
- chrome-devtools-mcp profile: `$HOME/.cache/chrome-devtools-mcp/chrome-profile` ([config](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md)).
- Copilot: `~/.copilot/installed-plugins/`, `~/.cache/copilot/marketplaces/`; Codex: `~/.codex/plugins/cache/`; Agent Plugins `PLUGIN_DATA` dirs ([Copilot ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference), [Codex](https://developers.openai.com/codex/plugins/build)).

## Traps for deep-mode

- `.omp/skills/verify-<app>/` is invisible outside omp. Put verify skills in `.agents/skills/verify-<app>/` (read by Codex, Gemini, Antigravity, Cursor, Copilot, OpenCode, Amp, Goose, Zed, Devin and omp). Also mirror to `.claude/skills/` for Claude Code and `.kiro/skills/` for Kiro.
- Claude Code makes its own: `/run-skill-generator` writes `.claude/skills/run-<name>/`, and `/verify` writes `.claude/skills/verify/SKILL.md` ([Claude skills](https://code.claude.com/docs/en/skills)). Check those before creating a new verify skill.
- On Windows, mirror skills by copying, not symlinking. Git checks symlinks out as text files without `core.symlinks` ([memory](https://code.claude.com/docs/en/memory)). Harnesses that read both dirs may list a skill twice; omp drops identical copies ([omp skills](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md)).
- `.omp/RULES.md` reaches omp only. Rules every harness must see go in `AGENTS.md`. Delegates still need them restated in the brief.
- Adding `CLAUDE.md` or `CLAUDE.local.md` to an AGENTS.md repo hides AGENTS.md from Claude Code. Use a `CLAUDE.md` that starts with `@AGENTS.md`. In Zed, delete stray `.rules` or `.cursorrules` or AGENTS.md never loads.
- `skill://deep-mode/...` resolves only in omp. Elsewhere resolve paths relative to the folder holding deep-mode's `SKILL.md`; open the files with the normal read tool.
- `/skill:<name>` is omp syntax. Use `/name` (Claude Code, Cursor, Copilot, Zed, Kiro, Devin), `$name` (Codex), `@name` (OpenCode), `/skills name` (Goose).
- deep-mode's `disable-model-invocation: true` is not a documented Codex field [inference: Codex may auto-invoke the skill]. Add `agents/openai.yaml` with `policy: allow_implicit_invocation: false` to keep it explicit-only there ([Codex skills](https://developers.openai.com/codex/skills)).
- `/deep-mode:poteto` comes from the Claude-format `commands/` dir. Agent Plugins defines no commands, and Cursor and Goose document no `.claude-plugin/` loading. Where the command is missing, invoke the deep-mode skill directly.
- Adding a root Agent Plugins `plugin.json` makes Copilot CLI ignore the Claude-layout `commands/`. If you add one, put Copilot-specific components under `com.github.copilot/` ([Copilot plugin ref](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)).
- `omp -p` on the subscription maps to `claude -p`, `codex exec`, `gemini -p` / `agy -p`, `agent -p`, `copilot -p`, `opencode run`, `amp -x`, `goose run -t`, `devin -p`, `kiro-cli chat --no-interactive`. Use each tool's signed-in login. Never mint a model API key; Amp CI tokens are account tokens.
- `todo`, `ask`, `task` with `agent: "scout"` or `reviewer` are omp tool names. Elsewhere use the harness's own plan or todo tool and subagents, or Orca orchestration workers when running under Orca.
- `local://` artifacts do not exist elsewhere. Write artifacts under the repo's `.scratch/` (self-ignoring), never system temp.
- Parallel browser proofs collide on one Playwright profile. Give each delegate `--isolated` or its own `-s=<session>`, `--session`, or `--user-data-dir` inside the repo.
- Running under Orca or the Codex app: the session cwd may already be a worktree outside the original checkout. Treat that worktree root as the project root and keep writes inside it.
