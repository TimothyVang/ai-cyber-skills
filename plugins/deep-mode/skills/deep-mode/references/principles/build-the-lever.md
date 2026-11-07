# build-the-lever

Group: core. When: any non-trivial work — edits, migrations, analyses, checks — not just bulk work.
- **Rule.** Build the tool that does or proves the work (codemod, script, generator, dump-to-sqlite query, rerunnable check, or a skill subagents follow). A deterministic script turns "trust me" into "run this". Skip only for a couple of obvious edits visible at a glance. The bar is triviality, not repetition.
- **Steps.** Do the first unit by hand to learn the recipe; build the tool; prove it by rerunning on that unit and diffing against the hand version; make it safe to rerun.
- A deterministic lever beats fan-out: if one pass covers every unit, run it yourself. When you do fan out, write the lever as a skill (recipe, verification contract, do-not-touch fences) outside the delegates' write scope.
- **Check.** Applying this produces a file. Cited it but no codemod/script/generator/delegate skill in the diff → not applied. Commit the lever when the work outlives the session. Smallest script, never a framework.
- **Anti-patterns.** Hand edits only re-verifiable by redoing them; delegates hand-applying what a script could do.
