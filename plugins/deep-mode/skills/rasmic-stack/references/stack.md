# Stack reference (Ras Mic, 2026)

Layer-by-layer picks distilled from his video transcripts (scraped 2026-11-06; full transcripts in `~/rasmic/transcripts/`). Each pick carries his reason and a citation; the newest video (ADS, 2026-10-01) wins conflicts. Use a pick as the default when the user asks for "his stack" or has no preference; an existing project's stack always wins over these defaults. Picks marked SPONSOR count only where he also endorses the tool outside the ad read.

Sources (abbreviations used in citations):
- **TTS** = "My 2026 Tech & Tool Stack", 2026-01-23
- **PAY** = "Payments for my SAAS" (short), 2026-02-04
- **NGB** = "I'm never going back" (Svelte), 2026-03-24. The transcript file stops at "now for the final point why you shouldn't use spelt let's talk about it", so his "when not to use Svelte" section is **missing**.
- **OSRC** = "This Tool Made My Coding Agent Powerful", 2026-04-03
- **SYS** = "If you're building with AI, watch this (System Design Overview)", 2026-07-02
- **ADS** = "My Agentic Development Stack", 2026-10-01 (newest; wins conflicts)

Disclosure he repeats: he works at Convex and built its Stripe component (TTS 2026-01-23; ADS 2026-10-01). He is an investor in Orgo (ADS 2026-10-01).

---

