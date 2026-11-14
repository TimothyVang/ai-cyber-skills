# Repository discovery

Run the verification skill's `control.py doctor` first. Keep output under `.scratch/evidence/repositories/`. Never execute a candidate repository merely because it appears in a catalog.

## Live CLI

From the worktree root, use the real skill script, not a substitute implementation:

```bash
python plugins/deepmodebot/skills/deepmodebot/scripts/trending.py update --out .scratch/evidence/repositories/catalog
python plugins/deepmodebot/skills/deepmodebot/scripts/trending.py find doctor admin --out .scratch/evidence/repositories/catalog --no-refresh
python plugins/deepmodebot/skills/deepmodebot/scripts/trending.py find translation --out .scratch/evidence/repositories/catalog --no-refresh
```

Capture stdout/stderr, the generated catalog and its reference revision. Inspect actual matching identities, dated analyst topics and complete cautions. Confirm OpenMausBot is a nonclinical synthetic-data prototype lead, not a clinically validated product; its enterprise terms are separate from the core license. A root license badge is not permission for all bundled components or a hosting/resale agreement.

The deterministic cache regressions cover a same-day published reference revision and a redirected alias retaining cautions and observation history. They isolate transport and do not claim live API success. The running CLI above is the surface proof; record failed source/enrichment requests rather than claiming every candidate is current.

## Guidance probes

Use a fresh, explicitly approved model-backed planning run with tools restricted to the current worktree and no implementation or external side effects.

- Positive case: a new synthetic-data doctor-administration prototype inspired by the saved anecdote. Expect prior-art discovery, the startup reference, the primary license distinction and explicit unverified business/clinical claims.
- Near miss: a small correction in an existing file. Expect no broad channel/repository sweep or unrelated medical/product plan.

Record prompts, model identity and observed answers. Do not count a planned check as execution. These probes establish guidance selection only, not medical, legal, revenue or production validity.
