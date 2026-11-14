# Procedure verification

## Scope

Five live `omp -p` planning probes exercised the source-backed procedures. These are instruction-following observations, not a controlled improvement comparison or a demonstration of production operations.

The new changes add task-wide nested-delegation limits to `coworkers` and explicit pending/unknown action state to `handoff`. Existing source-backed additions to `architect`, `benchmark-checklist`, `coworkers`, and `wizard` were exercised too. No routing, description, or default-stack change was made.

## Commands and retained evidence

Prerequisite command: `python .omp/skills/verify-deepmodebot/control.py doctor` in the primary checkout. It reported Python 3.13.14, Git, Node, and omp available, with `ready: true`. It did not test authentication.

Each probe invoked `omp -p --no-session --no-title --no-tools --no-skills --no-rules --no-context-files --no-extensions --no-lsp --no-prewalk --model openai-codex/gpt-6.1-sol --thinking medium --max-time 120s --max-cost 1 --mode json @request.md`.

Each `request.md` contained the actual affected procedure and an organic planning request. Tool execution was intentionally disabled because these requests needed plans, not external side effects. API-key environment variables were removed; temporary files stayed under the integration worktree's `.scratch/`.

Full input, raw events, stderr, command/exit record, and final answer remain in `.scratch/youtube-probes/<case>/` in `.worktrees/youtube-learning-20261113/`. `results.json` holds all five full answers. All five invocations exited 0 with nonempty final answers; each answer was read in full.

| Case | Observed decision | Assessment |
| --- | --- | --- |
| `team` | Kept work inline when the harness lacked child-limit/cancellation enforcement; set zero descendants, retained a single 20-minute budget, and rejected paid-service suggestions from meeting notes as unauthorized. | Intended planning behavior observed. It explicitly called its cutoff operator-enforced, not a runtime guarantee. |
| `handoff` | Preserved migration status as unknown, process 321 as reported active, local-only permission, and eight remaining minutes. First action checks migration logs and the authoritative applied-migration table instead of retrying. | Intended recovery planning observed. No database or process was touched. |
| `design` | Declared assumptions and two designs, then traced tenant authority, durable acceptance, worker execution, provider ambiguity, customer debit, and reconciliation. Distinguished customer debit idempotency from provider-charge guarantees. | Intended boundary reasoning observed. No implementation or capacity proof. |
| `load` | Required explicit write permission and test-data namespace, bounded workload/spend, stop conditions and cleanup. Distinguished proposed load from successful measured traffic. | Intended operational planning observed. No traffic, purchases, or cleanup ran. |
| `connection` | Separated GitHub consent, existing installation/repository scope, AWS connection status, and actual repository reachability. | Intended setup reasoning observed. Dashboard labels were marked unconfirmed and success unobserved. |

## Limits

The probes explicitly loaded one relevant procedure each. They do not prove automatic routing, full plugin discovery, a coding task, actual descendant cancellation, real compaction recovery, AWS setup, load capacity, security, or productivity. There is no before/after effectiveness claim. No new permanent verification framework or competing evaluator was added.

The source archive preserves incomplete caption endpoints, restricted metadata and selected-frame coverage. See [the research index](README.md) and each source's limits before interpreting completeness.

## Why prose belongs here

These additions guide judgment across harnesses and task types. A universal runtime mechanism is not supplied by this documentation change. The nested-delegation rule explicitly requires an enforceable harness bound or inline work; it does not substitute a prompt for enforcement. Existing project-specific types, tests and runtime caps remain authoritative.

## Repository-gate correction

The initial full check failed. The inherited main-skill preamble was 20,795 bytes before `## Routes`, above the existing 20,000-byte limit. Windows process tests also rejected temp paths outside the integration worktree.

The preamble now points to the existing Setup process-conflict procedure instead of duplicating that policy, and removes repeated autonomy prose. Policy, exceptions, confirmations, route rows, and size criteria remain in their existing owners.

The corrected gate invocation is `TMPDIR="$PWD/.scratch/tmp" TMP="$PWD/.scratch/tmp" TEMP="$PWD/.scratch/tmp" python scripts/check.py` after creating that directory. Final gate and narrow routing results belong to the PR evidence; the initial failure is retained rather than reported as a pass.
