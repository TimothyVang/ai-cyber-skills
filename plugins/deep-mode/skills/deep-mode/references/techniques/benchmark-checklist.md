# benchmark-checklist

**Use when:** you produce a perf number (PR before/after, regression claim, hillclimb harness, library/config choice). Answer each question with evidence from a run, not a guess. Quick ballpark the user asked for: one run, still check Q4 and Q7, say it's one run. A choice between options is never a ballpark.

Before running: write the claim you expect to ship ("export is 30% faster at p50 on the 60k-row dataset"); read the measurement script (what it times, counts, ignores); check load and cores (`uptime`, `nproc`, or OS equivalent). Busy machine you can't quiet → interleave sides and say so.

1. **Why not double?** Name the limiter from a profile in an unreported run (`top`/`pidstat`, `node --cpu-prof`, `py-spy`, `perf`, I/O wait, `strace -c`), mapped to source. Watch the load generator. If a change didn't move the number, the limiter explains why.
2. **Was it tuned?** Both sides as production runs them: release builds, prod flags/env, batching, pools, cache warmth, same versions and data. A setting-shaped limiter (commit per row, debug build, missing index) = untuned: tune and remeasure, or pick no winner. Narrowing the claim to "as shipped" doesn't fix this for adoption choices.
3. **Did it break limits?** Arithmetic vs disk/network bandwidth and cores; time saved vs time the changed piece took (removing 10% caps speedup ≈11%). Past a limit = measured a cache, no-op, or bug.
4. **Did it error?** Count failures and non-success; check outputs are correct, not just present. Add an error count if missing.
5. **Does it reproduce?** ≥5 runs per side, alternating A,B,A,B. Report median and range. Gap < spread = no measurable difference; close calls → rank-sum test or harness stats.
6. **Does it matter?** Measure the end-to-end path a user waits on with realistic sizes/concurrency; report the micro result as a share of the whole.
7. **Did it even happen?** Confirm the work ran inside the timed region (request reached server, rows written, result used). Lazy code and timeouts produce numbers for work that never happened.

**Output:** verdict first (faster / slower / no measurable difference / inconclusive); number with unit, run count, range, limiter ("p50 41 ms → 33 ms, median of 7 runs per side, range 32 to 35 ms after, bound by JSON parsing on one core"). Inconclusive when the limiter is unnamed, a side was untuned, or Q4/Q7 unchecked; name the gap. PR body gets one primary number; runs and evidence in a linked artifact.
