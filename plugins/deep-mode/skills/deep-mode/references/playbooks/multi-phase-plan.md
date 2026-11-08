# Multi-Phase Plan

Use when: a change spans multiple phases or PRs. You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from evidence. The plan is the deliverable; do not implement.

## Steps

1. One or two files with an obvious approach → skip the plan; say so and stop.
2. Settle open questions by prototype first (`references/playbooks/prototype.md`); keep branch, SHA, screenshots for Appendix A. `ask` the user only for product/preference calls no run can settle, with options (`references/principles/never-block-on-the-human.md`).
3. Explore via `scout` tasks (`references/principles/guard-the-context-window.md`); each returns file pointers, conventions, test commands, entry points; no inlined dumps.
4. Write the plan file (default `docs/<program>-plan.md` unless the user names a path) using the structure below; every heading and sub-block, in order. One section per PR; one PR = one change with its own evidence (`references/principles/sequence-verifiable-units.md`). Name the execution playbook in How to read this (`autopilot` in `merge` mode if the run may merge, `autopilot` in `stack-only` mode if the user lands PRs, `orchestrate` for a standing program).
5. Write with the **technical-writing** technique (`references/techniques/technical-writing.md`), then **unslop** (`references/techniques/unslop.md`). Body is how-to only; appendices hold explanation and reference. Each heading states a task or finding.
6. Run the Plan checklist below against the file; fix every failure.
7. Hand back the plan path and the checklist results, then stop.

## Plan structure

- `# <Program> plan`, then an intro under 10 non-blank lines: what changes, for whom, the rule enforced, PR ids in order.
- `## How to read this`, containing: "One box is one unit of work", "Every box names the evidence that checks it", "Check a box only when its evidence exists" (a file, log line, screenshot, test run, SHA), the execution playbook path, who merges, and the verification rule verbatim: **"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked."**
- `## Program checklist` with these `###` in order:
  - `Arm the program`: state protocol + plan, stop for the user's explicit go; list `read skill://deep-mode/references/playbooks/<name>.md` reads of the execution playbook and opening-a-pr, plus `read skill://<verify-skill>` for the repo's verification skill and each leaf skill (skills don't live in the repo; never `git show origin/main:`), re-read every tick; arm a recurring hourly audit tick (scheduled job or harness loop;
     never left to memory) with a verbatim tick prompt: re-read the playbook via `skill://deep-mode/`, audit and fix drift, probe lanes by side effects only, replace stuck lanes, post a status message only for tracked changes not yet reported (PR opened, code-ready head, round launched/closed, verdict, merge, stuck agent + action, blocker added/cleared, operator-only decision), else no reply text; log a decision-trail row each tick.
     On hold/stand-down, order every owner to zero writes at once.
  - `Spawn owners`: one owner (`task`) per PR with full lifecycle; dependency graph as nested boxes; file boundaries per PR (exclusive globs); review-gated PR ids.
  - `PR mechanics, for every PR`: `gh` for all PR ops; open ready via **Opening a PR**; lint + typecheck once before the PR-facing push, hooks on; slop review before commit and **no-comments** before review; triage every automated/security review comment, plus the **pr-review** technique (`references/techniques/pr-review.md`): local mode before the first push, PR mode re-review (steps 6-7) after every push; rebase onto trunk before code-ready, keep that base in fix rounds, rebase again only at merge prep, on a `git merge-tree` conflict, trunk-caused CI failure, or a known concurrent change to the same files.
  - `Verdict and merge, for every PR`: one full swarm (the **swarm** technique, `references/techniques/swarm.md`) at the code-ready head: a gates lane, the ten live lanes, the perf lane, 2+ audit lanes with distinct focus that distrust the PR body; another full swarm only for new behavior, redesign, or large new diff; rebase/conflict/minor fix → single verifier at new head; wording-only → none. Root audits receipts before the verdict. Clean = no blocking finding. A trunk failure in the regression lane is recorded against trunk and does not block. New head → fresh verdict unless the patch-id is unchanged. Merge/handoff rule from the execution playbook.
  - `Boot recipe, for every live lane`: `git fetch origin <head-branch> && git checkout <head SHA>` in the lane's own worktree; start backend + surface, wait for ready; input only through the project `verify-<app>` skill (else omp `eval` `browser` or bash), naming read-only diagnostics; save screenshots to `<tmp>/swarm-<pr-id>/worker-<n>/<slug>.png` and return paths.
