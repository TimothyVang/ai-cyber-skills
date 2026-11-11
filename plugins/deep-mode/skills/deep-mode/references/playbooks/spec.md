# Spec

Use when: the conversation has settled what to build and it should be written down before anyone builds it ("write the spec", "turn this into a spec", "spec it up", "make this an issue an agent can build"), or the Wayfinder playbook's route is clear and its destination is a feature. Synthesis, not interview: everything needed is already in the conversation, the code, and the decisions made so far. An open question → the **grill** technique (`references/techniques/grill.md`) first, then come back.

The spec is the contract a build is judged against: the **pr-review** technique's spec findings and the panel's Done when both read it. It lives in two places: the file `docs/specs/<slug>.md` and one tracker issue labeled `spec` that carries it.

## Steps

1. **Gather.** Collect the decisions from the conversation and its show-me-your-work trail. Read `GLOSSARY.md` and the ADRs in the area (`docs/adr/`) so the spec uses the project's words and does not contradict a recorded decision. Unknown code → `scout` tasks for entry points, the modules involved, and existing tests near them.
2. **Pick the test seams.** A seam is the boundary a test drives (an HTTP route, a CLI command, a public function, the UI). Prefer the highest seam that already exists; add a new one only when no existing seam can observe the behavior, and as high as possible. Fewer seams is better; one is ideal. Record the choice as a trail row.
3. **Write `docs/specs/<slug>.md`** with the template below, with the **technical-writing** technique (`references/techniques/technical-writing.md`), then **unslop** (`references/techniques/unslop.md`).
4. **Check it.** Every user story maps to at least one Done when item; every Done when item can be checked by a command, a test at a named seam, or an observation on the real surface; no file paths or line numbers (they rot), except a short snippet a prototype produced that states a decision better than prose.
5. **Commit** the file on branch `spec/<slug>` off the default branch. Push it when the repo has a remote; with no remote, the local branch is enough. That branch becomes the Implement spec playbook's integration branch, so the spec lands with its code. When the user wants the spec on trunk before any build, open a docs PR for it through Opening a PR (`references/playbooks/opening-a-pr.md`) instead (no remote: merge it into the default branch locally after a panel pass).
   - Local tracker → check out the branch this step commits on (`spec/<slug>` or the docs PR's branch) and run step 6 there first. Then make this one commit hold both the spec file and its issue file, staging only those two paths (`git add -- <spec file> <issue file>`). The issue then lands wherever the spec lands, before any docs PR opens or merges.
6. **Publish** per the **tracker** technique (`references/techniques/tracker.md`): one issue, title `Spec: <name>`, labels `spec`, the category role, and `triage:agent-ready`. Body: a link to the file on its branch (no remote: its path and branch name), then the file's full text.
   - Local tracker → this runs before step 5's commit, in the checkout of that commit's branch, so the next free issue number is counted on that branch.
7. **Next.** Hand off to the Tickets playbook (`references/playbooks/tickets.md`) unless the spec fits one PR, in which case the spec issue is itself the ticket.

## Spec template

```markdown
# <Name>

## Problem
<Who hits it, what they try to do, and what goes wrong today. Their view, not the code's.>

## Outcome
<What is true for them when this ships.>

## User stories
1. As a <role>, I can <action>, so that <benefit>.
<As many as it takes to cover every role, path, error, and empty state. A missing story is a missing feature.>

## Decisions
- <Module, interface, data shape, contract, or behavior decided, and why. Link the ADR when there is one.>

## Test seams
- <Seam>: <what it observes>. Nearby tests to copy: <test name or folder>.

## Done when
- [ ] <Observable result, with the command, test, or surface that shows it.>

## Out of scope
- <What this does not do, so the build doesn't grow into it.>

## Notes
- <Prototype evidence, research files, open risks.>
```

## Gates

- No interview. Facts are looked up; judgment calls are decided and logged (SKILL.md Autonomy).
- The spec never contradicts an accepted ADR. A spec that needs to → write the superseding ADR first (domain-model technique, `references/techniques/domain-model.md`).
- Done when items are behavior on a real surface, never "tests pass".

## Evidence

- The spec file path and branch, and the spec issue link.
- The chosen test seams and why.
- Decisions made while writing, each with how to reverse it.
