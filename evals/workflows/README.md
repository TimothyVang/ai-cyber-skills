# Workflow coverage and captured journeys

This directory separates **inventory coverage** from **observed agent outcomes**. A local route is not evidence that an agent follows it. Production tests for a helper CLI are not workflow execution evidence either.

## Pinned inventories

Observed on 2026-11-12 from the primary GitHub APIs:

| Source | Exact revision | Inventory |
| --- | --- | --- |
| [cursor/plugins, pstack](https://github.com/cursor/plugins/tree/ec569379616a4826b98f0f0a205dd3411b573611/pstack) | `ec569379616a4826b98f0f0a205dd3411b573611` | 61 `SKILL.md` files, 23 poteto-mode playbooks, 2 agent wrappers, 1 Benny automation pack |
| [mattpocock/skills](https://github.com/mattpocock/skills/tree/5863806dd4e15c63174bee4e7515a4256792ecfa) | `5863806dd4e15c63174bee4e7515a4256792ecfa` | 39 skills: 27 plugin-listed, 8 in-progress, 4 unlisted misc |

[Source snapshots](sources/) retain complete file-name/blob-ID/size inventories and the source tree API URLs, not skill prose. [matrix.json](matrix.json) accounts for all 126 named items. Each row has its exact upstream source link, distribution, local repository-relative route, scenario links, limits and evidence state. The initial map has 110 related local routes and 16 explicit missing entries. These counts are bookkeeping, **not 110 equivalent or successful workflows**. Shared principles, wrappers, dormant automations and full journeys have different units and must not be pooled into a capability score.

Scope includes every `SKILL.md` under either pinned source, every pstack poteto-mode playbook, both pstack agents and the Benny pack. Guide chapters, reference pages and source-maintenance GitHub Actions are not additional agent workflows. Generated harness copies outside `pstack/` are not counted twice. Cursor built-ins and companion-plugin integrations mentioned by pstack are dependencies, not skills shipped under that directory.

The mappings use the local [route table](../../plugins/deepmodebot/skills/deepmodebot/SKILL.md) and [flow map](../../plugins/deepmodebot/skills/deepmodebot/references/flows.md). They are a reviewed interpretation of overlapping purposes, not a text-equivalence assertion. Upstream names and inventory metadata are attributed to Lauren Tan/pstack and Matt Pocock. Both sources are MIT-licensed; their notices are retained in [LICENSE.upstream.txt](LICENSE.upstream.txt). No upstream skill prose or executable source was copied into these journeys.

## State and evidence

- `mapped`: a documented local route exists, not an execution claim.
- `executed`: linked, digest-bound collected agent output passed the named scenario's checks. Only that scenario is established, not every facet of the upstream workflow.
- `failed`: captured execution did not meet the scenario contract.
- `blocked`: a capability or execution prerequisite is absent. The row's limits say why.

`disposition` separately distinguishes `mapped`, `missing` and `not-applicable`. This prevents a missing platform integration from becoming “supported” because a vaguely related skill exists. A route in a missing row is a nearby alternative, not a replacement.

No empirical results are pre-populated. Matrix rows are never promoted automatically after running a related scenario. To assert execution, attach a collected `result.json` as `{"path": "<repository-relative path>", "sha256": "<file SHA-256>"}`, name the matching scenario, and retain all transitive raw evidence. `validate` rejects missing or duplicate mappings, missing local routes, unknown scenarios, bad source bindings and missing/changed files for asserted execution. A fabricated positive assessment cannot override a nonzero exit, absent phase, missing artifact, changed input/output or failed check. Evidence hashes detect accidental changes; they are not signatures against a malicious operator.

```bash
python evals/workflows/run.py validate
python evals/workflows/run.py report
python -m unittest discover -s evals/workflows -p 'test_*.py'
```

Tests use synthetic processes only to exercise the collector and validator. Their output must never enter a production evidence row. No agent journeys were run when this suite was authored.

## Runnable journeys

[scenarios.json](scenarios.json) is the operator manifest and contains expected outcomes. **Do not give that file, this README, the seed registry or assessment templates to a candidate.** `prepare` copies only benign candidate inputs and pinned local skills into its disposable project. User requests contain no experiment labels or expected defect labels.

| Journey | Candidate work | Required artifacts | Independent assessment |
| --- | --- | --- | --- |
| `planning` | Reservation spec and vertical tickets using the configured local tracker | `docs/specs/*.md`, `docs/deepmodebot/issues/*.md` | Scope, overlap/concurrency contract, parent/blocker graph, acceptance examples, no remote mutations |
| `review` | Read-only review of a reservation change against requirements | `review.md` | Supported findings and reproductions, precision, preservation of both implementations |
| `architecture` | Source-linked module-boundary analysis | `architecture.md` | Actual data flow and drift, a useful public boundary, migration/tests, concurrency limits |
| `handoff` | Pause first, then finish cancellation in a fresh session | `handoff.md`, `resume.md`, `test_reservations.py` in the root or a test directory | Handoff fidelity, fresh-session pickup, dictionary-based cancellation behavior, preservation of the user's unrelated edit |
| `bugfix` | Existing billsplit organic task | Existing outcome collector artifacts | [Outcome runner](../outcome/README.md), task `billsplit` |
| `feature` | Existing kitty organic task | Existing outcome collector artifacts | [Outcome runner](../outcome/README.md), task `kitty` |

The architecture journey is local source research, not a web-research benchmark. The planning journey tests the local tracker, not GitHub/GitLab/Jira/Linear integration. The review journey is one authored example, not an unseen review-quality evaluation; use [the dedicated review suite](../review/) for that measurement.

### Prepare and capture

Run from the repository root. Choose a new run ID for every attempt. Supply a committed skill revision; uncommitted skill edits are intentionally not included. `prepare` creates a fresh git root, snapshots the selected commit's skills into `.omp/skills/`, binds seed/scenario/skill/request digests, and prints project and request paths. It does not invoke a model or install packages.

```bash
python evals/workflows/run.py prepare planning --id planning-01 --ref <skill-commit>
python evals/workflows/run.py prepare review --id review-01 --ref <skill-commit>
python evals/workflows/run.py prepare architecture --id architecture-01 --ref <skill-commit>
python evals/workflows/run.py prepare handoff --id handoff-01 --ref <skill-commit>
```

`capture` starts the supplied command in the prepared project and sends the appropriate request on stdin. It strips the three standard model API-key environment variables and places process temp directories inside the project. Supply an **explicit approved subscription model ID** both to the collector and as an argv element of the command. There is no default model or automatic fallback. On Windows, supply the real executable or the operator's working launcher if `omp` resolves only to a shell shim.

An omp invocation using the existing outcome runner's isolation conventions is:

```bash
python evals/workflows/run.py capture --id planning-01 --phase 1 --model <approved-model-id> -- omp -p --mode json --no-title --no-session --no-rules --no-context-files --no-extensions --no-skills --no-lsp --max-time 15m --max-cost 4 --model <approved-model-id>
```

Repeat for `review-01` and `architecture-01`. `--no-skills` prevents global discovery; the request explicitly points at the pinned project-local skill file. This measures explicit local-file loading, not slash-command discovery. If testing native skill discovery instead, record that distinct harness configuration and restrict discovery to the copied project skills. Keep configuration, model, reasoning settings and budgets fixed for comparisons.

For handoff, run phase 1, inspect its captured handoff without altering it, then run phase 2 as a **new process**, not `--resume` or `--continue`:

```bash
python evals/workflows/run.py capture --id handoff-01 --phase 1 --model <approved-model-id> -- <isolated-agent-command-with-explicit-model>
python evals/workflows/run.py capture --id handoff-01 --phase 2 --model <approved-model-id> -- <isolated-agent-command-with-explicit-model>
```

The generic capture wrapper does not itself disable imported MCP servers, profiles, system prompts, global model roles or delegated-model defaults. The operator must use a reviewed, project-local `--config` overlay or an already isolated launcher to disable these where supported, and retain that config with the run. Never change user-wide settings to run this suite. No new login or model API key is needed. Use only existing subscription authorization. Do not put credentials in command arguments or captured configuration.

`--no-session` avoids implicit session reuse and user session files; raw JSON stdout still records the main process. If the agent delegates, retain its child transcripts too, using a project-local session directory instead, and include them in the assessment evidence. A main-process transcript does not establish which models or actions its descendants used. This suite makes no token/cost efficiency claim.

### Collect without inventing proof

Each phase retains `capture.json`, raw stdout/stderr, timestamps, command/model, status/exit code and a digest-bound file snapshot under `.scratch/workflows/<id>/phase-N/`. The operator inspects actual outputs and transcripts and independently executes the manifest's outcome checks. Record those checks' raw outputs in the run folder. Do not trust the candidate's final summary alone.

Run the supplied deterministic artifact checks before writing the assessment:

```bash
python evals/workflows/check_artifacts.py --id planning-01
python evals/workflows/check_artifacts.py --id review-01
python evals/workflows/check_artifacts.py --id architecture-01
python evals/workflows/check_artifacts.py --id handoff-01
```

These commands verify the captured snapshot and work on a copy under `artifact-checks/`. Planning checks resolve issue IDs, parent links, required headers and an acyclic blocker graph. Handoff checks independently exercise owner, non-owner, missing-ID and repeated cancellation, preserve the user's display prefix, and run the delivered regression suite. All journeys check required artifacts and immutable inputs. `artifact-checks/checks.json` and the raw subprocess records are evidence paths for the assessment. These checks do not assess prose quality or prove route adherence; the named semantic/transcript checks still require independent review. Inspect the local generated code before executing its behavior probes.

Copy `assessment-template.json` to a new `assessment.json` inside the run folder. Fill `reviewer`, every check's boolean `passed`, a specific rationale and a list of repository-relative evidence paths. Check requirements are in `scenarios.json`. A semantic failure is `false`, never omitted. Missing/failed process attempts need no positive assessment and can still be collected as failures.

```bash
python evals/workflows/run.py collect --id planning-01 --assessment .scratch/workflows/planning-01/assessment.json
python evals/workflows/run.py collect --id review-01 --assessment .scratch/workflows/review-01/assessment.json
python evals/workflows/run.py collect --id architecture-01 --assessment .scratch/workflows/architecture-01/assessment.json
python evals/workflows/run.py collect --id handoff-01 --assessment .scratch/workflows/handoff-01/assessment.json
python evals/workflows/run.py report
```

Inspect `phase-1/artifacts/` for handoff's pre-resume state. Run independent behavior probes against a copy of the final project, not the captured project itself. Keep the copy and resulting logs under the same run folder; the collector refuses a project changed after capture. `collect` writes an immutable `result.json` and returns nonzero on failure. Repeated capture/collection never overwrites an attempt. A corrected run gets a new ID; retain the earlier failure. Pending, failed and blocked attempts stay in `report`'s denominator. Zero attempts reports a null pass rate, not success. Linked billsplit/kitty runs retain their own denominator and are not silently pooled with these four journeys.

After a scenario changes, an older pass no longer proves the current contract. `report` retains that attempt as `invalid`, with the evidence error, rather than deleting it or counting it as a current pass. A failed handoff fixture originally left the booking container unspecified while its checker assumed a list. The corrected seed specifies a dictionary and the checker accepts conventional test directories. Keep the original attempt when rerunning.

### Reuse the existing coding tasks

Use the current outcome runner rather than making duplicate tasks. For matched baseline/candidate work:

```bash
python evals/outcome/run.py setup --task kitty --run-id delivery --compare-ref 37717c2cec9b4cc8c3750f0b34728506824b5698 --ref <new-skill-commit> --per-variant 1
python evals/outcome/run.py run --task kitty --run-id delivery --model <approved-model-id> --max-cost 4
python evals/outcome/run.py collect --task kitty --run-id delivery
```

Use `--task billsplit` and a fresh `--run-id` for bugfix. For optional model-assisted scoring, supply two explicit `--judge-model` arguments to the outcome runner's `judge` command. Preserve its variant key, raw event/session files, checked-out artifacts, measurement JSON and contamination review. A historical billsplit/kitty result does not establish current skills, a different model, or a matched baseline.

## Limits and missing capabilities

- No replacement for Cursor IDE/custom-mode UX, Origin stack integration, Bugbot, native `/loop`, Cursor Automations, or separately installed `control-ui`/`control-cli` tooling. Benny's Slack ingestion, hosted triggers, setup and UI reproduction are blocked as an integration, even where local triage/bugfix concepts overlap.
- No dedicated formal-verification authoring/maintenance, checked TLA+ statechart rendering, subtitled catch-up video, Grok Bot webhook/Tailscale UI or pstack per-role setup writer.
- Matt's TypeScript deep-module setup, Shoehorn migration, exercise scaffolding and three in-progress narrative-writing workflows have no dedicated local counterpart. In-progress and unlisted skills are counted but not presented as plugin-shipped.
- Interview-heavy Matt flows and deepmodebot's autonomous reversible decisions differ deliberately. Generic architecture/TypeScript advice is not full upstream behavior parity. Multi-day chief-of-staff, persistent shared wiki, external factory triggers and remote merge workflows remain unmeasured here.
- Ordinary filesystem/process execution is not a security sandbox. Candidate tools may still reach parent directories, hidden answers, other runs, global configuration or the network. Record any such access as failed/contaminated assessment evidence. The wrapper's path and hash checks protect its own files, not all agent tool actions. Timeout kills the immediate process; inspect possible descendants before starting another attempt.
- Preserve `.scratch/workflows/` evidence referenced by a result. Do not clean it up while making execution claims. For durable publication, retain or export the entire evidence tree and update all relative references and digests together. A result cannot remain asserted executed after its raw evidence has been deleted.

To refresh inventories, query the primary repositories' exact current commits and complete recursive trees, update the metadata snapshots, then account for every added/removed named item in `matrix.json`. Review changed workflow semantics and limits, not only names. Never advance an upstream commit while leaving an older tree snapshot behind.