## 1. Web framework
- **Default pick: SvelteKit.** Use Next.js sometimes. Both deploy well to Vercel. Why: "AI is really good with Svelte and SvelteKit" and "any app that I built with Svelte by default... is just fast, it's snappier" (ADS, 2026-10-01). SYS also uses SvelteKit for all Pluto web clients: "it's very minimal, it's fast, it's easy to build performant sites with it" (SYS, 2026-07-02).
- Why Svelte: it compiles to vanilla JS, has a minimal runtime (Svelte 5 runes), and has no virtual DOM. Example he cites: Strawberry browser rewrote 130,000 lines from React to Svelte in 2 weeks with AI (NGB, 2026-03-24).
- He says "AI is not trained on Svelte" doesn't matter: scaffold a SvelteKit project, then "your code in and of itself is context". Agents can web-search. Add the Svelte team's official skills file, which he says makes output "10 times better", though he didn't use it on his last two Svelte apps (NGB, 2026-03-24).
- The ecosystem is fine. shadcn has a Svelte port. Tailwind and HTML UI carry over. Use a vendor's plain JS package when there is no SvelteKit package (e.g. WorkOS JS). He bets "95%" of React things exist for Svelte, and you can have the agent build the rest (NGB, 2026-03-24).
- The Next.js mental model carries over: `src/routes/about/+page.svelte` style routing, SSR, data fetching, prerendering (NGB, 2026-03-24).
- **Alternative: Next.js.** Use it when you want it or it fits better; it's still in his rotation (ADS, 2026-10-01). In January it was his main frontend (TTS, 2026-01-23). See Superseded.
- **TanStack Start:** he avoided it in Jan 2026 because "the AI models have not been trained on it so it definitely does hallucinate" and it "is still in release candidate" (TTS, 2026-01-23). Conflict: in NGB he argues training data doesn't matter (for Svelte), which weakens that first reason (NGB, 2026-03-24).
- **Elysia (on Bun) inside Next.js** for one-off API routes. Use `app/api/[[...slugs]]/route.ts` as a catch-all and add an Eden treaty client in `lib/eden.ts` for end-to-end type safety (it's like tRPC). "Elysia is not going to be my main backend" (TTS, 2026-01-23). It isn't mentioned in later videos.

## 2. Mobile / desktop / monorepo
- **Mobile: Expo + React Native.** Why: it's cross-platform, "it's React so it's just easy" (TTS, 2026-01-23). He chose it again for Pluto's mobile app. Use Swift instead if you don't need Android: "unless I don't need an Android app, I usually like to go Swift" (SYS, 2026-07-02).
- **Desktop: Electron** wrapping the website (SYS, 2026-07-02).
- **Always start with a monorepo, using Turborepo.** "I almost always start with a monorepo." Why: the agent sees the whole codebase, and all clients share one backend and one UI library. He uses Turborepo because he deploys to Vercel (SYS, 2026-07-02; TTS, 2026-01-23).

## 3. Styling / UI
- **Tailwind v4 + shadcn/ui.** To start a project, go to shadcn/ui → New Project and pick Base UI for components, a style (e.g. "Mira"), radius, and theme. Then run the generated `bunx` command (TTS, 2026-01-23).
- Design tooling (Paper, Mobbin) is in §11.

## 4. Backend / database
- **Default backend: Convex**, on every project. Why:
  - "everything is code... think of Terraform but for your backend", so agents can build it.
  - It's type-safe and real-time by default.
  - It covers webhooks (HTTP actions), cron jobs, scheduled and background jobs, and queues.
  - Run `npx convex dev` to set it up.
  
  (TTS, 2026-01-23; ADS, 2026-10-01; SYS, 2026-07-02). "I can't imagine a world where I'm building applications without Convex" (TTS).
- Convex merges server and DB "in one box": queries = reads, mutations = writes, actions = external services (SYS, 2026-07-02).
- **Use Convex components for integrations:** give the agent the component link or repo and say "set up Stripe using the Stripe component". Components he names: Stripe, Polar, Autumn, Dodo Payments, Workflow (durable long-running flows with retries), Workpool (queues and parallel tasks), Cloudflare R2, Resend (email), WorkOS, PostHog, Browserbase, sandbox. "10 times out of 10... it's got it absolutely right" (TTS, 2026-01-23; PAY, 2026-02-04; SYS, 2026-07-02; ADS, 2026-10-01).
- **Effect (Effect-TS) for any standalone service or backend that isn't Convex.** "Whenever there is a service that I'm building I am always and forever going to be using Effect." Why: AI made it easy to learn and write, and it has strong typed error handling: "Effect is magnificent at handling errors." Example: his app Bezel is "one giant MCP server" written entirely in Effect, with a Svelte website (ADS, 2026-10-01). He used it for Pluto's inference/payments service: "when it comes to error handling nothing is as good as Effect" (SYS, 2026-07-02).
- **Postgres: PlanetScale** whenever he needs Postgres ("the big dog Postgres provider"). It works well with Effect and can be reached through Cloudflare Hyperdrive (ADS, 2026-10-01; SYS, 2026-07-02).
- **Supabase:** he avoids it because it encourages the client to talk directly to the DB with RLS: "to me that's just a fool's game" (SYS, 2026-07-02).

## 5. Auth
- **Current pick: WorkOS.** "WorkOS is my favorite auth provider, it's the big leagues auth" (ADS, 2026-10-01). He chose it for Pluto because it's "enterprise ready": companies with 15–60 employees, a manager inviting staff, SSO and compliance like SOC 2, "and the agents love it" (SYS, 2026-07-02). Note that NGB's WorkOS pitch (free first 1M users, enterprise SSO) is a **SPONSOR** read (NGB, 2026-03-24), but he independently endorses WorkOS in SYS and ADS.
- **Jan 2026 view:** "Clerk is still the simplest to use". Better Auth has a Convex component and "might be my de facto". Use WorkOS for enterprise apps. "You can't go wrong with any of these" (TTS, 2026-01-23). This was superseded by WorkOS as his favorite (ADS, 2026-10-01).

## 6. Payments
- **Simple subscriptions → Stripe**, through the Convex Stripe component (TTS, 2026-01-23; PAY, 2026-02-04; SYS, 2026-07-02).
- **Credits, usage-based billing, top-ups → Autumn**, through the Convex Autumn component. He uses it in Pluto, which has credits, free items, top-ups, and agent cards. "if it's just direct straight up subscription use Stripe, if you have some credit based stuff going on I would use Autumn" (SYS, 2026-07-02). In January he hadn't used Autumn yet but said he would for "usage based billing or some AI credit stuff" (TTS, 2026-01-23).
- Polar and Dodo Payments are mentioned only as providers that have Convex components; he doesn't pick them (PAY, 2026-02-04).

## 7. AI app tooling
- **Vercel AI SDK**: "basically what I use to build all my agents... there's no reason why you shouldn't use it" (TTS, 2026-01-23).
- **Claude Agent SDK**: he calls it "the most slept on". It runs Claude Code instances inside a sandbox, for coding agents or assistants (TTS, 2026-01-23).
- **Composio** as the tool and integration layer (Gmail, Calendar, Slack, GitHub, Sheets, Shopify…). Set it up by creating a tool-router session per user ID and passing its tools to AI SDK `streamText` (TTS, 2026-01-23). He also keeps Composio's codebase in opensrc (OSRC, 2026-04-03).
- **OpenRouter** is the inference provider behind Pluto's inference ledger (SYS, 2026-07-02).
- **OpenClaw** is the agent that Pluto runs (SYS, 2026-07-02).

## 8. Sandboxes / agent computers
- **Daytona** for agent sandboxes. "The developer experience for Daytona is absolutely the best... nothing comes as close." His Sandstorm app runs Claude Code agents in Daytona (TTS, 2026-01-23). He runs Pluto's OpenClaw on Daytona because each agent also gets a computer with a browser (SYS, 2026-07-02).
- **Orgo** (newest): "every Pluto instance has its own computer, the computer we're using is Orgo... whenever I want to give my agent a separate computer I'm using Orgo." He is an investor, "take that with a grain of salt" (ADS, 2026-10-01). Conflict: in Jul 2026 Pluto's agent computers came from Daytona (SYS); by Oct 2026 they come from Orgo (ADS). Prefer Orgo for agent computers. Captions render it as "Oracle", so the name is [INFERENCE: Orgo].

## 9. Deployment
- **Vercel by default.** He uses Turborepo with it and deploys Pluto's prod, staging, inference service, and admin site there. He's on the $20 plan and has spent over $100 (SYS, 2026-07-02; TTS, 2026-01-23).
- **Cloudflare, but only the full stack**: "if I'm ever using Cloudflare I'm probably using the entire stack": Workers, R2, Hyperdrive, Durable Objects, Cloudflare Email. Example: his agent email provider runs entirely on Cloudflare; captions say "go email", so the name is unclear (ADS, 2026-10-01). Rule: if anything in the app is Cloudflare, stay on Cloudflare; otherwise use Vercel (ADS, 2026-10-01).
- Avoid raw AWS, GCP, and Azure. "Azure is terrible to use, GCP is terrible to use." Use abstractions like Convex, Vercel, and PlanetScale instead (SYS, 2026-07-02).
- **Railway** for a separate server plus Postgres (Elysia/Bun/Drizzle template) (TTS, 2026-01-23). Superseded by the Cloudflare and PlanetScale picks (ADS, 2026-10-01).

## 10. Analytics / observability / CI / email
- **Sentry + PostHog** for error logging and analytics ("not sponsored"). Tell the agent: "whenever an error happens I need to know how to track it... use Sentry and PostHog" (SYS, 2026-07-02). PostHog is also available as a Convex component (ADS, 2026-10-01).
- **Email: Resend**, via its Convex component (TTS, 2026-01-23; PAY, 2026-02-04; SYS mentions "Resend" among components, 2026-07-02). For agent email he uses his own Cloudflare Email app (ADS, 2026-10-01).
- **CI / code review: Greptile** on every PR. He reviews a PR only if the confidence score is ≥4/5 (TTS, 2026-01-23); below 4/5 he tells the author or agent to address the comments. SYS has a **SPONSOR** Greptile read, but he uses it independently in TTS and ADS. Newest flow: his "GP loop" skill loops the agent on Greptile feedback until the score is 5/5 (ADS, 2026-10-01). These are the only CI tools the transcripts mention. deep-mode replaces Greptile and the GP loop with its pr-review technique (`skill://deep-mode/references/techniques/pr-review.md`).
- **Issue tracking: Linear**, connected over MCP. Assign a ticket to Cursor or Devin cloud agents so a fix PR exists before he has even read the bug (ADS, 2026-10-01).

## 11. Dev tools
- **opensrc** (by Vercel; captions say "open source"). It fetches an npm package's or GitHub repo's source into the project so agents use the real code as context, which helps with new libraries and new versions (e.g. Next.js 16.2 cache components, SvelteKit remote functions). Usage:
  1. Run `npx opensrc <package | github-url>`.
  2. It creates an `opensrc/` folder with `sources.json`, `settings.json`, and `repos/github.com/...`. The folder is auto-gitignored.
  3. Prompt: "look under the opensrc folder and check out the SvelteKit project and show me how to use remote functions in this codebase".
  
  He prefers it to Context7 MCP or pasting docs: "your codebase is the best piece of context" (OSRC, 2026-04-03). UX Pilot in that video is a **SPONSOR**; discard it.
- **Paper**, a Figma alternative that works well with agents and has an MCP. He used it for his portfolio and the Pluto redesign (ADS, 2026-10-01).
- **Mobbin** for design inspiration, which also has an MCP (ADS, 2026-10-01).
- **Wispr Flow** for voice-to-text prompting (ADS, 2026-10-01).
- **Ghostty** as his terminal (TTS, 2026-01-23).
- **His skills repo** (open source). It contains his `AGENTS.md`, plus the code-structure and GP-loop skills (ADS, 2026-10-01). The feature flow:
  1. Create a git worktree off main per feature, so agents work in parallel ("15 different features").
  2. Write code following the code-structure skill.
  3. Prove the change works: record a video if it's UI, otherwise run tests; fall back to before/after screenshots in the PR.
  4. Greptile reviews the PR, and the GP loop runs until 5/5 (deep-mode replaces this step with its pr-review technique).
  5. The PR is then ready for him to merge.
  
  (ADS, 2026-10-01)
- Grokbot (designer/engineer bots) in ADS is a **SPONSOR** read; discard it.

## 12. Harnesses and models
- **Daily driver: T3 Code**, "a harness's harness". It runs the real Claude Code, Cursor, and OpenCode harnesses and dispatches agents across machines on his network (Linux box, Mac). He likes its inbox-style sidebar, where threads settle when the PR is merged (ADS, 2026-10-01).
- **Claude Code: CLI only** ("I almost never used the app"), e.g. over SSH on new machines (ADS, 2026-10-01).
- **Codex app:** use it for computer use, research, 3D/Blender, and hardware projects, not mainly app building (ADS, 2026-10-01).
- **Cursor and Devin:** use their web apps for cloud agents, triggered from Linear. He also uses the Cursor CLI (`agent`) (ADS, 2026-10-01). In Jan he used the Cursor editor to review and write code (TTS, 2026-01-23).
- Be "very disloyal" to subscriptions. Pick whichever lab currently subsidizes most. "It was OpenAI for a minute... with the new Opus 5.5 model it lowkey is Anthropic" (ADS, 2026-10-01).
- **Models (current, Sep/Oct 2026):** Opus 5.5 is his main model: "well-rounded... listens to instructions... really good at long running tasks". GPT-6 Astra is for deep work, research, and understanding a codebase deeply. Expect this to change "in the next two to three months" (ADS, 2026-10-01).
- **Earlier:** Jan used Opus 4.5 thinking for coding, Codex for catching edge-case bugs, and GPT-5.2 for everyday chat (TTS, 2026-01-23). Jul used "Fable 5" as his model of choice, which is a caption-ambiguous model name (SYS, 2026-07-02). Oct: "Opus 5.5... better" than Astra/"Fable" (ADS).
- **Chat apps (Jan):** T3 Chat is his daily driver. He uses ChatGPT for Deep Research and Claude Cowork sometimes (TTS, 2026-01-23).

---

## System design for AI apps (SYS, 2026-07-02)
Principles:
- "Engineering is all about trade-offs." Weigh **scalability, reliability, performance, cost** for every tool.
- Build on managed abstractions (Convex, Vercel, PlanetScale) over raw AWS, GCP, or Azure. Their developer and agent experience is better and "every tool I'm using can handle scale". When scaling, "up my subscription" and use AI to optimize.
- **Never let the client talk to the DB.** Always go client → server → DB → server → client. Otherwise API keys leak through the network tab.
- Choose tools agents know well and that are configured as code ("everything is code, the agents love it").
- Start with a **Turborepo monorepo**: web (SvelteKit), mobile (Expo/React Native, or Swift if iOS-only), desktop (Electron wrapping the web app), a shared UI library, and one unified backend.
- **Use durable processes for agents and chat**, so work continues if the user leaves. Use the Convex Workflow component for this, Workpool for queues and parallel tasks, and Convex components for integrations (e.g. R2 storage).
- **Split out a separate service** when code "touches one surface area, does one specific thing", doesn't have a foothold across the codebase, could have a dedicated owner, or the main backend is growing too big. He says it's "more experience and vibes than a specific formula". You can ask the model which parts to segment.

Pluto architecture:
- Clients: web, desktop, mobile, and an internal admin site.
- **Control plane / source of truth: Convex**, with components.
- Services in the monorepo:
  - **inference/payments**: Effect, its own PlanetScale Postgres wallet/inference ledger, OpenRouter for inference.
  - **iMessage**: also Effect. One caption line says "Effect TS for the inference payments and Postgres for the iMessage", but he then says "I use Effect in the iMessage service". **Ambiguous**.
- Agent: OpenClaw on Daytona sandboxes (medium to large boxes), each agent with its own computer and browser.
- Auth: WorkOS for B2B. Billing: Autumn credits. Observability: Sentry + PostHog. Deploy: Vercel (prod, staging, inference service, admin).
- Trade-off he accepted: **cost**. "Cost is the one thing where I'm like, you know what, we ball." A single Convex backend would be cheaper, but he kept separate services.

---

## Superseded
| Was | Date | Now | Date |
|---|---|---|---|
| Next.js as main web frontend (with Elysia for API routes) | 2026-01-23 (TTS) | SvelteKit default, Next.js sometimes | 2026-03-24 (NGB), 2026-07-02 (SYS), 2026-10-01 (ADS) |
| Clerk "simplest", Better Auth possibly de facto, WorkOS only for enterprise | 2026-01-23 (TTS) | WorkOS "my favorite auth provider" | 2026-07-02 (SYS), 2026-10-01 (ADS) |
| Stripe only; hadn't used Autumn | 2026-01-23 (TTS) | Stripe for subscriptions, Autumn for credits | 2026-07-02 (SYS) |
| Railway for separate servers + Postgres | 2026-01-23 (TTS) | PlanetScale Postgres; Cloudflare full stack or Vercel | 2026-10-01 (ADS) |
| Daytona for agent computers in Pluto | 2026-07-02 (SYS) | Orgo for agent computers | 2026-10-01 (ADS) |
| Opus 4.5 thinking + GPT-5.2 / Codex | 2026-01-23 (TTS) | "Fable 5" (Jul), then Opus 5.5 main + GPT-6 Astra for deep work | 2026-07-02, 2026-10-01 |
| Cursor editor + Claude Code CLI as main tools | 2026-01-23 (TTS) | T3 Code as daily driver; Cursor/Devin for cloud agents | 2026-10-01 (ADS) |
| Context7 MCP / pasting docs | (rejected) | opensrc | 2026-04-03 (OSRC) |
| Greptile: manually review only at ≥4/5 | 2026-01-23 (TTS) | GP-loop skill auto-iterates to 5/5 (deep-mode uses its pr-review technique instead) | 2026-10-01 (ADS) |
