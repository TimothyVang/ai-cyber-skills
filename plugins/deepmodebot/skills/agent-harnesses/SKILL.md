---
name: agent-harnesses
description: "Cited, dated facts for using and scripting omp, Claude Code, Codex, and Antigravity SDKs: installation, embedding, config paths, flags, hooks, skills, headless runs, permissions, and MCP/ACP/A2A protocols. Use when installing SDKs, building agent applications, or configuring, scripting, or comparing an agent harness or protocol."
metadata:
  as-of: "2026-11-13"
---

# Harnesses, protocols, and AI-native tooling

Read when deepmodebot runs outside omp, when a task uses, configures, or scripts omp, Claude Code, or Codex, or when it touches MCP, ACP, A2A, WebMCP, skills, plugins, `AGENTS.md`, hooks, or sandboxes. deepmodebot's text names omp tools; this skill translates them and carries the cited facts.

Checked 2026-11-11 against primary docs and local `--help` of omp 18.18.9, Claude Code 2.1.322, and codex-cli 0.163.0. Every cell below is cited in the file for that harness. Versions move fast: recheck a flag or path before you build on it. `[inference]` and `[unverified]` marks in the files mean what they say.

| File | Read when |
|---|---|
| `references/omp.md` | Running in omp, scripting `omp -p`, omp hooks, approval modes, `task` agents, `omp acp` |
| `references/claude-code.md` | Running in Claude Code, `claude -p`, the Agent SDK, `.claude/` settings, hooks, permissions, plugins |
| `references/codex.md` | Running in Codex CLI, IDE, app, or cloud; `codex exec`, `config.toml`, sandbox and approvals, plugins |
| `references/sdks.md` | Installing or embedding Antigravity, Claude Agent, Codex, or omp SDKs; package names, tool APIs, isolated setup, CLI versus SDK auth, and local smoke checks |
| `references/protocols.md` | Building, configuring, testing, or securing MCP servers and clients; ACP; A2A; WebMCP |
| `references/ai-native-tooling.md` | Portable `AGENTS.md` and Agent Skills, plugin and marketplace formats, other harnesses (Gemini, Antigravity, Cursor, Copilot, OpenCode, Amp, Goose, Zed, Devin, Kiro), browser automation, docs for agents, orchestrators |
| `references/self-authoring.md` | Writing prompts, commands, or skills from inside a session; native goal and loop modes (`/goal`, `/loop`, ralph-loop, `/autoresearch`); headless loop flags and cost caps; skill spec and validation; self-modification risks |
| `references/delegation-efficiency.md` | Whether to delegate; which model and effort per task type in omp, Claude Code, and Codex; current model line-ups and prices; subscription limits; caching and token-saving; spend caps |

## Cross-harness map

