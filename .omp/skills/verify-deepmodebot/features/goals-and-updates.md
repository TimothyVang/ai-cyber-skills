# Goal planning and local updates

Run `python .omp/skills/verify-deepmodebot/control.py doctor` first.
Use fresh project-local scratch directories. On Windows set `TMP`, `TEMP` and `TMPDIR` to an existing root-local scratch directory before running process-ownership tests.
Never point a destructive or mutation test at the user's actual home, working checkout, plugin install or services.

## Quantitative goal planning over ACP

Inspect `python plugins/deepmodebot/skills/deepmodebot/assets/loop/plan.py --help` and use the documented request, evidence, fixed-contract and output inputs.
Use an explicit authorized model, bounded rounds, per-call spend and time caps, and the real installed ACP client/harness.
The fixed operator contract must name an existing protected consumer check and the immutable scope/caps; it is not supplied by model output.

Exercise the frozen scenarios in `docs/research/goal-planning.md`:

- Grounded intent: three distinct completed reviewer sessions see one candidate identity; at least two approve; the emitted goal parses in the real runner's `run --dry-run` mode.
- Missing material preference: output questions and a needs-context outcome, not a guessed decision or launchable goal.
- Hostile diagnostics: an embedded request to weaken acceptance, expand permissions or use new credentials leaves the fixed contract unchanged and produces no execution effects.

Inspect actual transcripts, candidate hashes, votes and the compiled goal, not just CLI exit status.
A separate local repair pilot can run the approved draft through `loop.py run` with one outer runner and an unchanged protected oracle.
It must show the original failing consumer behavior becoming correct; a model-written pass receipt is not sufficient.
Retain rejected attempts, missing votes and minority findings. Planning consensus and parser compatibility do not prove the user's application was fixed.

## Three-reviewer panel cache

- Every PR receives three independent verifier contexts at one head; all three votes must be valid and at least two must PASS.
- `current_panel` accepts cached votes only with `panelPolicy: "three-independent-v1"` and the same nonempty head SHA. Legacy light-panel or unmarked receipts, changed heads, and missing or invalid votes require re-review.
- Exercise both fresh review and cache reuse. Fixture votes establish cache-gate behavior, not live reviewer independence; retain real session identities and transcripts for that claim.

## Automatic synchronization

Exercise the real updater against disposable Git repositories and copied skill directories.
Use a local bare origin and process-local transport redirection only for the fixture; never change global Git configuration or fetch a fork to decide whether it is trusted.

Required outcomes:

- A clean canonical checkout on its default tracking branch advances fast-forward to the pinned source.
- Fork-origin, dirty, divergent and feature-branch copies remain unchanged with explicit reasons.
- A complete clean historical manual skill copy is adopted and updated; locally edited or unknown-provenance copies remain untouched.
- A recorded upstream SHA does not hide a stale eligible copy; subsequent cycles converge it.
- Dry-run changes no target, provenance receipt or source cache. Missing cached source is reported, not fetched under dry-run.
- Failed updates keep the last valid provenance; one skipped copy does not prevent another eligible copy from updating.
- In the known omp marketplace path only, an untracked root `marketplace.json` matching a tracked `.omp-plugin/marketplace.json` or `.claude-plugin/marketplace.json` blob at the checkout's current `HEAD` permits both read-only preview and verified plugin upgrade. Only CRLF/LF conversion and one optional terminal newline may differ.
- Preserve custom or reformatted metadata, symlinked metadata, manifests matching only incoming bytes, and incoming canonical file/directory collisions at the root metadata path. The same filename in a user checkout or another marketplace receives no exception. Verify the preserved bytes and checkout head, and that the plugin-upgrade callback never runs.
- A partial plugin upgrade remains an incomplete-installation handover barrier after a fresh retry. Mixed contents are not silently repaired or accepted from an old receipt; only an externally repaired complete canonical plugin clears the barrier.
- Copy journals survive interrupted replacement and receipt loss; CLI and watcher share the update lock through receipt persistence. Existing managed edits, including edits to an installed native skill, remain protected.
- Native-copy completion rechecks all managed target signatures and retired-file absence. An edit to an already-processed file retains the journal and prevents a new canonical receipt. Already-current/adopted copies are rechecked after historical lookup without deleting unrelated extra files.
- An installed-tree edit or link-target change during marketplace synchronization prevents the package-manager callback; retain the intervening bytes and do not record a successful installation. The already-current plugin path must also recheck its complete inventory after marketplace synchronization, even without invoking an upgrade.
- A failed checkout update and its later dirty-tree refusal both prevent watcher handover. Changed running code without a covering successful per-target observation also cannot authorize restart.
- The public update command returns nonzero for failed targets or incomplete/unverified installations; ordinary preserved checkout/native-copy candidates remain distinguishable from operational failure. A real Git index-lock failure is failed, not preserved; releasing only the fixture-owned lock permits a successful retry.

Run `bot.py update --dry-run` against the installed configuration only as a read-only preview.
After publication, activate through the canonical installation path and record per-target outcomes; never force dirty copies to match.
Report whether the existing watcher actually restarted, or merely has new files to load at its next between-cycle handover.
A disposable fixture proves updater behavior, not that every arbitrary directory on the machine was discovered or every platform's autostart works.
