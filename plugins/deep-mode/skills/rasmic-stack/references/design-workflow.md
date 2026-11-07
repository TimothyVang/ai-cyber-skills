# AI UI design workflow (Ras Mic, 2026)

Run the ordered steps below when designing or restyling a UI with an agent. Each step ends on a **Done when** check; finish it before moving on. The design system is the single source of truth: page fixes flow back into it, and agents build pages only from it.

Sources (abbrev.):
- **[SEP]** "How I Build Beautiful UIs with AI (My design workflow)", 2026-09-28 — most recent; Paper-based workflow.
- **[JUN]** "Building beautiful UI using AI (My design workflow)", 2026-06-23 — Claude Design-based workflow.
- **[MAY]** "These UI libraries + AI = beautiful looking web apps", 2026-05-08.
- **[DEC]** "Build polished web apps using these UI libraries", 2025-12-01.

Caption fixes assumed: "paper" = Paper (Figma alternative); "mobin.com" = Mobbin; "claw design" = Claude Design; "T3 code" = T3 Code; "Ghosty" = Ghostty; "spelt/speltkit" = Svelte/SvelteKit; "verscell" = Vercel; "Devon" = Devin (site used as inspiration); "Opus 55" = Opus 5.5; "chat scene" = shadcn; "IA promptkit.com" ≈ prompt-kit.com [INFERENCE].

## Conflict: which design tool (prefer SEP)
- **Current (SEP, 2026-09-28): Paper + Paper MCP**, driven from his coding harness (T3 Code nightly). "You're going to need to download paper… Paper is a Figma alternative very AI friendly one of my favorite tools right now" (SEP, 2026-09-28).
- **Earlier (JUN, 2026-06-23): Claude Design** (claude.ai design tool), exported to Claude Code via "Send to Claude Code" + Claude Design MCP. "claw design is absolutely amazing for creating design systems" (JUN, 2026-06-23).
- Both share the same core principle: inspiration → design system with tokens → tweak → build pages that follow it. Use Paper by default; Claude Design is an acceptable alternative.

## Core principles (why)
- Always have a design system + tokens before building pages. Without them his Pluto app was inconsistent: "when I was designing my app I did not build out a design system nor did I use design tokens" (JUN, 2026-06-23).
- Design system = "a single source of truth for all things design": UI components, design guidelines, brand identity (colors, copy) (JUN, 2026-06-23).
- Tokens = named design decisions, e.g. `padding: spacing-medium`, `color: brand-primary` instead of `16px` / raw hex. Benefits: dark mode by swapping token values; change brand color/radius once and it propagates (JUN, 2026-06-23).
- Never let AI design from nothing: "when you give them no design system and they design on their own then it's very AI smelly" (SEP, 2026-09-28). "if AI is your foundation it becomes a problem but if you use AI to build on that foundation… it works out great" (MAY, 2026-05-08).
- Inspiration is a base, not a 1:1 copy; add your own taste: "if you use AI to design the entire thing no sauce or input from you site's going to look like everybody else's" (JUN, 2026-06-23). AI won't reproduce a screenshot 1:1 — "it's good at giving you a canvas for a design system that you can tweak" (JUN, 2026-06-23).
- Never expect the first output to be final: "You're never going to get something perfect off the first prompt… It needs constant iteration" (SEP, 2026-09-28).
- Model: Claude/Anthropic models, specifically Opus 5.5: "generally the claude models are the best at design… Opus in particular 5.5 is really great at following design system and instructions"; OpenAI models are OK if given a design system (SEP, 2026-09-28).

## Prerequisites
- Paper (desktop app) with its MCP connected to your agent harness (SEP, 2026-09-28).
- A full-page screenshot tool. He vibe-coded his own (SEP); earlier used Zen browser's built-in full-page screenshot (JUN, 2026-06-23). "being able to take screenshots is 100% necessary" (SEP, 2026-09-28).
- Agent harness: T3 Code nightly (SEP) or Claude Code in `--dangerously-skip-permissions` mode in Ghostty (JUN, 2026-06-23).

