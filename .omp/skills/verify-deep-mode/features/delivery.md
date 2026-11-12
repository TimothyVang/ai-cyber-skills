# Local delivery

A developer requests a feature in a local project and receives working changes in the starting tree, not a stranded worktree or an unfinished review.

## Sub-features

- Local medium edits avoid remote publishing while retaining behavior verification and diff review.
- Published changes still require exact-head review and merge gates.
- Separate run IDs preserve previous evidence; explicit models prevent silently changing the comparison.
- Blind packs exclude supplied instructions but retain candidate-authored helpers needed to exercise delivered code.
- Attempt reuse is refused for model runs and judges; raw failed or interrupted attempts remain evidence.

## How to get to it (user POV)

Install the plugin and invoke `/deep` in a local project, or reproduce a controlled task with `evals/outcome/run.py`.

## Driving it with control-deep-mode

Preconditions: doctor passes; the selected model has a subscription login; the candidate and comparison commits exist.

Run `python .omp/skills/verify-deep-mode/control.py run --id delivery-prepare outcome setup --task kitty --run-id delivery --ref <candidate-commit> --compare-ref <previous-commit> --per-variant 5`.
Run the printed workspaces with `control.py run --id delivery-agents outcome run --task kitty --run-id delivery --model <authorized-model> --max-cost 4 --max-time 20m`, then `control.py run --id delivery-results outcome collect --task kitty --run-id delivery` using the full helper path above.
Inspect every completed tree, final reply, hidden-check result, exit and contamination hit. A successful result passes the requested behavior and leaves it in the starting tree. Compare revisions and plain agent only under the same settings. The judge command requires two explicit `--judge-model` options.

## Gotchas

The corpus is small and known during development. Concurrent host/provider load prevents a reliable speed claim from one batch. `process_finished` does not itself mean the feature is correct. Publishing gates need their own PR-head evidence; local task success does not prove them.
