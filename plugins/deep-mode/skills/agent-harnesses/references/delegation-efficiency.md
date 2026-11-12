# Delegation efficiency research: models, effort, tokens, limits (omp, Claude Code, Codex)

Read when deciding whether to delegate, which model and reasoning effort a delegate gets, how to cut token use, or how subscription limits are metered, in omp, Claude Code, or Codex. Model names and prices move monthly: recheck the vendor page before quoting one.

Date: 2026-11-11. Versions probed: omp 18.18.9, claude 2.1.322, codex 0.163.0.
Tags: `[unverified]` = not confirmed in a primary source this session; `[inference]` = derived, not stated.
Bundled omp agent frontmatter was read from the embedded definitions inside omp.exe 18.18.9 (cited as "omp 18.18.9 binary").

## 1. Model line-ups (2026-11)

### Anthropic (API list prices per MTok, input/output)
- Fable 5.2 `claude-fable-5-2`: $8/$40, "demanding reasoning and long-horizon agentic work", API default effort `high` ([anth-models](https://platform.claude.com/docs/en/about-claude/models/overview)).
- Opus 5.5 `claude-opus-5-5`: $4/$20, "long-running agentic coding and knowledge work", API default effort `medium`; Anthropic says start here for most workloads ([anth-models](https://platform.claude.com/docs/en/about-claude/models/overview)).
- Sonnet 5.5 `claude-sonnet-5-5`: $2/$10, "best combination of speed and intelligence", API default effort `high` ([anth-models](https://platform.claude.com/docs/en/about-claude/models/overview)).
- Haiku 5.5 `claude-haiku-5-5`: $0.10/$0.50 for prompts up to 100K tokens, $0.50/$2.50 above 100K (whole request repriced, cache reads included) ([anth-pricing](https://platform.claude.com/docs/en/about-claude/pricing)).
- All four: 1M context, 128K max output, adaptive thinking; Fable and Opus thinking is always on ([anth-models](https://platform.claude.com/docs/en/about-claude/models/overview)).
- Relative cost: Haiku 5.5 (short prompt) is 1/20 of Sonnet 5.5, Sonnet is 1/2 of Opus 5.5, Opus is 1/2 of Fable 5.2 [inference from list prices].
- Cache hit multiplier: 0.025x on Fable 5.2, 0.05x on Opus 5.5 and Sonnet 5.5, 0.1x elsewhere; Batch API is 50% off and stacks with caching ([anth-pricing](https://platform.claude.com/docs/en/about-claude/pricing)).
- Fast mode: Opus 5.5 $8/$40, Fable 5.2 $16/$80, so 2x price for up to 2.5x output speed ([anth-pricing](https://platform.claude.com/docs/en/about-claude/pricing)).
- Effort levels on Fable, Opus 5.5, Sonnet 5.5, Haiku 5.5: `low`, `medium`, `high`, `xhigh`, `max` ([cc-model](https://code.claude.com/docs/en/model-config)).
- In Claude Code, Fable 5.2, Opus 5.5, Sonnet 5.5 and Haiku 5.5 all default to `medium` (differs from API defaults above); "Opus 5.5 at medium matches or exceeds Opus 5 at high" on coding evals ([cc-model](https://code.claude.com/docs/en/model-config)).
- Effort guidance: `low` for straightforward work you review step by step; `medium` for clear-scope day-to-day features; `high` where verification or edge cases matter (bug fixes); `xhigh` deeper at higher spend; `max` for hard unattended problems, "prone to overthinking, so test before adopting" ([cc-model](https://code.claude.com/docs/en/model-config)).
- Thinking tokens bill as output; you cannot turn thinking off on Opus 5.5, Sonnet 5.5, Haiku 5.5 or Fable, so effort is the cost lever ([cc-costs](https://code.claude.com/docs/en/costs)).

### OpenAI / Codex
- Current Codex line-up: GPT-6 Astra (hardest end-to-end work), GPT-6.1 Sol (near-Astra at lower cost, repeated long-running work), GPT-6.1 Terra (fast writing, visual, computer use), GPT-6 Luna (focused, high-volume: extraction, classification, structured summaries) ([cx-models](https://learn.chatgpt.com/docs/models)).
- GPT-6.1 Sol default context in Codex is 500,000 tokens ([cx-models](https://learn.chatgpt.com/docs/models)).
- Retired for ChatGPT sign-in: `gpt-5.3-codex-spark` (2026-09-14), `gpt-5.4` and `gpt-5.4-mini` (2026-08-31; replace with `gpt-6-sol` / `gpt-6-luna`), `gpt-5.5` (2026-10-14; replace with `gpt-6.1-sol`); `gpt-5.2` and `gpt-5.3-codex` deprecated. API-key sessions are unaffected ([cx-models](https://learn.chatgpt.com/docs/models)). So "GPT-5.x Codex / mini" advice is stale; Luna is the current small model.
- `model_reasoning_effort` values: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`, model and client dependent ([cx-config](https://learn.chatgpt.com/docs/config-file/config-reference)). Luna supports up to Max, not Ultra ([cx-models](https://learn.chatgpt.com/docs/models)).
- Starting points: Luna `high`, Astra `low` (UI "Light"), Sol client default; Sol, GPT-6 Sol and Luna default to `medium` on the API; Sol does not accept `none`/`minimal` ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [oa-reasoning](https://developers.openai.com/api/docs/guides/reasoning)).
- "Max" = more reasoning time on one task; "Ultra" = subagents in parallel; "Most tasks do not need Max or Ultra" ([cx-models](https://learn.chatgpt.com/docs/models)).
- Codex credits per 1M tokens (input / cached / output): Astra 250/25/1,250; Sol 50/2.5/250; Terra 25/1.25/125; Luna 2.5/0.25/12.5. Luna is 1/20 of Sol; Astra is 5x Sol ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- OpenAI framing: "Treat `reasoning.effort` as a tuning knob, not the primary way to recover quality"; define done and verification for agentic work ([oa-reasoning](https://developers.openai.com/api/docs/guides/reasoning)).
- Reserve at least 25,000 tokens for reasoning plus output when experimenting; hitting `max_output_tokens` can bill reasoning with no visible answer ([oa-reasoning](https://developers.openai.com/api/docs/guides/reasoning)).
- Planner/workhorse split: reasoning models plan and decide, cheaper models execute well-defined tasks; "Most AI workflows will use a combination" ([oa-rbp](https://developers.openai.com/api/docs/guides/reasoning-best-practices)).

## 2. Subscription metering

### Claude Pro / Max / Ultra
- Pro and Max: five-hour session limit plus weekly limit; Ultra: weekly limit, verified Ultra accounts have no five-hour limit ([help-plan](https://support.claude.com/en/articles/11145838)).
- Max and Ultra have a separate weekly Fable limit; limits are shared between Claude apps and Claude Code ([help-plan](https://support.claude.com/en/articles/11145838)).
- Depending on plan and seat tier, Fable can bill to usage credits instead of included limits; `/model` shows "Requires usage credits" ([cc-model](https://code.claude.com/docs/en/model-config)).
- Factors that burn limits: message length, attachments, conversation length, tool use, model choice, effort level, multi-step tasks; cached content counts less ([help-best](https://support.claude.com/en/articles/9797557)).
- "Opus costs several times more per turn than Sonnet, and Sonnet more than Haiku. Spending Opus on routine work is the fastest way to drain a daily limit" ([help-limits](https://support.claude.com/en/articles/14552983)).
- Subagents send their own requests that count toward the same usage limits as the main conversation ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Session and weekly limits are shared across all models; after a model-specific "Opus limit" or "Sonnet limit" message, switching family keeps you working ([cc-costs](https://code.claude.com/docs/en/costs)).
- An exported `ANTHROPIC_API_KEY` makes Claude Code bill the API instead of the subscription ([help-plan](https://support.claude.com/en/articles/11145838)).

### ChatGPT Plus / Pro (Codex)
- Plus estimated local messages per five hours: Astra 5-45, Sol 15-160, Terra 35-285, GPT-6 Sol 15-150, Luna 350-3,000; "Weekly limits may also apply"; cloud tasks use more than local messages ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- Pro ($100/$200/$500) "currently ha[s] no five-hour limit" ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- Fast mode consumes included usage at 2.5x; Astra or Sol Ultrafast at 8x ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- Usage depends on model, context, reasoning, tool use, retrieval and caching; "prompt length alone isn't a reliable estimate" ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- Over limit: buy credits, or run local chats with an API key at API rates ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).

## 3. Harness knobs

### omp 18.18.9
- Chat roles: `default`, `smol`, `slow`, `vision`, `plan`, `commit`, `tiny`, `memory`, `task`, `advisor`; custom roles via `modelRoles`; `@role` aliases; role values take a `:level` suffix (omp://models.md, omp://settings.md).
- CLI: `--model`, `--smol` (`PI_SMOL_MODEL`), `--slow` (`PI_SLOW_MODEL`), `--plan` (`PI_PLAN_MODEL`) (omp://cli-reference.md).
- `--thinking off|minimal|low|medium|high|xhigh|max|auto`; `defaultThinkingLevel` defaults to `high`; `providers.autoThinkingMaxEffort` caps `auto` at `xhigh` by default (omp://cli-reference.md, omp://settings.md).
- Bundled agents (omp 18.18.9 binary): `scout` model `@smol`, `thinking-level: medium`, `read-summarize: false`, read-only tools; `sonic` model `@smol`, thinking `medium`, "strictly mechanical updates or data collection"; `reviewer` model `@slow`, may spawn `scout`; `task` model `@task`, thinking `auto`; `security-reviewer` sets no model (inherits).
- The model-facing task prompt "warns against offloading reasoning to `scout`/`sonic`" (omp://task-agent-discovery.md).
- Model precedence: `task.agentModelOverrides[agent]` > agent frontmatter `model` > parent active/default model (omp://task-agent-discovery.md).
- Per-call `model` on a task item requires `task.perCallModel: on` (default `off`), must be one exact `provider/model-id[:level]` granted by operator roles or agent frontmatter, and conflicts with an `agentModelOverrides` entry (omp://task-agent-discovery.md).
- Per-spawn `effort: lo|med|hi` requires `task.enableEffort` (default false); maps to the model's lowest/middle/highest level, clamped by `task.maxEffort` (default `max`) (omp://tools/task.md).
- `solutionSpace` is the sole input to the `auto` thinking classifier for the child; it describes open-endedness, not volume (omp://tools/task.md).
- User `^provider/model:level` tags create `m1`, `m2` agents pinned to that model and level (omp://task-agent-discovery.md).
- Concurrency: `task.maxConcurrency` default 32 (0 = unlimited); `task.maxRecursionDepth` default 2; `async.enabled` makes spawns background jobs (omp://tools/task.md).
- Budgets: `task.softRequestBudget` default 200 requests, wrap-up notice when crossed, force stop at 1.5x; scout/sonic capped at 100; `task.agentSoftRequestBudget[name]` overrides; `task.maxRuntimeMs` default 0 (off) (omp://tools/task.md).
- Session spend: `--warn-cost <usd>` and `--max-cost <usd>` include subagents; `--max-cost` stops new requests and print mode exits 3 (omp://cli-reference.md).
- Prewalk: one-shot handoff from planning model to `prewalk.into` (default `@smol`) at the first `edit`/`write`; off by default; `prewalk.auto: suggest|on` lets a native judge arm it only when "hard thinking comes first" with probability >= 0.70 (omp://prewalk.md).
- Subagent prewalk: frontmatter `prewalk`, `task.agentPrewalk[name]`, or `task.prewalk` for the bundled `task` agent (default off); per-call-model workers never prewalk (omp://task-agent-discovery.md).
- Plan-to-cheap execution: `--plan-yolo` plans read-only then executes on `--plan-yolo-into` (default `smol` role) (omp://cli-reference.md).
- Advisor: `advisor.enabled` attaches reviewer models that inject advice; the `advisor` role defaults to an explicitly configured `slow` else its own strong-model chain; subagents default to no advisor (omp://advisor-watchdog.md, omp://models.md, omp://tools/task.md).
- Compaction: on by default; `compaction.methodOrder` remote, snapcompact, handoff, shake, soft; `supersedeReads` and `dropUseless` default on; `task.agentCompactionThresholdOverrides[name]` per agent (omp://compaction.md, omp://settings.md).
- `read.summarize.enabled` default true gives structural summaries of code reads; `read.defaultLimit` 300 lines (omp://settings.md).
- Child sessions do not inherit conversation history; they get workspace tree, skills, rules, context files except `AGENTS.md`, and the shared `local://` root (omp://tools/task.md).
- Inline task results up to 11,500 chars; longer outputs return a 5,000-char preview plus `agent://<id>` (omp://tools/task.md).
- Prefer `write agent://<id>` to an existing agent over a fresh spawn for follow-ups: "it already holds the relevant context" (omp://tools/task.md).
- Visibility: `omp usage` (provider limits per account), `omp usage clients --days` (token burn per client), `omp stats`; Agent Hub (`Alt+A`) shows each agent's model and usage; task results carry `tokens`, `requests`, `usage`, `resolvedModel`, `resolvedThinkingLevel` (omp://cli-reference.md, omp://task-agent-discovery.md, omp://tools/task.md).
- Service tier: `tier.subagent` default `inherit`; `task.agentServiceTierOverrides[name]` per agent (omp://settings.md).

### Claude Code 2.1.322
- Aliases: `default`, `best`, `fable`, `opus`, `sonnet`, `haiku`, `sonnet[1m]`, `opus[1m]`, `opusplan`; on the Anthropic API `opus`/`sonnet`/`haiku` resolve to the 5.5 models ([cc-model](https://code.claude.com/docs/en/model-config)).
- `opusplan` uses Opus in plan mode and Sonnet for execution; `/model` switches mid-session and also changes subagents that inherit the session model ([cc-model](https://code.claude.com/docs/en/model-config)).
- `--effort low|medium|high|xhigh|max` (claude 2.1.322 --help); `/effort`, `CLAUDE_CODE_EFFORT_LEVEL` (highest precedence), per-model `modelSettings`, `maxEffortLevel` cap; `ultrathink` raises one turn to `xhigh` ([cc-model](https://code.claude.com/docs/en/model-config)).
- `ultracode` (via `/effort` or `--effort ultracode`) orchestrates dynamic workflows for every substantive task, at `xhigh` when set by flag ([cc-model](https://code.claude.com/docs/en/model-config)).
- Subagent `model`: `sonnet|opus|haiku|fable|<full id>|inherit`; resolution: per-invocation `model` > frontmatter > `CLAUDE_CODE_SUBAGENT_MODEL` > main model; `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` forces one model on all ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Subagent `effort` frontmatter or per-invocation `effort`; without it, a subagent on the main model uses the session level, on another model that level does not apply ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Other cost-relevant frontmatter: `maxTurns`, `autoCompactWindow` (100K-1M), `omitClaudeMd`, `background`, `isolation: worktree`, `experimental.cacheTtl` ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Built-in Explore: read-only, runs on the main conversation's model (Opus when main is Fable, on subscription/Console); skips CLAUDE.md and git status; define a user `Explore` with `model: haiku` to cheapen it ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Explore takes a thoroughness level: quick, medium, very thorough ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Subagents start in the background by default; concurrency cap 20 (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); nesting up to 3 layers (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`) ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Combined custom subagent descriptions over 15,000 tokens trigger a startup warning; keep descriptions short ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- A fork inherits the full conversation and reads the parent's prompt cache, so it "costs less than a fresh subagent for tasks that need the same context" ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Visibility: `/usage` Session block (token counts, list-price cost, prompt cache hit line), plan usage bars and attribution to subagents, skills, MCP; `/context`; `/tasks` shows each subagent's model and effort ([cc-costs](https://code.claude.com/docs/en/costs), [cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- `/cost` shows session token and dollar usage for API billing ([help-limits](https://support.claude.com/en/articles/14552983)).
- `--max-budget-usd <amount>` works only with `--print`; `--autocompact <auto|tokens>`; `--fallback-model`; `--json-schema` for structured output in print mode (claude 2.1.322 --help).
- Headless: read actual model from `modelUsage` in `--output-format json` results ([cc-model](https://code.claude.com/docs/en/model-config)).
- Auto-compact window: `/autocompact`, `autoCompactWindow`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`; default compacts at the model's limit (Haiku 5.5 about 967K) ([cc-model](https://code.claude.com/docs/en/model-config)).
- Agent teams use "approximately 7x more tokens than standard sessions when teammates run in plan mode"; use Sonnet teammates, keep teams small ([cc-costs](https://code.claude.com/docs/en/costs)).

### Codex 0.163.0
- `-m/--model`, `-c key=value` overrides, `-p/--profile <name>` layers `$CODEX_HOME/<name>.config.toml` (codex 0.163.0 --help).
- Profiles: separate files, top-level keys only; `[profiles.x]` tables and `profile = "x"` are unsupported since 0.134.0 ([cx-adv](https://learn.chatgpt.com/docs/config-file/config-advanced)).
- Config: `model`, `model_reasoning_effort`, `plan_mode_reasoning_effort`, `model_verbosity`, `model_auto_compact_token_limit`, `tool_output_token_limit`, `service_tier` ([cx-config](https://learn.chatgpt.com/docs/config-file/config-reference)).
- Subagents: built-ins `default`, `worker`, `explorer`; custom TOML in `~/.codex/agents/` or `.codex/agents/` with `model`, `model_reasoning_effort` ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Global: `agents.max_concurrent_threads_per_session`, `agents.default_subagent_model`, `agents.default_subagent_reasoning_effort` ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Unconfigured subagents inherit parent model and effort; precedence: agent file > explicit spawn value > `[agents]` default > parent ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Doc example roster: explorers and small fixers on `gpt-6-luna` at `high`, reviewers and UI debuggers on `gpt-6.1-sol` at `medium` ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Subagents spawn only on explicit request at most levels; Ultra delegates proactively ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Visibility: `/status` shows remaining limits in a CLI session; usage dashboard at chatgpt.com/codex/settings/usage ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- `codex exec --json` prints JSONL events; `--output-schema` constrains the final message; `-o` writes the last message to a file (codex 0.163.0 exec --help).
- No per-run dollar or turn cap flag appears in `codex --help` or `codex exec --help` 0.163.0 [inference from help text].

## 4. Delegation economics (primary sources)
- Agents use about 4x the tokens of chat; multi-agent systems about 15x; worth it only when task value pays for it ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Token usage alone explained 80% of BrowseComp performance variance; tool calls and model choice explained most of the rest ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Opus 4 lead + Sonnet 4 subagents beat single-agent Opus 4 by 90.2% on breadth-first research ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Model upgrade beat doubling token budget (Sonnet 4 vs 2x tokens on Sonnet 3.7) ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Poor fit: tasks where all agents need shared context or have many inter-agent dependencies; "most coding tasks involve fewer truly parallelizable tasks than research" ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Scaling rule from their prompts: simple fact-finding 1 agent with 3-10 tool calls; comparisons 2-4 subagents with 10-15 calls; complex research 10+ subagents with divided responsibilities ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Early failures: spawning 50 subagents for simple queries; vague delegation caused duplicated searches; each subagent needs objective, output format, tool guidance, boundaries ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Parallelism: 3-5 subagents at once plus 3+ parallel tool calls each cut research time up to 90% ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Have subagents write artifacts to a filesystem and pass lightweight references back, avoiding copying large outputs through the coordinator ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Claude Code: use a subagent when a side task "would flood your main conversation with search results, logs, or file contents you won't reference again" ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Claude Code: many subagents returning detailed results "can consume significant context, and each subagent spends tokens of its own" ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Claude Code: for a question about something already in the conversation, use `/btw`, not a subagent ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Codex: "subagent workflows consume more tokens than comparable single-agent runs"; use parallel agents for read-heavy work (exploration, tests, triage, summarization); be careful with parallel write-heavy work ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Fresh subagents pay their own prefix: separate cache from the parent and only a 5-minute TTL even on subscription unless configured ([cc-cache](https://code.claude.com/docs/en/prompt-caching)).
- Non-fork Claude subagents load CLAUDE.md and git status (except Explore/Plan); omp children get context files except `AGENTS.md` ([cc-subagents](https://code.claude.com/docs/en/sub-agents), omp://tools/task.md).
- Net: the main win is context isolation and parallel wall-clock, not token savings; delegation saves tokens only when the child is a cheaper model or its raw output would otherwise sit in an expensive main context [inference].

## 5. Token-saving practices
- Prompt caching is exact prefix match; any change recomputes everything after it ([cc-cache](https://code.claude.com/docs/en/prompt-caching), [oa-cache](https://developers.openai.com/api/docs/guides/prompt-caching)).
- Claude cache: 5-minute write 1.25x, 1-hour write 2x base input; 512-token minimum on current models; up to 4 breakpoints; 20-block lookback ([anth-pricing](https://platform.claude.com/docs/en/about-claude/pricing), [anth-cache](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).
- Claude Code requests a 1-hour TTL for the main conversation on a subscription within included usage; subagents get 5 minutes; set `promptCacheTtl` / `subagentPromptCacheTtl` ([cc-cache](https://code.claude.com/docs/en/prompt-caching)).
- Cache breakers in Claude Code: switching models, changing effort, fast mode, tool set changes when tool search is off, compaction ([cc-cache](https://code.claude.com/docs/en/prompt-caching)).
- A skill or command naming a different `model` makes that turn a model switch with no cache hits ([cc-cache](https://code.claude.com/docs/en/prompt-caching)).
- `/rewind` returns to an already cached prefix; `/compact` builds a new one and is expensive on a cold cache; `/clear` costs nothing ([cc-cache](https://code.claude.com/docs/en/prompt-caching), [cc-costs](https://code.claude.com/docs/en/costs)).
- OpenAI cache: 1,024-token minimum on GPT-5.6+; read 0.1x (0.05x on Sol 6.1 and Terra 6.1); write 1.25x for 30m, 2.5x for 12h ([oa-cache](https://developers.openai.com/api/docs/guides/prompt-caching)).
- OpenAI: keep tool definitions stable (use `tool_choice: "none"` instead of removing tools); change effort via `configuration_update` items to keep the prefix ([oa-cache](https://developers.openai.com/api/docs/guides/prompt-caching)).
- Codex subscription credits have no separate cache-write charge ([cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- Clear between unrelated tasks: "the single most effective lever for both quality and cost" ([help-limits](https://support.claude.com/en/articles/14552983)).
- Keep CLAUDE.md under about 200 lines; move workflow detail to skills, which load on demand ([cc-costs](https://code.claude.com/docs/en/costs)).
- Reference files by path rather than pasting; `@file` injects the whole file; trim logs to the relevant 20-30 lines ([help-limits](https://support.claude.com/en/articles/14552983)).
- Use hooks to filter output before the model sees it (example: tail test output to 100 lines) ([cc-costs](https://code.claude.com/docs/en/costs)).
- Prefer CLI tools over MCP servers; disable unused servers ([cc-costs](https://code.claude.com/docs/en/costs)).
- Use code intelligence (LSP) to replace grep plus multi-file reads ([cc-costs](https://code.claude.com/docs/en/costs)).
- Write specific prompts; vague ones "trigger broad scanning" ([cc-costs](https://code.claude.com/docs/en/costs)).
- Plan before big changes; a plan costs hundreds of tokens, a reverted wrong diff costs thousands twice ([help-limits](https://support.claude.com/en/articles/14552983)).
- Batch related requests into one message ([help-best](https://support.claude.com/en/articles/9797557)).
- omp: `read` with line selectors and structural summaries; `compaction.supersedeReads` blanks stale reads; parallel tool calls in one turn (omp://settings.md, omp://compaction.md).
- Structured outputs keep child reports short and parseable: omp `outputSchema`, Claude `--json-schema`, Codex `--output-schema` (omp://tools/task.md, claude 2.1.322 --help, codex 0.163.0 exec --help).
- Cap reasoning spend with effort, not prose; cap output with `max_output_tokens` on the API ([oa-reasoning](https://developers.openai.com/api/docs/guides/reasoning)).
- Idle background work burns tokens: scheduled loops, goal check-ins, session recap, prompt suggestions, idle compaction ([cc-costs](https://code.claude.com/docs/en/costs)).

## 6. Decision table

Tiers: S = small (Haiku 5.5, gpt-6-luna, omp `@smol`); M = mid (Sonnet 5.5, gpt-6.1-sol or gpt-6.1-terra, omp `@task`/`@default`); L = large (Opus 5.5 high/xhigh, Fable 5.2, gpt-6-astra, omp `@slow`). Mapping is [inference] from the sources in sections 1-5 unless cited.

| Task type | Tier and effort | omp | Claude Code | Codex | Delegate? | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Search / locate | S, low-medium | `scout` (`@smol`, medium) | Explore, or user `Explore` with `model: haiku` | `explorer` or custom agent on `gpt-6-luna` high | Yes if results span many files; no for one known symbol | Keeps raw search out of main context ([cc-subagents](https://code.claude.com/docs/en/sub-agents), [cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)) |
| Mechanical edit (rename, boilerplate) | S, medium | `sonic` | subagent `model: haiku`, `effort: low` | custom agent `gpt-6-luna` | Only when many files or parallel; else inline | Haiku "for quick mechanical work" ([help-limits](https://support.claude.com/en/articles/14552983)) |
| Routine feature | M, medium | main session or `task` (thinking auto) | Sonnet 5.5 or Opus 5.5 at medium | `gpt-6.1-sol` medium | Usually no; yes for independent slices | Shared context, few parallel parts ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)) |
| Hard design, debug, concurrency | L, high-xhigh | main on `@slow` or `^model:high`; delegate only evidence gathering | Opus 5.5 high/xhigh or Fable 5.2 | `gpt-6-astra` high/xhigh | No for the reasoning itself | omp warns against offloading reasoning to scout/sonic (omp://task-agent-discovery.md) |
| Review / judge | M-L, high | `reviewer` (`@slow`) | subagent `opus`, `effort: high` | reviewer agent `gpt-6.1-sol` medium-high | Yes; fresh context avoids author bias [inference] | `high` for reviewer agents ([cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)) |
| Long autonomous run | L planning, M/S execution | `--prewalk` or `prewalk.auto: on`; `--plan-yolo`; `--max-cost` | `fable` or `opusplan`; `--max-budget-usd` with `-p` | `gpt-6.1-sol` for repeated long runs, Astra for hardest | Plan once, execute cheaper | Fable sustains long sessions ([cc-model](https://code.claude.com/docs/en/model-config)); Sol for long-running work ([cx-models](https://learn.chatgpt.com/docs/models)) |
| Summarize transcripts / logs | S, medium-high | `sonic` or `seance` consult | subagent `haiku` (watch 100K repricing) | `gpt-6-luna` | Yes | Luna for structured summaries ([cx-models](https://learn.chatgpt.com/docs/models)); Haiku price jump over 100K ([anth-pricing](https://platform.claude.com/docs/en/about-claude/pricing)) |

When NOT to delegate:
- One-file or one-grep tasks: a fresh child re-pays system prompt, context files and a cold cache, and the parent pays to read its report [inference from [cc-cache](https://code.claude.com/docs/en/prompt-caching)].
- Tightly coupled or shared-context work, and concurrent writes to the same files ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system), [cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Questions answerable from current context (`/btw`) ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Follow-ups to a finished child: message it (`write agent://<id>`, Claude `SendMessage`) instead of a new spawn; resumed runs can reuse the warmed cache (omp://tools/task.md, [cc-cache](https://code.claude.com/docs/en/prompt-caching)).
- Fork instead of fresh subagent when the child needs the whole conversation (shared cache) ([cc-subagents](https://code.claude.com/docs/en/sub-agents)).

## 7. Guardrails
- Per-agent budgets: omp `task.softRequestBudget` / `task.agentSoftRequestBudget` / `task.maxRuntimeMs`; Claude `maxTurns`; Codex [unverified: no documented per-agent turn cap found] (omp://tools/task.md, [cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Session spend caps: omp `--max-cost` (subagents included, exit 3); Claude `--max-budget-usd` (print only) (omp://cli-reference.md, claude 2.1.322 --help).
- Concurrency caps: omp `task.maxConcurrency` 32; Claude 20; Codex `agents.max_concurrent_threads_per_session` (doc examples use 6-8) (omp://tools/task.md, [cc-subagents](https://code.claude.com/docs/en/sub-agents), [cx-subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Depth caps: omp `task.maxRecursionDepth` 2; Claude 3 layers (omp://tools/task.md, [cc-subagents](https://code.claude.com/docs/en/sub-agents)).
- Put explicit effort-scaling rules in the orchestrator prompt (agent count, tool-call budget) ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Measure after a run: omp `omp usage`, `omp stats`, Agent Hub, task `usage`; Claude `/usage` attribution (subagent share), `modelUsage` in JSON output; Codex `/status` and the usage dashboard weekly (omp://cli-reference.md, [cc-costs](https://code.claude.com/docs/en/costs), [cx-pricing](https://learn.chatgpt.com/docs/pricing)).
- Watch cache health: Claude `/usage` "Prompt cache (main)" line; OpenAI `cached_tokens` and `cache_write_tokens` ([cc-costs](https://code.claude.com/docs/en/costs), [oa-cache](https://developers.openai.com/api/docs/guides/prompt-caching)).
- Judges: a single LLM call with a rubric and 0.0-1.0 score plus pass/fail was most consistent with human judgment; keep human spot checks ([ma-post](https://www.anthropic.com/engineering/multi-agent-research-system)).
- Cross-family judging (e.g., Claude work reviewed by a GPT model and vice versa) reduces shared blind spots [inference; no primary source this session states it].
- Org caps: Claude `availableModels`, `maxEffortLevel`; omp `task.maxEffort`, `task.perCallModelAllow` ([cc-model](https://code.claude.com/docs/en/model-config), omp://task-agent-discovery.md).