## Ordered workflow (SEP 5-step version, enriched with JUN details)

### Step 1 — Collect inspiration
1. Browse Mobbin (mobbin.com) for sites in your niche *and* other niches; it aggregates well-designed sites/sections (onboarding, hero, dashboards) and has an MCP server. He uses the free tier and takes screenshots (SEP, 2026-09-28; JUN, 2026-06-23). (Mobbin sponsored a past video; "They're not the sponsor of this video but I genuinely enjoy their product" — SEP.)
2. Follow designers on X; bookmark designs you like; he uses **Gather OS** (by a designer) to aggregate his X bookmarks into an inspiration library (JUN, 2026-06-23).
3. Examples he used: Devin's website (SEP), family.co — "the funness… cuteness… cartoony but very tasteful" (JUN), his own portfolio's design system (SEP).
4. No inspiration? Use Vercel's `vercel.com/design.md` (light or dark variant) as a base layer — "it's not for you to copy this it's for you to have a foundation" (JUN, 2026-06-23).
5. Capture: full-page screenshot of the chosen site (SEP; JUN).
- **Done when:** you have ≥1 full-page screenshot (or a design.md) you'd want your app to feel like.

### Step 2 — Build the design system (most important step)
- **Paper route (current):** paste the screenshot into a new Paper project (or have the agent create one), then prompt your harness:
  > "create a project on paper using the MCP, create this website and its design system" (SEP, 2026-09-28)
  - It took ~28 minutes; result: Foundations + Components tabs covering colors, fonts, spacing (between products and UI elements), layouts, shades, depth (SEP, 2026-09-28).
  - Optionally ask in the same prompt to also build a landing page with the design system (SEP).
- **Claude Design route (JUN):** "Start with a file" → upload screenshot → prompt:
  > "please create a design system with the attached picture please. do create components using the design system and display the tokens. i want this displayed on one page" (JUN, 2026-06-23)
  - For a design.md base: "build me a design system using the design.markdown file I've attached below" + paste contents (JUN).
- **Required contents of the design system/tokens page** (from his generated "Family design system", JUN, 2026-06-23):
  - Colors: brand shades (e.g. blue scale), neutral/black shades, accent colors, semantic colors (success, warning, danger, info).
  - Typography: font family, sizes for display, H1, H2, H3, body.
  - Spacing scale; radius scale; elevation/depth (SEP adds layouts, shades, depth).
  - Components: buttons, badges, inputs & controls, avatars, then expand with dialog, form, alerts/notifications, checkboxes, radios, dropdown menu, tooltips, steps.
- Expand components prompt:
  > "can you create for me a dialogue component a form component and any other component that I might have missed that is important for a design system" (JUN, 2026-06-23)
  - Reason: "so when I port this over to Claude Code… it knows exactly how things are supposed to look and feel" (JUN).
- Clean up AI artifacts immediately in the design tool (markup/draw on canvas, then instruct): "please remove this from the design system" (random confetti dots), "remove this logo, will have no logo" ("i don't want AI to design my logo that looks very AI"), "please fix the alignment of the text in this badge" (JUN, 2026-06-23).
- **Done when:** a single page/project shows all tokens (color, type, spacing, radius, elevation) + a full core component set, with no stray decorative artifacts or AI logo.

### Step 3 — Build a landing page from the design system
- Ask the agent to build a landing page using the design system; verify it follows it "to a T" (SEP, 2026-09-28).
- Why landing page first: "you and I do not have the eyes to see what a design system looks like on an actual page. That's why we build the landing page first" (SEP, 2026-09-28).
- **Done when:** a landing page exists whose colors/type/spacing/components visibly match the system.

