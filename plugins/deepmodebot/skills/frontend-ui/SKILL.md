---
name: frontend-ui
description: "UI and UX rules for building, restyling, or reviewing interfaces: components, layout, typography, color, motion and animation, motion graphics, accessibility, copy, and chat or agent UI, with patterns learned from shipped apps. Use before writing or reviewing UI code."
metadata:
  as-of: "2026-11-12"
---

# Frontend UI/UX rules (bundled)

Exported from the private repo `TimothyVang/frontend` at `7c57c43` by its `scripts/export_deep_mode.py`. Edit there and re-export; don't edit here. These files are complete on their own.

Paths written `TimothyVang/frontend:<path>` and bracketed citations like `[youtube/...]` point at that repo's evidence (transcripts, clips, screenshots, vendored skills). If `gh` can read it, shallow-clone it into the project's self-ignored scratch folder (`gh repo clone TimothyVang/frontend .scratch/refs/frontend -- --depth 1`, about 300 MB) and never commit from it: deepmodebot keeps every write inside the project root, and `.scratch/` holds a `.gitignore` of `*`. Otherwise skip the evidence; the rules below stand alone.

## Playbook sections (read the one the task routes to)

- `references/playbook/01-workflow.md`
- `references/playbook/02-review-rubric.md`
- `references/playbook/03-ai-tells.md`
- `references/playbook/04-components.md`
- `references/playbook/04a-agent-ui.md`
- `references/playbook/05-motion.md`
- `references/playbook/05a-motion-graphics.md`
- `references/playbook/06-typography-layout.md`
- `references/playbook/06a-color.md`
- `references/playbook/07-copy.md`
- `references/playbook/08-quality-floor.md`
- `references/playbook/09-steering-agents.md`

## What the images and motion clips taught (text)

- `references/patterns/mobbin-shipped-apps.md`: layout patterns from shipped apps
- `references/patterns/pinterest-patterns.md`: patterns and AI tells from 341 popular UI pins
- `references/patterns/pinterest-animations.md`: 193 animated pins as motion techniques, by type
- `references/patterns/motion-clips.md`: what every reference-talk clip shows, as motion vocabulary
- `references/patterns/live-demos.md`: Sonner, Vaul, cmdk, NumberFlow behaviour
- `references/patterns/motion-graphics.md`: engines, stack, lessons for rendered video

## Playbook intro

The rules for building UI in this repo, distilled from `reference/`. Each rule cites its source. `TimothyVang/frontend:AGENTS.md` holds the short, always-loaded version; this file holds the detail.

Leading idea: **defaults are tells.** Every unexamined default (library styling, stock layout, generic motion) reads as AI-generated. Every visible choice must be one made *for this brief*.

**Bans are defaults, not laws.** The brief's explicit words always win, even when they ask for something listed in §3. [github/INDEX tensions; anthropic frontend-design]

**Decide the surface mode first; ambition follows from it.** [github/pbakaus-impeccable; github/Leonxlnx-taste-skill]

| Mode | Surfaces | How it expresses the brand |
| --- | --- | --- |
| Operate | App UI, dashboards, settings, the agent console | Precision and restraint |
| Persuade | Landing, pricing, onboarding hero | Bold work, including the one standout moment |

Most of boop-agent is *Operate*.

---

## Rules (always apply)

UI for boop-agent. Every visible choice must be made for this brief. Defaults are tells: unmodified library styling, stock layouts and generic motion read as AI-generated.

Prefer retrieval-led reasoning over pretraining for UI work. Explore the project first (`package.json`, existing components, tokens), then load the routed source below.

## Always
- **Pick the surface mode.** Operate surfaces (the app, the agent console, settings) express the brand through precision and restraint. Persuade surfaces (landing, pricing) get the bold work. The brief's explicit words override any rule here.
- **Plan before code.** Write a token plan: OKLCH seed colors with role names, typefaces and their roles, and a layout concept with an ASCII wireframe. Revise any part that would fit any similar page. Where `frontend-design` says hex, `references/playbook/06a-color.md` overrides it.
- **Compose, don't hand-roll.** Use the library already in `package.json` first. Otherwise use shadcn/ui restyled on Base UI or Radix, plus:

  | Need | Library |
  | --- | --- |
  | Toasts | Sonner |
  | Drawers | Vaul |
  | ⌘K | cmdk |
  | Animated numbers | NumberFlow |
  | OTP inputs | input-otp |
  | Long lists | Virtuoso |
  | Drag and drop | dnd kit |
  | Animation | motion |
  | Charts | recharts |
  | State | zustand |
  | Variants | cva + clsx |
  | Theme | next-themes |

