# Review quality and safe context

A contributor receives a code review informed by bounded committed source, without giving the reviewer tools or executing the contributor's code.

## Sub-features

- Git-object context includes supported direct local imports and records omissions.
- Unsafe paths, non-regular objects and oversized blobs are excluded from added context.
- Context admission is capped at 12 files, 128 KiB per file and 256 KiB total; the evaluator uses the same production defaults.
- Model calls use production `pr_agent_local.SYSTEM` and the `flatten` user-message envelope; run metadata records `system_prompt_sha256`.
- Known-bug and clean-control reviews record invalid runs, duplicate findings and false positives.
- Loading an old default trigger retires the unrelated-account mention without rewriting stored configuration or changing explicit custom triggers.
- Review manifests checkpoint completed, interrupted and pending cases instead of dropping an interrupted batch.
- Malformed finding field types fail one response rather than terminating the remaining batch.

## How to get to it (user POV)

A contributor opens a PR. The owner-installed bot builds a source packet and gives it to the sealed reviewer. Offline reproduction uses `evals/review/run.py` rather than posting real reviews.

## Driving it with control-deepmodebot

Preconditions: doctor passes, the review corpus is prepared and an explicit subscription model is available.

Run `python .omp/skills/verify-deepmodebot/control.py run --id review-help review --help`, then the prepare/run/adjudicate/score sequence in `evals/review/README.md`. Preserve raw responses and inspect each finding against its pinned case. Compare diff-only and enriched modes under identical settings.
Inspect `prompt.txt` for the flattened user-message envelope and the run's CLI metadata for the system-prompt hash. Preserve pre-repair attempts separately; their transport is not equivalent.
Run the GitHub App's `test_review_context.py` boundary cases as regression evidence in addition to the live model review. They must read committed blobs despite dirty worktree files and must never execute the injected source.
For mention migration, run the actual `load_bot_config` path against a disposable root-local config.
Verify the effective trigger changes, one warning is emitted, and stored bytes remain identical.
The observed integration receipt is `.scratch/evidence/mention-migration-smoke.json`; never use production config for this probe.
For interrupted-review proof, retain a completed real response, interrupt before the next case, and inspect
the manifest's completed/interrupted/pending states. Keep this fault-injection run separate from accuracy results.

## Gotchas

Import resolution is bounded and incomplete; secret-looking paths are excluded, but path filters cannot prove ordinary source contains no secret. Existing diff handling has its own exposure boundary. Historical labeled fixes may be in model training. No vendor superiority claim follows without actual matched vendor runs and adjudication.
