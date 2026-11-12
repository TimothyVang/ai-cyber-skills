<!-- Template from the deep-mode project-brief skill. Replace every {{...}} and delete every guidance comment. Drop a section only if nothing true can be said in it. -->

# {{PROJECT_NAME}}: project brief

Start here if you're new to this repo, human or agent. It says what the project is, how it's built, how to run and prove a change, what not to do, and where help is wanted. `/deep-mode:contribute` reads this file first.

Last refreshed: {{YYYY-MM-DD}} against commit `{{SHORT_SHA}}`.

## What and why

<!-- Two to four sentences: what the project does and the problem it solves. Plain words; no marketing. -->

{{WHAT_AND_WHY}}

## Who it's for

<!-- The real users and what they need from it. Name the one workflow that must never break. -->

{{USERS}}

## Status

<!-- Maturity (prototype, beta, production), what works today, what's known broken, and where it's headed next. Link the roadmap. -->

{{STATUS}}

Open work lives in GitHub Issues labeled `help wanted`; [ROADMAP.md](../ROADMAP.md) is generated from them.

## Architecture map

<!-- One row per top-level area that a contributor might touch. Responsibility in one line. Entry point = the file to read first. -->

| Path | Responsibility | Entry point |
|---|---|---|
| `{{dir/}}` | {{what it owns}} | `{{file}}` |

<!-- Then two or three sentences on how data or requests flow between these areas. -->

{{DATA_FLOW}}

## Stack

<!-- Language, framework, storage, deploy target, key libraries. Link STACK.md if it exists and don't repeat it. -->

{{STACK}}

## Run and verify

<!-- Exact commands, each one run by the brief's author, with the observed result. Mark any you couldn't run as "unverified: <reason>". -->

Setup:

```bash
{{SETUP_COMMANDS}}
```

Run:

```bash
{{RUN_COMMANDS}}
```

Test and check (run these before every PR; there is no CI):

```bash
{{TEST_COMMANDS}}
```

Prove a change on the real app:

<!-- If the repo has .omp/skills/verify-<app>/ (or .claude/skills/verify-<app>/), name it and its main commands. Otherwise give the manual steps that show a feature working. -->

{{VERIFY_PATH}}

## Conventions

<!-- Only conventions a newcomer would get wrong: naming, layout, error handling, commit and branch naming, formatting tools. Link config files rather than restating them. -->

- {{CONVENTION}}

## Constraints and don'ts

<!-- Hard rules from the maintainer. Examples: no real customer data in tests or fixtures; no telemetry or network calls leaving the local network; don't touch generated files; license limits on dependencies; files that need a named reviewer. -->

- {{CONSTRAINT}}

## Where help is wanted

<!-- The areas most in need, and the kinds of skills that fit. The issue list is the source of truth for specific tasks. -->

{{HELP_WANTED_AREAS}}

- All claimable tasks: issues labeled [`help wanted`]({{REPO_URL}}/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
- Small starter tasks: [`good first issue`]({{REPO_URL}}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

## How to contribute

Install the deep-mode plugin and run `/deep-mode:contribute` in a clone of this repo. Your agent reads this brief, picks an unclaimed task that doesn't overlap open PRs or other claims, claims it after you say yes, and builds and proves it before opening a PR. Full rules, including how to do it without an agent: [CONTRIBUTING.md](../CONTRIBUTING.md).
