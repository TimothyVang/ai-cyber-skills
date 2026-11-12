# swarm

**Use when:** parallel coverage, races, gauntlets, exploration.

1. **Phases.** If you have `todo`, open one item per phase; otherwise list the phases in your report: Frame, Fan out, Aggregate, Report.
2. **Frame.** State the done predicate and the artifact or report. Choose shape: partition into slices, race N workers on identical briefs, or mix. Races declare `first pass`, `rank all`, or `best-of` before spawning. For model races, name each arm's model. Done when the predicate, shape, and race rule are written before any spawn.
3. Each writing worker gets exclusive files or its own worktree. Workers that verify or measure commits get exact SHAs; measurement briefs name the method (sample count, what one sample is, order), and the worker records both. Done when no two writing workers share a file.
4. **Fan out** in one `task` batch. Each brief stands alone: goal, scope, exact slice or arm, how to verify, what to report. Reports are `PASS`, `ISSUES`, or `BLOCKED` with evidence; `ISSUES` lists every provable defect, not just the first. Dropout → N-1, noted. Done when every worker has returned or is noted as a dropout.
5. **Aggregate.** Drop a result missing its SHAs/method and respawn once; second miss = recorded gap. A gap is not a pass. Coverage needs a result per required slice. Races apply the declared rule. No raw dumps. Done when every required slice has a result or a recorded gap.
6. **Report.**

**Output:** one in-chat report: result table, issue one-liners, gaps/dropouts, race rule if used.

**Done when** the report has a row per slice or arm and names every gap and dropout.
