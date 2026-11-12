# Agentic engineering workflow (2026)

How to plan, run, verify, and review agent work. Distilled from 2026 talks dated 2026-01-20 to 2026-10-21. Read the conflicts table first: where practice changed, the "Use" column is the current rule. Harness features (plan mode, `/goal`, threads) map onto whatever the current harness offers. The rule behind each one carries over: plan before building, run autonomy only behind a feedback loop, one worktree per thread.

---

## 0. Changes over time (read first)

| Topic | Earlier | Latest | Use |
|---|---|---|---|
| `/goal`-style autonomous runs | Only for prototypes and throwaway tools (2026-05-20) | Valuable, but only with a feedback loop (2026-08-14) | Run them only with a defined finish line and a machine-checkable feedback loop. |
| Custom loop CLIs | A PRD-driven loop CLI (2026-01-20) | Harness-native goal loops replaced them (2026-05-20) | Don't build on custom loop CLIs; use the harness's loop with a feedback loop. |
| Plan mode | Right after one context-gathering prompt (2026-05-22) | Only after many discussion turns, then a plan file in `plan/` (2026-06-05) | Discuss first, plan mode last, save the plan file. |
| Review bar | Merge at a good-enough AI review score (2026-01-29, 2026-05-22) | Loop until the AI reviewer is fully clean, with an escape hatch when stuck (2026-09-01) | deep-mode's pr-review technique: no P0/P1 open, every P2 fixed or dismissed, 3-round cap. |
| Integration branch | Feature branches into `staging`, promoted to `main` (2026-05-22) | Fresh worktree from `origin/main`, merged to `main`; never build on `main` (2026-09-01) | Worktree off `origin/main`. A staging flow is project-specific. |
| Harness | Changed several times through the year (2026-02 to 2026-08) | A meta-harness over several agents; the workflow lives in AGENTS.md and skills (2026-09-01, 2026-10-21) | Keep the workflow in AGENTS.md and skills so any harness works. |

---

## 1. Planning before coding

- Never one-shot plan mode ("build X", toggle plan, build without reading). The model fills gaps with assumptions, and the product suffers (2026-06-05).
- Order: talk first, outside plan mode. Brainstorm and weigh trade-offs over several turns until the agent understands the intent. Ask for a step-by-step roadmap. Then enter plan mode and have it write a Markdown plan into `plan/` (subfolders per area such as `plan/active`, `plan/mobile`). Then build (2026-06-05).
- If the agent starts building during the discussion, stop it and keep discussing.
- Example opener: describe the thing to build and what it need not do, then ask the agent to brainstorm what a great version looks like and share its view. Follow with a request for an ordered roadmap, then the full plan in plan mode.
- Plan files serve the human too. With one session building and several planning, the files record where each thread stands (2026-05-22, 2026-06-05).
- The best plans include teammates' input, not only the agent's.
- A useful plan has a diagram, the stack, guiding principles, phases with the riskiest integrations proven first (auth, streaming, push), and to-dos. To-dos help the agent most (2026-06-05).
- Ignore model time estimates. They assume human working speed.
- Before planning a feature modeled on another product, have the agent research that feature and explain it back. Then ask for a plan that reviews the whole codebase and does not break other features (2026-05-22).
- Small features can skip the plan and go straight to back-and-forth building.
- Split work into small PRs, ideally a few hundred lines. Split a 2,000-line change into several smaller ones. Smaller PRs are easier for both humans and agents (2026-05-22).
- Stack PRs only when pieces truly depend on each other. Otherwise use independent branches.
- An autonomous loop needs a step-by-step checklist PRD (2026-01-20).
- Use a quick autonomous prototype to explore an idea before building the real thing (2026-05-20).
- When two architectures are plausible, run one thread per option, each in its own worktree with a running build, and compare them side by side (2026-08-14).

## 2. Execution

### Loops
- Autonomous runs need a defined finish line and a feedback loop. Example: have the agent use the browser to run Lighthouse and keep optimizing until every score is 100; that ran for hours and hit the target. Without a feedback loop the result is poor (2026-08-14).
- Use autonomous runs to improve a part of an app against a measurable signal, not to build whole apps, except small internal tools.
- Long unattended runs burn tokens, pile up assumptions, and leave the human out of the loop. Budget for that (2026-05-20).

### Isolation and parallelism
- Every feature, fix, or task starts in a fresh worktree from `origin/main` (`isolate.md`), so parallel agents never edit the same files (2026-09-01).
- AGENTS.md rules: no direct commits to `main`; one worktree and branch per task per agent; never touch another agent's worktree, branch, or uncommitted work; check open PRs for overlap before starting; never force-push `main`; regenerate lockfiles to resolve conflicts; remember that worktrees share ports and databases (2026-09-01). `AGENTS.template.md` carries these rules.
- Configure the harness so each new thread gets a new worktree. Let agents resolve their own merge conflicts (2026-10-21).
- Run agents on always-on machines (a spare laptop, a Linux box, a VPS) reachable over Tailscale or SSH, so work continues when the laptop closes (2026-10-21).
- Parallel pattern: one session building, several planning. Fire large refactors at a background agent and review when it finishes (2026-02-25, 2026-06-05).

