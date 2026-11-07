# Agentic engineering workflow (Ras Mic, 2026)

How he plans, runs, verifies, and reviews agent work, distilled from 10 transcripts. Read the conflicts table first: where his practice changed, the "Use" column is the current rule. Harness-specific features (plan mode, `/goal`, T3 Code threads) map onto whatever the current harness offers; the rule behind each one (plan before building, run autonomy only behind a feedback loop, one worktree per thread) carries over.

Sources: 10 assigned transcripts, 2026-01-20 → 2026-10-21. Citation format: (Title, date). SPONSOR = paid segment. Caption fixes applied: "GP loop / grep loop / Gre Loop" = Greptile's `/greploop` skill; "Grapile/Gravile/Reptile/Greal" = Greptile; "agents.mmd" = AGENTS.md; "Spelt" = Svelte; "work OS" = WorkOS.

---

## 0. Conflicts / changes over time (read first)

| Topic | Earlier | Latest | Use |
|---|---|---|---|
| `/goal` | "cooler than it is useful", only for prototypes/throwaway internal tools; "for anything other than that it is completely useless" (please stop using /goal, 2026-05-20) | "goal is one of my favorite tools — I use it only if I have a feedback loop" (I'm done with Claude Code, 2026-08-14) | Use `/goal` only with a defined finish line + machine-checkable feedback loop. |
| Ralph/Ralphy loop | Ralphy = his PRD loop CLI (I fixed Ralph. Meet Ralphy, 2026-01-20) | "I stopped maintaining Ralphie because I knew the models were going to do this themselves"; "Ralph Wiggum is officially dead it's now /goal" (please stop using /goal, 2026-05-20) | Don't build on Ralphy; use native `/goal` with feedback loop. |
| Plan mode | Used plan mode right after one context-gathering prompt (My Agentic Engineering Workflow, 2026-05-22) | Plan mode only after many back-and-forth turns, then write plan MD to `plan/` (stop using plan mode, 2026-06-05); factory pipeline (2026-09-01) has no explicit plan step | Discuss first, plan mode last, persist plan file. |
| Greptile bar | "minimum of four out of five" to merge (Do you really need Skills, 2026-01-29, SPONSOR); "four out of five and higher… good enough for me" (2026-05-22) | "until Greptile reports five out of five with zero unresolved comments"; "not getting merged by me until I get a five out of five" (software factory, 2026-09-01) | Target 5/5, 0 unresolved. Escape hatch from 2026-05-22: stop if stuck looping at 4/5. |
| Integration branch | Feature branches from `staging`, PR into `staging`, promote staging→main (My Agentic Engineering Workflow, 2026-05-22; This loop + skill fixes AI slop, 2026-06-09) | Fresh git worktree "branched from origin main", merge back to main; "Never build on main" (software factory, 2026-09-01) | Latest = worktree off `origin/main`. Staging flow may be project-specific (Pluto). |
| Harness | Claude Code = driver, Codex = fire-and-forget, Cursor resurging (1000+ Hours, 2026-02-25) → Cursor + GPT-5.5 extra high fast (2026-05-22) → Codex app, GPT 5.6 "Soul" (2026-08-14) | T3 Code as daily driver (meta-harness) (I stopped using Claude Code, 2026-10-21); factory is "harness agnostic and model agnostic" (2026-09-01) | Keep workflow in AGENTS.md + skills so any harness works. |

---

## 1. Planning before coding (replaces plain plan mode / plain /goal)

- Do NOT one-shot plan mode ("build X" + toggle plan + build without reading). "the model is going to be making a lot of assumptions for you and that's just not good product experience" (stop using plan mode, 2026-06-05).
- Workflow: converse first (not in plan mode) → brainstorm, discuss trade-offs over multiple turns → once the agent "understands what I have in my noggin" → ask for a step-by-step roadmap → THEN enter plan mode → have it write an MD file into a `plan/` folder (subfolders per area, e.g. `plan/active`, `plan/apps`, `plan/desktop`, `plan/simplify`, `plan/mobile`) → then build (stop using plan mode, 2026-06-05).
- If the model "gets jumpy and tries to build I'll tell her to shut up… what I want is for me and the model to chat and to plan" (stop using plan mode, 2026-06-05).
- Example opener prompt (cleaned): "I want to build a companion mobile app for Pluto… I don't expect it to be one-to-one with the desktop or web app but useful enough… brainstorm some ideas on what a great companion app would look like and share your thoughts." Later: "build out the road map… step by step what comes first, second, third", then "you have all the context… build the ultimate plan to build this to completion" + plan mode (stop using plan mode, 2026-06-05).
- Plan files are for the human too: "The MD files are just as much for you as they are for the agent" — he works in parallel (one tab building, multiple tabs planning) and needs to remember where he left off (stop using plan mode, 2026-06-05; also "the plan… most of the time is really for me", My Agentic Engineering Workflow, 2026-05-22).
- Best plans include input from teammates, not just agent: the `apps` plan came from "tons of back and forth not only me and the agent but me and one of our engineers" (stop using plan mode, 2026-06-05).
- Valued plan contents: diagram, tech stack, guiding principles, phases with de-risking first ("prove the three riskiest integrations on real device before building features": auth, streaming, push), and to-dos ("the to-dos is what I like from plan mode because this helps the agent") (stop using plan mode, 2026-06-05).
- Ignore model time estimates: models "overestimate how long it's going to take because they're thinking of human working time… Nah we're doing it right now 3 hours 2 hours max" (stop using plan mode, 2026-06-05).
- Context-gathering prompt pattern before planning: ask agent to web-search the reference feature and explain it back; then "create a plan… review the entire codebase… I don't want us to build this feature for the cost of breaking another one" (My Agentic Engineering Workflow, 2026-05-22).
- Planning is optional sometimes: "there are times where I'll just build the feature going back and forth with it" (My Agentic Engineering Workflow, 2026-05-22).
- Task granularity = small PRs. Prefer plans that split into multiple minimal PRs (accepted a 5-PR rollout; later split a 2,000-line PR into 4 stacked PRs each <1,000 lines; goal "a couple hundred lines each maybe even if it's thousand"). "the smaller the PR the more focused the PR the better your life is and I think the same applies to the agent" (My Agentic Engineering Workflow, 2026-05-22).
- Use stacked PRs when pieces genuinely depend on each other; else independent branches (My Agentic Engineering Workflow, 2026-05-22; AGENTS.md rule in This loop + skill fixes AI slop, 2026-06-09).
- PRD for autonomous loops (Ralphy era): needs "a step-by-step checklist"; he generated the PRD with AI (I fixed Ralph. Meet Ralphy, 2026-01-20).
- `/goal` as pre-planning: use a `/goal` prototype to explore an idea before building the real thing — "a great prototype to use before I even get in to build the actual real thing" (please stop using /goal, 2026-05-20).
- Thread-max design forks: when two architectures are possible, have the agent spin up separate threads, each in a worktree, each with a running browser version to compare; research competing frameworks one-thread-per-option then rank (I'm done with Claude Code, 2026-08-14).

## 2. Execution

### Loops
- Ralphy (historical, 2026-01-20): `npm install` the CLI; `ralphy init` → creates `config.yaml` + `progress.txt`; `ralphy --add-rule "..."` (e.g. Next.js 16, shadcn/ui, Tailwind v4); `ralphy --prd PRD.md --cursor` (engine selectable; input = markdown PRD, YAML, or GitHub issues); modes: single task, sequential, parallel agents in worktrees with clean merge, branch-per-task; `--browser` for browser testing; writes tests per feature. Use it to "build the entirety of the thing and then you can step in"; human-in-the-loop loops make no sense—"I would just rather use the agent" (I fixed Ralph. Meet Ralphy, 2026-01-20). Exact flag spelling is caption-derived; verify.
- Superseded: Ralphy unmaintained, `/goal` replaced it (please stop using /goal, 2026-05-20).
- `/goal` rules (latest, 2026-08-14): require (a) defined finish line and (b) feedback loop. Example: "use the browser… run a Lighthouse score test… make this site blazingly fast and get all hundreds" → ran ~3 hours → all-100 Lighthouse. "your /goal run is garbage… because it doesn't have a feedback loop." Don't use it to build apps (except random internal tools, e.g. env vars → 1Password); use it to improve parts of apps with a feedback loop (I'm done with Claude Code, 2026-08-14).
- Earlier `/goal` example prompt: "/goal I want to build the following: I want to run Among Us game but instead of humans playing I want different AI models to play… build a complete system that will allow for this." Caveat: "it will guzzle tokens", heavy assumptions, "you're not going to be in the loop" (please stop using /goal, 2026-05-20).

### Isolation / parallelism
- Every new feature/fix/task starts in a fresh git worktree branched from `origin/main` via the `new-feature` skill — "Never build on main… one of the most important lines in this AGENTS.md" — so parallel agents don't collide (delete/edit same files) (software factory, 2026-09-01).
- AGENTS.md rules: never commit directly to main; one worktree + one branch per task per agent; never reuse/modify another agent's worktree, branch, or uncommitted work; scope check before starting (skim open PRs, changed files); never force-push main; resolve lock files [caption "log files", INFERENCE: lockfiles]; "worktrees don't isolate shared resources"; how to complete a task (software factory, 2026-09-01).
- Configure the harness so every new thread = new worktree (T3 Code setting; projects' T3 JSON can override); agents fix merge conflicts themselves (I stopped using Claude Code, 2026-10-21).
- Run agents on always-on machines (spare laptop/Linux box/VPS) over Tailscale or T3 Connect/SSH, controlled from one T3 Code instance + mobile app, so work continues when the laptop closes (I stopped using Claude Code, 2026-10-21).
- Parallel pattern: 1 tab building, several tabs planning (stop using plan mode, 2026-06-05). Codex encourages firing big tasks and leaving (e.g. overnight "remove the white label feature"), then review/feedback cycles (1000+ Hours, 2026-02-25).

### Harness/model choice (by date)
- 2026-02-25: Claude Code (Opus 4.6) for continuous back-and-forth feature work in Ghostty; Codex (GPT 5.3 Codex, medium or extra high) for big refactors/architecture changes/fire-and-forget; try each 2 weeks; Cursor regained favor (all models) (1000+ Hours, 2026-02-25).
- 2026-05-22: Cursor + GPT-5.5 extra high fast; subagents on Composer 2.5 Fast; Wispr Flow dictation ("when you speak… you will say a lot more than you type") (My Agentic Engineering Workflow, 2026-05-22).
- 2026-08-14: Codex app, GPT 5.6 "Soul" (caption; Terra/Luna alternatives), effort medium for simple, extra high for brainy; speed fast (standard to save tokens); $200/mo plan. Install computer-use plugin + only workflow plugins (GitHub, Vercel, Convex, Linear) (I'm done with Claude Code, 2026-08-14).
- 2026-10-21: T3 Code meta-harness (via ACP) as daily driver; switch Claude Code/Codex/Cursor mid-thread with context handoff (Orchestrator V2), fork threads; settled-inbox sidebar (threads settle when PR merges). Nightly build caveat. Use if you have >1 subscription or >1 machine (I stopped using Claude Code, 2026-10-21).

## 3. Verification

- Before PR, the agent must prove the change: `evidence-driven-testing` skill — "Verify with the repo's checks plus runtime evidence. Capture the before state while reproducing the issue prior to fixing it, when it's cheapest, and after once the change works"; it reproduces the bug, fixes, records the solution (software factory, 2026-09-01).
- `before-and-after` skill (taken from Vercel's repo): screenshot before/after state of pages/elements and embed in PR. PR description must include proof: "Screenshot or video whenever the change has visible surface. Measure numbers or output pairs when it doesn't" (software factory, 2026-09-01).
- SPONSOR (Cursor Cloud Agents, 2026-09-01): Linear issue → MCP → cloud agent reproduces bug, fixes, records video; he watches the video before reading the PR; agent can also confirm whether reported bugs are real. Keep pattern (video proof) — consistent with his own evidence skills.
- Human tests the feature locally after the agent builds, before code review (This loop + skill fixes AI slop, 2026-06-09; My Agentic Engineering Workflow, 2026-05-22 — screenshot bugs, paste into chat, queue follow-up prompts).
- Browser QA: have the agent run the app locally and test it in the in-app browser — "I just don't want code review but I want user test review… the QA process automated." Prompt (cleaned): "use the browser that you have; I have an application running; test agent creation and tell me if it works or if something can be improved." Use annotate mode to stack UI change requests. Computer use for desktop apps (I'm done with Claude Code, 2026-08-14).
- Tests: Ralphy writes tests for every feature + browser testing (I fixed Ralph. Meet Ralphy, 2026-01-20); GPT-5.5 "just writes a bunch of tests" and revises them on review feedback (My Agentic Engineering Workflow, 2026-05-22).

## 4. Review (Greptile + greploop)

- Every push to a PR branch triggers a Greptile review with a confidence score /5 (My Agentic Engineering Workflow, 2026-05-22).
- Run `/greploop <PR#>` (e.g. `/greploop 128`, `/greploop PR87`): agent reads Greptile summary + inline comments via GitHub, fixes, pushes, re-triggers ("@greptile review"), waits, repeats until 5/5 with zero unresolved comments (ran 19 min in one case). Get it from Greptile's GitHub skills repo (This loop + skill fixes AI slop, 2026-06-09; My Agentic Engineering Workflow, 2026-05-22; I'm done with Claude Code, 2026-08-14).
- Turn cap: "maximum of like five to six turns"/"five turns, whichever comes first" (My Agentic Engineering Workflow, 2026-05-22). If stuck cycling at 4/5: stop, review yourself, merge — "you don't want the agent to keep editing… it's going to start hallucinating" (same).
- Big PRs: if ~2,000+ lines, split before greplooping (Greptile can't capture everything); latest factory uses `greploop-apps` variant when PR exceeds Greptile's file-count limit ("3,000 4,000 5,000 lines of code") (My Agentic Engineering Workflow, 2026-05-22; software factory, 2026-09-01).
- Stacked PRs: greploop each in order, merge each at 5/5 (#87→#88→#89→#90) (My Agentic Engineering Workflow, 2026-05-22).
- `check-pr` skill (SPONSOR context, 2026-02-25): inspects PR for unresolved comments, failing CI, incomplete description; usage "check PR 29" then greploop; greploop also waits for CI (1000+ Hours, 2026-02-25).
- Greptile strictness set to "low" to catch even minute issues (Do you really need Skills, 2026-01-29, SPONSOR). Not-sponsored endorsements: "this video is not sponsored. I genuinely love and use Greptile" (This loop + skill fixes AI slop, 2026-06-09; also 2026-08-14).
- Human's job after 5/5: "look at before and after… read the description and then I just merge" (software factory, 2026-09-01).
- Why: AI review catches what his own review missed (race condition Claude Code claimed fine; config-loading bug) (Do you really need Skills, 2026-01-29 / Ralphy, 2026-01-20 — both SPONSOR). "There's always something that gets caught" (This loop + skill fixes AI slop, 2026-06-09).
- Optional cleanup: run `code-simplifier` (Anthropic) by vibes when code "feels too complex"; run `code-structure` after a feature to tidy (This loop + skill fixes AI slop, 2026-06-09; My Agentic Engineering Workflow, 2026-05-22).

## 5. Skills philosophy

- Skills vs MCP are complementary: MCP = tool/data access; skills = SOP/expertise/workflow ("turn raw tool access into reliable outcomes"). Let MCP handle connectivity; let skills handle presentation, sequencing, workflow logic; avoid conflicting output instructions between them. One skill can use many MCPs; many skills per MCP (Do you really need Skills, 2026-01-29).
- Write a skill for multi-step workflows across tools, processes where consistency matters, knowledge that "gets reexplained every time" or should survive team turnover (Do you really need Skills, 2026-01-29).
- Progressive disclosure: level 1 = YAML `name` + `description` in system prompt; level 2 = full `SKILL.md` body when relevant; level 3 = bundled files referenced by name (e.g. `reference.md`, `forms.md`) (Do you really need Skills, 2026-01-29). Token demo: whole skill 944 tokens vs name+description 53 (This loop + skill fixes AI slop, 2026-06-09).
- AGENTS.md vs skills: AGENTS.md is injected every turn → only put "stuff that the agent needs to know all the time" (branching/PR workflow; that `opensrc/`-style folder of dependency source code exists for up-to-date reference). Skills = need-to-know, user-triggered actions (restructure, greploop, simplify). "for the love of all things do not put the codebase information… the agent knows it can search the code" (This loop + skill fixes AI slop, 2026-06-09).
- Use both: "Both are necessary. Both are important" (This loop + skill fixes AI slop, 2026-06-09).
- Keep a gitignored folder of source code for open-source deps (browser-use, Composio, Daytona, Crossmint, Supermemory…) via `npx opensrc <package|github-url>` ([vercel-labs/opensrc](https://github.com/vercel-labs/opensrc); see `stack.md` §11) and tell the agent in AGENTS.md to search it (This loop + skill fixes AI slop, 2026-06-09).
- Build your own skills from repetition: "figuring out what I do repeatedly… I would run greploop always. Right now this is part of my software factory" (software factory, 2026-09-01). "Yes you can copy my skills but… more powerful if you build your own" (same).
- Write skills so code matches YOUR review preferences: code-structure encodes service-layer architecture because "the code written makes sense to you" (software factory, 2026-09-01).

## 6. Principles / lessons

- Your engineering experience steers the agent: "the experience I have from building applications it's what steers me" (My Agentic Engineering Workflow, 2026-05-22).
- Codex vs Claude: Codex methodical/slow, asks questions ("European"); Opus fast, aggressive, makes assumptions ("American… F-150"); each fixes the other's mistakes — "it really is all about vibes" (1000+ Hours, 2026-02-25).
- Review code line by line when the model is weak in the domain: with TanStack Start "the models are not that good… so I dived in, I wrote some code" and "I missed looking at code, reviewing line by line" (1000+ Hours, 2026-02-25).
- With Claude Code: "let it do a feature, review the code" cycle; with Codex: delegate big task, leave, review, feedback, merge when perfect (1000+ Hours, 2026-02-25).
- Structure generated code so a human can review it "like it's 2022"; AI "loves to write duplicate code" → service-layer skill (software factory, 2026-09-01).
- Plan properly: "agentic engineering can only be successful for you when you the operator have planned properly" (stop using plan mode, 2026-06-05).
- Don't chase cool-sounding practices: "there are a lot of things in our space right now that sound cool but aren't productive" (thread maxing, I'm done with Claude Code, 2026-08-14).
- Feedback loops are what make autonomy work (`/goal`, greploop): "this works because there's a feedback loop" (I'm done with Claude Code, 2026-08-14). Autonomous loops need tools + feedback loop + well-written PRD (Ralphy, 2026-01-20).
- Short loops: "short simple concise to the point not too long, that's the sauce" (My Agentic Engineering Workflow, 2026-05-22).
- Avoid context-switching UIs: "context switching UIs is probably the worst thing that you could do to yourself" (I stopped using Claude Code, 2026-10-21).
- Don't use Antigravity/Gemini with the factory: "Gemini is just terrible" (software factory, 2026-09-01).
- Install only plugins in your actual workflow (I'm done with Claude Code, 2026-08-14).

## 7. The software factory (end-to-end, 2026-09-01)

Files: `AGENTS.md` + skills `new-feature`, `code-structure`, `evidence-driven-testing`, `before-and-after` (from Vercel), `greploop`, `greploop-apps`, `unslop`. Published at [michaelshimeles/skills](https://github.com/michaelshimeles/skills) (same tree as [michaelshimeles/rstack](https://github.com/michaelshimeles/rstack); vendored here under `references/`). Claim: harness- and model-agnostic (Codex, Claude Code, Cursor, Grok…). (I have a software factory, 2026-09-01)

1. **Isolate** — `new-feature` skill: "Start a new task in an isolated git worktree branched from origin/main so multiple agents can work on the same repo in parallel without conflicts. Use at the beginning of every new feature, fix, or task before writing any code."
2. **Build** — `code-structure` skill: service-layer architecture; "actions/boundaries orchestrating the why and when; a service layer owns the reusable how with explicit inputs and structured returns." Trigger description: "Use when multiple workflows duplicate the same operational logic… deciding what belongs in action versus shared services… refactoring repeated operational blocks… adding new features that share mechanics with existing ones."
3. **Prove** — `evidence-driven-testing` (repo checks + runtime evidence, before state captured while reproducing, after state once working); fallback `before-and-after` screenshots or a cloud agent if the machine can't run it.
4. **Ship** — open PR with before/after proof embedded; run `greploop` (or `greploop-apps` when PR exceeds Greptile's file-count limit) "until Greptile reports five out of five with zero unresolved comments. Finish by presenting the PR URL."
5. **Human** — check before/after + description, merge. Run many agents/features/harnesses in parallel.

Results he cites: Pluto v1 ~1–1.5 months without factory; Pluto v2 rebuilt from scratch, working in ~1.5 weeks + 2 weeks polish with the factory (software factory, 2026-09-01). How to adopt: copy skills, build a sample project, then tweak to your own workflow ("weeks and months of figuring out what my workflow is").
