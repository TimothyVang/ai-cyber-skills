# Agent-driven UI design workflow (2026)

Run the ordered steps below when designing or restyling a UI with an agent. Each step ends on a **Done when** check; finish it before moving on. The design system is the single source of truth: page fixes flow back into it, and agents build pages only from it.

Source dates: 2026-09-28 (Paper workflow, newest), 2026-06-23 (Claude Design workflow), 2026-05-08 and 2025-12-01 (component libraries). The newest wins conflicts.

## Which design tool
- **Default: Paper + its MCP**, a Figma alternative that agents drive well, controlled from the coding harness (2026-09-28).
- **Alternative: Claude Design**, exported to Claude Code with "Send to Claude Code" and the Claude Design MCP. It is strong at producing design systems (2026-06-23).
- Both follow the same loop: inspiration → design system with tokens → tweak → build pages from it.

## Principles
- Build a design system and tokens before any page. Apps designed page by page without them drift out of consistency (2026-06-23).
- A design system is the single source of truth for components, guidelines, and brand (colors, copy).
- Tokens are named decisions: `spacing-medium` instead of `16px`, `brand-primary` instead of a hex value. Dark mode becomes a token swap, and a brand change propagates from one place.
- Never let the agent design from nothing. Without a system, output looks generic and machine-made. Use the agent to build on a foundation, not to be the foundation (2026-09-28, 2026-05-08).
- Inspiration is a base, not a copy. Add your own taste, or the site looks like every other generated site. The agent will not reproduce a screenshot exactly; treat its output as a canvas to tweak (2026-06-23).
- The first output is never final. Plan for many rounds (2026-09-28).
- Model: Claude models, Opus 5.5 in particular, follow design systems best. OpenAI models are acceptable when given a system (2026-09-28).

## Prerequisites
- Paper desktop app with its MCP connected to the harness.
- A full-page screenshot tool. Screenshots are required at several steps.
- An agent harness with permission to edit and run the app.

## Ordered workflow

### Step 1: Collect inspiration
1. Browse Mobbin (mobbin.com) for sites in your niche and outside it. It collects well-designed sections (onboarding, hero, dashboards) and has an MCP server. The free tier is enough.
2. Bookmark designs you like from designers you follow, and keep them in one inspiration library.
3. With no inspiration, start from Vercel's `vercel.com/design.md` (light or dark) as a foundation, not a target.
4. Take a full-page screenshot of the chosen site.
- **Done when:** you have at least one full-page screenshot (or a design.md) that captures how the app should feel.

### Step 2: Build the design system (most important step)
- **Paper route:** put the screenshot in a new Paper project and ask the agent to use the Paper MCP to recreate the site and extract its design system. Expect it to take tens of minutes. The result has Foundations and Components boards covering colors, fonts, spacing, layouts, shades, and depth. You can ask for a landing page in the same prompt.
- **Claude Design route:** start from a file, upload the screenshot, and ask for a design system on one page: components built from it, with the tokens displayed. For a design.md base, paste its contents and ask for a system built from it.
- **The system page must show:**
  - Colors: brand scale, neutrals, accents, semantic colors (success, warning, danger, info).
  - Typography: family, and sizes for display, H1, H2, H3, body.
  - Spacing scale, radius scale, elevation.
  - Components: buttons, badges, inputs and controls, avatars, dialog, form, alerts, checkboxes, radios, dropdown menu, tooltips, steps. Ask the agent to add any standard component still missing, so the build agent later knows how everything should look.
- Remove generated artifacts at once: stray decorations, an AI-drawn logo, misaligned badge text. Mark them on the canvas and tell the agent to remove or fix them.
- **Done when:** one page shows every token (color, type, spacing, radius, elevation) and a full core component set, with no stray artifacts or generated logo.

### Step 3: Build a landing page from the system
- Ask the agent for a landing page that follows the system exactly. A design system is hard to judge in the abstract; a real page shows whether it works.
- **Done when:** a landing page exists whose colors, type, spacing, and components visibly match the system.

