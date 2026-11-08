# Ras Mic's technology-decision philosophy

These rules distill how Ras Mic picks technology, taken from 166 video transcripts (2024-02 to 2026-11). `any-app-stack.md` cites them by ID, and its step 4 scores candidates against them. His concrete web picks live in `stack.md`.

How to use:
- Each rule gives an imperative, one short verbatim quote with `(date, "title")`, and an "Applies to any app as:" line. That line is how an agent applies the rule outside web work.
- Quotes come from auto-captions. Their spelling is kept, and garbled names are marked `[caption?]`.
- When videos disagree, the newest one wins. Older positions go in [Reversals](#reversals).
- He gave the rule. Applying it to non-web apps is our inference. Label any pick derived this way **inferred**, never "his pick".
- Discount anything said during an ad read (see [Disclosures and bias](#disclosures-and-bias)).

## Choosing tools

**P1. Judge a stack by how fast it ships an outcome customers want, not by the tech.**
- "customers care about outcome… I'm talking shipping in a day or two" (2024-02-12, "My Ultimate Tech Stack for 2024")
- Applies to any app as: for a CLI, desktop app or pipeline, pick the option that gets a working end-to-end slice to its real user fastest.

**P2. Buy what's already solved (auth, rate limits, integrations, hard platform plumbing) and spend your time on business logic.**
- "I don't believe in… wasting time… in things that have already been perfected and built for me" (2024-02-19, "Authentication with Clerk in NextJS 14")
- Applies to any app as: use an existing library or service for parsing, crypto, packaging, signing or OAuth. Write only the code that makes your app different.

**P3. Use the highest managed abstraction you're allowed to use, and drop to a lower level only where it's required.**
- "on 90% of my nextjs applications I am going with the server actions… the only time… is… a web hook" (2024-03-13, "NextJS APIs vs Server Actions")
- Applies to any app as: prefer a batteries-included framework, a managed DB or a hosted queue over hand-rolled plumbing. Go lower only for the one job the abstraction can't do.

**P4. Constraints override: in a restricted environment, "managed" means the highest-level abstraction the constraints allow.** [INFERENCE: this is our generalization, not his words.]
- Closest source: "I'm not for my own custom VPS… too much time" (2024-04-19, "How To Protect your Nextjs App from a DDOS")
- Applies to any app as: on-prem, air-gapped, accredited or no-SaaS → pick a self-hostable product that removes the most plumbing. Examples: an embedded DB like SQLite over hand-rolled files, a packaged identity server over custom auth, a framework over raw sockets. Record the constraint that forced the choice.

**P5. Pick the stack for who the customer is. Enterprise buyers mean proven, compliant tools over novel ones.**
- "You have to use a tech stack that's battle tested proven and compliant" (2025-11-03, "How I build compliant software")
- Applies to any app as: for regulated, government or security buyers, pick tools that already hold the needed certifications or accreditations, and use them rather than becoming an expert in the standards yourself.

**P6. Pick the tool you know, then check that it scales and that successful companies run it.**
- "it's important to pick the tool you're familiar with" (2026-07-02, "System Design Overview")
- Applies to any app as: choose a CLI or service language the team (and the agents) already write well, as long as it's proven at the scale you need.

**P7. Prefer tools that hand you code you own, while other people maintain the base.**
- "you have other people maintaining this code for you… All I have to do is npm install it" (2026-03-13, "I've changed how I build software")
- Applies to any app as: prefer vendored or open-source components you can read and patch over closed black-box SDKs.

**P8. Don't ship production on beta, release-candidate or experimental tech. Learning with it is fine.**
- "it's really difficult for me to ship something to production with something that's still in release candidate" (2026-01-23, "My 2026 Tech & Tool Stack")
- Applies to any app as: pin stable releases of runtimes, drivers and frameworks. Keep pre-1.0 tools to spikes.

**P9. Drop tools that are unstable or unmaintained, even popular ones. Prefer open source so a vendor can't abandon you.**
- "openclaw tends to break every update… it's just too clunky… not stable" (2026-09-11, "Tired of OpenClaw & Hermes")
- Applies to any app as: check release cadence, breaking-change history and licence before adopting a dependency. Replace one that churns.

**P10. Prefer one primitive that replaces several tools.**
- "with convic you don't need a DB provider you don't need tanack query you don't need an orm" (2024-11-26, "I built Whatsapp using Nextjs & Convex")
- Applies to any app as: a single runtime, a single-binary tool or a single store that covers several layers beats wiring four separate parts.

**P11. Pick the middle of the control spectrum: full control over your logic, with no low-level plumbing.**
- "it gives me full control… and it's not super bare bones" (2026-09-11, "Tired of OpenClaw & Hermes")
- Applies to any app as: pick an agent, GUI or CLI framework that owns transport, streaming and packaging but leaves product logic to you.

**P12. Test lock-in claims yourself instead of trusting the discourse.**
- "I wanted to see if I could host Eve on Convex and Eve on Cloudflare and both of them worked" (2026-09-11, "Tired of OpenClaw & Hermes")
- Applies to any app as: before rejecting a tool as "lock-in", spike it on a second target. If you can't, record the cost of leaving.

**P13. Within one ecosystem, commit to the whole set.**
- "if I'm ever using Cloudflare I'm probably using the entire stack" (2026-10-01, "Agentic Development Stack")
- Applies to any app as: on a platform such as AWS, a cluster or an embedded vendor SDK, use its native storage, queue and secrets together rather than mixing in outside pieces.

**P14. Don't marry one tool. Cycle through options and go where the value is.**
- "don't be married to one don't be a Claude Code Maxi" (2026-03-27, "…time to LOCK IN")
- Applies to any app as: keep model, harness and vendor choices swappable behind config. Re-evaluate them every quarter.

**P15. For tools you live in every day, feel and aesthetics count.**
- "if I'm not feeling the theme I actually can't work" (2025-06-20, "My new favourite browser")
- Applies to any app as: for developer tools such as a terminal, TUI or editor plugin, UX quality is a valid tiebreaker.

## Agents and AI as the builder

**P16. Prefer tools agents already know well and that are configured as code.**
- "Windsurf and Cursor they're actually very very good with Convex… I essentially experienced no hallucination" (2025-04-28, "I launched my first AI SAAS")
- Applies to any app as: prefer mainstream languages and libraries with config-as-code (TOML, YAML, code) over GUI-configured tools that agents can't read.

**P17. Prefer end-to-end type safety, because it is the agent's feedback loop.**
- "the benefits of TypeScript type safety comes in clutch" (2026-01-16, "Ralph Wiggum killed programming")
- Applies to any app as: pick statically typed languages and typed boundaries (schemas, generated clients) so the compiler catches agent mistakes. Examples: Rust or Go for a CLI, typed IPC for desktop.

**P18. Give the agent real source and docs, not its memory. The codebase is the best context.**
- "your codebase is the best piece of context" (2026-04-03, "Tool Made My Coding Agent Powerful")
- Applies to any app as: vendor or fetch the source of key dependencies (`npx opensrc`, the official repo) before an agent integrates them, whatever the language.

**P19. A language with less training data is fine if the code and a skill file supply the context.**
- "your code in it of itself is context… plus a skill file is enough" (2026-03-24, "I'm never going back")
- Applies to any app as: a niche language or DSL is acceptable when you provide examples, source and a skill. It still counts against the language when no such context exists.

**P20. Prefer file-based conventions an agent can read.**
- "they use the files to define the API just makes it so easy for… the agent itself" (2026-09-11, "Tired of OpenClaw & Hermes")
- Applies to any app as: prefer file-routed commands, declarative pipelines and checked-in infra definitions over runtime registration that is hidden in code paths.

**P21. The plan and the environment around the model decide quality.**
- "the tools surrounding the models which is in our control really determine whether the software is valuable" (2026-01-16, "Ralph Wiggum killed programming")
- Applies to any app as: invest in tests, linters, typed builds and a clear PRD for any project type before scaling agent work.

**P22. Loop agents only when there's a clear, automatic success check.**
- "the evaluation needs to be clear and cut" (2026-07-09, "I ship more than you")
- Applies to any app as: pick tools that give fast, machine-checkable signals. Examples: a test runner, golden files for a CLI, eval sets for ML.

**P23. Run one worktree and one branch per agent, and keep PRs small.**
- "the smaller the PR the more focused the PR the better your life is" (2026-05-22, "Agentic Engineering Workflow")
- Applies to any app as: prefer a monorepo layout and a build that lets parallel agents work in isolation and merge small diffs.

**P24. Choose models per task by your own tests and price, not benchmarks.**
- "I'm not a big fan of the benchmarks" (2026-02-06, "Is Opus 4.6 actually any good")
- Applies to any app as: for an AI feature in any app, run your own small eval on real inputs, then pick the cheapest model that passes. Production can use a cheaper model than development.

**P25. Prefer controllable, open-weight intelligence where you depend on it.**
- "I'm very much bullish on intelligence that is controlled by myself that's running on my own hardware" (2026-09-06, "GPT 6 Astra")
- Applies to any app as: for offline, private or security work, prefer local open-weight models over hosted APIs. Note that he says "coding models need to be big".

**P26. Vibe-code v1 for clarity, then build v2 deliberately on the real stack. Know exactly how serious code works.**
- "once I have clarity I'm going to rewrite the second version" (2025-10-24, "My NEW AI workflow will piss you off")
- Applies to any app as: throwaway spikes can use any stack. The production rewrite follows these rules and gets human understanding of its high-stakes paths.

**P27. Review evidence and signatures, and keep your own skill as the fallback.**
- "I might look at the function signatures… but I'm not reviewing the entire code" (2026-07-09, "I ship more than you")
- Applies to any app as: pick stacks whose interfaces are readable by a human, so reviewing at the signature level is meaningful.

**P28. Build only the product and its harness. Buy the agent core.**
- "I wanted to focus more on the product and the harness around the product" (2026-05-05, "launching a new app soon")
- Applies to any app as: in an AI agent app, adopt an existing agent framework and tool layer, and spend effort on domain tools and evaluation.

## Architecture and security

**P29. Treat every server-callable function as a public endpoint, and authorize inside it.**
- "you should still treat your server actions as public HTTP endpoints" (2024-10-28, "Nextjs 15 is here")
- Applies to any app as: every IPC handler, RPC method, MCP tool or plugin hook validates and authorizes its own input.

**P30. Keep secrets and sensitive or expensive calls off the client. No client-to-data shortcuts.**
- "my client cannot directly call this function" (2025-04-28, "I launched my first AI SAAS")
- Applies to any app as: desktop, mobile and CLI clients never embed DB credentials or privileged API keys. They go through a service layer, or keep secrets in an OS keychain or vault.

**P31. Lock data down by default, and grant the least privilege needed.**
- "I'm enabling Ro level security but adding no policies meaning no one can have access" (2024-09-18, "Setting Up My Nextjs Starter Kit")
- Applies to any app as: use read-only credentials, scoped tokens and deny-by-default storage. Don't store user credentials you don't need.

**P32. Validate on the server as well as the client, and force structured output from LLMs.**
- "it forces the AI model to give me the response exactly how I wanted" (2025-02-24, "I built my own AI friends")
- Applies to any app as: validate at every trust boundary with a schema, including config files, CLI args, file imports and model output.

**P33. Isolate critical webhooks and payment flows from what users can reach. Verify signatures and log every event first.**
- "first I store all the web hook events but then I track for specific events" (2025-04-28, "I launched my first AI SAAS")
- Applies to any app as: any inbound event source (queues, sensors, webhooks) gets a durable raw log before processing, plus authenticity checks.

**P34. Move long-running or CPU-heavy work off the request path or UI thread.**
- "if it's CPU heavy causes UI jank use a web worker" (2025-04-25, "Make Your React App Faster")
- Applies to any app as: use background workers or durable jobs for services, worker threads for desktop and mobile, and async pipelines for data work.

**P35. Use typed, explicit errors for every backend service.**
- "TypeScript… hasn't applied to errors" (2026-10-01, "Agentic Development Stack")
- Applies to any app as: pick a language or library with errors as values (Rust `Result`, Go errors, Effect) for any service or CLI.

**P36. Put a human gate on irreversible or high-stakes agent actions, and shrink the blast radius.**
- "I wouldn't trust AI with my money" (2025-10-17, "The Tech Stack for my new SAAS")
- Applies to any app as: agents run in containers or sandboxes with their own accounts. Payments, sends and deletes need approval.

**P37. Deploy for compliance first, then latency.**
- "compliance is everything cuz you can lose business with compliance" (2025-01-09, "How Big Companies Deploy Web Applications")
- Applies to any app as: choose regions, hosts and data residency to satisfy the regulation first, then place compute near users.

**P38. Self-host what you depend on, on hardware you control, when uptime and privacy matter.**
- "imagine the provider goes down… it's within their control" (2026-02-12, "I finally understand OpenClaw")
- Applies to any app as: long-running agents, home and lab services, and sensitive pipelines run on owned hardware. A cheap VPS is fine for casual use.

**P39. Pen-test yourself on a schedule.**
- "scans the codebase for any vulnerabilities" (2026-07-15, "Cloud Agents")
- Applies to any app as: add scheduled automated security scans or agent audits to CI for any project type.

**P40. Let users own and export their data.**
- "I actually want people to own their memory… they shouldn't feel like they're stuck" (2026-05-05, "launching a new app soon")
- Applies to any app as: prefer open, portable storage formats and export paths over proprietary stores.

## Shipping and quality

**P41. Go scruffy first, and harden when real use demands it.**
- "when I'm building a side project I don't think a scale I just want to make it work" (2024-10-09, "Building an Email Software using AWS SES")
- Applies to any app as: a single process with an embedded store is a fine v1. Split it into services only when load or ownership requires it.

**P42. "Slop" means it breaks at scale or costs too much, not that it doesn't work.**
- "Slop doesn't mean it doesn't work it just means it will break the moment it scales" (2025-10-24, "My NEW AI workflow will piss you off")
- Applies to any app as: score candidates on how they behave under real load and on cost, not on whether the demo runs.

**P43. Prove the riskiest integrations first, and reproduce bugs before fixing them.**
- "prove the three riskiest integrations on real device before building features… I respect that" (2026-06-05, "stop using plan mode")
- Applies to any app as: spike hardware, driver, platform-API and model integrations before building features on them.

**P44. Test in a sandbox before production.**
- "make sure everything is rock solid then use uh production environment" (2025-06-06, "The Ultimate SAAS Starter Kit")
- Applies to any app as: use staging accounts, test networks and dry-run modes for anything touching money, devices or external systems.

**P45. Polish and care are the moat, because code is cheap to copy.**
- "the mo[at] is caring… Polish matters" (2026-10-16, "Software Is DEAD")
- Applies to any app as: prefer tools that let you finish UX details, such as native-feel desktop toolkits or good TUI libraries, over ones that cap quality.

**P46. Build something you'll use, for real non-developer users, and finish it.**
- "build for the normies" (2025-11-25, "What I would build using Nano Banana Pro")
- Applies to any app as: cut setup friction for the end user, for example one key instead of three, an installer instead of build steps, sensible defaults.

**P47. Keep one reusable starter or template that every project feeds back into.**
- "every time I build a new product… I add it to the starter kit" (2024-05-27, "Setup Stripe Subscriptions using Nextjs 14")
- Applies to any app as: keep a per-type template (CLI, service, agent) with features behind config flags.

## Cost and scale

**P48. Spend for reliability and speed early. Optimize cost later.**
- "cost is the one thing where I'm like you know what we ball" (2026-07-02, "System Design Overview")
- Applies to any app as: accept paid tools that buy speed or reliability. Revisit them when the bill matters.

**P49. Price a tool by its total cost, not the headline free tier.**
- "resent only gives you 3,000 free emails per month" (2025-02-24, "I built my own AI friends")
- Applies to any app as: add the hidden dependencies, such as email, egress, licences, ops time and model tokens, before comparing options.

**P50. Pay a bit more for much better developer experience.**
- "I rather pay 1% fees more… and get great developer experience" (2025-04-07, "This Tech Stack is INSANE")
- Applies to any app as: a slightly costlier SDK, host or runtime wins if it removes a class of bugs or plumbing.

**P51. Pick billing and pricing tools by the pricing model.**
- "if it's just direct straight up subscription use Stripe if you have some credit based stuff… Autumn" (2026-07-02, "System Design Overview")
- Applies to any app as: for licensing in desktop or CLI apps, choose by model (seat, usage, one-off) rather than by brand.

**P52. Don't switch architecture for small gains.**
- "the cost savings and even the latency savings are not high enough for me to have to switch" (2026-09-06, "GPT 6 Astra")
- Applies to any app as: migrate only when the measured gain beats the risk of a new class of bugs.

**P53. Split services partly by who will own them.**
- "if Pluto succeeds… there would be a dedicated person solely working on this" (2026-07-02, "System Design Overview")
- Applies to any app as: draw service and package boundaries where a future owner or team would sit, not by layer for its own sake.

## Evolving the stack

**P54. If it works, don't swap it for something new.**
- "it's one of those things if it ain't broke don't fix it" (2024-10-28, "Nextjs 15 is here")
- Applies to any app as: an existing project's stack wins. Change one layer at a time, with a stated reason.

**P55. Install only the plugins and integrations you actually use. Add agent tools one at a time.**
- "if you just smash all these tools all at once… it sort of becomes redundant and useless" (2026-02-12, "I finally understand OpenClaw")
- Applies to any app as: keep the dependency and tool lists minimal, and add each one when a task proves the need.

**P56. Turn every process that works into a skill, after walking it by hand.**
- "skills equals standard of procedure" (2026-02-20, "Recursively improve your OpenClaw agent")
- Applies to any app as: codify the build, release and debug loops for any project as checked-in skills or scripts.

**P57. Kill features that fight a vendor's limits rather than bending the stack.**
- "I finally decided to can the feature" (2026-02-25, "What 1000+ Hours of AI Coding Taught Me")
- Applies to any app as: if a chosen tool can't do a feature cleanly, drop the feature or replace the tool. Don't build a fragile workaround.

## Disclosures and bias

- **Convex employee from about 2025-08-22.** He disclosed this on 2026-07-24 and 2026-10-01, and he built Convex's Stripe component. Treat later Convex praise as employee praise.
- **Orgo investor**, disclosed 2026-10-01. That is when he moved his agent computers from Daytona to Orgo.
- **Tempo Labs employee until mid-2025** ("Tempo which is the uh company I work at", 2025-05-29). Template choices in Tempo videos reflect Tempo's product menu. Vite usage came from work there.
- **Discount sponsor reads.** Ad-only examples: Brilliant, Scrimba, cal.com, Miro, Retool, Framer, Leap, Augment, Macroscope, Grok Bot (2026-10/11). Sponsors he also praised unsponsored, so weigh them lightly: Convex, Clerk, Neon, Windsurf, Greptile, Daytona, Composio, WorkOS, CodeRabbit, Cursor cloud agents.
- He calls himself a Next.js/Vercel "fanboy" (2024-08-05).

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
| Claude Code "best agent" | 2025-06-06 | Cursor, then T3 Code; Claude CLI over SSH | 2025-10-17 / 2026-10-21 |
| Gemini "in the lead" | 2025-11-25 | "refrain from using the Gemini models" | 2026-02-12 |
| Codex/GPT best value | 2026-07-24 | Opus 5.5 main model | 2026-10-01 |
| OpenClaw as agent core | 2026-05-05 | Eve [caption?] ("terrible decision") | 2026-09-11 |
| Daytona agent computers | 2026-05-22 | Orgo (investor) | 2026-10-01 |
| Ghostty terminal | 2026-01-23 | cmux [caption?], then Ghostty plus a multiplexer | 2026-03-13 / 2026-08-19 |
| "models not trained on it" rules TanStack out | 2026-01-23 | Training data waived given code plus a skill (Svelte) | 2026-03-24 |
| Ralph loops "killed programming" | 2026-01-16 | "Is Ralphie even necessary" | 2026-03-07 |
| Web3 builder | 2017–2022 | "I hate the space" | 2025-11-12 |

## Known non-web picks

| Language / tool | Job | Citation |
|---|---|---|
| Python + Flask | AI research/plan/write pipeline and job queueing | 2024-05-09, "I launched an AI SAAS" |
| Bun + Elysia (+ Eden) | Standalone typed backend servers | 2024-03-04; 2026-01-23 |
| Hono on Cloudflare Workers + Drizzle + Neon | Standalone API backend | 2024-10-02; 2024-12-10 |
| Effect (TypeScript) | Every backend service; the Bezel MCP server | 2026-10-01, "Agentic Development Stack" |
| Railway | Hosting separate servers | 2026-01-23; 2026-08-19 |
| Expo + React Native (SwiftUI only if iOS-only) | Mobile | 2025-11-10; 2026-07-02 |
| Electron (wraps the site) | Desktop app | 2026-07-02, "System Design Overview" |
| Rust | Native-feel desktop clones; single sync server for hardware | 2026-10-16; 2026-11-06 |
| Bash script → npm CLI with YAML config (Ralphy) | Agent-loop CLI | 2026-01-20 |
| Express + JSON file on Fly.io, Vapi, ElevenLabs, Twilio | Voice agent | 2025-12-09 |
| Vercel AI SDK, Claude Agent SDK, Composio, Daytona | Agent SDKs, tools, sandboxes | 2026-01-23 |
| Supermemory, AgentMail, Plaid, Mistral OCR, OpenRouter, Caddy | Agent service dependencies | 2026-05-05; 2026-07-02 |
| Braintrust / Axiom / Sentry | Agent observability | 2026-07-02 |
| Linux mini PC, Tailscale, Synology NAS, UPS | Agent runtime machine | 2026-08-19, "don't use my macbook" |
| Nightly traces → NAS, fine-tunes on rented H100s | ML / fine-tuning | 2026-10-29, "Grok Bot" |
| REA (Ghidra, Hopper, IDA over MCP) | Reverse engineering for agents | 2026-10-16, "Software Is DEAD" |
| Abliterated DeepSeek via Morph LLM | Pen-testing his own devices | 2026-11-02 |
| 1Password | Environment variable secrets | 2026-08-14 |
| AdGuard Home (agent-managed) | Home network | 2026-10-29 |
| Raspberry Pi, ReSpeaker, Blender via Codex, 3D printing | Hardware prototype | 2026-11-06, "pivoting to hardware" |
| TradingView webhook → Convex; brokerage API; polygon.io | Fintech data and alerts | 2025-10-17; 2026-01-23 |
| thirdweb, Crossmint, Privy, viem [caption?] | Crypto wallets and Ethereum | 2025-11-12 |
| pass.js [caption?], ImageKit, R2 | Apple Wallet passes and images | 2025-08-28; 2026-03-13 |
| Web Workers | CPU-heavy parsing and inference in UI | 2025-04-25 |
| Cloudflare Tunnel / ngrok | Exposing local servers and webhooks | 2024-09-18; 2026-08-19 |
| Linear | Planning and issue tracking | 2026-07-09 |
