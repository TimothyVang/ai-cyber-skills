# Trace Forensics

Use when: a capture already exists (cpuprofile, `.json.gz` trace, spindump, heapsnapshot) and you must diagnose from it. The artifact is a fixed dataset: read it, don't re-run it. (Live process → `references/playbooks/runtime-forensics.md`.) Keep tooling generic: DevTools/trace parser, text editor for spindumps, heap tooling for snapshots.

## Steps
1. Identify the format and load it with the right tool. Parse large artifacts in a `task` subagent (`references/principles/guard-the-context-window.md`); keep the reduced finding in the main thread.
2. Transform into a queryable shape before reading: dump into sqlite, one row per sample, frame, or node.
3. Narrow to the cause:
   - CPU: query frames holding the most time; walk the call tree to the hot path.
   - Leak: follow the retainer chain from leaked object to a GC root.
   - Spindump: find the thread stuck on-CPU or blocked, and its wait reason.
4. Attribute to source via the artifact's own symbols: file, symbol, line.
5. Paired capture available → diff before/after to confirm. Otherwise label the finding the strongest hypothesis the artifact supports.
6. Hand back a cited diagnosis; route to `references/playbooks/bug-fix.md` or `references/playbooks/perf-issue.md` once the cause is known. Throughput checkpoint: `throughput checkpoint: n/a, read-only forensics`.

## Gates
- Don't re-run the capture; don't read raw before reaching the queryable shape.
- A frame with no source mapping is not a diagnosis: resolve symbols or state plainly the artifact lacks them.
- Unpaired → not a confirmed cause.
- No fix unless asked.

## Evidence
- Artifact and format; reduced finding; source location; artifact paths; whether a paired capture confirmed it.
