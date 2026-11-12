# arena

**Use when:** one attempt at a non-trivial artifact would lock in the wrong shape.

1. **Phases.** If you have `todo`, open one item per phase; otherwise list the phases in your report: Frame, Fan out, Cross-judge, Pick, Graft, Verify. Done when the six phases exist as `todo` items or a report list.
2. **Frame.** State the artifact. Derive a 3 to 6 criterion gradeable rubric (picker-only; candidates see only the task). Pick N runners, ≥2, mixing model families when available.
   Give each its own output location inside the project root (a git worktree under `.worktrees/` or its own folder under `.scratch/`, per SKILL.md "Contain the work"). Never shared files, never a temp dir outside the repo.
   Done when the rubric is written and each runner has its own existing output location.
3. **Fan out** in one `task` batch: task, grounding path, own output path; produce the artifact plus a short rationale naming alternatives considered and rejected. A dropout → proceed with N-1, note it.
   Done when every runner has returned an artifact and rationale, or is recorded as a dropout.
4. **Cross-judge.** One read-only judge from a different model family than yours, when one is available; skip and say so otherwise. Never your own family. Done when the judge's verdict is in hand, or the skip is recorded.
5. **Pick a base.** Read every candidate end to end. Score per rubric criterion, not holistic feel; compare with the judge. Disagreement → bias or ambiguous rubric; read both rationales. Pick what a future maintainer extends most easily without breaking invariants; ties → cleaner boundary or smaller API.
   Done when every candidate has a score per criterion and one base is named.
6. **Graft.** Walk each loser once for 1 or 2 portable strengths; fold in by hand so one mental model holds (redesign-from-first-principles). Convergence = strong agreement, ship it. Wild divergence = under-specified frame: reframe and re-run, never average.
   Done when each loser is either grafted from (with its source named) or recorded as having nothing portable.
7. **Verify** per prove-it-works. A miss means the frame was wrong (re-run) or a graft was skipped (back to 6).

**Output:** one artifact plus a synthesis note: base and why, judge verdict or skip, each graft with source, rejections and why, convergence/dropouts, verification result.

**Done when** the merged artifact passes its verification run and the synthesis note covers every output item above.
