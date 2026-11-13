# Local delivery results, 2026-11-12

The revised local workflow finished the feature task without publication gates or a mandatory verification framework. It did not beat plain-agent usage on this fixture. This is a development experiment, not a product leaderboard.

## Method

The real `omp` 18.19.0 CLI ran the organic `kitty` feature task in fresh repositories, five repetitions per arm per experiment. Every candidate requested and recorded `openai-codex/gpt-6-astra`, with the same prompt, tool permissions, contained temporary directories, a reported-usage cap of 4, and a 20-minute deadline. No API-key billing or fallback model was enabled. Arms were randomly assigned opaque letters before judging.

The task adds exact and percentage expense splits plus read-only settlement suggestions. The collector exercised the actual Node CLI, ran the candidate's tests, checked changed tests against old code, and applied 19 held-out assertions. These assertions cover this fixture, not arbitrary software delivery.

“Reported usage” is the harness's dollar-valued usage estimate. It is not a subscription invoice or evidence of API spending. Concurrent runs shared one Windows host; elapsed times are diagnostic, not a speedup claim. Repetitions are small and the fixture was already known during development.

## First experiment

The comparison used the pre-change instructions at `37717c2cec9b4cc8c3750f0b34728506824b5698`, the first local-delivery fix at `052a4c5dcde7caa96c7120d55f57291aa7ba9a77`, and no workflow instructions.

| Arm | Finished processes | Artifacts passing all 19 checks | Median reported usage | Median tool calls | Median elapsed seconds |
|---|---:|---:|---:|---:|---:|
| Pre-change | 0/5 | 5/5 | $4.1426 | 82 | 323 |
| First local-delivery fix | 5/5 | 5/5 | $2.1051 | 49 | 358 |
| Plain agent | 5/5 | 5/5 | $0.9609 | 26 | 196 |

All five pre-change processes stopped at the reported-usage cap. Their code still passed the artifact checks. Separating completion from artifact correctness prevents calling an interrupted workflow complete. In-flight work can overshoot the cap before the next model request is refused.

The first fix still created unnecessary verification helpers because the `/deep` command retained a conflicting instruction. The second change corrected that entrypoint rather than exempting this fixture.

## Second experiment

The revised command at `4a3d4a382e002ac10352e872ab036b74805edc12` was compared against the first fix and a fresh plain-agent arm. All completed work remained on the starting branch, uncommitted, with no stranded branches or additional worktrees.

| Arm | Finished processes | Artifacts passing all 19 checks | Median reported usage | Median tool calls | Median elapsed seconds |
|---|---:|---:|---:|---:|---:|
| First local-delivery fix | 5/5 | 5/5 | $1.7438 | 44 | 326 |
| Revised command | 5/5 | 5/5 | $1.6271 | 34 | 242 |
| Plain agent | 5/5 | 5/5 | $0.9754 | 27 | 180 |

The revised command avoided the unnecessary framework in all five observed runs. The median decreased in this experiment, but the usage ranges overlap and the same first-fix arm varied between experiments. This does not establish a statistically reliable general efficiency advantage. Plain agents remained cheaper here, and all arms reached the hidden-check ceiling.

## Blind review and evaluation corrections

Two judges, `openai-codex/gpt-6.1-terra:high` and `openai-codex/gpt-6-luna:high`, reviewed opaque candidate packs and exercised copied artifacts. They are different models in the same provider family, not independent vendor evaluations.

The first experiment's secondary scores are not used. Its pack omitted candidate-authored verification helpers along with the supplied skill snapshot, making some candidate test suites incomplete. The collector now retains newly authored helpers while excluding supplied instructions. The corrected second experiment's judges agreed on all six rubric scores for all 15 candidates. Each scored the revised and plain arms 11/12; four first-fix candidates scored 10/12 for unnecessary project instructions. Agreement does not prove judge accuracy.

The lexical outside-path detector also produced false positives. Manual review found search-pattern strings such as `/tmp/`, a Markdown link written into a file, and `$TMP` explicitly bound under the evaluation folder. Raw flags remain retained; they were not silently cleared. No actual outside-path access was established by those flags. The detector is not an OS sandbox.

## Separate bug-fix check

A single paired `billsplit` run compared the first local-delivery fix with a plain agent. Both finished and passed all nine hidden checks. The workflow arm's reported usage was $0.6500 and the plain arm's was $0.5103. This is a smoke-sized second task, not five repetitions or evidence of superiority.

## Reproduce and inspect

Use the [outcome runner](../outcome/README.md) with explicit model IDs, fresh run IDs and the commit references above. The original local receipts are `.scratch/kitty-delivery-runs/`, `.scratch/kitty-delivery-v2-runs/` and `.scratch/billsplit-current-runs/`. They contain prompts, raw events, model metadata, termination notices, measurements, artifacts and blind reviews. Derived summaries are in `summary.json`; the raw flags and events remain unchanged.

[The machine-readable result table](local-delivery-2026-11-12.json) records individual measurements and evidence digests. Original raw receipts are local development artifacts, not a public independently audited benchmark. A matched hosted-review comparison was not run. Broader held-out coding tasks and repeated independent runs are still required before stronger claims.
