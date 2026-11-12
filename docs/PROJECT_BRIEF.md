# deep-mode: project brief

Start here if you're new to this repo, human or agent. `/deep-mode:contribute` reads this file first.

Last refreshed: 2026-11-12. The manifest and live issue board are authoritative for the current version and available work.

## What and why

deep-mode is an MIT plugin for coding agents. Its skills take a task from an idea through a spec, tickets, implementation, review and recorded proof. Its local GitHub App bot runs ACP agents on the user's subscriptions to discuss issues, fix and review the owner's PRs, and merge them through a verifier panel and a code-enforced gate.

The product is the agent's behavior, not only its Python scripts. A wording change can change that behavior and needs proof on a real task.

## Who it's for

- Developers using omp, Claude Code, Codex or another harness that loads skills.
- Repo owners who want their own PRs reviewed and landed, with evidence in the thread.
- Maintainers opening a project to contributors and people contributing with or without an agent.

The workflow that must never break is installing the plugin, running `/deep <task>`, and getting an observable result with proof.

## Status

Read `plugins/deep-mode/.claude-plugin/plugin.json` for the release version. Both marketplace manifests must agree with it. Do not copy a version number into this brief.

Run evidence lives in `evals/results/` and merged PR threads. A reseller must obtain its own deployment evidence. Contributor PRs receive review comments only; their code is not run by write-enabled agents, and a maintainer decides whether to merge.

Known gaps reserved for contributors:

- Actual macOS and Linux autostart runs (#38 and #39).
- The wizard library on macOS bash 3.2 (#40).
- Live git-guard hook exercises in omp and Claude Code (#41 and #42).
- Exact GitLab tracker commands (#43).
- Checker edge cases (#44) and additional overlap/path test coverage (#45).

`scripts/test_claims.py` already covers claim lifecycle, competing claims, expiry, assignee fallback and excluding only the caller's own claim. Do not duplicate that work.

[ROADMAP.md](../ROADMAP.md) is a snapshot. Read an issue, its claims and open PRs before claiming it. Issues without `help wanted` are not part of the contributor queue.

## Architecture map

| Path | Responsibility | Entry point |
|---|---|---|
| `plugins/deep-mode/skills/deep-mode/` | Main routing, autonomy and engineering workflows | `SKILL.md` |
| `references/playbooks/`, `references/techniques/`, `references/principles/` under the main skill | Task flows, reusable operations and decision rules | The path selected by `SKILL.md` |
| `plugins/deep-mode/skills/agent-harnesses/`, `software-architecture/`, `secrets-and-auth/`, `cloud-devsecops/`, `domain-rules/`, `frontend-ui/` | Cited domain references | Each skill's `SKILL.md` |
| `plugins/deep-mode/skills/deep-mode/assets/github-app/` | App identity, polling, ACP conversations, verification and merge gates | `bot.py`, `ghapp.py`, `install.py` |
| `plugins/deep-mode/skills/deep-mode/assets/pr-conversation/` | Text and 8-bit displays of real PR and issue threads | `show_thread.py`, `arena.py` |
| Other main-skill `assets/` folders | Containment, git guards, goal loops, wizards, security checks and media helpers | The script named by the technique |
| `plugins/deep-mode/skills/deep-mode/scripts/` | Skill validation and trending discovery | `check_skill.py`, `trending.py` |
| `plugins/deep-mode/skills/project-brief/`, `contribute/` | Maintainer and contributor workflows | `SKILL.md`, `assets/` |
| `plugins/deep-mode/skills/deep-stack/` and the verification skills | Stack choices and reusable app verification | `SKILL.md` |
| `plugins/deep-mode/commands/` | `deep`, `review-pr`, `land-pr`, `pr-thread`, `contribute`, `project-brief` | The corresponding command file |
| `brand/`, `scripts/whitelabel.py`, `scripts/media/` | Brand inputs, distribution builds and rendered media | `brand/brand.json`, `scripts/whitelabel.py` |
| `scripts/` | Repository gate, overlap checks, claim tests and roadmap generation | `check.py`, `pr-overlap.py`, `sync-roadmap.py` |
| `evals/` | Routing and outcome evaluations with committed results | `evals/README.md` |
| `trending/` | Generated repository catalog | `trending/README.md` |
| `docs/` | Published site, machine-readable documentation and images | `index.html`, `llms.txt` |
| `.omp-plugin/`, `.claude-plugin/` | Marketplace manifests | `marketplace.json` |

## Stack

Markdown holds the skills. Runtime scripts use the Python standard library; media generators also use Pillow, agg and gifski. Shell and TypeScript assets implement harness hooks. Git, gh, bash and acpx supply the command-line integrations. No hosted model service or model API key is required by the bot.

## Run and verify

Clone the repo, then keep all commands at its root:

```bash
gh repo clone TimothyVang/deep-mode
cd deep-mode
py -3 scripts/check.py
py -3 scripts/test_claims.py
py -3 scripts/pr-overlap.py claims --repo TimothyVang/deep-mode
py -3 scripts/sync-roadmap.py --repo TimothyVang/deep-mode --check
py -3 plugins/deep-mode/skills/deep-mode/assets/github-app/bot.py --help
```

Use `python3` instead of `py -3` on macOS and Linux. `check.py` runs the repository's checks and test directories. The individual claim test is useful while changing the contributor tools. The roadmap command checks the committed snapshot against live issues and may legitimately report drift.

Use [.omp/skills/verify-deep-mode/SKILL.md](../.omp/skills/verify-deep-mode/SKILL.md) for the evaluation CLIs. Run its doctor, read the matching feature map, and capture the real agent path in a disposable project under `.scratch/`. Follow [CONTRIBUTING.md](../CONTRIBUTING.md) and include actual outcomes in the PR. Structural checks and collector tests do not replace live execution.

For bot changes, preview a read-only cycle with `bot.py once --repo <owner/repo> --dry-run`. Do not use a live cycle to test an untrusted contributor's code.

## Conventions

- Keep prose short and factual. Completion criteria describe observable outcomes.
- Follow `CONTRIBUTING.md` for line limits, skill frontmatter, links and checks.
- Branch `<issue number>-<slug>` for claimed tasks. Use commit subjects such as `fix(github-app): ...`.
- Reuse existing scripts and helpers rather than adding a second convention.

## Constraints and don'ts

- Write only inside the project root. Put scratch files in `.scratch/` and worktrees in `.worktrees/`.
- Upstream attribution stays in `LICENSE` and `NOTICE.md`. Do not remove legally required notices.
- Follow each reference skill's source instructions before changing exported material.
- Do not hand-edit the generated `trending/` catalog.
- Never put secrets, tokens, credentials or private user data in documentation, tests or model prompts.
- Contributor tasks carry `discussion-only` so the autonomous bot does not implement them ahead of contributors.
- Check active claims and overlapping PRs before starting, and again before opening the PR. An overlap is a coordination problem, not a reason to overwrite another person's work.

## Where help is wanted

- Cross-platform verification: #38, #39, #40, #41 and #42.
- Tracker support: #43.
- Tooling and regression coverage: #44 and #45. Read their latest scope before starting; parts may already exist.

The live lists are [help wanted](https://github.com/TimothyVang/deep-mode/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) and [good first issue](https://github.com/TimothyVang/deep-mode/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## How to contribute

Install deep-mode and run `/deep-mode:contribute` in a clone. The agent reads this brief, finds unclaimed work, checks overlap, requests permission to claim and publish, builds the change, proves it and opens a PR. You can follow the same steps by hand. [CONTRIBUTING.md](../CONTRIBUTING.md) has the full claim and review rules.