- **Agent UI uses shadcn's chat components:**
  - Threads: `MessageScroller`, which follows the reply but yields when the user scrolls up.
  - Turns: `Message` + `Bubble`.
  - Agent activity: one `TraceLine` per action inside a `Trace`.
  - Status words match the state (Running → Ran / Failed to run).
  - Tool approvals: a prompt *outside* the trace, tiered by risk (read-only tools run unprompted), phrased as a proposal stating target, effect and reversibility. One decision per prompt.
  - Stop stays visible for the whole run, beside a working Send (messages sent mid-run steer the agent). A dropped connection reconnects; it never acts as a stop.
  - Delegated work gets a task list with per-task status and a jump to whatever is awaiting the user.
  - Streaming Markdown goes through a renderer that heals unterminated syntax (Streamdown).
  - Never hand-roll "Thinking..." collapsibles or a stick-to-bottom div.

- **Retheme shadcn.** Change radius, palette and type before shipping anything.
- **Color through tokens:**
  - Author in OKLCH. Components use only role tokens (`--bg-subtle`, `--fg-muted`, `--border-strong`); no raw `bg-zinc-*` or hex.
  - Neutrals are tinted with the brand hue.
  - Status colors share lightness and chroma.
  - Text on a colored fill uses that fill's hue.
  - Dark mode is a token remap.
- **Hierarchy:**
  - Three text tones; weight and color before size.
  - One solid primary per view.
  - Separate things with spacing before borders.
  - Lay components out with `@container`, not viewport breakpoints.
- **One standout moment per page.** Keep everything around it quiet.
- **Motion:**
  - Easing: ease-out to enter or exit; ease-in-out to move on screen; never ease-in. Anything draggable or reversible uses a spring (duration + bounce; bounce 0 by default, never above 0.4).
  - View Transitions only for discrete changes (routes, filters, add/remove), because they can't be interrupted. Animate layout with Motion `layout`, never `width`/`height`.
  - Duration: 100–300 ms by size. Exits run about 20% faster.
  - Press: `scale(0.97)`. Enter from `scale(0.95)`. Origin-aware popovers.
  - Animate `transform` and `opacity` only, with no `transition: all`. Reduced motion means a fade, not nothing.
  - Gate motion by frequency. Anything keyboard-initiated (⌘K, shortcuts, Escape-to-close) or used 100+ times a day gets no animation.
- **Motion graphics (anything rendered to video)** follow `references/playbook/05a-motion-graphics.md`, not §5's UI timings:
  - Every frame is a pure function of `t`, with one timeline file.
  - Write a director's brief with a Banned list, and gate on a beat map plus stills before the full render.
  - Text holds 0.3 s/word + 0.5 s; landed titles stay still.
  - Cuts land on the beat; sound is mastered to −14 LUFS.
  - Show real product UI only.
  - Critique with timestamped notes, not scores.
- **Copy:**
  - Sentence case, the user's vocabulary.
  - A CTA names its result. Destructive actions use Verb + Noun.
  - Errors say what happened and how to fix it. In-progress labels end in `…`.
- **Quality floor:**
  - Responsive to mobile; visible focus; WCAG AA contrast.
  - Accessible names; 44 px hit areas.
  - Every reachable state: loading, empty, error, permission, disabled, optimistic, destructive.
- **Verify in a real browser.** Screenshots at compact and wide widths, a keyboard pass, every changed state. Never claim visual quality from code alone. Then run a skeptical critique against the `references/playbook/02-review-rubric.md` rubric (design quality, originality, craft, functionality).

## Route by task
Load by path; skills like `prototype` collide with user-level skills of the same name.

