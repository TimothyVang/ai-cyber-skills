# writing-for-agents

**Use when:** writing or editing anything an agent reads as instructions: a skill (`SKILL.md` and its references), `AGENTS.md`, `CLAUDE.md`, a rule file, a subagent brief, or a doc an instruction file points to. Read it before step 3 of the Authoring a skill playbook (`references/playbooks/authoring-a-skill.md`). The audit laws for agent systems are in `references/domain-rules/agent-engineering.md`.

The goal is not identical output every run. It is the same process every run: the agent reaches the right material at the right moment and knows when each step is finished.

## Pointers decide what gets read

A **pointer** is a line that stays in the agent's context and names material that does not: a skill's `description`, a routing row, an `AGENTS.md` line like "API conventions: `docs/api.md`". The pointer's wording, not the target's quality, decides whether the agent opens the target. If the agent skips a file it needed, rewrite the pointer before you inline the file.

- Put the trigger word first: the word the user or the task will actually contain.
- One trigger per distinct case. Synonyms for one case are one trigger; keep the one people use.
- Say what the target is and when to open it. Nothing else; the target describes itself.

## Two budgets

- **Context cost:** everything always loaded (instruction files, skill descriptions, routing tables) is paid on every turn, used or not. Keep always-loaded text to pointers and rules that apply to nearly every task.
- **Human memory cost:** a command or skill only a person can invoke costs nothing in context, but someone has to remember it exists. Spend it where human judgment should choose; a router that names the others turns many things to remember into one.

## Where each piece goes

A document holds **steps** (ordered actions) and **reference** (facts, rules, definitions read on demand). Rank each piece by how soon the agent needs it:

1. Steps in the main file.
2. Reference in the main file, when every path through the steps needs it.
3. Reference in a separate file behind a pointer, when only some paths need it.

Moving material down this ladder keeps the main file readable; that is the reason to do it, more than saving tokens. Too little moved down and steps drown in reference; too much and the agent misses what it needed. Keep a concept's definition, rules, and exceptions together under one heading. A file that is long even though every line is live should be split by path (what only some cases need) or by sequence.

## Steps end on a check

Each step ends with how the agent knows it is done. A vague end ("once you understand the code") invites the agent to rush to the next step. Make the end checkable ("every caller listed with its file") and demanding ("every rule applied to every changed file", not "review the changes"); demand is what makes the agent dig. If a fuzzy step still gets rushed, move the later steps behind a real context boundary (a separate file a subagent receives, or a handoff); a later section in the same file stays visible and does not help.

## Words that carry weight

- Reuse a word the model already knows well that names the whole behavior: "tracer bullet", "red", "tight loop", "frontier". Repeated as a term, it steers more cheaply than a sentence that describes the behavior. Coin a new word only with a definition, and only when no existing one fits.
- State the behavior you want, not the one you forbid. "Write one-line comments" works; "don't write long comments" puts long comments in the agent's mind. Keep a prohibition only for a hard guardrail, and pair it with the positive rule.
- Use the codebase's own names: real files, commands, flags, and `GLOSSARY.md` terms.

## Pruning

- **One home per rule.** A rule written in two places drifts and looks more important than it is. Point to the home instead.
- **Don't restate the environment.** `package.json` scripts, config files, `--help`, and the directory tree are already the truth. Write down only what the agent cannot find by looking: the unwritten convention, the reason behind a choice, the trap no config reveals.
- **Delete no-ops.** A sentence that tells the agent to do what it already does by default changes nothing and costs every turn. Test a doubtful sentence by running with and without it, not by debate. Delete whole sentences, not words. A word too weak to change behavior ("be thorough") needs a stronger word, not more sentences.
- **Delete stale lines** the moment behavior changes. Adding feels safe and removing feels risky, so instruction files accumulate dead layers unless someone cuts them.
- A rule that a lint, type, test, or hook could enforce goes there instead (the **correct** technique, `references/techniques/correct.md`).

## Skills specifically

- **Invocation.** A skill with a model-facing `description` can be picked by the agent and by other skills; the description is a pointer that is always loaded, so write it as one (trigger branches first). A skill marked `disable-model-invocation: true` loads only when a person invokes it; its description is a one-line human summary. Choose the model-facing form only when the agent or another skill must reach it alone.
- **Shared reference.** Material two user-invoked skills both need goes in a plain file both point to, since neither can call the other.
- **Splitting.** Split off a separate skill when it has its own trigger word that people use, or another skill must reach it, and that reach is worth one more always-loaded description.
- **Routing.** Route on the words of the request. A file existing in the repo is evidence, never a trigger, or unrelated work in that repo gets captured.

**Output:** the edited document, with each change justified by one of the rules above, and the pointer lines that lead to it.

**Done when** every step in the edited document ends on a check, every pointer leads with its trigger word, and every no-op and stale line is gone.
