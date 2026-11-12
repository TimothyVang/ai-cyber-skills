# Technology-decision rules

These rules describe how to pick technology. They were distilled from 2024 to 2026 public talks on building software with agents. `any-app-stack.md` cites them by ID, and its step 4 scores candidates against them. The concrete web defaults live in `stack.md`.

How to use:
- Each rule gives an imperative, the date of its source, and an "Applies to any app as:" line. That line is how an agent applies the rule outside web work.
- When sources disagree, the newest one wins. Older positions go in [Reversals](#reversals).
- The rules came from web and SaaS work. Applying them to other kinds of app is inference. Label any pick derived this way **inferred**, never "default pick".
- Discount any endorsement that came from a sponsored segment or a vendor relationship (see [Bias to correct for](#bias-to-correct-for)).

## Choosing tools

**P1. Judge a stack by how fast it ships an outcome customers want, not by the tech.**
- Source date: 2024-02-12.
- Applies to any app as: for a CLI, desktop app or pipeline, pick the option that gets a working end-to-end slice to its real user fastest.

**P2. Buy what's already solved (auth, rate limits, integrations, hard platform plumbing) and spend your time on business logic.**
- Source date: 2024-02-19.
- Applies to any app as: use an existing library or service for parsing, crypto, packaging, signing or OAuth. Write only the code that makes your app different.

**P3. Use the highest managed abstraction you're allowed to use, and drop to a lower level only where it's required.**
- Source date: 2024-03-13.
- Applies to any app as: prefer a batteries-included framework, a managed DB or a hosted queue over hand-rolled plumbing. Go lower only for the one job the abstraction can't do.

**P4. Constraints override: in a restricted environment, "managed" means the highest-level abstraction the constraints allow.** [INFERENCE: generalized from the managed-services rule.]
- Source date: 2024-04-19.
- Applies to any app as: on-prem, air-gapped, accredited or no-SaaS → pick a self-hostable product that removes the most plumbing. Examples: an embedded DB like SQLite over hand-rolled files, a packaged identity server over custom auth, a framework over raw sockets. Record the constraint that forced the choice.

**P5. Pick the stack for who the customer is. Enterprise buyers mean proven, compliant tools over novel ones.**
- Source date: 2025-11-03.
- Applies to any app as: for regulated, government or security buyers, pick tools that already hold the needed certifications or accreditations, and use them rather than becoming an expert in the standards yourself.

**P6. Pick the tool you know, then check that it scales and that successful companies run it.**
- Source date: 2026-07-02.
- Applies to any app as: choose a CLI or service language the team (and the agents) already write well, as long as it's proven at the scale you need.

**P7. Prefer tools that hand you code you own, while other people maintain the base.**
- Source date: 2026-03-13.
- Applies to any app as: prefer vendored or open-source components you can read and patch over closed black-box SDKs.

**P8. Don't ship production on beta, release-candidate or experimental tech. Learning with it is fine.**
- Source date: 2026-01-23.
- Applies to any app as: pin stable releases of runtimes, drivers and frameworks. Keep pre-1.0 tools to spikes.

**P9. Drop tools that are unstable or unmaintained, even popular ones. Prefer open source so a vendor can't abandon you.**
- Source date: 2026-09-11.
- Applies to any app as: check release cadence, breaking-change history and licence before adopting a dependency. Replace one that churns.

**P10. Prefer one primitive that replaces several tools.**
- Source date: 2024-11-26.
- Applies to any app as: a single runtime, a single-binary tool or a single store that covers several layers beats wiring four separate parts.

**P11. Pick the middle of the control spectrum: full control over your logic, with no low-level plumbing.**
- Source date: 2026-09-11.
- Applies to any app as: pick an agent, GUI or CLI framework that owns transport, streaming and packaging but leaves product logic to you.

**P12. Test lock-in claims yourself instead of trusting the discourse.**
- Source date: 2026-09-11.
- Applies to any app as: before rejecting a tool as "lock-in", spike it on a second target. If you can't, record the cost of leaving.

**P13. Within one ecosystem, commit to the whole set.**
- Source date: 2026-10-01.
- Applies to any app as: on a platform such as AWS, a cluster or an embedded vendor SDK, use its native storage, queue and secrets together rather than mixing in outside pieces.

**P14. Don't marry one tool. Cycle through options and go where the value is.**
- Source date: 2026-03-27.
- Applies to any app as: keep model, harness and vendor choices swappable behind config. Re-evaluate them every quarter.

**P15. For tools you live in every day, feel and aesthetics count.**
- Source date: 2025-06-20.
- Applies to any app as: for developer tools such as a terminal, TUI or editor plugin, UX quality is a valid tiebreaker.

## Agents and AI as the builder

**P16. Prefer tools agents already know well and that are configured as code.**
- Source date: 2025-04-28.
- Applies to any app as: prefer mainstream languages and libraries with config-as-code (TOML, YAML, code) over GUI-configured tools that agents can't read.

**P17. Prefer end-to-end type safety, because it is the agent's feedback loop.**
- Source date: 2026-01-16.
- Applies to any app as: pick statically typed languages and typed boundaries (schemas, generated clients) so the compiler catches agent mistakes. Examples: Rust or Go for a CLI, typed IPC for desktop.

**P18. Give the agent real source and docs, not its memory. The codebase is the best context.**
- Source date: 2026-04-03.
- Applies to any app as: vendor or fetch the source of key dependencies (`npx opensrc`, the official repo) before an agent integrates them, whatever the language.

**P19. A language with less training data is fine if the code and a skill file supply the context.**
- Source date: 2026-03-24.
- Applies to any app as: a niche language or DSL is acceptable when you provide examples, source and a skill. It still counts against the language when no such context exists.

**P20. Prefer file-based conventions an agent can read.**
- Source date: 2026-09-11.
- Applies to any app as: prefer file-routed commands, declarative pipelines and checked-in infra definitions over runtime registration that is hidden in code paths.

**P21. The plan and the environment around the model decide quality.**
- Source date: 2026-01-16.
- Applies to any app as: invest in tests, linters, typed builds and a clear PRD for any project type before scaling agent work.

**P22. Loop agents only when there's a clear, automatic success check.**
- Source date: 2026-07-09.
- Applies to any app as: pick tools that give fast, machine-checkable signals. Examples: a test runner, golden files for a CLI, eval sets for ML.

**P23. Run one worktree and one branch per agent, and keep PRs small.**
- Source date: 2026-05-22.
- Applies to any app as: prefer a monorepo layout and a build that lets parallel agents work in isolation and merge small diffs.

**P24. Choose models per task by your own tests and price, not benchmarks.**
- Source date: 2026-02-06.
- Applies to any app as: for an AI feature in any app, run your own small eval on real inputs, then pick the cheapest model that passes. Production can use a cheaper model than development.

**P25. Prefer controllable, open-weight intelligence where you depend on it.**
- Source date: 2026-09-06.
- Applies to any app as: for offline, private or security work, prefer local open-weight models over hosted APIs. Coding models still need to be large to be useful.

**P26. Vibe-code v1 for clarity, then build v2 deliberately on the real stack. Know exactly how serious code works.**
- Source date: 2025-10-24.
- Applies to any app as: throwaway spikes can use any stack. The production rewrite follows these rules and gets human understanding of its high-stakes paths.

**P27. Review evidence and signatures, and keep your own skill as the fallback.**
- Source date: 2026-07-09.
- Applies to any app as: pick stacks whose interfaces are readable by a human, so reviewing at the signature level is meaningful.

**P28. Build only the product and its harness. Buy the agent core.**
- Source date: 2026-05-05.
- Applies to any app as: in an AI agent app, adopt an existing agent framework and tool layer, and spend effort on domain tools and evaluation.

## Architecture and security

**P29. Treat every server-callable function as a public endpoint, and authorize inside it.**
- Source date: 2024-10-28.
- Applies to any app as: every IPC handler, RPC method, MCP tool or plugin hook validates and authorizes its own input.

**P30. Keep secrets and sensitive or expensive calls off the client. No client-to-data shortcuts.**
- Source date: 2025-04-28.
- Applies to any app as: desktop, mobile and CLI clients never embed DB credentials or privileged API keys. They go through a service layer, or keep secrets in an OS keychain or vault.

**P31. Lock data down by default, and grant the least privilege needed.**
- Source date: 2024-09-18.
- Applies to any app as: use read-only credentials, scoped tokens and deny-by-default storage. Don't store user credentials you don't need.

**P32. Validate on the server as well as the client, and force structured output from LLMs.**
- Source date: 2025-02-24.
- Applies to any app as: validate at every trust boundary with a schema, including config files, CLI args, file imports and model output.

**P33. Isolate critical webhooks and payment flows from what users can reach. Verify signatures and log every event first.**
- Source date: 2025-04-28.
- Applies to any app as: any inbound event source (queues, sensors, webhooks) gets a durable raw log before processing, plus authenticity checks.

**P34. Move long-running or CPU-heavy work off the request path or UI thread.**
- Source date: 2025-04-25.
- Applies to any app as: use background workers or durable jobs for services, worker threads for desktop and mobile, and async pipelines for data work.

**P35. Use typed, explicit errors for every backend service.**
- Source date: 2026-10-01.
- Applies to any app as: pick a language or library with errors as values (Rust `Result`, Go errors, Effect) for any service or CLI.

**P36. Put a human gate on irreversible or high-stakes agent actions, and shrink the blast radius.**
- Source date: 2025-10-17.
- Applies to any app as: agents run in containers or sandboxes with their own accounts. Payments, sends and deletes need approval.

**P37. Deploy for compliance first, then latency.**
- Source date: 2025-01-09.
- Applies to any app as: choose regions, hosts and data residency to satisfy the regulation first, then place compute near users.

**P38. Self-host what you depend on, on hardware you control, when uptime and privacy matter.**
- Source date: 2026-02-12.
- Applies to any app as: long-running agents, home and lab services, and sensitive pipelines run on owned hardware. A cheap VPS is fine for casual use.

**P39. Pen-test yourself on a schedule.**
- Source date: 2026-07-15.
- Applies to any app as: add scheduled automated security scans or agent audits to CI for any project type.

**P40. Let users own and export their data.**
- Source date: 2026-05-05.
- Applies to any app as: prefer open, portable storage formats and export paths over proprietary stores.

## Shipping and quality

**P41. Go scruffy first, and harden when real use demands it.**
- Source date: 2024-10-09.
- Applies to any app as: a single process with an embedded store is a fine v1. Split it into services only when load or ownership requires it.

**P42. "Slop" means it breaks at scale or costs too much, not that it doesn't work.**
- Source date: 2025-10-24.
- Applies to any app as: score candidates on how they behave under real load and on cost, not on whether the demo runs.

**P43. Prove the riskiest integrations first, and reproduce bugs before fixing them.**
- Source date: 2026-06-05.
- Applies to any app as: spike hardware, driver, platform-API and model integrations before building features on them.

**P44. Test in a sandbox before production.**
- Source date: 2025-06-06.
- Applies to any app as: use staging accounts, test networks and dry-run modes for anything touching money, devices or external systems.

**P45. Polish and care are the moat, because code is cheap to copy.**
- Source date: 2026-10-16.
- Applies to any app as: prefer tools that let you finish UX details, such as native-feel desktop toolkits or good TUI libraries, over ones that cap quality.

**P46. Build something you'll use, for real non-developer users, and finish it.**
- Source date: 2025-11-25.
- Applies to any app as: cut setup friction for the end user, for example one key instead of three, an installer instead of build steps, sensible defaults.

**P47. Keep one reusable starter or template that every project feeds back into.**
- Source date: 2024-05-27.
- Applies to any app as: keep a per-type template (CLI, service, agent) with features behind config flags.

## Cost and scale

**P48. Spend for reliability and speed early. Optimize cost later.**
- Source date: 2026-07-02.
- Applies to any app as: accept paid tools that buy speed or reliability. Revisit them when the bill matters.

**P49. Price a tool by its total cost, not the headline free tier.**
- Source date: 2025-02-24.
- Applies to any app as: add the hidden dependencies, such as email, egress, licences, ops time and model tokens, before comparing options.

**P50. Pay a bit more for much better developer experience.**
- Source date: 2025-04-07.
- Applies to any app as: a slightly costlier SDK, host or runtime wins if it removes a class of bugs or plumbing.

**P51. Pick billing and pricing tools by the pricing model.**
- Source date: 2026-07-02.
- Applies to any app as: for licensing in desktop or CLI apps, choose by model (seat, usage, one-off) rather than by brand.

**P52. Don't switch architecture for small gains.**
- Source date: 2026-09-06.
- Applies to any app as: migrate only when the measured gain beats the risk of a new class of bugs.

**P53. Split services partly by who will own them.**
- Source date: 2026-07-02.
- Applies to any app as: draw service and package boundaries where a future owner or team would sit, not by layer for its own sake.

## Evolving the stack

**P54. If it works, don't swap it for something new.**
- Source date: 2024-10-28.
- Applies to any app as: an existing project's stack wins. Change one layer at a time, with a stated reason.

**P55. Install only the plugins and integrations you actually use. Add agent tools one at a time.**
- Source date: 2026-02-12.
- Applies to any app as: keep the dependency and tool lists minimal, and add each one when a task proves the need.

**P56. Turn every process that works into a skill, after walking it by hand.**
- Source date: 2026-02-20.
- Applies to any app as: codify the build, release and debug loops for any project as checked-in skills or scripts.

**P57. Kill features that fight a vendor's limits rather than bending the stack.**
- Source date: 2026-02-25.
- Applies to any app as: if a chosen tool can't do a feature cleanly, drop the feature or replace the tool. Don't build a fragile workaround.

## Bias to correct for

- Some sources had a commercial tie to Convex, Orgo, or Tempo Labs. Treat praise of those products as interested praise, and confirm it with your own prototype.
- Ignore tools that appeared only in sponsored segments. Weigh lightly tools that were both sponsors and independently praised.
- The sources lean toward Next.js and Vercel. Check that lean against the app's real constraints.

## Reversals

| Was | Date | Now | Date |
|---|---|---|---|
| Next.js as the whole backend | 2024-02-12 | Separate server for payments and core work | 2024-04-01 |
| Server actions for data fetching | 2024-06-06 | Fetch in server components; actions for mutations | 2024-07-12 |
| Supabase + Prisma | 2024-09-18 | Neon + Drizzle (free tier), then PlanetScale Postgres (stack.md §4) | 2024-10-02 / 2026-07-02 |
| Stripe for payments | 2024-10-15 | Polar for DX; Stripe for plain subscriptions, Autumn for credits | 2025-02-11 / 2026-07-02 |
| Bun package manager | 2024-11-26 | pnpm | 2025-03-18 |
| Next.js for everything | 2025-11-03 | SvelteKit (compiled, snappy) | 2026-03-24 |
| Clerk as default auth | 2026-01-23 | WorkOS default; Better Auth when you need ownership | 2026-03-13 |
| Claude Code as the best agent | 2025-06-06 | Cursor, then T3 Code; Claude CLI over SSH | 2025-10-17 / 2026-10-21 |
| Gemini models as the lead pick | 2025-11-25 | Avoid Gemini models for agent work | 2026-02-12 |
| Codex/GPT best value | 2026-07-24 | Opus 5.5 main model | 2026-10-01 |
| OpenClaw as agent core | 2026-05-05 | Eve [caption?], a lighter agent core | 2026-09-11 |
| Daytona agent computers | 2026-05-22 | Orgo | 2026-10-01 |
| Ghostty terminal | 2026-01-23 | cmux [caption?], then Ghostty plus a multiplexer | 2026-03-13 / 2026-08-19 |
| "models not trained on it" rules TanStack out | 2026-01-23 | Training data waived given code plus a skill (Svelte) | 2026-03-24 |
| Custom agent-loop CLIs are essential | 2026-01-16 | Native harness loops replace them | 2026-03-07 |

## Known non-web picks

| Language / tool | Job | Citation |
|---|---|---|
| Python + Flask | AI research/plan/write pipeline and job queueing | 2024-05-09 |
| Bun + Elysia (+ Eden) | Standalone typed backend servers | 2024-03-04; 2026-01-23 |
| Hono on Cloudflare Workers + Drizzle + Neon | Standalone API backend | 2024-10-02; 2024-12-10 |
| Effect (TypeScript) | Every backend service, including an MCP server | 2026-10-01 |
| Railway | Hosting separate servers | 2026-01-23; 2026-08-19 |
| Expo + React Native (SwiftUI only if iOS-only) | Mobile | 2025-11-10; 2026-07-02 |
| Electron (wraps the site) | Desktop app | 2026-07-02 |
| Rust | Native-feel desktop clones; single sync server for hardware | 2026-10-16; 2026-11-06 |
| Bash script → npm CLI with YAML config (Ralphy) | Agent-loop CLI | 2026-01-20 |
| Express + JSON file on Fly.io, Vapi, ElevenLabs, Twilio | Voice agent | 2025-12-09 |
| Vercel AI SDK, Claude Agent SDK, Composio, Daytona | Agent SDKs, tools, sandboxes | 2026-01-23 |
| Supermemory, AgentMail, Plaid, Mistral OCR, OpenRouter, Caddy | Agent service dependencies | 2026-05-05; 2026-07-02 |
| Braintrust / Axiom / Sentry | Agent observability | 2026-07-02 |
| Linux mini PC, Tailscale, Synology NAS, UPS | Agent runtime machine | 2026-08-19 |
| Nightly traces → NAS, fine-tunes on rented H100s | ML / fine-tuning | 2026-10-29 |
| REA (Ghidra, Hopper, IDA over MCP) | Reverse engineering for agents | 2026-10-16 |
| Abliterated DeepSeek via Morph LLM | Pen-testing your own devices | 2026-11-02 |
| 1Password | Environment variable secrets | 2026-08-14 |
| AdGuard Home (agent-managed) | Home network | 2026-10-29 |
| Raspberry Pi, ReSpeaker, Blender via Codex, 3D printing | Hardware prototype | 2026-11-06 |
| TradingView webhook → Convex; brokerage API; polygon.io | Fintech data and alerts | 2025-10-17; 2026-01-23 |
| thirdweb, Crossmint, Privy, viem [caption?] | Crypto wallets and Ethereum | 2025-11-12 |
| pass.js [caption?], ImageKit, R2 | Apple Wallet passes and images | 2025-08-28; 2026-03-13 |
| Web Workers | CPU-heavy parsing and inference in UI | 2025-04-25 |
| Cloudflare Tunnel / ngrok | Exposing local servers and webhooks | 2024-09-18; 2026-08-19 |
| Linear | Planning and issue tracking | 2026-07-09 |
