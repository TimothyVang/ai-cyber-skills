# grill

**Use when:** a plan, design, or idea needs stress-testing before work starts ("grill me", "grill this plan", "stress-test it", "poke holes in this"), or a Wayfinder ticket labeled `wayfinder:grilling`. Adapted from Matt Pocock's grilling and grill-me skills (MIT, github.com/mattpocock/skills).

You run the interview, and by default you also answer it: the user prefers the agent decide. A grilling that ends in questions nobody answered has failed.

1. **Tree.** Map the plan as a design tree: every decision, and the decisions that hang off it. The **frontier** is every decision whose prerequisites are settled.
2. **Round.** Write the whole frontier as numbered questions, each with its real options.
3. **Resolve each question** by its kind, in this order:
   - A fact the environment holds (code, config, docs, an API's behavior) → a `scout` subagent looks it up. Only the questions downstream of it wait.
   - An observable fork (behavior, perf, layout, whether an eval separates) → the Prototype playbook (`references/playbooks/prototype.md`) settles it by running it.
   - A judgment call (product, design, preference) → decide it. Prefer the option that is reversible, smallest, and consistent with the codebase and the user's stated goal.

   Log each answer as one row in the decision trail per the **show-me-your-work** technique (`references/techniques/show-me-your-work.md`): the question, the choice, why, the evidence, and how to reverse it.
4. **Recompute.** Settled answers push the frontier outward. A question that depends on another question still open waits for a later round. Repeat until the frontier is empty: every branch visited, nothing silently assumed.
5. **Report and proceed.** Show the user the decisions as a short table (question, choice, why, how to reverse), then carry on with the work. Don't wait for confirmation; the user overrides any row by saying so.

**Live mode.** Only when the user asks to answer themselves ("interview me", "wait for my answers", "ask me live"): present each round with your recommended answer, worded so "yes" accepts it, and wait for their answers before the next round. Facts are still yours to look up; never ask the user for one.

**Done when** the frontier is empty and every decision has a trail row.
