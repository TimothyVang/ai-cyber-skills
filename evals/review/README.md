# Review-quality evaluator

The evaluator runs sealed, read-only reviews through `omp -p` and scores independently adjudicated findings. It is standard-library Python around the existing `omp` CLI. It makes no GitHub writes, downloads no source itself, and executes no corpus code. Prompts and raw outputs live under `.scratch/review-runs/`.

## Prepare, run, adjudicate, score

From the repository root in a POSIX-compatible shell:

```bash
python evals/review/run.py prepare
STAMP=$(date +%Y%m%d-%H%M%S)
RUN=.scratch/review-runs/$STAMP/run.json
ADJ=.scratch/review-runs/$STAMP/adjudication.json
python evals/review/run.py run --model openai-codex/gpt-6-astra --mode diff-only --split calibration --out "$RUN"
python evals/review/run.py adjudicate "$RUN" --out "$ADJ"
# Independently inspect source evidence for each finding. Set adjudication to true_positive only for a verified,
# unique expected bug; set maps_to to that bug ID. Set unsupported and duplicate findings to false_positive.
# Add a short evidence-based rationale to every adjudicated finding, save the worksheet, then:
python evals/review/run.py score "$RUN" "$ADJ"
```

`diff-only` is the neutral baseline: it applies the production sealed reviewer prompt to the source patch without repository context. `enriched` uses the same prompt and patch plus that case's pinned bounded source packet.

The run artifact points to raw model output and every failed case.
The run manifest exists before any case starts and is atomically checkpointed before and after each case.
Completed results survive interruption. A started case without a completion checkpoint remains `interrupted`;
unstarted selected cases remain `pending`. Raw process output streams directly to case-local files.
Scoring retains all selected cases, including interrupted and pending cases, in its conservative denominator.
Use a fresh output path for another attempt; never overwrite the incomplete record.
Malformed finding field types, including array or object severities, fail the individual case without aborting the batch.

`--mode enriched` uses a separately pinned git-object packet for each case, never one unrelated context for the whole corpus:

```bash
python evals/review/run.py run --model openai-codex/gpt-6-astra --mode enriched --split calibration --context-repos-dir .scratch/review-context --out .scratch/review-runs/enriched.json
```

Before that optional command, prepare local Git object repositories under `.scratch/review-context/{pytest,requests,django}` with the exact commit IDs pinned in each case's `context`. Bug packets read the pre-fix commit; paired clean packets read the fix commit. The evaluator never checks out or executes those files.

Case IDs must be portable alphanumeric/hyphen/underscore directory slugs, unique ignoring case. Traversal, absolute paths and reserved Windows device names are rejected before a model launches.

Context packets use the production builder's defaults, up to 12 whole UTF-8 blobs, each at most 128 KiB and 256 KiB total. The report records included paths, packet digests, pinned commits and omissions. A packet with no source blobs fails the case instead of being presented as enriched. Partial packets remain explicitly bounded; omitted files and unresolved imports mean source coverage is incomplete.

Each case has its own working directory and runs sequentially. `--max-cost` bounds each case (default 0.25); `--timeout` bounds seconds (default 180); `--only ID` selects one case. The evaluator reuses `pr_agent_local`'s OAuth-only credential check and scrubbed environment.
It disables model fallback and tool/MCP discovery through the no-discovery overlay, and supplies `--no-tools --no-rules --no-context-files --no-skills --no-extensions --no-lsp`. Output tripwires reject tool execution and file mentions. Missing `omp`, unavailable OAuth identity, nonzero exit, timeout, unsafe tool/file event, malformed JSON, or requested/observed model mismatch fails that case without fallback.
Reports retain CLI executable/version/SHA-256, exact settings, corpus/prompt/context digests, requested and observed model, token/cost usage when emitted, raw stdout/stderr, and elapsed time.

The evaluator calls production `bot.review_prompt` with a minimal sealed conversation and no author reply/comments.
It uses production `pr_agent_local.SYSTEM` and the `flatten` user-message envelope, including `@` defanging.
The system prompt digest is bound to the CLI metadata. Expected bug IDs never enter model prompts.

## Adjudication and scoring

