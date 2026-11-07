# arena

**Use when:** one attempt at a non-trivial artifact would lock in the wrong shape.

1. **Phases.** If you have `todo`, open one item per phase; otherwise list the phases in your report: Frame, Fan out, Cross-judge, Pick, Graft, Verify.
2. **Frame.** State the artifact. Derive a 3–6 criterion gradeable rubric (picker-only; candidates see only the task). Pick N runners, ≥2, mixing model families when available. Give each its own output location (git worktree or a dedicated temp dir) — never shared files.
3. **Fan out** in one `task` batch: task, grounding path, own output path; produce the artifact plus a short rationale naming alternatives considered and rejected. A dropout → proceed with N-1, note it.
4. **Cross-judge.** One read-only judge from a different model family than yours, when one is available; skip and say so otherwise. Never your own family.
5. **Pick a base.** Read every candidate end to end. Score per rubric criterion, not holistic feel; compare with the judge. Disagreement → bias or ambiguous rubric; read both rationales. Pick what a future maintainer extends most easily without breaking invariants; ties → cleaner boundary or smaller API.
6. **Graft.** Walk each loser once for 1–2 portable strengths; fold in by hand so one mental model holds (redesign-from-first-principles). Convergence = strong agreement, ship it. Wild divergence = under-specified frame: reframe and re-run, never average.
7. **Verify** per prove-it-works. A miss means the frame was wrong (re-run) or a graft was skipped (back to 6).

**Output:** one artifact plus a synthesis note: base and why, judge verdict or skip, each graft with source, rejections and why, convergence/dropouts, verification result.
