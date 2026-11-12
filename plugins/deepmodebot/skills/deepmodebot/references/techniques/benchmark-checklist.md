# benchmark-checklist

**Use when:** you produce a perf number (PR before/after, regression claim, hillclimb harness, library/config choice). Answer each question with evidence from a run, not a guess. Quick ballpark the user asked for: one run, still check Q4 and Q7, say it's one run. A choice between options is never a ballpark.

Before running: write the claim you expect to ship ("export is 30% faster at p50 on the 60k-row dataset"); read the measurement script (what it times, counts, ignores); check load and cores (`uptime`, `nproc`, or OS equivalent). Busy machine you can't quiet → interleave sides and say so.

Authorized network load tests first declare the owned target/environment, allowed read/write operations, test-data namespace, load shape, duration, stop conditions, and cleanup.
Bound generator cost and downstream spend, verify account eligibility, and obtain any authorization required by deepmodebot's Autonomy hard stops before provisioning or sending traffic.
Watch side effects as well as throughput: unexpected writes, storage growth, errors, or spend stop the run; clean up only the test data and resources it created.
Done when the workload and limits are recorded before execution, observed effects stay within them, and cleanup has evidence; proposed load is not measured capacity.

1. **Why not double?** Name the limiter from a profile in an unreported run (`top`/`pidstat`, `node --cpu-prof`, `py-spy`, `perf`, I/O wait, `strace -c`), mapped to source. Watch the load generator. If a change didn't move the number, the limiter explains why.
   Done when the limiter is named with a profile artifact and a source location.
2. **Was it tuned?** Both sides as production runs them: release builds, prod flags/env, batching, pools, cache warmth, same versions and data. A setting-shaped limiter (commit per row, debug build, missing index) = untuned: tune and remeasure, or pick no winner. Narrowing the claim to "as shipped" doesn't fix this for adoption choices.
   Done when both sides' settings are listed and match production.
3. **Did it break limits?** Arithmetic vs disk/network bandwidth and cores; time saved vs time the changed piece took (removing 10% caps speedup ≈11%). Past a limit = measured a cache, no-op, or bug.
   Done when the arithmetic is written and the result sits inside every limit.
4. **Did it error?** Count failures and non-success; check outputs are correct, not just present. Add an error count if missing. Done when the run prints an error count of zero and a correctness check passes.
5. **Does it reproduce?** ≥5 runs per side, alternating A,B,A,B. Report median and range. Gap < spread = no measurable difference; close calls → rank-sum test or harness stats.
   Done when each side has at least 5 alternated runs with median and range reported.
6. **Does it matter?** Measure the end-to-end path a user waits on with realistic sizes/concurrency; report the micro result as a share of the whole.
   Done when an end-to-end number exists and the micro result is stated as its share.
7. **Did it even happen?** Confirm the work ran inside the timed region (request reached server, rows written, result used). Lazy code and timeouts produce numbers for work that never happened.
   Done when a work-done count or output check from the timed run proves the work ran.

**Output:** verdict first (faster / slower / no measurable difference / inconclusive); number with unit, run count, range, limiter ("p50 41 ms → 33 ms, median of 7 runs per side, range 32 to 35 ms after, bound by JSON parsing on one core").
Inconclusive when the limiter is unnamed, a side was untuned, or Q4/Q7 unchecked; name the gap. PR body gets one primary number; runs and evidence in a linked artifact.

**Done when** all seven questions have run evidence and the verdict line is written, or the verdict is inconclusive with its gap named.

Load-test lesson: the [walkthrough's unintended article creation](https://www.youtube.com/watch?v=hOYzvUQKq8s&t=4556s) motivates the side-effect check; its dashboard traffic is not a capacity benchmark.