### Step 4 — Iterate on the landing page, then sync back into the design system
1. Leave comments directly on Paper elements (comment tool), then tell the agent: "address all the comments I left" / "go address the feedback I left". Example comment: "I like this card but I'd like there to be a little bit more spacing and for it to be rounded" (SEP, 2026-09-28).
2. Typical fixes to request (SEP, 2026-09-28):
   - Replace copied/random images (Paper can generate images).
   - Add color: e.g. code samples should have syntax-highlight colors, not plain black.
   - Explore color on a grayscale system: "I want us to explore adding color" → get several versions, pick one (Pluto ended with blue accents, colored buttons, in dark + light).
   - Ask for variants of the system: "I want you to change the design system. I actually want different versions because the base color is orange… Can you create for me different versions with different colors" — then delete the variants you don't like (SEP).
3. Combine systems: copy one design system board in Paper, paste into another project, and say "combine these two design systems and build me a new page" (SEP, 2026-09-28).
4. Once the landing page looks right: tell the agent to "make sure the design system is up to date". Don't tweak the system abstractly — "We tweak the landing page. Then we tweak the design system" (SEP, 2026-09-28).
5. In the JUN flow: do all tweaking in the design tool before export — "you don't change your design system once you've passed it over to Claude Code… change it and tweak it here to your liking then you move it over there" (JUN, 2026-06-23).
6. Expect "multiple rounds, multiple days. This will take time" (SEP, 2026-09-28).
- **Done when:** you're happy with the landing page and the design system file reflects every accepted tweak.

### Step 5 — Exploration: design the remaining pages in multiple versions
- Prompt for explorations, not single designs: "can we do an exploration of the banking page" → got variants (balance sheet, ledger by bank, summary) from one prompt (SEP, 2026-09-28). "I would never build one version. I would ask AI to build you multiple versions" (SEP).
- Dashboard prompt he read out (he called it "a terrible prompt" yet it worked because of the design system):
  > "build out the product dashboard using the paper MCP on the paper project. You already have access to the code so you know what the app can do, but using the design system and the landing page that was created, design for me the product which is the dashboard" (SEP, 2026-09-28)
- Also design empty states and flows (e.g. unlinking a bank account) (SEP).
- **Done when:** each product page has ≥2 explored variants in Paper and one chosen per page, all consistent with the system.

### Step 6 — Build it in the app
- SEP: "once you're done it's just a matter of telling your agent build this out on the app" (SEP, 2026-09-28).
- JUN concrete path: create a minimal SvelteKit + TypeScript app (npm), run `claude --dangerously-skip-permissions`, in Claude Design click Share → "Send to Claude Code", paste the generated prompt; the agent imports via the Claude Design MCP and first implements the design system page. Then prompt:
  > "now that you understand the design system please build out a landing page. i want you to build out an auth page with signin and sign up and I want you to build a dashboard page" (JUN, 2026-06-23)
  - He ran this in "ultra code" mode (caption; exact mode name ambiguous). He did not repeat "use the design system" — "it's baked into the codebase" (JUN).
- Fix mismatches at the design-system level; a fix there propagates everywhere (JUN, 2026-06-23).
- **Done when:** landing, auth, dashboard all share the same colors, fonts, spacing, radius with no leftover artifacts (he still had to remove "confetti" bits).

### Step 7 (optional) — Add flair with component libraries, constrained by your system
- Give the agent the component's code or URL and tell it to add the component "but to use the design system for the design" (JUN, 2026-06-23).
- Reverse method: download a standout component into the codebase, then "extract the design system from this component and make the rest of my app site look the exact same" — but don't apply the effect everywhere (e.g. liquid metal only on CTAs) (MAY, 2026-05-08).
- Small touches he uses: keypress sounds (componentry.fun keyboard), spin-the-wheel, balloon animations via balloon.js on his Convex "Ship" voting app (MAY, 2026-05-08).

