# explain-the-number

Group: verification. When: before you measure, and before you trust, report, or act on a measured number (speedup, regression, throughput, latency, eval result).
- **Write the decision before you run.** Name the result that would change a decision and the noise floor. Stop when run-to-run spread exceeds the effect.
- **Ask "why not double?"** Name the bounding resource or path (core, lock, disk, network, the load generator) from a profile or system counters taken during a run, mapped to source. A guess from reading code is not a limiter.
- **List what else it could measure and rule each out with evidence:** errors, skipped or cached work, code that never ran, an untuned side, noise, a piece too small to matter end to end.
- **Keep evidence with the number:** run count, spread, limiter in notes or a linked artifact.
- Perf numbers → full **benchmark-checklist** technique. Eval results → did every run do the task, does the gap hold across trials and models, does the scenario matter.
- **You skipped this when** a run started without the decision-changing result written, evidence lacks run count/spread/limiter, or claimed time saved exceeds the time the changed piece took. Distinct from prove-it-works (which checks an output is real).
