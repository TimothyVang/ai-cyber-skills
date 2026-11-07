# Prototype

Use when: a design or empirical decision (layout, interaction, density, behavior, timing, approach) should be settled with a cheap throwaway. You own the decision, not the code; the real build follows Feature.

This playbook inverts the laziness protocol's "smallest change" and the verification bar: speed over polish, code quality doesn't matter, no planning. Rigor goes into picking the right design cheaply — propose variations the user didn't ask for; throw an approach away and try another.

## Steps
1. Scope the decision the prototype exists to make.
2. Open design space → gather references: search prior art, summarize a moodboard (themes, palettes, layouts), let the user pick directions (`ask`). Skip when the direction is set.
3. Build throwaway in an isolated scratch dir outside production source:
   - Visual: vanilla HTML/CSS/JS or the lightest stack that renders it, CDN deps, hot-reload dev server.
   - Behavioral/timing: the smallest script that exercises the question.
4. Comparing alternatives → put variants behind one labeled switcher (buttons or keypress) (`references/principles/exhaust-the-design-space.md`).
5. Verify on the matching surface: visual → screenshot each variant via the repo's `verify-<app>` skill (`.omp/skills/verify-<app>/`); if none, omp `eval` `browser` or bash and drive the interaction; behavioral → log the timing, print output, or watch the render. Observation is the test.
6. Present alternatives, tradeoffs, recommendation. Hand the chosen direction to Feature (or the **architect** technique (`references/techniques/architect.md`) for the shape).

## Gates
- No decision to make → no prototype; route to Feature.
- No production framework, no tests, no abstractions, nothing merged into production source.
- Output is the decision plus throwaway artifact, never shippable code.

## Evidence
- Variants explored; evidence (screenshots for visual, observed output/timing for behavioral); tradeoffs; recommendation; scratch path.
- State plainly the prototype is throwaway.