## What he explicitly avoids ("AI slop" tells)
- "weird borders"; inconsistent radius between pages (JUN, 2026-06-23).
- Purple as a primary color: "purple got ruined by AI… everybody thinks of purple as AI now" (MAY, 2026-05-08).
- AI-designed logos (JUN, 2026-06-23); random confetti/sticker decorations (JUN).
- Default/AI-ish colors left unreviewed — "you might think the colors feel a little AI… you mark it up and then you change" (JUN); "still some AI-ness to it with… these colors" (SEP).
- Building without a design system, or prompting per-element ("make it rounded here and do this") — "then you're going to have a messy designed app like I have with Pluto" (JUN, 2026-06-23).
- Single-version designs (SEP); 1:1 copying of another site (JUN, SEP).
- Generic sameness: "let's not all generate the same slop… it is so easy to stand out just a little bit of quality just a little bit of time investment" (MAY, 2026-05-08).
- Default HTML `<video>` player — prefers hover video players (DEC, 2025-12-01).

## UI component libraries & templates (install by giving code/CLI/URL to your agent)
| Library | Use for | Source |
|---|---|---|
| shadcn/ui | Assumed base; Cult UI etc. install onto it ("if you're building on shadcn which I'm sure you are") | DEC, 2025-12-01 |
| Coconut UI | Unique components: slide-text button, liquid-glass music player, Apple activity rings card, bento grids, card flip, card stack, currency-transfer animation, AI input/search/tool-call loading, AI voice, text animations, profile dropdown; via npx/bunx, v0, or copy | DEC, 2025-12-01 |
| Cult UI | Family-style drawers, Family button, expandable full-screen waitlist modal, browser window mockup, 3D image carousel, hover video player, shift card, lightboard, dot-matrix loaders; has paid Pro | DEC, 2025-12-01; MAY, 2026-05-08 |
| Motion Primitives | Motion/animation: animated & sliding numbers, dynamic toolbar, dock, glow effect, before/after compare slider, scroll progress bar, magnetic button, morphing dialog/popover | DEC, 2025-12-01 |
| prompt-kit (caption "IA promptkit.com") | AI app blocks: chain of thought, chat container, code blocks | DEC, 2025-12-01 |
| Liquid Metal | Animated liquid-metal border for premium CTAs/pricing; "use this with caution and wisdom" | MAY, 2026-05-08 |
| Style UI (styleui.dev / "style.dev") — his own team's | Free templates **Access** (B2B SaaS landing, light mode) and **Noha** (consumer app; forest green / sunny orange); was waitlist in DEC. Self-promotion | MAY, 2026-05-08; DEC, 2025-12-01 |
| Skipper UI | Free + paid: image hover/glide cards, Star-Wars crawl scroll, card stacking/swipes, expanding video player | MAY, 2026-05-08 |
| "Ali Mom" library (name unclear in captions) | Hero shaders, bento grids, device mockups, patterns, logo reels, typewriter, Apple-Intelligence-style AI glow, gauge | MAY, 2026-05-08 |
| Watermelon UI | Springy Apple-like components (onboarding, card swiper) | MAY, 2026-05-08 |
| componentry.fun | Unique: tactile keyboard with key-press sounds, flight status tracker, GitHub tracker, matrix effects | MAY, 2026-05-08 |
| balloon.js | Celebration balloon/text animations | MAY, 2026-05-08 |
| "BUI" (name unclear in captions) | Micro-animations: bouncy accordion, side drawers, tilt card | JUN, 2026-06-23 |

Design/inspiration tools: Paper + MCP (SEP), Claude Design + MCP (JUN), Mobbin (SEP, JUN), Gather OS (JUN), vercel.com/design.md (JUN), Zen browser screenshots (JUN).

## SPONSOR segments (discount)
- Firecrawl "Alexandria" (SEP, 2026-09-28); Scrimba AI engineer path (JUN, 2026-06-23); CodeRabbit CLI (MAY, 2026-05-08). None are design tools.
