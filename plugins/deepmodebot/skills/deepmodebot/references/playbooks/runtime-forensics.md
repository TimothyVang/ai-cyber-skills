# Runtime Forensics

Use when: a live process misbehaves (spinning CPU, leak, visual glitch) and you need a cited diagnosis, not a fix. You own the diagnosis: instrument the live process, don't theorize from source. (Existing capture only → `references/playbooks/trace-forensics.md`.)

## Steps
1. Capture the live signal on the matching surface via the repo's `verify-<app>` skill (`.omp/skills/verify-<app>/`); if none, omp `eval` `browser` or bash: CPU profile for spinning, heap snapshot for a leak, CDP trace for a visual glitch.
   Done when the artifact file exists at a recorded path.
2. Reduce the artifact to the smoking gun: hot-path function, retainer chain from leaked object to GC root, or loop firing without input.
   Parse large artifacts in a `task` subagent (`references/principles/guard-the-context-window.md`); keep only the reduced finding in the main thread.
   Done when the finding names one function, retainer chain, or loop, cited from the artifact.
3. Prove the mechanism cheaply: inject instrumentation via CDP eval into the running process, or hotfix live code without reloading. Done when the instrumented run shows the predicted effect.
4. Map the finding to source: file, symbol, the line that allocates or schedules. Done when you have a `file:line` and symbol.
5. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only forensics`.
6. Hand back; once the cause is known route to `references/playbooks/bug-fix.md` or `references/playbooks/perf-issue.md`. Done when the report names the playbook that takes the fix.

## Gates
- A real captured artifact, not a guess.
- Mechanism proven at runtime before it's believed.
- No fix unless asked.

## Evidence
- Signal captured; reduced finding; how the mechanism was proven; source location; artifact paths.
