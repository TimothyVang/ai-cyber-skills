# boundary-discipline

Group: architecture. When: wiring validation, error handling, or framework adapters.
- **Rule.** Validate, narrow, and handle errors at system boundaries (CLI args, config, external APIs, network). Trust internal types. Business logic in pure functions; the shell is thin and mechanical.
- **Across the boundary.** Expose domain concepts, not the boundary's private representation; general mechanism inside, special-purpose policy at the edge. Don't re-export transport, storage, framework, or wire types.
- **Applications.** Validate config at parse time; parse raw data into domain types at the boundary; no redundant nil checks deep in call chains. Pure parse functions (bytes → typed state), prompt construction (state → string), scoring (state → results).
- **Tests.** "Is this data crossing a system boundary right now?" If not, validation is redundant. "Can this be a pure function the shell calls?" If yes, extract it.
- **Anti-patterns.** Scattered re-validation (noisy, false sense of safety); logic tangled in framework wiring.
