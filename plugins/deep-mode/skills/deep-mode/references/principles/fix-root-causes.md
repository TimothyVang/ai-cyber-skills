# fix-root-causes

Group: verification. When: debugging.
- **Rule.** Fix the fault, not where it surfaced. Root cause = first place the system did something it shouldn't, or failed to handle a state it should.
- **Steps.** Reproduce first. Ask "why" until the answer is a wrong decision in the code, not a consequence. When stuck, instrument: read the actual error and state, don't guess. Ask whether the triggering state is legitimate: if yes, the code that broke on it is the root cause and handling it there is the fix; if it should never exist, a guard there hides the bug — find what produced the state. Fails only after restart → suspect persisted state first (config, caches, lock files, serialized state). Fix the pattern, not just the instance. If the deciding fact took a deep dig, propose the cheap always-on signal that would have shown it at first look.
- **Anti-patterns.** Guards, retries, swallowed errors, clamped values, discarded state hiding a bug; a workaround needing a paragraph-long comment (fix the code, not the comment).
