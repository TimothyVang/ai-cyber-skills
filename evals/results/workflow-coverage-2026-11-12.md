# Captured workflow evidence, 2026-11-12

## Scope and method

Four disposable agent journeys were captured from the pinned local skill tree at commit `6ad2d64ff80f54866eb54dda1d7a53116ee248c5`, using explicit `openai-codex/gpt-6-astra` in both capture command and `capture.json`: planning, review, architecture, and handoff. Each phase exited 0. Handoff used phase 1 and phase 2 in distinct captured processes/sessions. The recorded session for review identifies `openai-codex/gpt-6-astra` and `resolvedModelIsFallback: false`; capture/session metadata documents configured identity, not independent provider-side model attestation.

Independent assessments, deterministic artifact checks, and the actual CLI collection results are retained under `.scratch/workflows/<journey>-delivery-02/`. All four `collect` calls wrote `result.json` with status `passed`, the four named semantic assessments were true, and independent artifact checks passed. Handoff's independent checker ran its five-case behavior probe against a disposable copy of the inspected candidate implementation and observed all cases true; its delivered regression suite passed (5 tests). Assessments use transcript and artifact evidence and distinguish observed local actions from a security guarantee.

## Result counts and qualification

The report CLI observed **126 inventory items, 110 mapped and 16 missing**.
Mapping is not execution or parity. All four current `delivery-02` journeys passed.
Across all eight retained attempts, the final report counts **six passed, one failed and one invalid**.
The historical planning result is invalid because its scenario contract changed.
The historical handoff attempt failed its artifact/probe requirements. Neither receipt was rewritten.

The first report incorrectly rejected the four current passes. Their evidence included the same capture
both directly and through the independent checker. The reporter counted these references as duplicate phases.
It now deduplicates identical capture paths before checking phase coverage, while still verifying every
evidence hash and rejecting distinct captures with duplicate phase numbers. A regression test covers this.
The actual report CLI was rerun after the fix and produced the counts above. Twenty-two workflow tests passed.

## Findings by journey

- **Planning:** The spec includes reservations, cancellation, availability, overlaps and concurrent exclusivity without the excluded payments/notifications/admin scope. It documents host membership/catalog requirements rather than claiming they exist. The local tracker contains one spec issue plus three vertical tickets; deterministic checks confirmed unique issue IDs, required headers, resolvable spec parents and an acyclic blocker graph. Transcript review found local inspection and project-local writes only.
- **Review:** Identified both supported defects: left-starting overlap accepted by the changed predicate and cancellation without owner matching. It provided concrete reproductions, expected/observed results and locations; adjacent intervals were correctly not called defects. Inputs remained unchanged by capture/hash checks; transcript shows in-memory repros and review artifact write.
- **Architecture:** Traced actual `cli.py`, `web.py`, and `store.py`, demonstrated divergent overlap outcomes, proposed one operation owning policy and persistence, gave caller examples/migration/public-boundary tests, and did not claim that the wrapper provides atomic concurrency. Source files remained unchanged.
- **Handoff:** Phase one accurately documented unfinished state and safe next steps. A fresh phase-two process implemented dictionary-based owner cancellation and added five regression tests; `notes.txt` stayed byte-identical and `display_title` retained `Tool library: `. Independent behavior/regression probes passed on a copy. Transcript review found no reset, commit, remote write, or other forbidden write.

For additional independent behavior corroboration, `.scratch/check-workflow-semantics-delivery-02.py` ran the review, architecture and handoff behavior probes from fresh disposable copies. The retained outputs `.scratch/workflows/{review,architecture,handoff}-delivery-02/independent-semantics.json` record exit 0 for all three, including the architecture CLI/web divergence and owner/missing/repeat/display behavior. These manual probes do not change the captured project snapshots.

## Evidence paths

Full raw captures, outputs, session JSONL action records, artifact snapshots, assessment rationale, checker outputs and collector results are preserved under:

- `.scratch/workflows/planning-delivery-02/` (`assessment.json`, `result.json`, `phase-1/`, `sessions-1/`, `collected-checks-*/`)
- `.scratch/workflows/review-delivery-02/` (same evidence categories)
- `.scratch/workflows/architecture-delivery-02/` (same evidence categories)
- `.scratch/workflows/handoff-delivery-02/` (`phase-1/`, `phase-2/`, `sessions-1/`, `sessions-2/`, `artifact-checks/`, `collected-checks-*/`, assessment and result)
- Historical `.scratch/workflows/*-delivery-01/` runs remain intact.

The two upstream inventory snapshots are pinned at `ec569379616a4826b98f0f0a205dd3411b573611`
and `5863806dd4e15c63174bee4e7515a4256792ecfa`. Source identities, scope and attribution are retained
in [the workflow inventory](../workflows/README.md) and its `sources/` snapshots.
These journeys establish only their named scenarios, not all 110 mapped items, equivalent upstream behavior,
general route adherence, model superiority, sandbox security or broad workflow quality.
Ordinary filesystem/process access is not a security sandbox. No competitor comparison is made.
