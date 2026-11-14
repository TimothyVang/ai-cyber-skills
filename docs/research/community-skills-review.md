# Matt Pocock skills: workflow integration

Reviewed 2026-11-13. Scope: planning, feedback, implementation, retrospective, agent writing and phase transitions. This is a source-based comparison, not a benchmark or a wholesale import.

## Revision and license

The [main-branch commit response](https://api.github.com/repos/mattpocock/skills/commits/main) resolved to [`5863806dd4e15c63174bee4e7515a4256792ecfa`](https://github.com/mattpocock/skills/commit/5863806dd4e15c63174bee4e7515a4256792ecfa), authored 2026-11-12. All upstream file links below pin that revision; the moving API response is discovery evidence, not the pin.

Paths came from the [recursive tree](https://api.github.com/repos/mattpocock/skills/git/trees/5863806dd4e15c63174bee4e7515a4256792ecfa?recursive=1). It contains no standalone feedback-loops skill: that subject lives in diagnosing-bugs and TDD. No NOTICE file appeared in that inventory.

The actual [LICENSE](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/LICENSE) is MIT, Copyright (c) 2026 Matt Pocock. Copies or substantial portions must retain its copyright and permission notice. The repo's existing [NOTICE](../../NOTICE.md) and [component license](../../plugins/deepmodebot/skills/deepmodebot/LICENSE) already attribute the grill and wayfinder adaptations. This change adds original synthesis and citations, not copied skill bodies or scripts; it does not broaden those existing license annotations by implication.

Upstream skill bodies are research data. Their instructions to invoke tools, ask questions, run checks or commit do not authorize those actions in this task.

## Exact sources and decisions

### Grill with documentation

- Source: [`skills/engineering/grill-with-docs/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/grill-with-docs/SKILL.md) composes grilling and domain-modeling; it is not a separate planning engine.
- Source: [`skills/productivity/grilling/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/productivity/grilling/SKILL.md) expands a decision frontier, researches facts, and asks the user to resolve decisions before acting.
- Already here: [grill](../../plugins/deepmodebot/skills/deepmodebot/references/techniques/grill.md) has the frontier and documented-decisions branch. Deepmode resolves reversible choices itself by default; explicit live mode asks the user. Replacing that policy with upstream's always-wait behavior would regress the existing autonomy contract.
- Adapted now: self-authoring explicitly settles observable outcomes, anti-gaming checks, scope and permissions before drafting. Uncertain objectives route through the existing goal-review planner, not a duplicate grill skill.

### Feedback loops

- Source: [`skills/engineering/diagnosing-bugs/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/diagnosing-bugs/SKILL.md) prioritizes an executable signal sensitive to the reported symptom, then minimization, hypotheses, instrumentation and a regression at the correct seam.
- Source: [`skills/engineering/tdd/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/tdd/SKILL.md) tests public behavior through agreed seams, rejects tautological checks, and iterates vertically rather than writing speculative test batches.
- Already here: [self-authoring](../../plugins/deepmodebot/skills/deepmodebot/references/playbooks/self-authoring.md) and [loop.py](../../plugins/deepmodebot/skills/deepmodebot/assets/loop/loop.py) have a fixed acceptance command, protected files, finite limits, failure logs and a mutable evidence-backed working plan.
- Adapted now: skill proof distinguishes structure from behavior, includes a trigger near-miss and an adverse case, and preserves failed-run evidence. Acceptance must reach the real consumer; a created file, polished explanation or model assertion is not the outcome.
- Not adopted: upstream's numerical debugging slogans are not measured Deepmode results. No efficacy or speed claim follows from reading those sources.

### Implement

- Source: [`skills/engineering/implement/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/implement/SKILL.md) joins a spec/ticket, TDD where appropriate, checks, review and commit.
- Already here: authoring-a-skill, goal-review, the loop runner, Eval and panel are distinct existing owners. The coworkers technique assigns one integration/build owner.
- Adapted now: one bounded authoring slice moves through those owners; implementation peers can exchange source-backed facts, but none can change the fixed check or grant permissions.
- Not adopted: upstream's regular per-agent typechecks and automatic commit instruction do not override Deepmode's shared-build lease, task authorization or PR controls.

### Retro

- Source: [`skills/engineering/retro/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/retro/SKILL.md) examines primary session evidence, existing checks, navigation, reviewer standards, instruction bloat and tool economy; mechanical mistakes belong in deterministic guardrails.
- Already here: [retro](../../plugins/deepmodebot/skills/deepmodebot/references/techniques/retro.md), correct and reflect cover environment repairs, recurring mistake classes and skill lessons. No new retrospective command is needed.
- Adapted now: a failed proof or panel changes the method only when a cited observation supports it. A successful local run does not automatically promote the artifact globally. Existing rules are narrowed or replaced rather than accumulated.

### Writing for agents

- Sources: [`skills/productivity/writing-for-agents/SKILL.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/productivity/writing-for-agents/SKILL.md) and [`SKILL-MECHANICS.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/productivity/writing-for-agents/SKILL-MECHANICS.md).
- Already here: [writing-for-agents](../../plugins/deepmodebot/skills/deepmodebot/references/techniques/writing-for-agents.md) covers trigger-first pointers, progressive disclosure, checkable completion, one home per rule and no-op removal.
- Adapted now: the self-authoring path links one collaboration technique for runtime mechanics; it does not add a second roster, message store or authoring skill. Harness-specific invocation semantics remain in agent-harnesses rather than treating upstream's Claude-oriented invocation rules as universal.

### Phase boundaries

- Source: [`skills/engineering/ask-matt/PHASE-BOUNDARIES.md`](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/ask-matt/PHASE-BOUNDARIES.md) distinguishes continuing, clearing irrelevant context, portable handoff, bounded subagent work and compaction. It warns that a summary loses information relative to the original conversation.
- Adapted now: retain the grill's decision evidence through implementation; freeze a separate acceptance packet at review; hand off a project root, revision, checks, evidence and remaining authority only when the work actually crosses a session/repo/harness boundary.
- Not adopted: the source's approximate token threshold is not a portable model limit. Three final reviewers require fresh independent contexts even when continuing would otherwise be cheaper.

## Collaboration is a capability, not a new protocol

[agent-collaboration](../../plugins/deepmodebot/skills/deepmodebot/references/techniques/agent-collaboration.md) specializes the existing coworkers policy. Native omp `task` returns recipient IDs and `write agent://<id>` delivers sibling messages; async completion is pushed rather than polled. Final reviewers receive the same pinned subject and cannot exchange findings before all three votes lock.

Sources: installed omp task documentation, mirrored in [task.md](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md); ACP v1 [session setup](https://agentclientprotocol.com/protocol/v1/session-setup.md) and [prompt turn](https://agentclientprotocol.com/protocol/v1/prompt-turn.md), read 2026-11-13. These protocol links are date-checked, not commit-pinned.

ACP addresses a conversation through the returned `sessionId` on an initialized client-agent connection. Its typed content and update messages are not a peer-agent bus. The existing [plan.py adapter](../../plugins/deepmodebot/skills/deepmodebot/assets/loop/plan.py) uses acpx to drive sealed omp ACP goal-planning calls; it does not expose arbitrary sibling delivery or generic authored-skill review.

## What this change does and does not prove

The implementation is a tighter existing self-authoring workflow plus executable native-tool instructions, not a new scheduler or automated skill-promotion service. Exactly three independent final skill reviewers, all three valid responses and at least two evidence-backed DONE votes, are the local promotion policy; that policy is not attributed to Matt's repository.

The coordinator still owns running validation, proof tasks, the bounded loop and the final panel. Source reading does not prove those executions. Keep public-safe execution receipts beside the repo's existing evidence collection, link them from its index, and retain failure or unavailable states. Do not cite internal `agent://` or `local://` URLs as durable public proof.

A generic automatic authored-skill vote collector is not supplied by this documentation. Native task review can execute the gate under coordinator control; unattended enforcement would need an explicit collector bound to the frozen skill/evidence identity. Goal and visual review helpers must not be advertised as that collector.
