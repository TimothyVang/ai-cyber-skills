# Flows

Use when: the user asks which flow fits ("what's the process for X", "how should we approach this", "which flow do I use", "explain the deepmodebot workflow"), or you are choosing between flows for work bigger than one PR. The Route section of SKILL.md still picks the route; this file explains the map so you can show it. Paths are relative to this skill.

## The main line: idea to merged code

| Phase | Flow | Leaves behind |
|---|---|---|
| 1. Sharpen the idea | **grill** technique (`references/techniques/grill.md`), With docs mode in a repo with a glossary | Decision table, `GLOSSARY.md` terms, ADRs |
| 2. Settle a fork by running it | Prototype playbook (`references/playbooks/prototype.md`) | A decision backed by an observation |
| 3. Write it down | Spec playbook (`references/playbooks/spec.md`) | `docs/specs/<slug>.md` and a `spec` issue |
| 4. Cut it up | Tickets playbook (`references/playbooks/tickets.md`) | Tracer-bullet tickets with blockers |
| 5. Build it | Phased build in build mode (`references/playbooks/phased-build.md`) for one integration branch, or Work a queue with the board source (`references/playbooks/work-a-queue.md`) for one PR per ticket | Merged code |
| 6. Review and land | **pr-review** (`references/techniques/pr-review.md`), Opening a PR, **panel**, **pr-conversation** | A merged PR with evidence |

Skip phases the work doesn't need. One PR of settled work starts at phase 5 with the Feature or Bug fix playbook. A spec that fits one PR skips phase 4.

## On-ramps

| Situation | Flow |
|---|---|
| First use of the planning flows in a repo | Setup (`references/playbooks/setup.md`) |
| Issues or outside PRs pile up | Triage (`references/playbooks/triage.md`), which feeds phase 5 with `triage:agent-ready` items |
| A defect | Bug fix (`references/playbooks/bug-fix.md`) |
| The route itself is unknown, more than one session of deciding | Wayfinder (`references/playbooks/wayfinder.md`), which hands its decisions to phase 3 |
| A question to answer once | Investigation (`references/playbooks/investigation.md`) |
| A question whose answer should stay in the repo | **research** (`references/techniques/research.md`) |
| Words or decisions need recording | **domain-model** (`references/techniques/domain-model.md`) |
| A queue of labeled issues and the `factory` CLI | Work a queue with the factory source (`references/playbooks/work-a-queue.md`) |
| A multi-day program with many owners | Run a goal at program scale (`references/playbooks/run-a-goal.md`) |
| A workflow done the same way twice, or a goal to run unattended until a check passes | Self-authoring (`references/playbooks/self-authoring.md`), to write and prove a prompt, skill, goal, or loop |
| Choosing a repo layout, data model, database, or backend shape | `skill://software-architecture` |
| Secrets, logins, or agent authentication | `skill://secrets-and-auth` |
| Running in or scripting omp, Claude Code, or Codex; MCP or ACP | `skill://agent-harnesses` |

## Between phases

A phase boundary is where the context window gets managed. Mid-phase, keep going or split the rest into subagents. At the boundary, take the first that fits:
1. **Keep going** in this session when the next phase needs this phase's reasoning first hand (a grill straight into its spec) and there is room left.
2. **Start fresh** when nothing here matters to what comes next.
3. **Write it down for later.** Same repo, later session → a resume note with Pause safely (`references/playbooks/pause-safely.md`). Another harness, folder, or person → a portable doc with Handoff (`references/playbooks/handoff.md`).
4. **Hand it to a subagent** when the next phase runs without steering (a review, a research file).
5. **Compact** otherwise, telling the summary which phase comes next.

Each artifact above (spec, tickets, ADRs, research files) exists so a fresh session can pick up from the file instead of from memory.
