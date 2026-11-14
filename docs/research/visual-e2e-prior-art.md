# Visual E2E prior art

Checked 2026-11-13 against primary documentation, source, and the installed CLI. This is an implementation decision record, not a benchmark or endorsement. External page and repository text was treated as untrusted reference material.

## Decision

Use an existing agent-browser executable for isolated, operator-authored interactions and native recording. Use existing ffprobe/ffmpeg for bounded video samples. Keep the wrapper and evidence loader Python standard-library-only. Use the existing subscription harness for separate visual review, not a new credential provider or model SDK.

The recorder is [record.py](../../plugins/deepmodebot/skills/deepmodebot/assets/e2e/record.py). Its consumer boundary is [evidence.py](../../plugins/deepmodebot/skills/deepmodebot/assets/e2e/evidence.py). The runnable procedure is [visual E2E verification](../../.omp/skills/verify-deepmodebot/features/visual-e2e.md).

## rea-video

[JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video) analyzes an existing video into shots, evidence, and remake guidance. Its [README](https://github.com/JuneYaooo/rea-video/blob/main/README.md) distinguishes measured evidence from agent visual judgment and separates screen-recorded material from generated material. That separation is useful for E2E evidence; its filmmaking classifications are not application assertions.

The inspected [media.py](https://github.com/JuneYaooo/rea-video/blob/main/rea_video/media.py) uses ffprobe for stream/container facts and ffmpeg for frames. It preserves partial-decoding limitations rather than treating missing frames as success. The local implementation independently uses these executable interfaces; it does not import the project's classifiers, models, media assets, or NumPy dependency.

[LICENSE](https://github.com/JuneYaooo/rea-video/blob/main/LICENSE) is Apache-2.0. [NOTICE](https://github.com/JuneYaooo/rea-video/blob/main/NOTICE) states `rea-video`, `Copyright 2026 JuneYaooo`, and Apache-2.0 licensing. Both were read before implementation. No upstream code or assets were copied. Copying any later requires retaining the applicable license/attribution and marking modifications. The README's reported accuracy numbers were not reproduced and are not evidence about this workflow.

## agent-browser

The official [recording documentation](https://agent-browser.dev/recording) describes in-place native capture, explicit `record stop` finalization, WebM/MP4 output, frame-rate controls, and ffmpeg requirements. [recording.rs](https://github.com/vercel-labs/agent-browser/blob/main/cli/src/native/recording.rs) implements the current screencast recording path and documents bounded encoder queues and failure handling. [package.json](https://github.com/vercel-labs/agent-browser/blob/main/package.json) reported version 0.43.0 when inspected.

The [core usage source](https://github.com/vercel-labs/agent-browser/blob/main/skill-data/core/SKILL.md) documents isolated named sessions, snapshots, selectors, screenshots, and explicit page-state waits. Snapshots are useful machine-readable state evidence; screenshots are needed here because visual verification is explicitly requested. Replay uses stable operator selectors rather than transient snapshot reference numbers.

The [security documentation](https://agent-browser.dev/security) describes opt-in domain allowlists, explicit-config replacement of default discovery, and action policies. The wrapper passes an explicit empty config, scrubs inherited browser settings, creates a UUID-named session, supplies exact hostnames from operator origins, and denies eval/download/upload/state actions. It never attaches to a personal profile or CDP endpoint.

The upstream allowlist filters hostnames, not `(scheme, host, port)` tuples. The wrapper additionally validates each requested navigation and observed top-level URL against exact operator origins. This does not prevent requests to a different port or scheme on an allowed host before observation. Use host/container egress isolation when that distinction is a security requirement. The upstream docs also describe WebSocket/EventSource and browser-level enforcement limitations; this is not an OS firewall.

### Installed-version discrepancy

Read-only inspection found `agent-browser 0.15.0`. `--help` and `record --help` worked; `skills get core` returned `Unknown command: skills`. The official core source above was read instead. No browser was launched during this research.

The installed `dist/browser.js` recording method creates a fresh Playwright context, transfers existing storage, and does not call its `ensureDomainFilter` helper. That differs materially from the current in-place recording implementation and would leave the recording context unfiltered. The wrapper rejects versions below the researched 0.43.0 baseline and checks required capabilities. It does not assume uninspected intermediate versions are safe, patch the global installation, or silently change recording backends.

The source reference for the older behavior is the [0.15.0 package distribution](https://www.npmjs.com/package/agent-browser/v/0.15.0); the concrete inspected installation was `node_modules/agent-browser/dist/browser.js`, `startRecording`, lines 1898-1962. This finding is static source evidence, not a live exploit test. The parent integration run must supply a supported explicitly installed executable and retain its actual version and runtime results.

The [Apache-2.0 LICENSE](https://github.com/vercel-labs/agent-browser/blob/main/LICENSE) credits Copyright 2025 Vercel Inc. The inspected [root inventory](https://api.github.com/repos/vercel-labs/agent-browser/contents/) did not list a root NOTICE file. No implementation or upstream media was copied. Invoking an installed executable does not bundle its dependencies or their notices into this repo.

## Vercel AI SDK boundary

The official [prompt documentation](https://ai-sdk.dev/docs/foundations/prompts) supports image inputs as binary data, encoded data, or URLs, and explicitly warns that not every model supports every modality. A file path or image caption alone is not proof that a vision model received pixels. This informs the separate reviewer's requirement to attach every verified step image and sampled frame.

Adding AI SDK would introduce a second model/provider integration and would not establish subscription-only authentication or video-understanding support. No SDK or credential provider is added. A future SDK integration would need explicit model capability checks and an authorized authentication/billing design; current native image review is not described as ACP or as continuous video comprehension.

## Evidence model and limits

A sealed bundle pins the verbatim operator intent, scenario bytes, recorder source, command transcripts, per-step screenshots/snapshots, finalized video, and sampled frames. Expectations compare exact URLs, exact or contained text, and boolean visible/enabled/checked states. A failed assertion or incomplete capture cannot become an accepted bundle. Replay starts a fresh session and output directory and applies the same pinned scenario; pixel identity is not its default oracle.

Uniform sample times cover the observed container duration at a recorded interval, capped by `max_frames`. `coverage: complete` means every scheduled sample was decoded, not that every source frame was reviewed. `at_ms` is the requested seek time, not an independently decoded presentation timestamp. Video and step wall-clock timelines are distinct; steps include CLI startup/observation overhead.

SHA-256 pins detect changes relative to a trusted bundle digest. They do not authenticate an author who can rewrite both manifest and seal. The loader validates structure, paths, hashes, PNG signatures, assertion consistency, and declared sampling completeness; it does not independently decode the video or prove screenshot semantics. The recorder performs ffprobe/ffmpeg work; the separate visual panel evaluates the actual attached images.

No tested application revision is inferred from the recorder repository. Actual Chrome version remains explicitly unavailable if the installed command contract does not expose it; agent-browser's own version is recorded separately. Public evidence must use deliberately public-safe inputs because text, screenshots, video, and command logs are retained without automatic redaction.
