# Self-authoring research: prompts, skills, goals, loops (omp, Claude Code, Codex)

Read when writing a prompt, command, skill, goal, or loop from inside a session, or choosing between native goal and loop modes and `skill://deepmodebot/assets/loop/loop.py`. The steps are in `skill://deepmodebot/references/playbooks/self-authoring.md`; this file holds the cited per-harness facts.

Date: 2026-11-11. Versions probed: omp 18.18.9, claude 2.1.322, codex 0.163.0.
Exit codes are the reliable loop gate in headless runs: omp `--max-cost` exits 3; nonzero on terminal turn failures (omp://cli-reference.md).
Tags: `[unverified]` = not confirmed in a primary source this session; `[inference]` = derived, not stated.

## 1. Saved prompts / slash commands

### omp
- Project: `<cwd>/.omp/commands/*.md`; user: `~/.omp/agent/commands/*.md` (named profile: `~/.omp/profiles/<name>/agent/commands/*.md`). Project beats user on name collision (omp://slash-command-internals.md).
- omp also discovers foreign dirs: `.claude/commands/**/*.md` (recursive, `foo/bar.md` also aliased `foo:bar`), `.codex/commands/*.md`, `.opencode/commands/*.md`, `.agent(s)/commands/*.md` walking cwd up to repo root (omp://slash-command-internals.md).
- Format: Markdown + optional YAML frontmatter. `description` (else first body line, max 60 chars), `argument-hint`/`argumentHint`, `name` (Codex/OpenCode providers), `side: true` runs as a `/btw` side question (omp://slash-command-internals.md).
- Placeholders: `$1`, `$2`..., `$@[start]` / `$@[start:length]` (1-based), `$ARGUMENTS` and `$@`; args appended if template has no placeholder (omp://slash-command-internals.md).
- Discovery: rebuilt on interactive init, cwd change (`/move`), `/reload-plugins`, and session command-metadata notifications (settings changes, skill management). "There is no continuous file watcher for command directories" (omp://slash-command-internals.md). So a command written mid-session needs `/reload-plugins` or a new session [inference: `/reload-plugins` covers native dirs; doc lists it as an explicit refresh flow].

### Claude Code
- "Custom commands have been merged into skills." `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`; skill wins on collision ([skills](https://code.claude.com/docs/en/skills)).
- Command files support the same frontmatter as skills except `name` and `paths`; prefer skills for new work ([skills](https://code.claude.com/docs/en/skills)).
- Placeholders: `$ARGUMENTS`, `$ARGUMENTS[N]` / `$N` (0-based), `$name` from `arguments:` frontmatter, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`; escape with `\$1`. Unused args appended as `ARGUMENTS: <value>` ([skills](https://code.claude.com/docs/en/skills)).
- `` !`cmd` `` lines inject shell output before the model sees the skill (dynamic context injection) ([skills](https://code.claude.com/docs/en/skills)).
- Reload: skill dirs are watched (see 2); `.claude/commands/` in `--add-dir` dirs is NOT watched, restart needed ([skills](https://code.claude.com/docs/en/skills)). Live watch of a project `.claude/commands/` file: [unverified].
- `--disable-slash-commands` disables all skills and commands (claude 2.1.322 --help).

### Codex
- Custom prompts are DEPRECATED: "Use skills for reusable instructions" ([custom-prompts](https://learn.chatgpt.com/docs/custom-prompts.md)).
- Legacy location user-only: `~/.codex/prompts/*.md` (top level only, not shared via repo). Invoke `/prompts:<name>`. Frontmatter `description`, `argument-hint`. Placeholders `$1`..`$9`, `$ARGUMENTS`, named uppercase `$FILE` passed as `KEY=value`, `$$` literal. Restart Codex or open a new chat after edits ([custom-prompts](https://learn.chatgpt.com/docs/custom-prompts.md)).
- `/presets` saves and runs prompts or slash commands in the CLI ([slash-commands](https://learn.chatgpt.com/docs/cli/slash-commands.md)); storage format [unverified].
- Agent-authorable, repo-shareable path in Codex is therefore a skill in `.agents/skills/` [inference from deprecation note].

## 2. Skills

### Common standard (agentskills.io)
- `skill-name/SKILL.md` + optional `scripts/`, `references/`, `assets/` ([spec](https://agentskills.io/specification)).
- Required: `name` (1-64 chars, `a-z0-9-`, no leading/trailing/double hyphen, must match parent dir) and `description` (1-1024 chars, what + when, include trigger keywords). Optional: `license`, `compatibility` (<=500 chars), `metadata` (string map), `allowed-tools` (experimental, space-separated) ([spec](https://agentskills.io/specification)).
- Progressive disclosure: metadata ~100 tokens loaded at startup; body <5000 tokens recommended; resources on demand. Keep `SKILL.md` under 500 lines; references one level deep, relative paths ([spec](https://agentskills.io/specification)).
- Validate: `skills-ref validate ./my-skill` from [agentskills/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) (Python package: `pyproject.toml`, `src/`, `tests/` per GitHub API listing).

### omp
- Layout `<skills-root>/<skill-name>/SKILL.md`, non-recursive; nested `group/skill/SKILL.md` not discovered (omp://skills.md).
- Native provider (priority 100) loads `.omp` user/project skills (omp://skills.md); exact paths `.omp/skills/` and `~/.omp/agent/skills/` [inference from commands layout; doc names only "`.omp` user/project skills"].
- Also loads `.claude`, codex/agents, opencode, `.github/skills/<name>/SKILL.md` (project-only), plugin `skills/` dirs, `skills.customDirectories` (omp://skills.md).
- Frontmatter: `name` (defaults to dir name), `description` (REQUIRED for native `.omp`, omp-plugins, github, customDirectories), `globs`, `alwaysApply` (metadata only), `hide`, `disable-model-invocation`, `enabled: false` (omp://skills.md).
- Agent Plugins packages use strict Agent Skills validation: closed field set, `hide`/`enabled` rejected (omp://skills.md). Portable rule: stick to spec fields.
- Built-in creation tool `manage_skill` (create/update/delete) writes ONLY `~/.omp/agent/managed-skills/<name>/SKILL.md` (user-level, outside project); body without frontmatter; frontmatter generated with only `name` + `description`; cap 64,000 UTF-8 bytes; create fails if an authored skill owns the name; refreshes active skills immediately after success; tool gated by `autolearn.enabled` (omp://tools/manage_skill.md, omp://skills.md).
- Managed skills have priority 5 and always defer to a same-named authored skill (omp://skills.md).
- Registry CLI: `omp skill publish|install|update|uninstall|search|info|list ...`; `-g` user-global `skills.json`; `-y` installs script-shipping skills without asking; `--dry-run` packs and validates; `--allow-secrets` overrides credential scan (omp 18.18.9 `omp skill --help`). Pins in `.omp/skills.lock.json` (omp://skills.md).
- `skill://<name>` reads the skill's `SKILL.md`; `skill://<name>/<path>` reads inside it (omp://skills.md).
- Mid-session pickup of a hand-written (non-`manage_skill`) skill file: no file watcher documented [unverified]; safe path is `manage_skill` or a new session.
- Flags: `--no-skills`, `--skills=<globs>` (omp 18.18.9 --help).

### Claude Code
- Paths: personal `~/.claude/skills/<name>/SKILL.md`; project `.claude/skills/<name>/SKILL.md` (also every parent up to repo root); nested `<subdir>/.claude/skills/` loads when Claude touches files there; `--add-dir` dirs; plugin `<plugin>/skills/<name>/SKILL.md` as `/plugin:skill` ([skills](https://code.claude.com/docs/en/skills)).
- Precedence: enterprise > personal > project; your skill replaces a same-named bundled skill or built-in command (not aliases) ([skills](https://code.claude.com/docs/en/skills)).
- Reserved names: `synced`, `anthropic-skills*` ([skills](https://code.claude.com/docs/en/skills)).
- Frontmatter (Claude extensions beyond spec): `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `context: fork`, `agent`, `paths`. `description` + `when_to_use` truncated at 1,536 chars in listing (`skillListingMaxDescChars`); listing budget ~1% of context window ([skills](https://code.claude.com/docs/en/skills)).
- claude.ai / Skills API reject non-spec keys ("Unexpected key(s) in SKILL.md frontmatter"); restrict to the six spec fields for portability ([skills](https://code.claude.com/docs/en/skills)).
- Live reload: watches `~/.claude/skills/`, project `.claude/skills/`, `--add-dir` `.claude/skills/`; add/edit/remove picked up in-session without restart (not in bare mode). New top-level skills dir created mid-session needs `/reload-skills` (and again after each change there). Watch covers `SKILL.md` text only; plugin parts need `/reload-plugins` ([skills](https://code.claude.com/docs/en/skills)).
- Creation helpers: `skill-creator` plugin, `/plugin install skill-creator@claude-plugins-official`; stores tests in `evals/evals.json` inside the skill dir, runs isolated subagent per case, compares with/without skill ([skills](https://code.claude.com/docs/en/skills), [repo](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator)). `claude plugin eval` gates plugin skills in CI, non-zero exit below threshold ([skills](https://code.claude.com/docs/en/skills)). Bundled `/run-skill-generator` writes `.claude/skills/run-<name>/`; `/verify` may write `.claude/skills/verify/SKILL.md` ([skills](https://code.claude.com/docs/en/skills)).
- A skill folder with `.claude-plugin/plugin.json` becomes a plugin with hooks/MCP; in project `.claude/skills/` requires accepting workspace trust ([skills](https://code.claude.com/docs/en/skills)).

### Codex
- Paths: `$CWD/.agents/skills`, each parent up to `$REPO_ROOT/.agents/skills` (REPO); `$HOME/.agents/skills` (USER); `/etc/codex/skills` (ADMIN); bundled SYSTEM skills `skill-creator`, `skill-installer` ([build-skills](https://learn.chatgpt.com/docs/build-skills.md)).
- Required frontmatter `name`, `description`; optional `agents/openai.yaml` (`interface.*`, `policy.allow_implicit_invocation`, `dependencies.tools`) ([build-skills](https://learn.chatgpt.com/docs/build-skills.md)).
- Invoke `$skill-name` or `/skills`; built-in creator `$skill-creator`; installer `$skill-installer <name>` ([build-skills](https://learn.chatgpt.com/docs/build-skills.md)).
- Initial skill list budget: 2% of context or 8,000 chars; `skills.max_context_tokens` up to 10,000 ([build-skills](https://learn.chatgpt.com/docs/build-skills.md)).
- "Codex detects skill changes automatically. If an update doesn't appear, restart Codex." Config changes (`[[skills.config]] enabled=false`, `[skills.bundled] enabled=false`) need restart ([build-skills](https://learn.chatgpt.com/docs/build-skills.md)).
- Same-name skills are not merged; both appear ([build-skills](https://learn.chatgpt.com/docs/build-skills.md)).

### Cross-harness portable recipe [inference]
- One `<name>/SKILL.md` with only spec fields loads in all three if placed in each harness's dir; omp additionally reads `.claude/skills` and `.agents`-style dirs, so `.claude/skills/<name>/` + `.agents/skills/<name>/` (or symlink; Claude and Codex both follow symlinks per their docs) covers all three.

## 3. Goals (native)

### omp
- `/goal <objective>` interactive; `omp --goal "<objective>"` starts fresh in goal mode. Requires setting `goal.enabled`; interactive only; rejected with positional prompt, stdin/@file, resume/continue/fork, `--plan-yolo`, `--no-tools`, startup plan mode (omp://cli-reference.md, omp 18.18.9 --help).
- Lifecycle (RPC mirrors `/goal`): create (non-empty `objective`, optional positive integer `token_budget`, no active/paused goal, not in plan mode) adds a `goal` tool; `pause`, `resume`, `drop`. Agent completes the goal via the `goal` tool, which is then removed (omp://rpc.md).
- Continuation: hidden `goal-continuation` turn after each terminal `agent_end` only if goal active, session idle, nothing queued, plan mode off, open todos not all blocked. Stops after a goal turn with no new tool activity; `abort` pauses the goal (omp://rpc.md).
- Over RPC, goals continue only if `goal.continuationModes` contains `"rpc"` (omp://rpc.md). Print mode (`-p`) continuation: [unverified].
- Goal restored at process start is paused until `goal resume` (omp://rpc.md).
- Related: `/autoresearch <goal>` mode (metric-driven experiment loop, see 4) (omp://autoresearch.md).

### Claude Code
- `/goal <condition>` (max 4,000 chars); one goal per session; `/goal` shows status (turns, token spend, last reason); `/goal clear` (aliases stop/off/reset/none/cancel) ([goal](https://code.claude.com/docs/en/goal)).
- Mechanism: session-scoped prompt-based Stop hook; small fast model judges Not yet met / Met / Impossible from the transcript only (no tools, no file reads) ([goal](https://code.claude.com/docs/en/goal)).
- Write conditions with one measurable end state, a stated check Claude will print (e.g. "`npm test` exits 0"), constraints, and a bound like "or stop after 20 turns" ([goal](https://code.claude.com/docs/en/goal)).
- Headless: `claude -p "/goal <condition>"` runs to completion; add `--output-format stream-json --verbose` to see progress ([goal](https://code.claude.com/docs/en/goal)).
- Anti-spin: no tool use for several turns stops the loop with goal still set; unrecoverable errors (auth, credits, context overflow) clear it; transient errors retry up to 3 then pause ([goal](https://code.claude.com/docs/en/goal)).
- Requires workspace trust (hooks rule); unavailable if `disableAllHooks` or `allowManagedHooksOnly` ([goal](https://code.claude.com/docs/en/goal)).
- Does not change permission mode; unattended needs auto mode ([goal](https://code.claude.com/docs/en/goal)).

### Codex
- Feature `goals` stable, enabled (`codex features list`, 0.163.0). Available since 0.128.0 ([cookbook](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex.md)).
- `/goal <objective>`, `/goal` view, `/goal edit`, `/goal pause`, `/goal resume`, `/goal clear`; objective non-empty, max 4,000 chars, point at a file for longer ([slash-commands](https://learn.chatgpt.com/docs/cli/slash-commands.md)).
- Thread-scoped persisted state: active, paused, complete, budget-limited. Model may start a goal and mark complete only with evidence; pause/resume/clear/budget transitions belong to user or system. Continuation only when idle, no queued input; a continuation turn with no tool call suppresses the next continuation; interruptions pause ([cookbook](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex.md)).
- Recommended template: `/goal <end state> verified by <evidence> while preserving <constraints>. Use <boundaries>. Between iterations, <policy>. If blocked, <report>.` ([cookbook](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex.md)).
- Budget config key name for goals: [unverified].
- Structured one-shot: `codex exec --output-schema <FILE>` (JSON Schema for final message), `--json` JSONL events, `-o/--output-last-message <FILE>` (codex 0.163.0 exec --help).

## 4. Loops

### omp
- Goal mode (above) and `/autoresearch <goal>`: loop is the `agent_end` hook sending a hidden `resume-message.md` turn; one iteration = edit, `run_experiment`, `log_experiment`; requires clean worktree, creates branch `autoresearch/<slug>-<YYYYMMDD>`; sessions store `max_iterations`, metric direction, scope and off-limits paths; experiment-limit shutdown writes `mode: "off"`; subagents cannot activate it (`runCommands: false`) (omp://autoresearch.md, omp://session.md).
- `/loop` exists with a condition evaluated in its own shell namespace `loop-condition:<id>`; settings `loop.*` (omp://bash-tool-runtime.md, omp://settings.md). Full `/loop` syntax not in docs read [unverified].
- Headless: `omp -p "<prompt>"`; `--wait-async` keeps the run alive and starts new turns as background jobs finish; `--max-time <dur>`; `--max-cost <usd>` stops new requests (exit status 3; in-flight request may exceed); `--warn-cost <usd>`; `--plan-yolo` auto-approves plan then executes (omp://cli-reference.md).
- Loop guards: settings `model.loopGuard.*`, `model.toolCallLoopGuard.*` exist (omp://settings.md); semantics [unverified].
- External loop: `while ...; do omp -p ... --max-cost N; done` with exit-code checks [inference].

### Claude Code
- `/goal` (condition, see 3). `/loop` bundled skill: `/loop 5m <prompt>` fixed cron (1 min granularity), `/loop <prompt>` self-paced (1 min to 1 h), bare `/loop` runs `.claude/loop.md` then `~/.claude/loop.md` (25,000 byte cap; edits apply next iteration) or a built-in maintenance prompt ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks)).
- Stop: self-paced via Esc or `ScheduleWakeup` with `stop: true`; fixed via `CronDelete`; recurring tasks expire after 7 days; max 50 tasks per session; `CLAUDE_CODE_DISABLE_CRON=1` disables ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks)).
- `/loop` only fires skills Claude may invoke itself (not `disable-model-invocation: true`) ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks)).
- Durable: Cloud routines (min 1 h, fresh clone, no `~/.claude/skills`), Desktop scheduled tasks (local), GitHub Actions ([scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks)).
- Stop hooks: return `"decision": "block"` with reason to continue; input has `stop_hook_active` (true when already continuing) and must be checked to avoid infinite loops; Claude Code overrides a Stop hook after 8 consecutive blocks with no tool call ([hooks](https://code.claude.com/docs/en/hooks), [hooks-guide](https://code.claude.com/docs/en/hooks-guide)). Prompt (`type: "prompt"`) and agent (`type: "agent"`) hooks evaluate with a model ([hooks](https://code.claude.com/docs/en/hooks)).
- `ralph-loop` official plugin: `/ralph-loop "<prompt>" --completion-promise "DONE" --max-iterations N`; `/cancel-ralph`. Stop hook `hooks/stop-hook.sh` re-feeds the SAME prompt; state lives in files and git. Default iterations unlimited; promise is exact string match; README says always set `--max-iterations`. Windows: bash may resolve to WSL; point hook at Git Bash ([README](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-loop)).
- Budgets: `--max-budget-usd <amount>` (claude 2.1.322 --help). `--max-turns` not present in 2.1.322 --help output [unverified whether hidden].

### Codex
- `/goal` (above). Scripted loop: `codex exec "<prompt>"` then `codex exec resume --last "<prompt>"` (or `resume <SESSION_ID>`; `-` reads prompt from stdin; `--all` disables cwd filter) (codex 0.163.0 exec resume --help). Gate each iteration on `--output-schema` JSON or `-o` file [inference].
- Hooks: `~/.codex/hooks.json`, `<repo>/.codex/hooks.json` or inline `[hooks]`; `Stop` event can continue the turn; `continue: false` ends without another model request ([hooks](https://learn.chatgpt.com/docs/hooks.md)).
- Scheduled tasks (app automations): ChatGPT desktop app runs them in the project dir or an isolated worktree; machine and app must be on; feature `in_app_local_automation` stable ([automations](https://learn.chatgpt.com/docs/automations.md), `codex features list`).
- `codex cloud` [EXPERIMENTAL]: browse Codex Cloud tasks and apply locally (codex 0.163.0 --help).
- `codex queue` queues a message to an existing session (codex 0.163.0 --help).
- No `--max-turns`/USD cap flag in `codex --help` 0.163.0; goal budget is the documented cap [inference].

## 5. Skill authoring best practice (Anthropic)
Source: [best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
- Concise is key: only metadata preloads; assume the model already knows general facts.
- Set degrees of freedom: "Match the level of specificity to the task's fragility and variability" (exact scripts for fragile ops, prose for open tasks).
- Descriptions: third person, what + when, key trigger words first.
- Names: gerund form suggested (`processing-pdfs`).
- `SKILL.md` body under 500 lines; references one level deep.
- "Create evaluations BEFORE writing extensive documentation."
- Test with every model you plan to use.

## 6. Self-improvement loop patterns
- Ralph (Huntley): "Ralph is a Bash loop": `while :; do cat PROMPT.md | claude-code ; done`. Rules: one prompt file; persistent plan file (`fix_plan.md`) updated each turn; one item per loop; single subagent for build/test backpressure; "no cheating" (no placeholders); tune the prompt when Ralph misbehaves ([ghuntley.com/ralph](https://ghuntley.com/ralph/)).
- Karpathy autoresearch: three files; `prepare.py` fixed (never modified), `train.py` the only agent-edited file, `program.md` human-edited instructions ("a super lightweight skill"). Fixed 5-minute budget, metric `val_bpb` lower is better ([README](https://github.com/karpathy/autoresearch)).
- autoresearch rules: log each run to untracked `results.tsv` (commit, metric, mem, keep|discard|crash, description); if metric improved keep commit else `git reset`; >10 min = crash and revert; simplicity criterion; NEVER STOP to ask ([program.md](https://github.com/karpathy/autoresearch/blob/master/program.md)).
- DSPy: latest release 3.5.0 (2026-11-10), MIT ([GitHub API](https://github.com/stanfordnlp/dspy)). GEPA (reflective prompt evolution): latest v0.1.4 (2026-07-15), MIT ([GitHub API](https://github.com/gepa-ai/gepa)). Optional tooling; need a dataset + metric.
- Eval before promotion: skill-creator with/without comparison and `claude plugin eval` threshold gate ([skills](https://code.claude.com/docs/en/skills)); agentskills [evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills).
- Actionable rule set [inference from above]: fixed metric + fixed evaluator the agent cannot edit; one mutable artifact; keep/revert per run on a branch; append-only log; hard cap (iterations, time, USD); promote to user-level only after eval beats baseline.

## 7. Safety facts
- Writes outside the project: omp `manage_skill` (`~/.omp/agent/managed-skills/`), `omp skill install -g`, user commands `~/.omp/agent/commands/`; Claude `~/.claude/skills/`, `~/.claude/loop.md`, plugin cache `~/.claude/plugins/cache/...`; Codex `~/.codex/prompts/`, `$HOME/.agents/skills`, `~/.codex/config.toml`, `~/.codex/hooks.json` (sources above).
- Restart/reload needed: omp commands (no watcher; `/reload-plugins` or new session); Claude new top-level skills dir (`/reload-skills`), plugin parts (`/reload-plugins`), `--add-dir` commands/agents (restart); Codex prompts (restart), skills config (restart), skills auto-detected else restart (sources above).
- Trust gates: Claude `/goal` and project hooks need workspace trust; `-p` shows no trust prompt ([goal](https://code.claude.com/docs/en/goal), [security](https://code.claude.com/docs/en/security)). Codex non-managed hooks need review and are trusted by hash; changed hooks skipped until re-trusted; project hooks load only when `.codex/` layer trusted; `--dangerously-bypass-hook-trust` skips ([hooks](https://learn.chatgpt.com/docs/hooks.md), codex --help). omp hook trust model [unverified].
- Documented attack: repo-committed Claude Code project files (hooks, MCP settings) enabled RCE and API token exfiltration, CVE-2025-59536 and CVE-2026-21852 ([Check Point](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/)).
- Self-modification risk [inference]: an agent writing hooks, settings, or skills with `allowed-tools`/`!` shell injection can escalate its own permissions or persist across sessions; never let an agent author hooks/settings unattended; keep self-authored files in project scope, reviewed via git diff before promotion.
- omp `omp skill install -y` installs script-shipping skills without asking; publish scans for credentials unless `--allow-secrets` (omp skill --help).
- Loop runaway guards: omp `--max-cost`/`--max-time`, no-tool-activity stop; Claude 8-block cap, `stop_hook_active`, 7-day cron expiry, goal no-progress stop, `--max-budget-usd`; Codex no-tool-call suppression and budget-limited state; ralph-loop `--max-iterations` (sources above).
