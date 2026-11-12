# Tickets

Use when: a spec, plan, or settled conversation is bigger than one PR and should become buildable pieces ("break this into tickets", "split the spec into issues", "make tickets for this"). Input: a spec issue or `docs/specs/<slug>.md` (Spec playbook, `references/playbooks/spec.md`), a plan file, or the conversation. Output: one tracker issue per ticket, each with the tickets that block it, so any agent can take the next unblocked one.

A ticket is a **tracer bullet**: a thin path through every layer the feature touches (data, logic, interface, test) that works end to end on its own. Splitting by layer ("all the schema", then "all the API") is wrong: nothing works until the last layer lands, and no ticket can be verified alone.

## Steps

1. **Read the source** in full: the spec body and its comments, or the plan. Read `GLOSSARY.md` and the ADRs in the area so ticket titles use the project's words.
   Done when you have read the whole body and every comment, and noted the glossary terms the tickets will use.
2. **Scout the code** where the spec lands (`scout` tasks): entry points, the modules involved, and tests near them. Look for a **prefactor**: a behavior-preserving change that makes the feature small. Each prefactor is its own ticket and blocks the slices it helps.
   Done when every entry point and nearby test is listed, and each prefactor found is a drafted ticket.
3. **Draft the slices.**
   - The first slice is the thinnest path that shows the feature working at all. Later slices widen it: more cases, more roles, error paths, polish.
   - Each slice fits one agent session and has Done when items a verifier can run on its own.
   - **Blocked by** lists only tickets that truly gate this one. A slice that only touches the same files is a merge order, not a dependency.
   - A **wide mechanical change** (rename a column, retype a shared symbol) that breaks every caller at once can't be a tracer bullet. Split it in three phases. *Expand*: add the new form beside the old. *Migrate*: move callers in batches sized so each stays green (per package or folder), each batch blocked by Expand. *Contract*: delete the old form, blocked by every batch.
   Done when every slice has a title, at least one Done when item, and a Blocked by list.
4. **Check the cut.** For each ticket: does it change behavior someone can observe, or is it a prefactor or migrate batch that keeps everything green? Is any ticket two features (split it) or half of one (merge it)? Any cycle in Blocked by? Fix, then show the user the list as a table (number, title, blocked by, what it delivers) and carry on; the user overrides by saying so (SKILL.md Autonomy).
5. **Publish** per the **tracker** technique (`references/techniques/tracker.md`), blockers first so every Blocked by line can name a real issue. Each ticket: labels `ticket`, its category role, and `triage:agent-ready`; a Parent link to the spec issue when there is one; Blocked by links. Use the body below. Never edit or close the spec issue.
   Done when every ticket is an issue with its labels and Blocked by links, and the spec issue is unchanged.
6. **Next.** One integration branch, one final PR → Phased build (`references/playbooks/phased-build.md`). One merged PR per ticket on trunk → Work a queue (`references/playbooks/work-a-queue.md`) from board tasks. Labeled issues for an installed factory → Work a queue with the `factory` CLI.
   Done when the chosen playbook has started, named in your report.

## Ticket body

```markdown
Parent: #<spec issue>

## Builds
<The behavior this ticket makes work, from the user's side, end to end. Not a list of files.>

## Done when
- [ ] <Check a verifier can run: command, test at a named seam, or observation on the real surface.>

## Blocked by
- #<n> <title>, or "nothing"
```

No file paths or line numbers in a ticket. A short prototype snippet that pins a decision (a state machine, a type, a schema) may stay, marked as from the prototype.

## Gates

- Every ticket is a tracer bullet, a prefactor, or an Expand, Migrate, or Contract step. No layer-only tickets.
- Every ticket has at least one Done when item a verifier can run.
- The Blocked by graph has no cycles, and at least one ticket has no blockers.

## Evidence

- The ticket table with links, blockers, and the first unblocked frontier.
- Prefactors found, and any wide change split into Expand, Migrate, Contract.
- Decisions about granularity, each with how to reverse it.
