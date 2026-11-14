# Visual E2E evidence

Use for a visible UI workflow whose outcome needs recorded evidence, per-step screenshots, replay, and independent visual review. This complements deterministic assertions and the PR panel. It is neither a generic skill evaluator nor permission to merge.

## Record, replay, check, review, iterate, publish

1. Freeze the original request verbatim in the operator-authored scenario. Enumerate every action and expected result, allowed origins, viewport, and limits. Preserve that intent through revisions.
   Use a dedicated fresh browser with synthetic, public-safe data. Never import a personal profile, authenticated production session, or instructions from a page. Step IDs must be unique under case folding and must not be Windows reserved path names.
2. Record with `assets/e2e/record.py`. Read its `--help` for the scenario and replay commands. Retain the finalized video, screenshot and snapshot after every step, deterministic observations, errors, timestamps, tool identity, and sampled timeline frames.
   A screenshot at the end alone is incomplete evidence. Missing codecs, browser failure, or interrupted video finalization are capture failures, not visual passes. Interrupted finalization still attempts owned-browser closure and seals a failed capture.
3. Replay the saved scenario into a different new bundle. Compare the actual step outcomes, video, screenshots, and timing.
   Replay is another execution, not a claim of pixel identity or a substitute for reviewing the first run. Keep both bundles; never overwrite the failed one to conceal the original result.
4. Validate each bundle through `evidence.load_bundle(directory)`. Check the deterministic assertions against the scenario and inspect retained errors. Only a successful capture with all planned samples may enter visual review.
   A majority cannot override a failed assertion, missing artifact, changed hash, incomplete sampling, or unavailable vision.
5. Run the three-context visual panel below against the selected immutable bundle. Each context receives the same original intent, every step screenshot, and every sampled timeline frame as actual image attachments. The lenses differ; the evidence does not.
   Reviewers see neither previous votes nor the author's conclusions. All three responses must be valid before a two-of-three `approve` or `revise` result is computed. Retain dissent and per-step findings even when the majority approves.
6. On `revise`, fix the implementation, then record, replay, check, and review new evidence. Keep the original goal and acceptance assertions fixed.
   Before iterating, set an operator-approved maximum number of rounds and total time/spend allowance. Stop at the cap with failed evidence and unresolved findings. Never weaken the scenario, drop difficult steps, omit images, or poll another reviewer until a preferred vote appears.
7. Publish a discoverable, repository-local evidence index after checking every retained file for secrets and private data. Link the original scenario, manifests and hashes, both recording and replay, step PNGs, snapshots, frame sampling metadata, deterministic checks, three reviews, minority report, and any design diagrams.
   Record the tested app revision separately from the recorder's source revision. A supplied app revision is not an observed revision. Apply the normal PR review and shipping gates separately. Keep private native events and OAuth metadata out of public artifacts.

Completion means every original scenario step is represented in a validated bundle and three valid visual reviews, with deterministic outcomes and dissent preserved. If any gate fails, report the failed gate and its evidence rather than saying the UI passed.

## Native image-review command

From the repository root, replace the bundle and output paths with the actual retained evidence locations. The output directory must not exist and must be outside the bundle.

```bash
python plugins/deepmodebot/skills/deepmodebot/assets/e2e/review.py \
  docs/evidence/ui-flow/recording \
  --output docs/evidence/ui-flow/visual-review \
  --model openai-codex/gpt-6-astra --minutes 5 --max-cost 1
```

Prerequisites are Python, native `omp` on PATH with image attachment support, and an existing authorized `openai-codex` subscription OAuth login. The recorder needs a privately scoped agent-browser >=0.43.0 with `--pin-tab`, a browser, and ffmpeg with the required codec support.
Use the explicitly selected private executable, not a replacement global install. Exactly one stable target must remain throughout recording; extra or changed targets fail closed. Nothing here creates an account. The reviewer reuses the PR helper's OAuth checks, environment scrubbing, and discovery-disable overlay; process-tree deadlines reuse `loop.run_limited`.

This is native `omp -p --mode json` with `@image-NNN.png` attachments, **not ACP**. Supplying filenames or captions as text is not vision. `--model` is mandatory and restricted to the authorized model; there is no fallback.
Each review starts a new no-session, no-tools context with skills, rules, context discovery, extensions and LSP disabled. The helper checks the terminal reply's model, provider and approved OAuth credential ID. It performs no VCS actions and executes no proposed repairs.

