# coworkers

**Use when:** two or more agents work at the same time: owners, workers, and verifiers under Board, Autopilot, Orchestrate, Wayfinder, or any fan-out. They work like colleagues on one team: they talk to each other directly, honestly, and only when it moves the work.

## The roster

Every brief carries the roster: each coworker's agent id, role, and the files or tickets it owns. The root also keeps the roster in the program's tracker file, so a replacement agent can find its team.

## How to reach a coworker

- omp: `write agent://<id>` sends a message and wakes an idle agent. `agent://all` broadcasts; use it only for something every coworker must act on (trunk is red, a shared contract changed).
- Claude Code: `SendMessage` to the agent's name.

## When to message

- You need a fact a coworker owns → ask that owner, not the root.
- You are about to change something a coworker's work depends on (a shared type, API, schema, or a file outside your ownership) → tell the owner first and agree on the change.
- You found a bug in a coworker's area → send it with a command that reproduces it.
- A coworker blocks you → say exactly what would unblock you.
- You finished something a coworker waits on → hand it off with the SHA, path, or PR.

## How to talk

- One message: what you need, the evidence pointer (SHA, `file:line`, command, artifact), and the answer you expect.
- Answer when asked. "I don't know" plus who might is a full answer.
- Be honest and skeptical. Disagree with evidence; never agree to be agreeable. A claim without a pointer gets "show me".
- Status belongs in the tracker, not in messages. No check-in pings, no thanks-only replies.
- Change only your own files. To change a coworker's, ask the owner.

## Escalate to the root only when

- two coworkers still disagree after each has shown its evidence once;
- ownership of a file or task is unclear;
- the work reaches a hard stop (SKILL.md Autonomy).

## Exceptions

Panel verifiers (`references/techniques/panel.md`) don't message each other or the author before they vote. After the vote, a dissenting verifier sends its reproduction to the owner.

**Done when** every agreement two coworkers reached is either in the code or in one trail row written by the agent that acts on it.
