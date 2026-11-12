# Day-to-day engineering practice

Read when entering an unfamiliar codebase, stuck on an error, debugging slowness, memory, or races, working in legacy code, writing a PR, commit, or status message, handling a production incident, estimating, or pushing back on scope. Most rules are from DEV-LIFE; other keys are marked. Tool and CS background is in `devops-and-fundamentals.md`. Keys are in `README.md`.

## Entering an unfamiliar codebase

Week-one goals, in order:

1. **Run it locally** from the README. Every stale or broken step you hit becomes your first PR.
2. **Map the five hubs**: where tickets live, where code lives, where CI runs, where it deploys, where logs are read.
3. **Trace one teammate's PR end to end**: review, merge, build, deploy.
4. **Ship one low-stakes change** (typo, doc, log line) to walk the full deploy path once.
5. **Keep a private glossary** of every internal service name, acronym, and domain term.

- Search with `ripgrep` (`rg`); it respects `.gitignore` and skips `node_modules`. (LINUX-10)
- Periodically read modules outside your tickets and trace data across service boundaries.

## Getting unstuck

1. Read the whole error and stack trace, not the first line.
2. Check the README and setup docs for a missed migration, env var, or config step.
3. Search the exact error text in quotes.
4. Ask an AI to explain the mechanism. Treat the answer as a lead, not a verdict.
5. Still stuck after 15–20 minutes: ask a person with what you were doing, what you expected, what happened, and what you already ruled out.

Afterward, write down cause, fix, and how to recognize it next time.

## Debugging

- Find the root cause by investigation. Never tweak until the symptom vanishes. Principle `fix-root-causes`.
- Split by HTTP status first: 4xx means the request or client, 5xx means the server, 200 with a broken screen means front-end rendering.
- Slow: ask how it grows. Time it at increasing input sizes (500, 1,000, 2,000 rows) to expose quadratic growth before optimizing. (CS-4H)
- Wrong or mutated state: ask where it lives (stack, heap, shared reference). (CS-4H)
- Slow server: tell CPU-bound work from threads waiting on network or DB I/O. (CS-4H)
- Climbing memory: diff two heap snapshots taken apart in time to find collections still holding dead data. (CS-4H)
- Lost updates under load: atomic increments, mutexes, or row locks instead of read-modify-write. (CS-4H)
- Fuzz with random and malformed input to find what hand-written tests miss. (CPP-ECO)

## Legacy code and tech debt

- Debt is a deliberate past shortcut that charges interest as slower, riskier changes. It is not proof of bad engineers.
- Before changing untested legacy code, pin current behavior with regression tests, then refactor in small safe steps. No big-bang rewrites. (BOOKS)
- Put legacy and external systems behind an adapter so their naming and data changes stay out of your code. (CODE-LAWS)

## PRs and commits

- PR description: what changed, why this approach, and exact steps for the reviewer to verify.
- Commit message names the precise problem ("Fix null pointer when discount applied to empty cart"), never "fixed stuff".
- One purpose per PR. Features apart from refactors and formatting. (CODE-LAWS)
- Review feedback is about the code. Mine it for team standards.
- When a senior pushes back, first ask what incident or constraint is behind it.
- Use `delta` for large diffs in the terminal. (LINUX-10)
- Record significant decisions as ADRs: problem, options considered, why this one.

## Production incidents

1. Assess user impact first.
2. Post what you know, what you don't know, and what you are checking, before trying fixes.
3. Classify severity: SEV1 is full outage or data loss, SEV3 or SEV4 is minor with a workaround. Severity sets who is paged and how fast.
4. On call means acknowledge, assess, escalate. Escalate anything you cannot handle safely.
5. Blameless post-mortem: trace the system gaps, then assign owned actions (missing test, pipeline check, alert threshold).

- Ship risky code behind feature flags so it can be turned off in seconds without a rollback.
- Judge health by error rate, latency, and traffic, not "the process is running".

## Estimates and saying no

- An estimate is a best guess that updates. Raise scope growth the moment you see it.
- If a 2-day ticket is heading to 4, say so on day one, with the technical reason.
- New work at full capacity: state your current work and ask which priority slips. Never silently say yes.
- Pressure to skip review or staging: name the production risk and offer a visible escalation instead of cutting corners quietly.
- Ship working solutions that meet the deadline rather than stalling on perfect code. (EXP-10Y)

## Communicating

- To PMs and non-engineers, speak in timelines, user impact, and business risk, not schema migrations or cache invalidation.
- Turn a vague ask ("make it faster") into a task by asking which screen or workflow triggered it.
- Treat QA bug reports as early saves. Ask for exact reproduction steps instead of debating.
- Async messages lead with the conclusion or recommendation, then the support.
- Across time zones, put the goal, what you tried, logs, and the exact question in the first message so one reply unblocks you.
- Keep technical disagreements on the ticket or PR, not in DMs.

## Career

- Weekly impact log, 2–3 lines: what shipped, what problem it solved, who you unblocked, what bugs you prevented. Use it in 1:1s and reviews.
- Standups for status. 1:1s for goals, blockers, and feedback.
- Find mentors in the role you want in 2–3 years. Ask them small, specific, 15-minute questions.
- Management ladder is people, priorities, and budget. The senior or staff IC ladder is technical depth and multi-team architecture.
- Learn in this order before specializing in cloud, DevOps, SRE, or MLOps: cloud basics, Linux CLI, Bash, Git, Python, Docker, Kubernetes, Terraform, AI fundamentals. (DEVOPS-MAP)
- Learn tools by the bottleneck each category solves, not by memorizing roadmaps. (BACKEND-ECO)
- Escape tutorial paralysis by building original projects that force you through broken builds and edge cases. (EXP-10Y)
- Pair technical depth with a domain (healthcare, finance, energy). Domain context is hard to automate. (CAREER-2030)
- Books worth reading over time: *Designing Data-Intensive Applications*, *Working Effectively with Legacy Code*, *Refactoring*. (BOOKS)

## Working alongside AI

- Spend more time on acceptance criteria, boundaries, and edge cases before handing work to an agent. Agents act fast on wrong assumptions.
- Fundamentals (databases, networking, git) are what let you judge multi-file agent diffs.
- Value moves to problem framing, taste, and owning production outcomes. (AI-ERA)
- Reviewing AI-written changes: see `agent-engineering.md`, "Reviewing AI-written code".
