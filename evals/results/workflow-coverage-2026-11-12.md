# Captured workflow evidence, 2026-11-12

## Scope and method

Four disposable journeys used the pinned skill tree at `b72facc78121071ed885eacc8efd0ac841b42b6d`: planning, review, architecture and handoff. Five captured phases exited 0. Handoff used two distinct processes and session receipts. Every observed assistant message identifies `openai-codex/gpt-6-astra`. This is captured client metadata, not independent provider-side model attestation.

The current capture protocol records each phase's input snapshot. The first must match preparation; each later phase must match the preceding successful output snapshot. Collection verifies that chain and runs trusted artifact checks on disposable copies rather than trusting a saved success flag. Capture and probe subprocesses use the shared credential-environment scrubber. This reduces environment exposure but does not provide a security sandbox.

Independent assessments read the artifacts and complete executable actions in the transcripts. All four `delivery-03` collections passed their named criteria and artifact checks. The handoff checker passed five behavioral cases, and the delivered regression suite passed six tests. Separate source-reviewed probes corroborated review, architecture and handoff behavior. Assessments are by the session assistant, not an independent human or vendor.

## Result counts and qualification

The actual report CLI observed **126 inventory items, 110 mapped and 16 missing**. Mapping is not execution or parity. All four current journeys passed. Across **12 retained attempts**, the current protocol counts **four passed, one failed and seven invalid**.

The earlier handoff failure remains failed. All seven earlier passes lack the new input-bound capture protocol and are invalid under it. Their receipts were not rewritten or upgraded. Earlier reporting also exposed duplicate references to the same capture; the reporter now deduplicates identical paths while rejecting distinct captures for the same phase. Twenty-five focused workflow tests passed after the integrity repairs, including rejection of intervening handoff edits and scrubbing credentials from actual test subprocesses.

## Findings by journey

- **Planning:** One specification and three vertical tickets cover reservations, owner cancellation, availability, inclusive overlaps and concurrent exclusivity. Payments, notifications and an admin dashboard are excluded. The proposed application/auth/catalog baseline is explicitly unimplemented. Ticket headers, parents, acceptance examples and dependency graph were checked. Observed actions were local reads and planning writes, not remote publication or implementation.
- **Review:** Identified both supported defects: left-starting/enclosing overlaps accepted and cancellation without owner matching. Candidate reproductions and independent probes confirmed both. Adjacent intervals were correctly allowed. Protected source files remained unchanged.
- **Architecture:** Traced `cli.py`, `web.py` and `store.py`, proposed one operation owning policy and persistence, and supplied migration, caller examples and public-boundary tests. The candidate labeled the divergent outcomes as inference; the independent probe executed the functions and confirmed CLI rejection versus web acceptance for the same enclosing interval. No source refactor or atomic-concurrency guarantee was claimed.
- **Handoff:** Phase one accurately described the unfinished stub and preservation requirements. A fresh second process implemented dictionary-based owner cancellation and added six regression tests. Its recorded input matched phase one's output. `notes.txt` stayed byte-identical and `display_title` retained `Tool library: `. Independent behavior and regression checks passed. No reset, commit, installation or remote write was observed.

## Evidence paths

Full captures, raw output, session action records, snapshots, assessments, checker outputs and collector results remain in the ignored local checkout:

- `.scratch/workflows/planning-delivery-03/`
- `.scratch/workflows/review-delivery-03/`
- `.scratch/workflows/architecture-delivery-03/`
- `.scratch/workflows/handoff-delivery-03/`
- `.scratch/evidence/workflow-report-protocol-v2.json`

Each journey retains `assessment.json`, `result.json`, phase artifacts, distinct session directories and `collected-checks-*/`. Review, architecture and handoff also retain `independent-semantics.json`. Historical `delivery-01` and `delivery-02` receipts remain intact. These local paths are not a public independent archive.

The inventory sources are pinned at `ec569379616a4826b98f0f0a205dd3411b573611` and `5863806dd4e15c63174bee4e7515a4256792ecfa`. Identities and attribution are in [the workflow inventory](../workflows/README.md) and its source snapshots.

These observations establish only the named scenarios. They do not establish all 110 mapped workflows, equivalent upstream behavior, general instruction adherence, model superiority, sandbox security or broad workflow quality. No competitor comparison is made.
