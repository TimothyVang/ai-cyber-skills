# figure-it-out

**Use when:** no narrower playbook fits: large migrations, ambitious multi-part changes, work reviewed after the human steps away. The first deliverable is the workflow itself.

1. Read the principles in `references/principles/`. If you have `todo`, open one item per phase; otherwise list the phases in your report: Frame, Design, Loop, Trail, Verify.
   Done when the five phases exist as `todo` items or as a list in your report.
2. **Frame.** Ground, then state: done as a falsifiable predicate (prove-it-works); quantified scope (units, effort, blockers grounding found).
   Rigor level biased high (one-way doors and high blast radius get more; rigor is gates and artifacts, not "try harder").
   Present framing and tradeoffs; reversible work proceeds, but a multi-hour run earns one checkpoint.
   Done when the predicate, scope numbers, and rigor level are written down.
3. **Design.** Atomic, independently landable units; riskiest unknown first; scaffold and verification before features. Build the verification harness first with a baseline from the pre-change state ("old vs new").
   One-way-door design → **architect**; skip for mechanical work, and never a second arena over a settled design. Fan out only across seams, each worker owning its files.
   Write the phase list down; it's what the human reviews. Add its steps between Loop and Trail (as `todo` items if you have `todo`, else in the reported phase list).
   Done when the unit list is written and the harness reports a baseline on the pre-change state.
4. **Loop.** Each unit is an experiment: hypothesis, smallest change, measure the real artifact against the predicate, keep if advanced, revert if not; verify each before the next (sequence-verifiable-units).
   Inspect artifacts, never self-reports; passing too easily → suspect the observation. Pair delegated work with a judge; a worker gaming the gate → reset and harden the contract; a wrong gate → fix it in its own change.
   Verdicts: VERIFIED, NOT VERIFIED, INCONCLUSIVE (not a pass). Never hide a negative.
   Done when every unit has a verdict and every unit not kept is reverted.
5. **Trail.** Log via **show-me-your-work**, a row as each step lands. Done when each landed unit has a trail row.
6. **Verify.** Check the whole against the predicate on the real product, not just the harness. Encode recurring corrections as gates, lints, checks, or scripts.
   Done when the predicate check on the real product has a recorded result and each recurring correction has a gate or a stated reason it has none.

**Done when** the predicate holds on the real product, or the report names each unmet part with its evidence.

**Output:** the playbook designed, rigor level and why, trail path, what's verified against the predicate, what's open.
