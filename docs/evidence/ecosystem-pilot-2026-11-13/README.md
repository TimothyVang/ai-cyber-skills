# Ecosystem and workflow pilot — 2026-11-13

This is one synthetic local invoice-export pilot, not a general quality benchmark. Runs continued into 2026-11-14. Public artifacts contain synthetic invoice identifiers; private credentials, raw model thoughts/events and OAuth metadata are excluded.
These receipts belong to canonical `TimothyVang/deepmodebot`. Rebranded distributions retain them unchanged as upstream observations, not proof that the new distribution has run.

## Observed results

| Boundary | Actual result | Evidence |
| --- | --- | --- |
| Grounded goal planning | Three independent ACP approvals of one fixed contract; quantitative eight-case oracle | [Contract](goals/contract.json), [candidate](goals/candidate.json), [receipt](goals/grounded-receipt.json), [provenance](goals/provenance.json) |
| Missing context | Three valid `needs_context` responses; no goal emitted | [Receipt](goals/missing-context-receipt.json) |
| Hostile supplied context | Three approvals of the unchanged fixed contract, not the injected instruction | [Receipt](goals/hostile-context-receipt.json) |
| Authorized goal execution | One iteration, 31 seconds, eight cases and zero errors; unchanged oracle | [Repair trail](goals/repair/trail.tsv), [oracle](goals/acceptance.py), [final worker](goals/worker-after.py) |
| Browser recording | Six of six steps passed | [Sealed manifest](recording/manifest.json) |
| Fresh-session replay | Six of six steps passed; 1.6-second video, two sampled frames | [Sealed manifest](replay/manifest.json) |
| Independent visual panel | All three valid; two approve, one revise | [Votes and dissent](visual-review.json) |
| Real backend | Persisted first-seen unique IDs `inv-2`, `inv-1`, `inv-3`, source count four | [HTTP log](backend/http.log), [SQL observation](backend/observation.json), [database snapshot](backend/observed.sqlite3) |
| Popup negative | Failed closed with upstream network-control auto-attach timeout | [Failed manifest](popup-negative/manifest.json) |
| Generated design | Six SVG groups and embedded thumbnails rendered; HTML video playback reached its end | [Portable index](design/index.html), [SVG](design/workflow.svg), [browser proof](design/invoice-design-playback.png) |
| Native design editor | Local Penpot 2.18 imported SVG; rectangle width changed from 984 to 1000; native archive and SVG downloaded | [Provenance](penpot/provenance.json), [native file](penpot/workflow-edited.penpot), [after edit](penpot/penpot-rectangle-after.png) |
| Canonical update | Real GitHub identity/network; clean canonical checkout advanced and historical native copy synchronized; three negative cases unchanged | [Receipt](updater-proof.json), [CLI logs](updates/update-bare-boundary.stdout.txt), [detailed state](updates/update-receipt.json) |
| Update failure and recovery | Real Windows handle denied replacement: CLI exit 1; handle release and retry: exit 0; all 140 files matched pinned Git blobs | [Receipt](updates/failure-recovery.json), [failure output](updates/sharing-failure.stdout.txt), [recovery output](updates/sharing-recovery.stdout.txt) |
| Concurrent edit before upgrade | Real canonical-network API run retained the edit and never invoked the upgrade callback | [Receipt](updates/concurrent-edit.json), [retained driver](updates/concurrent-edit-driver.py) |
| Git transaction failure | Actual index lock caused CLI exit 1 with unchanged tracked files; removing only the owned lock allowed exit 0 and fast-forward | [Receipt](updates/index-lock-recovery.json), [failure output](updates/index-lock-failure.stdout.txt) |
| Concurrent edit to current install | Current canonical plugin was edited during marketplace fetch; edit retained, no canonical receipt or upgrade | [Receipt](updates/current-plugin-edit.json), [retained driver](updates/current-plugin-edit-driver.py) |

## Inspect or replay

Each recording bundle retains its scenario, ordered step screenshots/snapshots, video, sampled frames, exact capture-tool source bytes, artifact hashes and limitations. `manifest.sha256` authenticates the manifest's bytes; the manifest authenticates its artifact bytes. The current recorder source matched the retained replay capture-tool SHA-256 when this index was assembled.

Run from the repository root with Python 3.10+, an explicitly selected agent-browser 0.43.0+ executable, matching skill data when required, existing Chrome/Chromium, ffmpeg with libvpx, and ffprobe. No dependency is installed by these commands.

```bash
python evals/fixtures/invoice-export/server.py --database .scratch/invoice-replay.sqlite3 --port 18991
```

In another terminal, with `BROWSER` set to the chosen executable:

```bash
E2E=plugins/deepmodebot/skills/deepmodebot/assets/e2e
python "$E2E/record.py" replay docs/evidence/ecosystem-pilot-2026-11-13/replay --output .scratch/invoice-replay-new --browser "$BROWSER"
```

