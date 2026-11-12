# Prove a change

A change is proven by evidence from the running artifact, captured before the fix and after it. Passing unit tests alone is not proof of changed behavior.

## Steps

1. Run the repo's own checks (typecheck, lint, tests, build). Record the commands and results.
2. List the test targets: each behavior the change touches.
3. **Before.** Reproduce the problem first, while it is cheapest to show. Capture it.
4. Make the change.
5. **After.** Repeat the same steps and capture the result.
6. Mark each target `passed`, `failed`, or `untested`, each backed by an artifact. `untested` needs a reason.

## Capture by kind of change

| Change | Evidence |
|---|---|
| UI | Screenshots of the same view before and after, taken with the `browser` tool or Playwright. Record a video with `ffmpeg` when the behavior is a sequence. |
| CLI | The same command with its output, before and after. |
| API or backend | The same request with status and body, before and after. |
| Performance | The same measurement run several times, with the numbers. |

Store artifacts under `.scratch/evidence/<task>/`. `.scratch/` holds a `.gitignore` of `*`, so nothing in it reaches a commit (deep-mode's Contain the work). A repo with a `verify-<app>` skill uses that skill instead of ad hoc captures.

Put a before and after table in the PR body. Host the images where the repo's readers can see them, for example committed to a separate `evidence/<branch>` branch and linked by raw URL. Never upload sensitive screens to a public host.

A missing tool (no browser, no `ffmpeg`) stops that capture. Report it and the evidence you do have. Never substitute a weaker check silently.

## Done when

Every test target has a result backed by an artifact, and the PR body shows the before and after pairs.
