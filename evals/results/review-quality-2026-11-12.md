# Review-quality experiment, 2026-11-12

Bounded source context found one more labeled calibration defect in this run. Both modes found the single held-out defect. This is not evidence of superiority over a hosted reviewer.

## Measured results

Sixteen calls completed with explicit `openai-codex/gpt-6-astra`, omp 18.19.0, a per-case usage cap of 1 and a 300-second timeout. Each arm reviewed the same eight source patches once. Production reviewer wording, system instruction, message envelope and source-context builder were reused. Tools, repository instruction discovery and model fallback were disabled.

| Split | Mode | Expected defects found | Adjudicated false findings | Clean controls with a finding | Failed calls |
| --- | --- | --- | --- | --- | --- |
| Calibration | Diff only | 5/6 | 0 | 0/1 | 0 |
| Calibration | Bounded source context | 6/6 | 0 | 0/1 | 0 |
| Held out from prompt tuning | Diff only | 1/1 | 0 | 0/1 | 0 |
| Held out from prompt tuning | Bounded source context | 1/1 | 0 | 0/1 | 0 |

The additional calibration finding concerns UTF-8 sizing of `StringIO` while the supported older transport uses Latin-1. Context includes the version-dependent string policy that the short diff omits. One observation is not a reliable estimate of improvement; no confidence or general accuracy claim follows from these counts.

[Machine-readable findings, adjudication and scores](review-quality-2026-11-12.json) retain the complete model findings and source-based rationales. Scoring binds each worksheet to its exact run, corpus, requested/observed model, CLI binary/version, system instruction, settings and original finding hashes. Severity calibration was not evaluated.

## Corrections retained in the record

- `quality-v1` completed but omitted the production system instruction and user-message envelope. Findings were not inspected before excluding it and repairing the transport.
- `quality-v2` used the correct transport. Calibration exposed three missing labels. A repair was not necessarily a clean control: it could fix one defect while introducing another. Confirmed additional findings were not counted as false positives.
- The original `cases.json` is retained. The corrected default `cases-v2.json` has seven expected defects in six bug inputs and two controls. Source patches and reviewer prompts are unchanged. Django's held-out labels are unchanged.
- `quality-v3` was rejected before any model call because corpus admission incorrectly equated forward repair direction with a clean classification. Admission now validates immutable forward/reverse source pairs independently of bug classification.
- `quality-v4`, shown above, reran both arms against the corrected labels. Calibration is explicitly development data informed by earlier findings, not unseen evaluation data.

## Source adjudication

Exact reviewed functions from pinned Requests commits were extracted with Python's AST and exercised with explicit standard-library globals. They reproduced conflicting framing headers, unknown-length bodies receiving a zero length, and the version-dependent `StringIO` discrepancy. No package setup or arbitrary repository initialization ran.

For the legacy encoding finding, [urllib3 1.26.20's connection implementation](https://raw.githubusercontent.com/urllib3/urllib3/1.26.20/src/urllib3/connection.py) delegates non-chunked requests to the inherited standard-library implementation. Executing that readable-body encoder on `StringIO("é")` yielded one byte, `e9`, without opening a connection. This supports the source-level discrepancy, not a complete Requests network exchange.

The original pytest, Requests and Django labels are tied to the [pinned repair sources and licenses](../review/README.md). Findings were adjudicated by this session's assistant against source evidence, not an independent human panel or a competing vendor. No target server, full pytest/Django application, or end-to-end SQL exploit was run.

## Source-context boundary

The old 16 KiB per-file cap excluded all four representative changed modules. The revised default admits whole UTF-8 blobs up to 128 KiB each and 256 KiB total, at most 12 files. All four modules were admitted in the observed probe. Included paths, immutable object IDs, digests and omissions are recorded; this is not full-repository coverage.

Packets read Git objects, not the mutable checkout. Hidden/configuration paths, secret-shaped names, symlinks, gitlinks and binary blobs are excluded.
External diffs, text conversion, filesystem monitors, replacement objects and lazy fetch are disabled.
Those controls do not prove arbitrary source is free of secrets or make model output trusted. Prompts still reach the configured provider.

## Reproduction and limits

Use [the evaluator CLI](../review/README.md) with the pinned repositories and default corrected corpus. Local receipts remain in `.scratch/review-runs/quality-v4-*`, with wrapper output under `.scratch/evidence/quality-v4-*`. Source probes are `.scratch/evidence/review-label-probes.json` and `review-legacy-transport-observation.json`; context admission is `context-admission.json`. Raw local receipts are not a publicly archived independent benchmark.

The corpus uses historically public repairs, including repair comments that can reveal intent. Training overlap is possible. The holdout is one Django bug/control pair. One model family, one run per case, two clean controls and development-driven label corrections cannot establish broad accuracy, statistical superiority, complete feature parity or a replacement for any named product. No matched hosted-reviewer results were obtained.

## Post-review execution integrity

Publication review found that interrupted batches could lose their denominator because the report was written only at the end.
The runner now creates the manifest first, checkpoints before and after each case, and streams raw output to files.
A controlled in-process interruption after one real subscription-model response retained `valid`, `interrupted` and `pending`
cases plus the completed raw response. Receipt: `.scratch/evidence/review-interruption-smoke.json`.

Two additional held-out calls completed through the checkpointed transport in `quality-v5-holdout-enriched.json`.
Both had valid responses, with the expected alias finding on the reverse patch and none on the forward patch.
These integrity smoke runs are not pooled into the paired accuracy table. Fifteen evaluator regression tests passed. The actual CLI also rejected traversal, absolute-path, reserved-device and case-colliding corpus IDs before launch; controlled malformed-severity inputs produced handled validation errors. These are boundary probes, not additional agent accuracy runs.
