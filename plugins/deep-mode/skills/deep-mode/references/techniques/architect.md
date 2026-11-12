# architect

**Use when:** "architect/design this", or non-trivial work where jumping to code would lock in the wrong shape.

1. **Phases.** If you have `todo`, open one item per phase; otherwise list the phases in your report: Ground, Sketch, Agree, Implement, Scrap. Done when the five phases exist as `todo` items or a report list.
2. **Ground.** Run **how** over every subsystem the code touches (naming a file isn't grounding). If ownership or layering changes, run **why** on the existing shape so rationale is a constraint. Skip only for true greenfield.
   Done when every touched subsystem has a how output, or the work is recorded as greenfield.
3. **Sketch.** Run **arena** with the design task and grounding. Candidates produce types, signatures, class shapes, module boundaries with `not implemented` bodies and pseudocode, caller usage written first. Require ≥2 structurally distinct whole-shape candidates even when the first looks fine (exhaust-the-design-space).
   Done when at least two structurally distinct candidates exist, each with caller usage.
4. Screen every candidate against the red flags below. Assume the next contributor is an agent that sees only files it opened, copies the nearest example, takes the shortest path that compiles; prefer the design where a change that looks right from one file is right repo-wide. Compare viable ones on interface depth: more complexity hidden behind a smaller public surface.
   Done when each candidate has a pass or hit recorded for every red flag.
5. **Agree** (opt-in). Default: proceed with no checkpoint. If asked ("with checkpoint", "show me first"), present and `ask` for sign-off. The sketch may land as its own scaffold step. Pushback on the shape = new grounding evidence: re-ground and re-sketch before more code. Adversarial review (**interrogate**) only for a contested design.
   Done when the sketch is signed off, or no checkpoint was asked for.
6. **Implement** against the sketch; it's the contract. Surface deviations: was the sketch wrong, the requirement missed, or the implementation overreaching?
   Done when the code matches the sketch or every deviation is listed with its cause.
7. **Scrap** on a *pattern* of friction: same workaround shape across unrelated code; many unrelated special-case branches; types needing escape hatches (`any`, casts, always-set optionals); a "we need a lock" reflex where state was meant unshared; callers needing the abstraction's internals; ≥2 independent same-shape deviations.
   Then re-run how on what's built, redesign as if constraints were day-one, make the new sketch smaller first, return to step 3. Complexity in the data isn't complexity in the design.
   Done when no friction pattern is present, or a smaller new sketch has replaced the old one.

**Red flags:** shallow module (big interface, little hidden; callers coordinate several methods for one operation; options expose internal stages) · information leakage (one internal decision known by several modules; re-exported wire/transport types) · temporal decomposition (load/validate/transform/save modules repeating one representation) · pass-through method · split ownership (several writers or copies of one state) · two ways to do one task · importable internals · hand-synced lists (derive from one, or fail the build on disagreement).

**Output:** caller usage sketch → type sketch (one file for small changes; module map + types for larger), plus a rationale: usage sketch, candidates considered, red-flag screen, synthesis decision.

**Done when** the implemented code matches the agreed sketch, or every deviation is listed with its cause, and the rationale names every candidate considered.