| deepmodebot needs | omp | Claude Code | Codex |
|---|---|---|---|
| Add its marketplace | `omp plugin marketplace add TimothyVang/deepmodebot` | `/plugin marketplace add TimothyVang/deepmodebot` | `codex plugin marketplace add TimothyVang/deepmodebot` |
| Install deepmodebot | `omp plugin install deepmodebot@deepmodebot` | `/plugin install deepmodebot@deepmodebot` | `codex plugin add deepmodebot@deepmodebot` |
| Start deepmodebot | `/deepmodebot:deep <task>` | `/deepmodebot:deep <task>` | `$deepmodebot:deepmodebot <task>` (plugin `commands/` don't load) |
| Read a skill file | `skill://<name>/<path>` | `${CLAUDE_PLUGIN_ROOT}/skills/<name>/<path>`, or relative to the skill folder | Real path from the skill list Codex shows |
| Invoke a skill | `/skill:<name>` | `/<name>`; plugin skills `/deepmodebot:<name>` | `$<name>`; plugin skills `$deepmodebot:<name>` |
| Context file | `AGENTS.md`/`CLAUDE.md` walking up to the repo root, `.omp/AGENTS.md`; subagents get only `.omp/RULES.md` | `CLAUDE.md`, `.claude/rules/*.md`; `AGENTS.md` only when no `CLAUDE.md` exists | `AGENTS.md` (and `AGENTS.override.md`) from repo root down to cwd, 32 KiB cap; no `CLAUDE.md` |
| Project skills (verify skills) | `.omp/skills/<name>/` (also reads `.claude/`, `.codex/`, `.agents/` skills) | `.claude/skills/<name>/` only | `.agents/skills/<name>/` (sandbox makes `.agents` read-only) |
| User skills | `~/.omp/agent/skills/` | `~/.claude/skills/` | `~/.agents/skills/` |
| Subagents | `task`; agents `scout` (read-only), `reviewer`, `task`, `sonic` | `Agent`; `Explore` and `Plan` (read-only), `general-purpose` | `spawn_agent`; `explorer`, `worker`, `default`; spawns only when told |
| Todo list | `todo` (main session only) | `TaskCreate`/`TaskUpdate`, or `TodoWrite`; may be off on current models | Plan tool, `/plan` |
| Ask the user | `ask` (interactive only) | `AskUserQuestion` (not in `-p`) | `request_user_input` (Plan mode only) |
| Headless run on the subscription | `omp -p --mode json`; never `--api-key` | `claude -p --output-format json`; unset `ANTHROPIC_API_KEY`, no `--bare` | `codex exec --json`; unset `OPENAI_API_KEY` and `CODEX_API_KEY` |
| Fence writes to the root | No sandbox; deepmodebot's `skill://deepmodebot/assets/contain/omp-contain.ts` hook | deepmodebot's plugin `hooks/hooks.json` plus skill hook; `permissions.blockWritesOutsideWorkingDirectories`; sandbox off on native Windows | `-s workspace-write` plus `[sandbox_workspace_write] exclude_tmpdir_env_var = true`, `exclude_slash_tmp = true` |
| Hook that blocks a tool call | `.omp/hooks/pre/*.ts`, `tool_call` returns `{ block: true, reason }` | `PreToolUse` in settings, plugin `hooks/hooks.json`, or skill frontmatter; `permissionDecision: "deny"` | `PreToolUse` in `.codex/hooks.json` after the user trusts it; path is inside `tool_input.command` |
| MCP servers | `.omp/mcp.json`, `~/.omp/agent/mcp.json`; imports Claude, Codex, Cursor, VS Code configs; `/mcp` | `.mcp.json` (project), `claude mcp add -s local\|project\|user` | `[mcp_servers.<name>]` in `config.toml`; `codex mcp add` |
| ACP | Native: `omp acp` | Adapter `agentclientprotocol/claude-agent-acp` | Adapter `agentclientprotocol/codex-acp` |
| Worktrees | `.worktrees/<branch>` (deepmodebot); isolated `task` subagents | `claude -w <name>` makes `.claude/worktrees/<name>/` in the repo | The app defaults to `$CODEX_HOME/worktrees` (outside the repo); use `.worktrees/` |
| Session store you must not treat as yours | `~/.omp/agent/sessions/` (`local://`, `artifact://`) | `~/.claude/projects/`, `~/.claude/plans/` | `~/.codex/sessions/` |

## Rules that hold in every harness

- deepmodebot's **Contain the work** section (SKILL.md) wins over any harness default: scratch in `<root>/.scratch/`, worktrees in `<root>/.worktrees/`, never system temp. Codex and Claude Code both make temp dirs writable by default.
- Subagents in every harness start without your conversation. Put the goal, root, files, rules, and acceptance check in the brief.
- deepmodebot's own model runs use the user's subscription. SDK applications have separate provider/authentication requirements; follow `references/sdks.md` and obtain explicit approval for API billing. Never assume a CLI subscription authorizes an SDK product.
- Secrets and logins follow `skill://secrets-and-auth` in every harness: never read or print a value, inject at run time, one scoped identity per agent. It lists the per-harness settings (Claude Code sandbox and deny rules, Codex `shell_environment_policy`, omp `secrets.enabled`).
- Translate, don't skip: when a step names an omp tool your harness lacks, use the mapped tool above; when nothing maps, do the step by hand and say so.