- One `## <Task as verb phrase> (<PR id>)` per PR, with bold sub-blocks in exactly this order: `**Depends on.**` (PR id or None) · `**Files.**` (Edit/Create/Delete `<path>` boxes) · `**Build.**` (one change, symbol + file) · `**You see.**` (exact log line or screen state) · `**Verify, unit.**` (test file + case, `Run <command>`) · `**Verify, live.**` · `**Verify, perf.**` · `**Review gate.**` · `**Merge.**`.
  - The three Verify blocks open with the verification rule verbatim.
  - Verify, live continues "Ten lanes on `<model>` at the PR head, per the boot recipe." Boxes `Lane 1.`…`Lane 10.`, each with a scenario, ``Save `<slug>.png`.``, and `Pass when <predicate>.` Lane 1 is the "Regression lane against trunk": same load-bearing scenario at trunk and head; if trunk lacks the feature, record that and gate the diff-added behavior plus the end state the user waits for; never invent a trunk result.
  - Verify, perf boxes in order: `Metric.` (measured at trunk and head) · `Probe.` (command, run interleaved at trunk and head, both producing the metric) · `Baseline.` (trunk value first) · `Rule.` (head vs trunk, with the failing number; unlike scenarios → absolute budgets for diff-added work and user-visible end state, no ratio).
  - Review gate: interaction-changing PR → boxes to copy lane screenshots to `<media>/<pr-id>-review-<slug>.png`, record a 30–60 s video `<media>/<pr-id>-review.mp4`, post both to the operator in chat, stop at merge-ready. Otherwise exactly `**Review gate.** None. <PR id> is not review-gated.` with no boxes.
  - Merge boxes: root's clean verdict at the exact head SHA; review-comment triage done; a pr-review round on the merge head with no P0/P1 open and every P2 fixed or dismissed with a reason; rebased on trunk after the verdict with patch-id unchanged; who merges.
- `## Close the program`: every box checked with evidence; reply with the report the execution playbook names, with each PR's review line from the pr-review technique.
- Then only appendices: `## Appendix A. Prototype evidence` (questions answered with branch/SHA/artifacts; what stays unproven), `B. Alternatives rejected`, `C. Risks` (per PR, what the owner watches; any surface with no verification skill), `D. Links and reading list` (docs to read, which PRs get **how** and contested-design review, the **show-me-your-work** trail).

## Gates

Plan checklist (replaces pstack's `check-plan.mjs`); every item must pass, outside code fences:
- No long dashes (– —), no curly quotes, no mid-sentence `: ` in prose (code spans and links excepted).
- H1 present; intro under 10 non-blank lines; How to read this contains the four markers above, a `playbooks/` path, and the rule.
- Program checklist has the five `###` in order and contains `skill://deep-mode/`, the recurring tick, and "status message".
- Program checklist `PR mechanics, for every PR` contains `pr-review` and the technique path `references/techniques/pr-review.md`.
- At least one PR section between Program checklist and Close the program; Close the program exists.
- Each PR section: all nine sub-blocks in exact order; Depends on non-empty; Files, Build, You see, Verify unit, Merge each have ≥1 box; three Verify blocks open with the rule; live names the lane model and has exactly Lanes 1–10, every box a lane with a ``Save `…` `` screenshot and "Pass when"; perf boxes exactly Metric, Probe, Baseline, Rule; Review gate either "None." with no boxes, or boxes mentioning screenshot, video, operator.
- Every `##` after Close the program is an Appendix; Appendix A Prototype evidence exists.
- Execution starts only on the user's explicit go, under the playbook the plan names.
- A surface with no verification skill is a risk in Appendix C; its live block still names how each lane drives it.

## Evidence

- Plan path; PR ids with dependencies and the review-gated set.
- What prototypes proved and what stays unproven.
- Plan checklist results: per PR section, box counts per sub-block; total PR sections; the pr-review PR-mechanics item; every failure fixed (0 remaining).