### Step 4: Iterate on the landing page, then sync the system
1. Leave comments on Paper elements, then tell the agent to address every comment.
2. Typical requests: replace copied or random images (Paper can generate images); add syntax colors to code samples; explore adding color to a grayscale system in several versions and pick one; generate variants of the system with different base colors and delete the ones you reject.
3. To merge two systems, copy one board into the other project and ask the agent to combine them into a new page.
4. Once the page looks right, tell the agent to bring the design system up to date. Tweak the page first, then the system, never the system in the abstract.
5. In the Claude Design flow, finish all tweaks in the design tool before exporting. Do not change the system after handing it to the coding agent.
6. Expect several rounds over several days.
- **Done when:** the landing page is accepted and the design system reflects every accepted tweak.

### Step 5: Explore the remaining pages in several versions
- Ask for explorations, not single designs. One prompt can produce several variants of a page (for example summary, ledger, and detail layouts).
- A short prompt works once the system exists: ask the agent to design the product dashboard in the Paper project, using the design system, the landing page, and its knowledge of what the app's code can do.
- Design empty states and secondary flows too.
- **Done when:** each product page has at least two explored variants and one chosen, all consistent with the system.

### Step 6: Build it in the app
- Tell the agent to build the chosen designs in the app.
- Claude Design path: create a minimal app, hand off with "Send to Claude Code", let the agent import through the MCP and build the design system page first, then ask for landing, auth (sign in and sign up), and dashboard pages. The system is in the codebase, so prompts need not repeat it.
- Fix mismatches in the design system, where a fix propagates everywhere.
- **Done when:** landing, auth, and dashboard share the same colors, fonts, spacing, and radius, with no leftover artifacts.

### Step 7 (optional): Add flair, constrained by the system
- Give the agent a component's code or URL and tell it to style the component with the design system.
- Reverse method: bring in one standout component and ask the agent to extract its design language for the rest of the app. Keep strong effects (such as a liquid-metal border) to a few places like primary CTAs.
- Small touches that add character: key-press sounds, a spin-the-wheel, celebration animations.

## Tells of generated design to avoid
- Odd borders and radius that changes between pages.
- Purple as the primary color; it now reads as machine-made.
- Generated logos and random decorations.
- Default colors nobody reviewed.
- Building without a system, or styling element by element in prompts.
- Single-version designs, and exact copies of another site.
- Generic sameness. A little time on quality makes a product stand out.
- The default HTML `<video>` player where a hover player fits better.

## UI component libraries (install by giving the agent the code, CLI, or URL)
| Library | Use for | Date |
|---|---|---|
| shadcn/ui | Assumed base; most libraries below install onto it | 2025-12-01 |
| Coconut UI | Distinctive components: slide-text button, glass music player, activity rings, bento grids, card flip and stack, transfer animation, AI input and tool-call loaders, voice, text animations | 2025-12-01 |
| Cult UI | Drawers, expandable waitlist modal, browser mockup, 3D carousel, hover video player, dot-matrix loaders; paid Pro tier | 2025-12-01, 2026-05-08 |
| Motion Primitives | Animated numbers, dynamic toolbar, dock, glow, before/after slider, scroll progress, magnetic button, morphing dialog | 2025-12-01 |
| prompt-kit | AI app blocks: chain of thought, chat container, code blocks | 2025-12-01 |
| Liquid Metal | Animated liquid-metal border for premium CTAs and pricing; use sparingly | 2026-05-08 |
| Style UI (styleui.dev) | Free templates: a light B2B SaaS landing and a consumer app | 2026-05-08 |
| Skipper UI | Hover and glide cards, crawl scroll, card stacks and swipes, expanding video player | 2026-05-08 |
| Watermelon UI | Springy, native-feeling components (onboarding, card swiper) | 2026-05-08 |
| componentry.fun | Tactile keyboard with sounds, flight tracker, GitHub tracker, matrix effects | 2026-05-08 |
| balloon.js | Celebration balloon and text animations | 2026-05-08 |

Design and inspiration tools: Paper + MCP, Claude Design + MCP, Mobbin, vercel.com/design.md.
