# Review quality and safe context

A contributor receives a code review informed by bounded committed source, without giving the reviewer tools or executing the contributor's code.

## Sub-features

- Git-object context includes supported direct local imports and records omissions.
- Unsafe paths, non-regular objects and oversized blobs are excluded from added context.
- Context admission is capped at 12 files, 128 KiB per file and 256 KiB total; the evaluator uses the same production defaults.
- Known-bug and clean-control reviews record invalid runs, duplicate findings and false positives.

## How to get to it (user POV)

A contributor opens a PR. The owner-installed bot builds a source packet and gives it to the sealed reviewer. Offline reproduction uses `evals/review/run.py` rather than posting real reviews.

## Driving it with control-deep-mode

Preconditions: doctor passes, the review corpus is prepared and an explicit subscription model is available.

Run `python .omp/skills/verify-deep-mode/control.py run --id review-help review --help`, then the prepare/run/adjudicate/score sequence in `evals/review/README.md`. Preserve raw responses and inspect each finding against its pinned case. Compare diff-only and enriched modes under identical settings.
Run the GitHub App's `test_review_context.py` boundary cases as regression evidence in addition to the live model review. They must read committed blobs despite dirty worktree files and must never execute the injected source.

## Gotchas

Import resolution is bounded and incomplete; secret-looking paths are excluded, but path filters cannot prove ordinary source contains no secret. Existing diff handling has its own exposure boundary. Historical labeled fixes may be in model training. No vendor superiority claim follows without actual matched vendor runs and adjudication.
