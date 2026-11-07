# Eval

Use when: measuring whether a variant (skill, prompt, rule) changes agent behavior. You own the experiment design: plan, blind, run, synthesize.

## Steps

1. Frame: state the variant under test and what behavior counts as success. Write a 3–6 criterion rubric for the judge only; hold it back from candidates.
2. Set up one sanitized working dir per candidate with the variant installed under its `.omp/skills/`. Plant the context an organic task would have (project skeleton, skills the candidate would naturally read). Never run candidates as `task` children: they inherit this session's skills, rules, and cwd.
3. Author one organic prompt: what a user would type, goal not meta.
4. Run N candidates in parallel (the **arena** technique's step 3, Fan out, `references/techniques/arena.md`), each as an isolated `omp -p "<prompt>"` process via background `bash` with `cwd` set to that candidate's sanitized dir, same prompt, different models where available (`--model`). Capture each process's output and session file.
5. Spawn one blinded judge via `task` on a different model family than the candidates, when one is available (arena step 4, Cross-judge). Judge gets outputs by sanitized label plus the rubric.
6. Verify chain-following from transcripts, not self-report: read each candidate's session transcript (the `omp -p` session file for its sanitized dir), note which files it actually opened, and grade from those reads plus code shape. Never read transcripts outside this experiment's candidates.
7. Read every candidate output end to end yourself. Compare with the judge's verdict; disagreement means model bias or an ambiguous rubric. Synthesize.

## Gates

Blinding non-negotiables; any breach invalidates the run:
- No `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, or `arena` in any directory, file, or prompt a candidate sees.
- Prompt reads as an organic user request.
- No chain-eliciting cues: never ask candidates to list skills, principles, or files applied; ask for design notes generally.
- Directory and slug names are project-shaped, as a user would pick.
- Candidates are not told other candidates exist.
- The judge may know it is judging but sees outputs by sanitized label only, never model name.
- Two variants: one judge scores both sets in a single pass on one scale, blind to set origin.

## Evidence

- Variant under test and the rubric.
- Per-candidate notes, including files actually read (from transcripts).
- The judge's verdict.
- Your synthesis, including any judge disagreement.
- Recommendation: promote the variant or not.