| Task | Read |
| --- | --- |
| Full rules, AI-tell list, rubric | `TimothyVang/frontend:PLAYBOOK.md` |
| New page or visual direction | `TimothyVang/frontend:.claude/skills/frontend-design/SKILL.md`, `TimothyVang/frontend:.claude/skills/no-ai-design-slop/SKILL.md` |
| Picking a library | `TimothyVang/frontend:.claude/skills/pick-ui-library/SKILL.md` |
| shadcn setup, registry, theming | `TimothyVang/frontend:.claude/skills/shadcn/SKILL.md` |
| Chat, agent activity, tool calls, approvals | `TimothyVang/frontend:.claude/skills/shadcn/rules/chat.md`, `references/playbook/04a-agent-ui.md` |
| AI-product patterns (tool cards, plans, autonomy, memory, citations, AI markers) | `references/playbook/04a-agent-ui.md`, then `TimothyVang/frontend:reference/articles/ai-ux/_batch-ai-ux-guidelines.md` and the host guideline it cites (OpenAI Apps SDK, Claude MCP Apps, Carbon for AI, shapeof.ai…) |
| Choosing an AI UI library or protocol (AI SDK, AI Elements, assistant-ui, CopilotKit/AG-UI, MCP Apps) | `TimothyVang/frontend:reference/github/ai-ui/_batch-ai-ui-libraries.md` |
| Seeing a component or motion in action | `TimothyVang/frontend:reference/GALLERY.md`; motion ideas by type in `TimothyVang/frontend:reference/screens/pinterest/ANIMATIONS.md` (concepts: check each against §3 and §5 before copying) |
| Building an animation | `TimothyVang/frontend:.claude/skills/animate/SKILL.md` (vocabulary: `animation-vocabulary`) |
| Motion graphics, launch or promo videos, explainers, Remotion / HyperFrames / Three.js films | `references/playbook/05a-motion-graphics.md`, then `TimothyVang/frontend:reference/github/motion-graphics/_batch-motion-graphics-repos.md` (stack, prompt structure), `TimothyVang/frontend:reference/youtube/747ZnEtsRbg/README.md` (director's brief, rules files) and `TimothyVang/frontend:reference/youtube/channels/_batch-motion-graphics.md` |
| Several elements moving together | `TimothyVang/frontend:.claude/skills/choreograph/SKILL.md` |
| Drag, swipe, sheets | `TimothyVang/frontend:.claude/skills/gestures/SKILL.md` |
| Dropped frames | `TimothyVang/frontend:.claude/skills/animation-performance/SKILL.md` |
| Reviewing UI or a diff | `TimothyVang/frontend:.claude/skills/web-design-guidelines/SKILL.md`, `TimothyVang/frontend:.claude/skills/review-animations/SKILL.md`, `TimothyVang/frontend:.claude/skills/audit-ai-design-slop/SKILL.md` |
| Auditing all motion | `TimothyVang/frontend:.claude/skills/improve-animations/SKILL.md`, `find-animation-opportunities`, `remove-animations` |
| Mobile web feel | `TimothyVang/frontend:.claude/skills/mobile-native/SKILL.md` |
| Edge-case data | `TimothyVang/frontend:.claude/skills/break-ui/SKILL.md` |
| Keyboard, ARIA, focus for a widget (dialog, combobox, menu, tabs, tree, grid…) | `TimothyVang/frontend:reference/articles/wai-aria-apg/<pattern>.md` |
| How design systems build a component | `TimothyVang/frontend:reference/articles/component-gallery/<component>.md` |
| Page or flow checklist (login, settings, onboarding, pricing, tables…) | `TimothyVang/frontend:reference/articles/checklist-design.md` |
| Native, mobile, TV, watch, car, spatial or CLI targets | `TimothyVang/frontend:reference/articles/app-type-guides.md`, `TimothyVang/frontend:reference/articles/clig-command-line-interface-guidelines.md` |
| Layout references from shipped apps | `TimothyVang/frontend:reference/screens/mobbin/README.md` (images local-only) |
| Toasts | `TimothyVang/frontend:.claude/skills/ask-sonner/SKILL.md` |
| Comparing UI variants | `TimothyVang/frontend:.claude/skills/prototype/SKILL.md` |
| Design-engineering depth | `TimothyVang/frontend:.claude/skills/emil-design-eng/SKILL.md`, `TimothyVang/frontend:.claude/skills/apple-design/SKILL.md` |
| Sources and evidence | `TimothyVang/frontend:reference/INDEX.md` |