### Harness and model choice
- Match the agent to the task: a fast, assumption-making model for interactive feature work; a slower, question-asking model for large refactors run unattended. Each catches the other's mistakes (2026-02-25).
- Effort: medium for simple work, highest for hard reasoning. Fast mode when speed matters, standard to save tokens (2026-08-14).
- Install computer use plus only the plugins in your real workflow (GitHub, Vercel, Convex, Linear) (2026-08-14).
- Dictate prompts by voice. Spoken prompts carry more detail (2026-05-22).
- A meta-harness that switches agents mid-thread with context handoff pays off once you have more than one subscription or machine (2026-10-21).

## 3. Verification

- Before the PR, the agent proves the change (`prove.md`): run the repo's checks, capture the bug while reproducing it, fix it, then capture the working result (2026-09-01).
- The PR shows proof: screenshots or video for visible changes, numbers or output pairs otherwise (2026-09-01).
- A cloud agent can take an issue, reproduce the bug, fix it, and record a video. Watch the video before reading the diff. The same agent can confirm whether a reported bug is real (2026-09-01).
- A human tries the feature locally after the agent builds it and before review. Screenshot bugs, paste them back, and queue follow-ups (2026-05-22, 2026-06-09).
- Automate QA: have the agent run the app and test the flow in a browser, reporting what works and what could improve. Use computer use for desktop apps (2026-08-14).
- The agent writes tests for every feature and revises them on review feedback (2026-01-20, 2026-05-22).

## 4. Review

deep-mode reviews with its pr-review technique (`skill://deep-mode/references/techniques/pr-review.md`). The rules it follows:

- Review every push to the PR branch.
- Loop: read every finding, fix, push, re-review, until clean. Cap the rounds. If the loop cycles without progress, stop and review by hand; more agent edits past that point add errors (2026-05-22).
- Split very large PRs (about 2,000 lines or more) before review. Reviewers miss things in huge diffs.
- Review stacked PRs in order and merge each when clean.
- Check for failing CI and an incomplete description alongside open comments (2026-02-25).
- Tune the reviewer to be strict. Small issues are cheap to fix early (2026-01-29).
- After a clean review, the human checks the before and after proof and the description, then merges (2026-09-01).
- AI review keeps catching bugs a human missed, such as race conditions and config-loading errors (2026-01-20, 2026-06-09).
- When code feels too complex after a feature, run a simplify pass and tidy shared operations with `structure.md`.

## 5. Skills and AGENTS.md

- Skills and MCP complement each other. MCP gives tool and data access. Skills give procedure, expertise, and workflow, turning access into reliable outcomes. Avoid conflicting output instructions between them (2026-01-29).
- Write a skill for multi-step work across tools, for processes that need consistency, and for knowledge you keep re-explaining or that must survive team turnover (2026-01-29).
- Progressive disclosure: the `name` and `description` load always; the `SKILL.md` body loads when relevant; bundled files load by name. A full skill can cost many times the tokens of its description (2026-01-29, 2026-06-09).
- AGENTS.md loads every turn, so keep it to what the agent always needs: branching and PR workflow, and where vendored dependency source lives. Do not describe the codebase there; the agent can search it. Skills hold on-demand actions such as restructuring or simplifying. Use both (2026-06-09).
- Keep a gitignored folder of dependency source via `npx opensrc <package|github-url>` ([vercel-labs/opensrc](https://github.com/vercel-labs/opensrc); see `stack.md` §11), and tell the agent in AGENTS.md to search it (2026-06-09).
- Build skills from repetition: whatever you do every time becomes a skill. Copied skills are a start; your own fit better (2026-09-01).
- Encode your review preferences in skills, so generated code reads the way you would write it.

## 6. Principles

- Engineering experience steers the agent. The operator's judgment sets the quality ceiling.
- Review line by line when the model is weak in the domain, such as a new framework.
- Agents duplicate code readily. Structure output so a human can review it, and use `structure.md` to pull shared operations into services (2026-09-01).
- Agentic engineering succeeds only when the operator plans properly (2026-06-05).
- Skip practices that sound impressive but don't improve output (2026-08-14).
- Feedback loops make autonomy work: autonomous runs need tools, a feedback loop, and a clear PRD (2026-01-20, 2026-08-14).
- Keep prompts and loops short and to the point (2026-05-22).
- Avoid UIs that force constant context switching (2026-10-21).
- Install only the plugins your workflow uses (2026-08-14).

## 7. The ship loop end to end

This skill's `SKILL.md` runs the full loop:

1. **Isolate:** a worktree from `origin/main` per task (`isolate.md`).
2. **Build:** entry points own product rules, services own reusable operations (`structure.md`).
3. **Prove:** checks plus runtime evidence, before and after (`prove.md`).
4. **Ship:** a PR with the proof, reviewed by deep-mode's pr-review technique until clean.
5. **Human:** check the proof and description, then merge on a deep-mode panel pass.

Run many tasks in parallel, each in its own worktree. A rebuild run through this loop can take a fraction of the time of the first build (2026-09-01). To adopt it, copy `AGENTS.template.md`, try it on a sample project, and adjust it to how your team works.