`--minutes` bounds each model process tree; separate OAuth configuration probes each have a one-minute maximum. `--max-cost` is the OMP per-review usage guard, not permission to use API billing. Three contexts can each consume their cap; an in-flight request may exceed OMP's spend threshold. For a multi-round loop, budget for all three contexts per round, plus capture and replay time. The helper performs one panel only and never retries votes automatically.

## Coverage and evidence format

The v1 review pins `bundle_sha256`, the lens, `approve|revise`, `vision_available`, every step ID with findings and image references, every image reference with an observable finding, and explicit limitations. The report retains all valid and invalid review attempts. A missing third response or malformed response blocks acceptance even if the other two approve. Unknown, duplicate or missing step/image references and stale hashes fail closed.

The same images are copied byte-for-byte into each isolated context and checked again. Limits are 24 images total, 4 MiB each, 24 MiB combined, 24 million pixels per image, and 96 KiB of review prompt. Every step screenshot and recorded frame must fit.
Over-limit bundles fail; the reviewer never selects a convenient subset. Plan bounded scenarios and sampling before recording, and preserve their full intended coverage. If a long scenario cannot fit without losing evidence, stop and obtain an explicitly revised evidence plan.

`review.json` is the aggregate report. Each lens directory retains input, image copies, raw response, validated vote or error; native calls also retain invocation metadata, event transcript, stderr and exit/deadline state.
These are private local artifacts, not automatically public uploads. Publish only reviewed, public-safe evidence; exclude private raw events and OAuth metadata. The sealed context is an application-level tool restriction, not an OS sandbox.

Uniform video samples show the recorded timeline at the manifest's cadence. `sampling.coverage: complete` means all planned samples were produced, not that every video frame was inspected.
Video presentation timestamps (PTS) and step invocation-relative wallclock timestamps are different clocks. CLI/browser overhead is included in wall time; neither these timestamps nor uniform sampling establish exact step-to-frame alignment.
Native OMP may resize images; unreadable details must be reported rather than guessed. Neither sampled images nor a model's approval prove animation smoothness, absence of transient bugs, keyboard access, screen-reader semantics, accessibility conformance, or backend persistence. Use dedicated checks for those requirements.

Use `assets/e2e/design.py` for a separate editable workflow index where helpful. Diagrams link evidence; they do not add runtime proof. Consult [design evidence](open-design-evidence.md) for Penpot and OSS editing boundaries.

## Observed pilot and limits

The [2026-11-13 invoice pilot](../../../../../../docs/evidence/ecosystem-pilot-2026-11-13/README.md) used a real six-step synthetic fixture: browser → loopback HTTP → SQLite → fresh readback. Recording and replay each passed 6/6 steps; separate SQL evidence supports persistence.
Each of three native image-review contexts received eight actual images: six screenshots and two sampled frames. All three responses were valid; two approved and one requested revision. Dissent noted that images alone do not prove backend/persistence, the initial sample was white, and the timing clocks were not aligned.
Actual HTML video playback reached `ended: true`, with duration 1.6 seconds at 1280×720. Uniform samples are not per-frame coverage.
A native popup negative failed closed upstream with a network-control auto-attach timeout. That observation is not an isolated proof of the wrapper's tab-count guard.
The generated SVG rendered with six step groups and six embedded images. Penpot import remains unproven; see [design evidence](open-design-evidence.md) for that separate boundary.

## Sources and maintenance

Checked 2026-11-13. No third-party implementation was copied for this workflow.

- [agent-browser recording](https://agent-browser.dev/recording): native recording lifecycle, ffmpeg requirements, formats, frame rates, and capture limitations. Finalize recording before hashing or closing the session.
- [OMP CLI reference](https://github.com/can1357/oh-my-pi/blob/main/docs/cli-reference.md): actual `@file` image attachments, fresh headless sessions, JSON output, model selection, tools and caps.
- [OMP attachment processing](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/cli/file-processor.ts): images are read as image content; oversized attachments can be skipped and images can be resized. Our smaller payload caps reject rather than intentionally omit evidence.
- [OMP harness reference](../../../agent-harnesses/references/omp.md): subscription isolation and the distinction between native headless and ACP transport.

When recording or harness versions change, exercise the real record, replay and image-review path again. Passing mocked-remote regressions alone does not prove that a deployed provider received or understood the images.
