# separate-before-serializing-shared-state

Group: architecture. When: concurrent actors might write the same file, branch, key, or state object.
- **Rule.** First eliminate the sharing; serialize structurally only when one shared writer is a real invariant. Instructions and conventions are not concurrency control.
- **Steps.** (1) Identify shared mutable state (files read+written by both, branches both push, APIs both define and consume). (2) Default: give each actor its own file/key/branch/state dir; merge only at the read/reporting boundary. Two workers writing their own `lastX` into one `state.json` is still shared; `indexer-state.json` + `metrics-state.json` is not. (3) Only if one target is a real invariant: lockfile, sequential phases, single-writer actor, or atomic CAS. "We need a lock" is a design smell to check, not the default.
- omp note: subagents share one workspace, so every parallel `task` gets exclusive file ownership.
