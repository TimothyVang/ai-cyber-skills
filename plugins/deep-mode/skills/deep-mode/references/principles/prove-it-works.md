# prove-it-works

Group: verification. When: after a task, before declaring done.
- **Rule.** Verify against the real artifact (run the feature, read the actual value, inspect the diff), never a proxy, self-report, or "it compiles".
- **Checks.** Check process liveness directly, not through derived state. Read the actual value, not a cached/derived one. When verification fails, suspect the observation method before the system. A new test or gate counts only after you have seen it go red on the state it guards against.
- **Field-shaped fixtures.** A green suite on tidy fixtures (absolute paths, LF files, one job at a time) still misses field bugs. Run the real path once after the suite passes; when it finds a bug the suite missed, reshape the fixture so the suite catches it next time.
- **Script the check.** Strongest proof is a deterministic script rerunning the comparison; keep its output as an artifact a reviewer reruns. Keep it visible; commit only for large/complex work needing an auditable trail (the **show-me-your-work** technique).
- **Anti-patterns.** File mtimes, output freshness, agent self-reports, cached screenshots as proof.
