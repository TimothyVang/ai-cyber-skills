# Wayfinder

Use when: an effort is too big for one session and the route is foggy ("wayfinder", "chart the way to X", "figure out how we'd migrate to Y", "plan this before anyone builds it"). You find the way; you don't charge at the destination. A multi-phase build whose design is already settled is the Multi-phase plan playbook; a multi-day build program is Orchestrate.

The **map** is one issue labeled `wayfinder:map`. Its **tickets** are child issues, each one question whose answer is a decision, sized to one agent session. The map is an index: a decision lives in its ticket, and the map links to it by the ticket's title, never a bare number. Asking for a map grants creating and editing its issues and labels.

Where it lives: the repo's GitHub issues (`gh`). Children attach with the sub-issues API (`gh api repos/<owner>/<repo>/issues/<map>/sub_issues -F sub_issue_id=<child issue id>`); blocking is a `Blocked by: #<n>` line in the ticket body. No GitHub remote → local markdown under `plan/wayfinder/<slug>/` (`map.md` plus one file per ticket).

Map body sections: **Destination** (one or two lines: the spec, decision, or change the map is finding its way to), **Notes** (domain, skills every session should read, standing preferences), **Decisions so far** (one line per closed ticket: linked title and a one-line gist), **Not yet specified** (in-scope fog too vague to ticket), **Out of scope** (ruled out, with why).

Ticket types, one `wayfinder:<type>` label each. All are worked by agents by default:
- `research`: a `scout` subagent finds a fact the decision waits on.
- `prototype`: build the cheap concrete artifact and decide by observing it (`references/playbooks/prototype.md`).
- `grilling`: the **grill** technique (`references/techniques/grill.md`); you answer its questions.
- `task`: work that must happen before a decision can be made (provision access, move data to see its shape). Do it yourself; only steps that need the user's identity (an account, a payment, a secret) become a precise checklist for them.

## Steps

**Chart the map** (the user brings a loose idea):
1. Name the destination with the **grill** technique. It fixes the scope.
2. Grill again breadth-first across the whole space to find the open decisions. No fog (the whole route fits one session) → no map: say so and run the matching playbook instead.
3. Create the map issue, then every ticket you can state precisely now. Wire `Blocked by` lines in a second pass, once every ticket has a number. A question you can't yet phrase sharply goes in **Not yet specified**, not a ticket.
4. Start every `research` ticket in parallel, one fresh `scout` each.

**Work the map** (repeat until done):
1. Load the map body, not every ticket. The **frontier** is the open, unblocked, unclaimed tickets.
2. Claim a frontier ticket by assigning it to the dev driving the map, before any work, so parallel sessions skip it.
3. Resolve it as its label says, in a fresh subagent: one non-research ticket per agent, so each context stays small. Independent frontier tickets may run in parallel.
4. Record it: post the answer as a comment, close the ticket, and add its line to **Decisions so far**.
5. Graduate fog the answer made specific into new tickets; delete it from **Not yet specified**. A ticket now past the destination is closed and moved to **Out of scope** with why. Update or close tickets the decision invalidated.

## Gates

- Produce decisions, not deliverables, unless the map's **Notes** say to carry execution into the map.
- Every decision traces to a closed ticket; nothing on the map is decided twice or only in chat.
- A ticket answer that rests on a judgment call gets a decision-trail row per **show-me-your-work** (`references/techniques/show-me-your-work.md`).

## Evidence

- The map's link, its Destination, and whether the route is clear: frontier empty and **Not yet specified** empty.
- Decisions made this session, each with its ticket and how to reverse it.
- The handoff: when the route is clear, the next step is the Multi-phase plan playbook, or issues labeled for the Factory playbook (`references/playbooks/factory.md`).