A standalone native executable may additionally need `--browser-skills-dir /path/to/matching/skill-data`. Use an absent output directory. A replay creates fresh evidence; it never edits the source bundle. See the [verification feature](../../../.omp/skills/verify-deepmodebot/features/visual-e2e.md) for the doctor, capture, review and export commands.

The goal fixture's original evidence records five failing cases in an eight-case oracle. [worker-before.py](goals/worker-before.py) reconstructs the observed two-line baseline; it was not recovered from a Git commit. The approved goal is [immutable compiler output](goals/approved-goal.txt), whose SHA-256 matches the original receipt. The [separate working goal](goals/working-goal-after-stalls.txt) contains execution-time planning changes. Earlier failed runs and their check logs remain under [earlier-stalls](goals/earlier-stalls/). Planning receipts are draft-only; separate execution logs prove the authorized repair.

## Limits and retained failures

- Visual reviewers received six actual screenshots and two actual sampled frames, not a claim of whole-video model understanding. The dissent notes a white initial frame, omitted transient entry/submission states, different wallclock/PTS clocks, and insufficient image-only persistence proof. SQL and HTTP observations support the separate backend claim.
- The popup failure originated in the native browser's network-control auto-attach handling. It is not isolated live proof of the wrapper's tab-count guard.
- Penpot text remained raw SVG, not native editable rich text. One native rectangle edit is proven. No native-file re-import, interaction prototype, hosted Penpot workflow or design-wide editability is claimed.
- [Raw Penpot SVG](penpot/workflow-native.svg) references the temporary local server. [workflow-portable.svg](penpot/workflow-portable.svg) is an explicitly derived copy embedding the archive's unchanged PNG media. Its [browser render](penpot/penpot-portable-svg.png) is retained. The supplementary [101.233-second edit video](penpot/penpot-edit.webm) was not reviewed by the invoice visual panel.
- Native agent-browser download reported cancellation; a fresh owned Chrome session downloaded the actual native archive and SVG. The cancellation's cause was not isolated.
- Initial updater runs correctly refused a native-copy fixture nested inside another Git working tree. An empty bare Git boundary isolated the fixture; the successful run changed no guard. [Initial log](updates/update.stdout.txt) and [environment-boundary attempt](updates/update-standalone.stdout.txt) remain. The foreign-origin negative used a synthetic noncanonical URL, not a live GitHub fork.
- This updater receipt uses an isolated home and real canonical upstream. It does not establish activation of the workstation's production watcher.
- The failure/recovery fixture initially inherited CRLF conversion from Git archive and was safely refused as unknown provenance. A separate candidate used per-command `core.autocrlf=false` and matched canonical blobs before the actual Windows sharing fault. No global Git setting changed.
- The first concurrent-editor attempt encountered a Windows backup-handle sharing error before injecting its edit. Its [receipt](updates/concurrent-edit-initial.json) and [stderr](updates/concurrent-edit-initial.stderr.txt) remain. The resumed driver waited for the backup writer to release its handle, reused the owned fixture, and passed. The upgrade callback was an observation-only stop, not a package-manager execution.

The research, routing and implementation are separate from these measured outcomes. A two-of-three vote does not override a failed deterministic check, a missing artifact, a fork/dirty-copy guard, or an explicit user requirement.

## Additional receipts

- [Native agent mailbox exchange](agent-message-receipt.json): observed two-way scoped clarification, with local-history and portability limits.
- [Rendered public quorum policy](docs-policy-observations.json): wide and compact views, no horizontal overflow, keyboard focus and inspected link destinations. Settled screenshots are explicitly distinguished from premature smooth-scroll captures.
- `.gitattributes` disables text normalization for this evidence tree. Recorded bytes, including original CRLF logs, must survive Git publication unchanged; normalizing them would invalidate artifact hashes.
- [Rebrand preservation proof](branding-proof.json): the actual builder preserved every existing evidence file's path and bytes; the built distribution's own loader validated all three sealed bundles. This is not a media-rendering or model-backed rebrand test.
- [Rejected frozen review round](reviews/85099c4.json): all three independent native reviewers returned NOT DONE at `85099c4`, despite three successful repository gates. Updater defects, complete reports and limits are retained; these are not votes on later heads.
- [Historical updater regression check](updates/regressions.json): 53 tests passed at the earlier correction. Process-boundary doubles in these tests are distinguished from the separate real CLI/network evidence.
- [Second rejected frozen round](reviews/2b16ae2.json): all three returned NOT DONE at `2b16ae2` despite successful repository gates. Actual Git failure classification and already-current installation provenance remained defective; complete reports and the additional copy-completion finding are retained.
- [Expanded updater regression check](updates/regressions-postconditions.json): 58 tests passed after typed Git failures and final/current inventory verification were added. Controlled edit scheduling and process doubles are explicitly distinguished from live CLI/network/editor observations.