The worksheet copies every run case and every complete model finding, with a finding digest. Only `maps_to`, `adjudication`, and rationale are editable. Scoring refuses a changed run/corpus digest, missing/duplicate/reordered cases, changed status/error/expected labels, changed/reordered/added findings, pending decisions, incompatible model, CLI binary/version, mode or settings. Each expected bug can earn at most one true positive per case; duplicate mappings count as false positives. A worksheet cannot improve a score by dropping a hard case or editing its result.
If a finding establishes a real bug missing from the labels, mark the case invalid in the publication report, revise the corpus under a new identity and rerun both arms. Do not call a confirmed unlabelled bug a false positive merely to improve the comparison.

Precision, expected-bug recall, clean-case false-positive rate, missed bugs and errors are reported. Bug recall denominator includes every attempted expected bug; failed or invalid bug runs count as misses. Clean-case false-positive rate uses only valid clean reviews; failed clean runs are reported separately and never count as clean successes. Valid-only bug recall and failure counts are also reported. Zero-denominator metrics are null. A finding near a labeled line or a model self-score is not evidence of correctness.

## Corpus provenance and limitations

The default corpus is `cases-v2.json`. Pytest and Requests are calibration/development data;
Django is held out from review-prompt tuning. This is not independence from model training.
The original `cases.json` remains an immutable record of the first labeling attempt.

Calibration exposed three missing bug labels in that attempt. Two nominal clean controls contained
additional regressions. The corrected corpus has seven bug labels across six bug inputs and two controls.
Its revision metadata records the source evidence. Both review arms are rerun after relabeling.
Historical case IDs ending in `clean` do not override their corrected `kind` and expected labels.

Each input is the exact Git diff of a named source file at a pinned repair, with eight context lines.
Reverse patches introduce the original regression; forward patches can fix one bug while introducing another.
These are constructed reviews, not original bug-introducing PRs. Repair comments can make the task easier.
Expected labels never enter prompts. The evaluator does not execute corpus source.

| Project / source license | Verified behavior and pinned upstream evidence |
| --- | --- |
| pytest / MIT | Indirect parametrization colliding with fixture parameters. Regression commit [`d56b1af`](https://github.com/pytest-dev/pytest/commit/d56b1af5252ceb8578d6751a6b2006e79defbb08); repair [`3a85b5e`](https://github.com/pytest-dev/pytest/commit/3a85b5ead0753e50b7689c489235237acfa7b94e), including a regression test. [MIT license](https://github.com/pytest-dev/pytest/blob/3a85b5ead0753e50b7689c489235237acfa7b94e/LICENSE), copyright Holger Krekel and others. |
| Requests / Apache-2.0 | Known-empty request body incorrectly falling back to chunked framing. [Issue #6122](https://github.com/psf/requests/issues/6122), repair [`818d927`](https://github.com/psf/requests/commit/818d92764bd7035a0450d7b4e52ec9fc6d07abb6), with a regression test. [Apache license and notices](https://github.com/psf/requests/blob/818d92764bd7035a0450d7b4e52ec9fc6d07abb6/LICENSE). |
| Requests / Apache-2.0 | `StringIO.tell()` character count used as UTF-8 byte length. [Issue #6917](https://github.com/psf/requests/issues/6917), repair [`0406663`](https://github.com/psf/requests/commit/0406663e1b802bb839aca40e9f6ea89d0c9255ef), with multibyte and partial-read regression tests. [Apache license and notices](https://github.com/psf/requests/blob/0406663e1b802bb839aca40e9f6ea89d0c9255ef/LICENSE). |
| Django / BSD-3-Clause | Missing MySQL/MariaDB `#` column-alias rejection enabled SQL injection. Security fix [`41b43c7`](https://github.com/django/django/commit/41b43c74bda19753c757036673ea9db74acf494a), CVE-2025-59681. [Django license](https://github.com/django/django/blob/41b43c74bda19753c757036673ea9db74acf494a/LICENSE), copyright Django Software Foundation and individual contributors. |

The complete upstream license texts ship in [licenses/](licenses/); root [NOTICE.md](../../NOTICE.md) records the patch attribution. Preserve them when redistributing the corpus.

This small, historically public corpus may overlap model training and is not an unseen benchmark. The held-out set is one Django bug/control pair, so its estimates are high-variance. No superiority claim or vendor comparison is justified without actual imported, matched results. Enriched runs require the pinned local repositories; diff-only runs do not.
