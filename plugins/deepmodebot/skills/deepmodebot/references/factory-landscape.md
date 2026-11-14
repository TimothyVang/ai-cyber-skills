# Software-factory GitHub landscape

Checked 2026-11-13. Read when choosing a factory, improving Work a queue, or looking for reusable orchestration, isolation, and verification patterns. This is a source map, not an installation recommendation or a benchmark.

## Evidence and reuse

The 61 projects below were inspected through their own READMEs and, where named, their in-repo docs. GitHub's repository API supplied license metadata. Descriptions are maintainer claims, not demonstrated behavior. No candidate was installed or run for this survey. A documented gate is not proof that it is enforced.

Repository links lead to the inspected project's source and README. Branches move; record the selected commit before adoption. Recheck its implementation, current maintenance, license text, dependencies, and a runnable example through the **prior-art** technique (`references/techniques/prior-art.md`). No source code is copied here.

`Unresolved` means GitHub reported `NOASSERTION`; it is not a license grant. `None reported` means no license was reported. Read the actual license before reuse, including subdirectory and commercial terms. Apache-2.0 and MIT entries still require their notices. AGPL-3.0 needs a compatibility review. A public repository can depend on a paid sandbox, hosted control plane, or model API.

Discovery started with [awesome-software-factories](https://github.com/varun1505/awesome-software-factories), a CC0-1.0 list, and GitHub searches for software factories, dark factories, issue-to-PR pipelines, and agent orchestrators. That list is a discovery source, not evidence for the individual claims below. Stars and throughput claims do not determine the shortlist.

## Start with the missing capability

These are candidates to evaluate, not instructions to replace the existing `factory` CLI.

| Need | Read first | What to evaluate |
|---|---|---|
| Tracker-driven dispatch and cancellation | [Symphony](https://github.com/openai/symphony), [Sortie](https://github.com/sortie-ai/sortie) | Reconciliation before dispatch, cancellation when an issue stops being active, durable attempt recovery |
| A deterministic workflow graph | [zeroshot](https://github.com/the-open-engine/zeroshot), [Fabro](https://github.com/fabro-sh/fabro), [Attractor](https://github.com/strongdm/attractor) | Graph validation, bounded cycles, checkpoints; Attractor is a specification, not a runner |
| Isolated workers and reproducible gate receipts | [ESF](https://github.com/mitkox/esf), [HAR](https://github.com/os-factory/har), [Inkwell](https://github.com/disler/inkwell-agent-sandboxes-and-software-factory) | Gate-integrity checks, argv-only verification, tree-bound evidence, host/worker credential separation |
| More parallel work without integration chaos | [Gas Town](https://github.com/gastownhall/gastown), [Foremerge](https://github.com/naw103/foremerge), [watt-mind/factory](https://github.com/watt-mind/factory) | Merge-queue isolation, semantic intent conflicts, disjoint owned paths |
| Independent completion evidence | [Fluent](https://github.com/mrinalwadhwa/fluent), [Agent Smith](https://github.com/holgerleichsenring/agent-smith), [Pullboard](https://github.com/pullboard-dev/pullboard) | A reviewer actually read the candidate, per-criterion receipts, frozen acceptance bars |
| Local subscription-authenticated CLI workers | [iradulovic/software-factory](https://github.com/iradulovic/software-factory), [Hangar](https://github.com/timoknapp/hangar) | Non-mutating login probes, independent critics, deterministic publication; self-hosted orchestration is not local inference |
| A small human-gated workflow | [Turbo](https://github.com/tobihagemann/turbo), [Squid](https://github.com/iusztinpaul/squid), [Finn-loop](https://github.com/finna/Finn-loop) | Plan approval, cross-model review, runtime tryout; distinguish shipped steps from roadmap items |
| Multi-system intake and feedback | [AI Workflow](https://github.com/Blazity/ai-workflow), [Optio](https://github.com/jonwiggins/optio), [Shipfox](https://github.com/ShipfoxHQ/shipfox) | Clarification waits, verified PR identity, bounded resumes on CI/review feedback |

## Patterns to evaluate in this factory

These are proposed improvements, not claims that deepmodebot implements them. Keep its existing panel, exact-head merge, deployment permissions, subscription policy, and hidden-test boundaries. Importing a candidate's auto-merge or deployment policy is a separate decision.

| Pattern | Concrete acceptance experiment | Primary source |
|---|---|---|
| Intake back-pressure | Fill the human-review queue to a configured cap; the next tick starts no builder and still services in-flight work. | [addyosmani/factory](https://github.com/addyosmani/factory), README `STOP_IF` and `CHARTER.md` |
| Reconcile before dispatch | Remove an issue from the active tracker state while its worker runs; the next tick cancels or parks it without starting a duplicate. | [Symphony SPEC.md](https://github.com/openai/symphony/blob/main/SPEC.md) |
| Fail-closed stop and configuration gates | Make the stop-label query fail and remove a required gate command; both cases stop dispatch with a distinct error instead of passing. | [dark-factory-experiment](https://github.com/coleam00/dark-factory-experiment), `FACTORY_RULES.md`; [addyosmani/factory](https://github.com/addyosmani/factory), `MISCONFIGURED` verdict |
| Protect the gate itself | Mutate a gate program or verification policy in the builder's diff; the trusted runner rejects it, including changes that weaken a test. | [ESF](https://github.com/mitkox/esf), deterministic-verification ADR; [nicolasmelo1/software-factory](https://github.com/nicolasmelo1/software-factory), `POLICY_ONLY_TIGHTENS` and mutation fixtures |
| Bind evidence to the exact candidate | Push another commit after review or verification; the old receipt becomes invalid. Review evidence must identify the files and candidate actually read. | [Fluent](https://github.com/mrinalwadhwa/fluent), reviewer tool-event evidence; [HAR](https://github.com/os-factory/har), tree-hash verification |
| Separate hidden-test authorship | Use a different model family for holdouts and builders; access to a vault canary invalidates the result. Evaluate the canary's actual enforcement before adopting it. | [DUBSOpenHub/dark-factory](https://github.com/DUBSOpenHub/dark-factory), sealed-envelope and model-independence sections |
| Own paths before parallel dispatch | Queue two tasks with overlapping owned paths; run them serially or repartition them before any shared write. Extend to semantic conflicts when paths alone miss the dependency. | [watt-mind/factory](https://github.com/watt-mind/factory), `Owned Paths`; [Foremerge](https://github.com/naw103/foremerge), conflict-detection docs |
| Fence stale workers at publication | Pause an old worker, reassign its lease, then resume it; the publication destination rejects its stale generation even if its process survived. | [software-factory-reliability](https://github.com/sjarmak/software-factory-reliability), fault-injection examples and contract reference |
| Recover an ambiguous merge result | Drop the merge response after the forge accepted it; reconciliation identifies the landed result before retrying or marking failure. | [Hivemill](https://github.com/volekerb/hivemill), `docs/verdict-gates.md` |
| Freeze and account for acceptance criteria | Change the task after claim; require a new scope decision. A partial run returns unmet criteria explicitly, rather than silently weakening Done. | [Pullboard](https://github.com/pullboard-dev/pullboard), frozen spec bar; [Agent Smith](https://github.com/holgerleichsenring/agent-smith), delivery account |
| Trust policy from the base | Change repository policy in the candidate branch; only the trusted default-branch policy determines permissions, and target-repo policy can tighten it. | [Lastlight](https://github.com/nearform/lastlight), default-branch configuration rules |
| Correlate the whole run | Follow a failure from tracker comment to worker attempt, review, and merge receipt using one stable run identity; a retry preserves the previous attempt. | [Orbi](https://github.com/orbi-build/orbi), `run_id`; [SMILE](https://github.com/DavidChen-006/smile-software-factory), event log and merge audit |

## Workflow engines and agent fleets

Merge descriptions below are limited to the inspected documentation. `Not established` means the survey did not verify that behavior, not that the project cannot do it.

| Repository | License metadata | Distinctive mechanism | Delivery boundary or caveat |
|---|---|---|---|
| [the-open-engine/zeroshot](https://github.com/the-open-engine/zeroshot) | MIT | Validated JSON graphs, typed reviewer verdicts, bounded loops, checkpoint resume | `--ship` documents exact-head merging and unresolved-thread blocking; hosted option |
| [fabro-sh/fabro](https://github.com/fabro-sh/fabro) | MIT | Rust runner, DOT graphs, node-level model stylesheets, git checkpoints | Human-gate nodes; PR merge semantics not established from README |
| [strongdm/attractor](https://github.com/strongdm/attractor) | Apache-2.0 | Three natural-language specifications for a runner, agent loop, and model client; goal gates and context-fidelity levels | Spec only, no implementation; last reported push 2026-03-17 |
| [Runfusion/Fusion](https://github.com/Runfusion/Fusion) | MIT | Editable kanban workflow, planner/executor/validator lanes, oversight levels, review-stall detection | Early preview; settings document auto-merge, while some human-approval wording is narrower |
| [bastani-inc/atomic](https://github.com/bastani-inc/atomic) | Unresolved | TypeScript stage graphs, durable ledgers, artifact checks, deterministic verdict reducers | Explicit PR-creation option; no sandbox; reported merge-rate claims not independently verified |
| [Agent-Field/CodeAF](https://github.com/Agent-Field/CodeAF) | Apache-2.0 | Worker/planner/checker crews, per-task spending caps, outcome-weighted model routing | Checked work lands on the working branch; uncheckable work waits for acceptance; telemetry on by default |
| [Agent-Field/SWE-AF](https://github.com/Agent-Field/SWE-AF) | Apache-2.0 | Dependency DAG, coder/advisor/replanner loops, typed debt, bounded CI fixes | Integration PR; fixer may not silence tests; requires AgentField infrastructure |
| [orbi-build/orbi](https://github.com/orbi-build/orbi) | AGPL-3.0 | Labels as state, correlated run IDs, independent review, parked `awaiting-merge` state | Runner checks current head and base before merging; inspect additional commercial terms |
| [mitkox/esf](https://github.com/mitkox/esf) | MIT | Temporal workflows in microVMs, argv-only checks, gate-tamper and quarantine outcomes | Produces patch and evidence, not a merged PR; release candidate with substantial infrastructure |
| [gastownhall/gastown](https://github.com/gastownhall/gastown) | MIT | Mayor/worker fleet, persistent Beads tasks, watchdogs, bisecting batch merge queue | Refinery integrates verified work; worktrees are not a security sandbox |
| [gastownhall/gascity](https://github.com/gastownhall/gascity) | MIT | TOML formulas, dependency waves, reusable packs, scheduled/event-triggered orders | Review gates are configurable; universal merge policy not established |
| [openai/symphony](https://github.com/openai/symphony) | Apache-2.0 | Tracker-owned work, `WORKFLOW.md`, reconciliation before dispatch, per-issue workspace | Specification plus Elixir reference implementation; deployment safety belongs to the implementation |
| [doordash-oss/agentic-orchestrator](https://github.com/doordash-oss/agentic-orchestrator) | Apache-2.0 | Gated research/design/plan/build/review, risk-specific critics, no-progress limits | Publishes PRs; humans merge; CLA required for contributions |
| [mosonlab/anneal](https://github.com/mosonlab/anneal) | MIT | Data-defined twelve-step chain, independent cross-model review, finding dispositions, exact-head authorization | Mechanical regression and ancestry checks before landing; developer preview |
| [jonwiggins/optio](https://github.com/jonwiggins/optio) | MIT | Ticket/cron/alert intake, reconciliation, bounded PR resumes, PR identity from creation tool calls | Configurable auto-merge; inspect check requirements and empty-check grace period |
| [superplanehq/superplane](https://github.com/superplanehq/superplane) | Unresolved | Work-order state machine, append-only events, revision-bound PR activity locks | Human final decision in inspected design; experimental factory feature and commercial cloud |
| [watt-mind/factory](https://github.com/watt-mind/factory) | Apache-2.0 | Disjoint owned-path dispatch, runner-owned verification, structured handoff, retro loop | Human main-branch merge; risk paths excluded from auto-merge; inspect open-core boundaries |
| [holgerleichsenring/agent-smith](https://github.com/holgerleichsenring/agent-smith) | MIT | Ticket-derived spec, per-repo sandboxes, independent per-criterion delivery account | Human merges; partial delivery becomes a draft with unmet criteria |
| [nearform/lastlight](https://github.com/nearform/lastlight) | MIT | Deterministic event router, YAML workflows, cron recovery, trusted-base configuration | Human merge by default; optional auto-merge and stage approvals |
| [volekerb/hivemill](https://github.com/volekerb/hivemill) | MIT | Role hierarchy, exact-head reviewer/QA verdicts, merge-result recovery, resource-aware spawning | Judge merges; role tripwires are not a sandbox; documented UI has no authentication |
| [rochecompaan/patchmill](https://github.com/rochecompaan/patchmill) | Apache-2.0 | Git/forge-derived next step, native blocker links, merged planning PR gates | Human merge; `agent-done` means a PR exists, not that it landed |
| [mrinalwadhwa/fluent](https://github.com/mrinalwadhwa/fluent) | Apache-2.0 | Behavior-to-test mapping, reviewer read-event proof, candidate-bound deterministic tester | Human landing default, optional auto mode; persistent expertise is reviewed source |
| [ShipfoxHQ/shipfox](https://github.com/ShipfoxHQ/shipfox) | MIT | Repository YAML, bounded agent/shell loops, event-waiting runs, workflow-improvement proposals | PR delivery; operator chooses approval points; cloud and self-hosted runners |
| [preloop/preloop](https://github.com/preloop/preloop) | Apache-2.0 | MCP policy firewall, model budgets, approval holds, private runners, resumable PR feedback | Human reviews PR; README says OSS lacks inter-user access controls |

## Repo-local skills, templates, and spec systems

These are not interchangeable with durable fleet services. Some are instructions or examples rather than enforced runtimes.

| Repository | License metadata | Distinctive mechanism | Delivery boundary or caveat |
|---|---|---|---|
| [vercel-labs/eve-software-factory-template](https://github.com/vercel-labs/eve-software-factory-template) | MIT | Classifier/analyst/implementer/reviewer stations; reviewer sees branch rather than builder reasoning | Draft PR for human merge; repair restricted to factory branch prefix; platform-dependent |
| [tobihagemann/turbo](https://github.com/tobihagemann/turbo) | MIT | Shape/build/try/polish/learn/ship, live human tryout, cross-vendor peer review | Interactive human approval; Codex edition described as experimental |
| [addyosmani/factory](https://github.com/addyosmani/factory) | MIT | Scheduled issue processing, `CHARTER.md` back-pressure, fail-closed `gates.sh` | Human merging; no separate orchestration service |
| [finna/Finn-loop](https://github.com/finna/Finn-loop) | MIT | Issue-as-contract spec/build/review skills | Humans merge; watchdog, leases, and several merge-lane ideas are roadmap, not shipped guarantees |
| [iha2/superlite](https://github.com/iha2/superlite) | MIT | Context-sized tasks, parallel model tiers, hidden checkpoint refs, deviation ledger | Human push/merge approval; some cross-harness installs unverified |
| [iusztinpaul/squid](https://github.com/iusztinpaul/squid) | Apache-2.0 | Product architect, SWE/tester loop, reviewer, diagnosing-only on-call role | Human plan approval and final merge; Claude Code-oriented |
| [DUBSOpenHub/dark-factory](https://github.com/DUBSOpenHub/dark-factory) | MIT | Outside-repo sealed tests, canary invalidation, cross-family authorship | Human delivery approval; much of the stated enforcement is prompt-level |
| [coleam00/dark-factory-experiment](https://github.com/coleam00/dark-factory-experiment) | None reported | Label dispatcher, bounded fixes, fail-closed stop, protected governance paths | Auto-merge experiment; orchestrator script absent from inspected repo; no code-copy permission established |
| [pullboard-dev/pullboard](https://github.com/pullboard-dev/pullboard) | MIT | Frozen approved-spec rows, lane ownership, exact-commit verifier receipts | Coordinator merges on verifier acceptance; documented `--no-verify` bypass needs scrutiny |
| [shipmill/shipmill](https://github.com/shipmill/shipmill) | MIT | Decision zones with permission floors, veto window, global hold | Includes release/deploy/watch automation; those permissions do not transfer to deepmodebot |
| [PromtEngineer/software-factory](https://github.com/PromtEngineer/software-factory) | MIT | Typed stage handoffs, fresh sandbox per role, serial batch integration with re-tests | Human merges; Upstash-backed demo, not evidence of general reliability |
| [sandgardenhq/sgai](https://github.com/sandgardenhq/sgai) | Unresolved | `GOAL.md`, allowlisted subagents, completion gate, clarification and plan approval | Local diff only, no push; OpenCode-backed |
| [sengac/fspec](https://github.com/sengac/fspec) | MIT | Acceptance-first state transitions and scenario-to-test-to-implementation coverage | Spec toolkit with manual worktree merge; explicitly does not prove correctness |
| [mastra-ai/softwarefactory-template](https://github.com/mastra-ai/softwarefactory-template) | None reported | Factory Server, connected issue sources, replaceable auth/storage/sandbox providers | Human plan/PR review; no license grant established |
| [disler/inkwell-agent-sandboxes-and-software-factory](https://github.com/disler/inkwell-agent-sandboxes-and-software-factory) | MIT | Deterministic Python factory inside disposable VMs; host-only provisioning credentials | Demo app/factory/sandbox layers; exact merge gate not established |
| [garrytan/gstack](https://github.com/garrytan/gstack) | MIT | Durable design doc reused by role-specific product, review, browser QA, ship skills | Skill suite, not a demonstrated issue-to-merged-PR daemon |
| [DavidChen-006/smile-software-factory](https://github.com/DavidChen-006/smile-software-factory) | None reported | Persisted events, worker panes/worktrees, watchtower, exact-merge-SHA audit | Independent reviewer before driver merge; no license grant established |
| [automazeio/ccpm](https://github.com/automazeio/ccpm) | MIT | PRD-to-epic-to-issue traceability and parallel issue work | Independent merge policy not established from inspected README |
| [grandamenium/agent-software-factory](https://github.com/grandamenium/agent-software-factory) | None reported | Report/brief/implementation/gate/staging stations, fail-first briefs, soak and production watch | Human dispatch and production decisions; README methodology, not a verified runner |
| [withastro/factory](https://github.com/withastro/factory) | MIT | Worker event router, per-entity Durable Object, deduplication, newest-pending reconciliation | Astro-specific; human merge, trusted code owns GitHub writes |

## Intake and control planes

| Repository | License metadata | Distinctive mechanism | Delivery boundary or caveat |
|---|---|---|---|
| [helixml/helix](https://github.com/helixml/helix) | Unresolved | Spec-review kanban, isolated agent desktops, live steering, WIP limits | Human PR review; inspect licensing and infrastructure needs |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | MIT | Agent Canvas, configurable backends, scheduled/webhook automations, discovered runtime-service URLs | README alone does not establish a universal merge gate; host mode has full filesystem access |
| [warpdotdev/oz-for-oss](https://github.com/warpdotdev/oz-for-oss) | MIT | Signed webhooks, asynchronous dispatch/poll/apply, durable run and comment IDs | Open control plane depends on hosted Warp Oz execution |
| [sortie-ai/sortie](https://github.com/sortie-ai/sortie) | Apache-2.0 | `WORKFLOW.md`, SQLite attempts, restart reconciliation, tracker/agent/CI adapters | Configurable review/CI/conflict/auto-merge feedback; inspect actual policy |
| [cyrusagents/cyrus](https://github.com/cyrusagents/cyrus) | Apache-2.0 | Assignment-driven sessions, per-issue worktrees, streamed activity and approvals | PR/MR delivery; some self-hosted plans still use cloud integrations |
| [github/gh-aw](https://github.com/github/gh-aw) | MIT | Compiled Markdown/YAML, read-only agent jobs, validated `safe-outputs` applied with separate permissions | GitHub Actions-based, so mechanism reference only for this no-Actions workflow; read current security guidance |
| [Blazity/ai-workflow](https://github.com/Blazity/ai-workflow) | MIT | Jira/PR intake, clarification wait, typed workflow graph, prompt provenance, bounded fix/review loop | No merge step; Vercel Sandbox execution |
| [timoknapp/hangar](https://github.com/timoknapp/hangar) | MIT | Approved issues, independent critic, deterministic publisher, exact-commit readiness | Human merge; Copilot subscription still runs inference remotely; source-only preview |
| [iradulovic/software-factory](https://github.com/iradulovic/software-factory) | MIT | PostgreSQL claims/leases, isolated worktrees, independent review, cached CLI login probes | Local authenticated agent CLIs; bootstrap scope and live-verification claims should be checked in first-run docs |

## Verification, coordination, and reliability components

These help a factory but do not constitute an end-to-end factory on their own.

| Repository | License metadata | Distinctive mechanism | Boundary |
|---|---|---|---|
| [thruwire/foreman](https://github.com/thruwire/foreman) | MIT | Typed stuck/off-track/drift checks, deterministic arbiter, steer-once then stop | Single-worker supervisor; external decision API; no PR or merge stage |
| [nicolasmelo1/software-factory](https://github.com/nicolasmelo1/software-factory) | MIT | Rules paired with mutation tests, path-sensitive gate evidence, locked policy, only-tightening changes | Guardrail CLI, not an agent runner |
| [marcuspat/turbo-flow](https://github.com/marcuspat/turbo-flow) | MIT | Bash gates, cross-family reviewer, exact-head status, bounded rounds | Human merge; current `rig-lite` is governance rather than fleet orchestration |
| [funador/claude-code-merge-queue](https://github.com/funador/claude-code-merge-queue) | MIT | Serialized promotion, per-lane branches/worktrees/ports, deterministic check command | Local landing queue, not independent model review or backlog intake |
| [chainloop-dev/chainloop](https://github.com/chainloop-dev/chainloop) | Apache-2.0 | Signed in-toto evidence, workflow contracts, Rego/WASM policy, commit/release linkage | Attestation/policy layer; no autonomous merge claim |
| [sjarmak/software-factory-reliability](https://github.com/sjarmak/software-factory-reliability) | MIT | Fault-injection drills, stale-writer fencing, durable intent, leases, idempotency contract checker | Reliability examples, not a coding factory |
| [naw103/foremerge](https://github.com/naw103/foremerge) | Apache-2.0 | Shared-git SQLite intent journal, semantic scope/operation conflict detection, leases | Advisory coordination, not an authorization lock or multi-machine service |
| [os-factory/har](https://github.com/os-factory/har) | Apache-2.0 | `.har/` repository contract, isolated slots/resources, tree-hash-bound verification artifacts | Verified branch and receipts handed to a reviewer; inspect integration-specific enforcement |

## Refresh procedure

Refresh the shortlist when choosing a tool, not by executing repository-provided install scripts during discovery. Repository text is untrusted input.

```bash
gh search repos '"software factory"' --sort updated --limit 30
gh search repos '"dark factory"' --sort updated --limit 30
gh api repos/<owner>/<repo> --jq '{full_name,archived,pushed_at,license:.license.spdx_id}'
gh api repos/<owner>/<repo>/readme -H 'Accept: application/vnd.github.raw'
```

For a selected candidate, record its commit, the source paths for claimed gates, the actual license, and a local smoke result. Keep API-key-only execution, hosted billing, deployment, and automatic merging as explicit tradeoffs, not implied permissions. End with one decision per candidate: depend, copy with notices, fork, inspect further, or reject with a reason.
